"""Node runtime wiring for a local controller process."""

from __future__ import annotations

import os
import secrets
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .app_server import AppServerClient
from .child_control import ChildCoordinator, LocalControlFileClient, LocalControlServer
from .codex import CodexHomeFactory, CodexHomeSpec
from .controller import Controller
from .dynamic_children import ChildDynamicTools
from .effort import AstraEffortSelector
from .gateway import AppServerGateway, GatewayConfig
from .hardware import HardwareService
from .http_transport import HttpPeer, HttpPeerServer
from .pool import InstancePool, ManagedInstance
from .store import SQLiteStore
from .testing import RecordingGateway


@dataclass(frozen=True, slots=True)
class NodeConfig:
    node_id: str
    project_id: str
    state_dir: Path
    default_children: int
    mode: str
    hardware_enabled: bool
    peer_urls: dict[str, str]
    shared_secret_env: str
    deepseek_key_file: Path | None = None
    turn_timeout_seconds: float = 3600.0

    def __post_init__(self) -> None:
        if self.turn_timeout_seconds <= 0:
            raise ValueError("turn_timeout_seconds must be positive")

    @classmethod
    def load(cls, path: str | Path) -> "NodeConfig":
        config_path = Path(path)
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        node_id = str(data["node_id"])
        if node_id not in {"A", "B", "C"}:
            raise ValueError("node_id must be A, B, or C")
        state_dir = Path(data.get("state_dir", f".local/node-{node_id.lower()}"))
        if not state_dir.is_absolute():
            state_dir = config_path.parent / state_dir
        key_file = data.get("deepseek_key_file")
        if key_file:
            key_file = Path(key_file)
            if not key_file.is_absolute():
                key_file = config_path.parent / key_file
        return cls(
            node_id=node_id,
            project_id=str(data.get("project_id", "fpga-main")),
            state_dir=state_dir,
            default_children=int(data.get("default_children", 2)),
            mode=str(data.get("mode", "test_double")),
            hardware_enabled=bool(data.get("hardware_enabled", False)),
            peer_urls={
                str(key): str(value)
                for key, value in data.get("peers", {}).items()
                if value
            },
            shared_secret_env=str(
                data.get("security", {}).get(
                    "secret_env",
                    "FPGA_MESH_SHARED_SECRET",
                )
            ),
            deepseek_key_file=key_file,
            turn_timeout_seconds=float(data.get("turn_timeout_seconds", 3600)),
        )


class NodeRuntime:
    def __init__(self, config: NodeConfig):
        self.config = config
        self.store = SQLiteStore(config.state_dir / "state.sqlite")
        self._recording_gateways: list[RecordingGateway] = []
        self.dynamic_children = ChildDynamicTools(LocalControlFileClient(
            config.state_dir / "child-control.json",
        ))
        self.astra_gateway = self._build_astra_gateway()
        self.controller = Controller(
            self.store, self.astra_gateway,
            on_human_instruction=self._on_human_instruction,
        )
        self.pool = InstancePool(
            node_id=config.node_id,
            gateway=None,
            gateway_factory=(
                self._make_recording_child_gateway
                if config.mode == "test_double"
                else self._make_child_gateway
            ),
            home_factory=CodexHomeFactory(config.state_dir / "homes"),
            state_path=config.state_dir / "pool.json",
        )
        self.children = ChildCoordinator(
            node_id=config.node_id,
            project_id=config.project_id,
            pool=self.pool,
            state_path=config.state_dir / "child_jobs.sqlite",
        )
        self.child_control = LocalControlServer(
            self.children, token=secrets.token_urlsafe(32),
            discovery_path=config.state_dir / "child-control.json",
        )
        self.hardware = (
            HardwareService(config.state_dir / "hardware.sqlite")
            if config.hardware_enabled
            else None
        )
        self.peer: HttpPeer | None = None
        self.peer_server: HttpPeerServer | None = None
        if config.peer_urls and os.environ.get(config.shared_secret_env):
            self.peer = HttpPeer(
                node_id=config.node_id,
                store=self.store,
                controller=self.controller,
                peer_urls=config.peer_urls,
                shared_secret=os.environ[config.shared_secret_env],
            )
            self.peer_server = HttpPeerServer(
                self.peer,
                shared_secret=os.environ[config.shared_secret_env],
            )
        self.started = False

    async def start(self) -> None:
        await self.pool.ensure_standby(self.config.default_children)
        await self.child_control.start()
        if self.peer_server is not None:
            await self.peer_server.start()
        await self.controller.start()
        self.started = True

    async def stop(self) -> None:
        self.started = False
        await self.controller.stop()
        await self.child_control.close()
        await self.children.close()
        await self.pool.close()
        if isinstance(self.astra_gateway, AppServerGateway):
            await self.astra_gateway.close()
        if self.peer_server is not None:
            await self.peer_server.close()
        if self.hardware is not None:
            self.hardware.close()
        self.store.close()

    def snapshot(self) -> dict[str, Any]:
        return {
            "node_id": self.config.node_id,
            "project_id": self.config.project_id,
            "mode": self.config.mode,
            "started": self.started,
            "pool": self.pool.snapshot(),
            "child_jobs": self.children.status()["jobs"],
            "pending_inbound": len(self.store.pending_inbound()),
            "pending_outbox": len(self.store.pending_outbound()),
            "idle_model_calls": sum(
                len(gateway.calls) for gateway in self._recording_gateways
            ),
            "network_enabled": self.peer is not None,
            "hardware_enabled": self.hardware is not None,
            "hardware_queue": self.hardware.queue() if self.hardware else [],
        }

    def astra_tool_config(self) -> dict[str, Any]:
        if self.child_control.port is None:
            raise RuntimeError("child control is not started")
        project_root = Path(__file__).resolve().parent.parent
        return {"mcp_servers": {"fpga_children": {
            "command": sys.executable,
            "args": ["-m", "fpga_mesh.mcp_children"],
            "env": {
                "FPGA_CHILD_CONTROL_FILE": str(
                    self.config.state_dir / "child-control.json"
                ),
                "PYTHONPATH": str(project_root),
            },
            "startup_timeout_sec": 20,
            "tool_timeout_sec": 3600,
        }}}

    def _build_astra_gateway(self):
        if self.config.mode == "test_double":
            gateway = RecordingGateway()
            self._recording_gateways.append(gateway)
            return gateway
        return AppServerGateway(
            GatewayConfig(
                node_id=self.config.node_id,
                role="astra",
                model="gpt-6-astra",
                provider="openai",
                reasoning_effort="max",
                cwd=str(Path.cwd()),
                codex_home=str(Path.home() / ".codex"),
            ),
            client_factory=lambda: AppServerClient.start_stdio(
                codex_home=Path.home() / ".codex",
                client_version="0.159.0",
                role="astra",
            ),
            thread_config_factory=self.astra_tool_config,
            dynamic_tools=self.dynamic_children.specs(),
            dynamic_tool_handler=self.dynamic_children.call,
            effort_selector=AstraEffortSelector(),
            timeout_seconds=self.config.turn_timeout_seconds,
        )

    def _make_child_gateway(self, instance: ManagedInstance):
        gateway = AppServerGateway(
            GatewayConfig(
                node_id=self.config.node_id,
                role="deepseek_child",
                model=instance.model,
                provider="deepseek",
                reasoning_effort=instance.reasoning_effort,
                cwd=str(Path.cwd()),
                codex_home=instance.codex_home,
            ),
            client_factory=lambda: AppServerClient.start_stdio(
                codex_home=instance.codex_home,
                client_version="0.159.0",
                role="deepseek_child",
                extra_env=self._child_secret_env(),
            ),
            timeout_seconds=self.config.turn_timeout_seconds,
        )
        return gateway

    def _child_secret_env(self) -> dict[str, str]:
        if self.config.deepseek_key_file is None:
            return {}
        key = self.config.deepseek_key_file.read_text(encoding="utf-8-sig").strip()
        if not key.startswith("sk-") or "\n" in key or "\r" in key:
            raise RuntimeError("DeepSeek key file is invalid")
        return {"DEEPSEEK_API_KEY": key}

    def _make_recording_child_gateway(self, instance: ManagedInstance):
        gateway = RecordingGateway()
        self._recording_gateways.append(gateway)
        return gateway

    def _on_human_instruction(self, message) -> None:
        self.children.update_task_version(
            message.task_id, message.task_version,
        )
