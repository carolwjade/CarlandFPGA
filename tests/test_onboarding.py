import tempfile
import unittest
from pathlib import Path

from fpga_mesh.onboarding import OnboardingInputs, reuse_local_settings, write_node_config
from fpga_mesh.runtime import NodeConfig


class OnboardingTests(unittest.TestCase):
    def test_config_uses_local_secret_paths_and_all_peer_urls(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            key = root / "deepseek-key.txt"
            key.write_text("sk-test-only", encoding="utf-8")
            shared = root / "mesh-secret.txt"
            shared.write_text("test-mesh-secret", encoding="utf-8")
            config_path = root / "node-b.toml"
            write_node_config(config_path, OnboardingInputs(
                node="B", deepseek_key_file=key,
                shared_secret_file=shared,
                bind_host="100.64.0.2",
                peer_urls={"A": "http://100.64.0.1:8787",
                           "C": "http://100.64.0.3:8787"},
                group_id="oc_team", astra_app_id="cli_astra_b",
                astra_secret_file=root / "astra-secret.txt",
                deepseek_app_id="cli_deepseek_b",
                deepseek_secret_file=root / "deepseek-secret.txt",
            ))
            text = config_path.read_text(encoding="utf-8")
            self.assertNotIn("sk-test-only", text)
            self.assertNotIn("test-mesh-secret", text)
            config = NodeConfig.load(config_path)
            self.assertEqual(config.node_id, "B")
            self.assertEqual(config.peer_bind_host, "100.64.0.2")
            self.assertEqual(len(config.peer_urls), 2)
            self.assertTrue(config.feishu_enabled)
            self.assertEqual(config.peer_shared_secret_file, shared)

    def test_missing_group_or_bot_keeps_feishu_disabled(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_path = root / "node-c.toml"
            write_node_config(config_path, OnboardingInputs(node="C"))
            config = NodeConfig.load(config_path)
            self.assertFalse(config.feishu_enabled)
            self.assertIsNone(config.deepseek_key_file)
            self.assertIsNone(config.peer_shared_secret_file)
            self.assertEqual(config.peer_urls, {})

    def test_wrong_node_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "node"):
                write_node_config(Path(temp) / "config.toml",
                                  OnboardingInputs(node="D"))

    def test_retry_keeps_local_key_and_peer_settings_without_reentering_them(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_path = root / "node-b.toml"
            first = OnboardingInputs(
                node="B", deepseek_key_file=root / "key.txt",
                shared_secret_file=root / "shared.txt", bind_host="100.64.0.2",
                peer_urls={"A": "http://100.64.0.1:8787"},
            )
            write_node_config(config_path, first)
            retry = reuse_local_settings(config_path, OnboardingInputs(
                node="B", bind_host="", peer_urls={"C": "http://100.64.0.3:8787"},
            ))
            self.assertEqual(retry.deepseek_key_file, first.deepseek_key_file)
            self.assertEqual(retry.shared_secret_file, first.shared_secret_file)
            self.assertEqual(retry.bind_host, first.bind_host)
            self.assertEqual(retry.peer_urls, {
                "A": "http://100.64.0.1:8787", "C": "http://100.64.0.3:8787",
            })
