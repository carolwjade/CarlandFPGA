import json
import tempfile
import tomllib
import unittest
from pathlib import Path

from fpga_mesh.codex import (
    CodexHomeFactory,
    CodexHomeSpec,
    RouteGuard,
    RouteViolation,
)


class CodexHomeFactoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.factory = CodexHomeFactory(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_astra_home_matches_the_main_model_without_deepseek_provider(self):
        path = self.factory.create(
            CodexHomeSpec.astra(node_id="A", login_mode="chatgpt")
        )
        config = tomllib.loads((path / "config.toml").read_text(encoding="utf-8"))

        self.assertEqual(config["model"], "gpt-6-astra")
        self.assertNotEqual(config.get("model_provider"), "deepseek")
        self.assertFalse((path / "auth.json").exists())

    def test_child_home_explicitly_pins_deepseek_flash_and_max(self):
        path = self.factory.create(
            CodexHomeSpec.deepseek_child(node_id="A", instance_id="deepseek-a-1")
        )
        config = tomllib.loads((path / "config.toml").read_text(encoding="utf-8"))
        models = json.loads((path / "models.json").read_text(encoding="utf-8"))

        self.assertEqual(config["model"], "deepseek-flash")
        self.assertEqual(config["model_reasoning_effort"], "max")
        self.assertEqual(config["model_provider"], "deepseek")
        provider = config["model_providers"]["deepseek"]
        self.assertEqual(provider["base_url"], "https://api.deepseek.com")
        self.assertEqual(provider["env_key"], "DEEPSEEK_API_KEY")
        self.assertEqual(provider["wire_api"], "responses")
        self.assertEqual(
            {model["slug"] for model in models["models"]},
            {"deepseek-flash"},
        )

    def test_home_factory_does_not_write_credentials(self):
        path = self.factory.create(
            CodexHomeSpec.deepseek_child(node_id="B", instance_id="deepseek-b-1")
        )
        config_text = (path / "config.toml").read_text(encoding="utf-8")
        self.assertNotIn("sk-", config_text)
        self.assertFalse((path / "auth.json").exists())

    def test_route_guard_rejects_wrong_model_provider_or_effort(self):
        guard = RouteGuard()
        guard.assert_child_request(
            model="deepseek-flash",
            provider="deepseek",
            effort="max",
        )
        for model, provider, effort in (
            ("deepseek-v4-pro", "deepseek", "max"),
            ("deepseek-flash", "openai", "max"),
            ("deepseek-flash", "deepseek", "high"),
        ):
            with self.assertRaises(RouteViolation):
                guard.assert_child_request(
                    model=model,
                    provider=provider,
                    effort=effort,
                )


if __name__ == "__main__":
    unittest.main()
