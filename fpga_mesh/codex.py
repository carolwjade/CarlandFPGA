"""Codex home isolation and route guardrails."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


class RouteViolation(RuntimeError):
    """Raised before an unapproved model/provider/effort combination is sent."""


@dataclass(frozen=True, slots=True)
class CodexHomeSpec:
    role: Literal["astra", "deepseek_child"]
    node_id: str
    name: str
    login_mode: str
    model: str
    reasoning_effort: str | None = None
    provider: str | None = None

    @classmethod
    def astra(cls, *, node_id: str, login_mode: str = "chatgpt") -> "CodexHomeSpec":
        if node_id not in {"A", "B", "C"}:
            raise ValueError("node_id must be A, B, or C")
        return cls(
            role="astra",
            node_id=node_id,
            name=f"{node_id}-astra",
            login_mode=login_mode,
            model="gpt-6-astra",
            provider=None,
        )

    @classmethod
    def deepseek_child(
        cls,
        *,
        node_id: str,
        instance_id: str,
    ) -> "CodexHomeSpec":
        if node_id not in {"A", "B", "C"}:
            raise ValueError("node_id must be A, B, or C")
        if not instance_id:
            raise ValueError("instance_id is required")
        return cls(
            role="deepseek_child",
            node_id=node_id,
            name=instance_id,
            login_mode="api_key",
            model="deepseek-flash",
            reasoning_effort="max",
            provider="deepseek",
        )


class CodexHomeFactory:
    """Create isolated, non-secret configuration homes."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, spec: CodexHomeSpec) -> Path:
        home = self.root / spec.name
        home.mkdir(parents=True, exist_ok=True)
        if spec.role == "astra":
            self._write_astra_config(home, spec)
        else:
            self._write_deepseek_config(home, spec)
        return home

    def _write_astra_config(self, home: Path, spec: CodexHomeSpec) -> None:
        text = (
            f'model = "{spec.model}"\n'
            f'# Login mode: {spec.login_mode}; complete the official login manually.\n'
        )
        (home / "config.toml").write_text(text, encoding="utf-8", newline="\n")

    def _write_deepseek_config(self, home: Path, spec: CodexHomeSpec) -> None:
        text = (
            f'model = "{spec.model}"\n'
            'model_provider = "deepseek"\n'
            f'model_reasoning_effort = "{spec.reasoning_effort}"\n'
            "\n"
            "[model_providers.deepseek]\n"
            'name = "DeepSeek"\n'
            'base_url = "https://api.deepseek.com"\n'
            'env_key = "DEEPSEEK_API_KEY"\n'
            'wire_api = "responses"\n'
            "requires_openai_auth = false\n"
            "supports_websockets = false\n"
        )
        (home / "config.toml").write_text(text, encoding="utf-8", newline="\n")
        model_entry = {
            "slug": "deepseek-flash",
            "display_name": "DeepSeek V4.1 Flash",
            "description": "DeepSeek V4.1 Flash via the Responses API.",
            "context_window": 1048576,
            "max_context_window": 1048576,
            "default_reasoning_level": "high",
            "supported_reasoning_levels": [
                {"effort": "low", "description": "Fast responses"},
                {"effort": "high", "description": "Extra reasoning depth"},
                {"effort": "max", "description": "Maximum reasoning depth"},
            ],
            "input_modalities": ["text", "image"],
            "supports_image_detail_original": True,
            "supports_parallel_tool_calls": True,
            "use_responses_lite": False,
            "apply_patch_tool_type": "freeform",
            "shell_type": "shell_command",
            "visibility": "list",
            "supported_in_api": True,
            "prefer_websockets": False,
        }
        (home / "models.json").write_text(
            json.dumps({"models": [model_entry]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )


class RouteGuard:
    """Fail closed when a child call is not the specified DeepSeek route."""

    def assert_child_request(
        self,
        *,
        model: str,
        provider: str,
        effort: str,
    ) -> None:
        actual = (model, provider, effort)
        expected = ("deepseek-flash", "deepseek", "max")
        if actual != expected:
            raise RouteViolation(
                f"child route must be {expected}, got {actual}"
            )

    def assert_deepseek_config(self, config: dict) -> None:
        self.assert_child_request(
            model=str(config.get("model", "")),
            provider=str(config.get("model_provider", "")),
            effort=str(config.get("model_reasoning_effort", "")),
        )
