"""Dynamic, non-reusing child instance pool."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

from .codex import CodexHomeFactory, CodexHomeSpec
from .controller import ActionResult
from .protocol import ChildInstance, Envelope


class Gateway(Protocol):
    async def handle(self, message: Envelope) -> ActionResult:
        ...


@dataclass(slots=True)
class ManagedInstance:
    instance_id: str
    node_id: str
    model: str
    reasoning_effort: str
    generation: int
    state: str
    codex_home: str
    created_at: str

    @classmethod
    def from_child(
        cls,
        instance: ChildInstance,
        codex_home: str,
        generation: int,
    ) -> "ManagedInstance":
        return cls(
            instance_id=instance.instance_id,
            node_id=instance.node_id,
            model=instance.model,
            reasoning_effort=instance.reasoning_effort,
            generation=generation,
            state=instance.state,
            codex_home=codex_home,
            created_at=datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        )


class InstancePool:
    """Persist the pool independently of model execution."""

    def __init__(
        self,
        *,
        node_id: str,
        gateway: Gateway | None = None,
        gateway_factory: Callable[[ManagedInstance], Gateway] | None = None,
        home_factory: CodexHomeFactory,
        state_path: str | Path,
    ):
        if node_id not in {"A", "B", "C"}:
            raise ValueError("node_id must be A, B, or C")
        self.node_id = node_id
        self.gateway = gateway
        self.gateway_factory = gateway_factory
        self.home_factory = home_factory
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._next_sequence = 1
        self._active: dict[str, ManagedInstance] = {}
        self._retired: set[str] = set()
        self._gateways: dict[str, Gateway] = {}
        self._allocation_lock = asyncio.Lock()
        self._load()

    async def ensure_standby(self, count: int) -> None:
        async with self._allocation_lock:
            self._ensure_standby_unlocked(count)

    def _ensure_standby_unlocked(self, count: int) -> None:
        if count < 0:
            raise ValueError("count must not be negative")
        while len(self._active) < count:
            self._create_one()
        self._save()

    async def scale_to(self, count: int) -> None:
        async with self._allocation_lock:
            await self._scale_to_unlocked(count)

    async def _scale_to_unlocked(self, count: int) -> None:
        if count < 0:
            raise ValueError("count must not be negative")
        if count < len(self._active):
            standby = [instance_id for instance_id, instance in self._active.items()
                       if instance.state == "standby"]
            to_reap = len(self._active) - count
            if len(standby) < to_reap:
                raise RuntimeError("cannot scale below the number of assigned children")
            for instance_id in standby[-to_reap:]:
                await self._reap_unlocked(instance_id)
        else:
            self._ensure_standby_unlocked(count)

    async def close(self) -> None:
        gateways = list(self._gateways.values())
        self._gateways.clear()
        for gateway in gateways:
            if hasattr(gateway, "close"):
                await gateway.close()

    async def reap(self, instance_id: str) -> None:
        async with self._allocation_lock:
            await self._reap_unlocked(instance_id)

    async def _reap_unlocked(self, instance_id: str) -> None:
        instance = self._ensure_active(instance_id)
        if instance.state != "standby":
            raise RuntimeError("cannot reap a non-standby child")
        self._active.pop(instance_id)
        self._retired.add(instance_id)
        gateway = self._gateways.pop(instance_id, None)
        self._save()
        if gateway is not None and hasattr(gateway, "close"):
            await gateway.close()

    async def reserve(self, instance_id: str) -> None:
        async with self._allocation_lock:
            instance = self._ensure_active(instance_id)
            if instance.state != "standby":
                raise RuntimeError("child is already assigned")
            instance.state = "reserved"
            self._save()

    async def wake(self, instance_id: str, message: Envelope) -> ActionResult:
        instance = self._ensure_active(instance_id)
        if instance.state not in {"standby", "reserved"}:
            raise RuntimeError("child is already working")
        if instance.model != "deepseek-flash" or instance.reasoning_effort != "max":
            raise RuntimeError(f"instance {instance_id} is not route-compliant")
        instance.state = "working"
        self._save()
        result = await self._gateway_for(instance).handle(message)
        return result

    async def return_to_standby(self, instance_id: str) -> None:
        instance = self._ensure_active(instance_id)
        instance.state = "standby"
        self._save()

    def snapshot(self) -> dict[str, Any]:
        instances = [asdict(item) for item in self._active.values()]
        counts: dict[str, int] = {}
        for item in instances:
            counts[item["state"]] = counts.get(item["state"], 0) + 1
        return {
            "node_id": self.node_id,
            "instances": instances,
            "retired_ids": sorted(self._retired),
            **counts,
        }

    def _create_one(self) -> ManagedInstance:
        instance_id = f"deepseek-{self.node_id.lower()}-{self._next_sequence}"
        self._next_sequence += 1
        child = ChildInstance(
            instance_id=instance_id,
            node_id=self.node_id,
            model="deepseek-flash",
            reasoning_effort="max",
            state="standby",
        )
        home = self.home_factory.create(
            CodexHomeSpec.deepseek_child(
                node_id=self.node_id,
                instance_id=instance_id,
            )
        )
        managed = ManagedInstance.from_child(
            child,
            codex_home=str(home),
            generation=child.generation,
        )
        self._active[instance_id] = managed
        return managed

    def _ensure_active(self, instance_id: str) -> ManagedInstance:
        try:
            return self._active[instance_id]
        except KeyError as exc:
            raise KeyError(f"instance is not active: {instance_id}") from exc

    def _gateway_for(self, instance: ManagedInstance) -> Gateway:
        gateway = self._gateways.get(instance.instance_id)
        if gateway is not None:
            return gateway
        if self.gateway_factory is not None:
            gateway = self.gateway_factory(instance)
        elif self.gateway is not None:
            gateway = self.gateway
        else:
            raise RuntimeError("no gateway configured for child instance")
        self._gateways[instance.instance_id] = gateway
        return gateway

    def _load(self) -> None:
        if not self.state_path.exists():
            return
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        self._next_sequence = int(data.get("next_sequence", 1))
        self._retired = set(data.get("retired_ids", []))
        for item in data.get("instances", []):
            if item["state"] != "standby":
                # A prior process died while this instance was assigned. Keep
                # its identity retired so a late result cannot enter a new job.
                self._retired.add(item["instance_id"])
                continue
            self._active[item["instance_id"]] = ManagedInstance(**item)

    def _save(self) -> None:
        data = {
            "node_id": self.node_id,
            "next_sequence": self._next_sequence,
            "instances": [asdict(item) for item in self._active.values()],
            "retired_ids": sorted(self._retired),
        }
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, self.state_path)
