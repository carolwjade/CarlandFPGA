"""Desired recovery invariant; these negatives expose an unclosed PR28 path.

No executables run. Source/cache bundles consist only of harmless fixture bytes.
"""
from pathlib import Path
import tempfile
import unittest

from fpga_mesh.app_server import resolve_codex_command


class CachedRuntimeRelaunchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.bundle=self.root/'OpenAI/Codex/bin/release'
        self.bundle.mkdir(parents=True)
        self.binary=self.bundle/'codex.exe'
        self.host=self.bundle/'codex-code-mode-host.exe'
        self.binary.write_bytes(b'fixture-official-binary-not-executable')
        self.host.write_bytes(b'fixture-matching-code-mode-host')
        self.cache=self.root/'state/codex-runtime'

    def test_explicit_source_cleanup_does_not_strand_a_verified_cache(self):
        first=resolve_codex_command(platform='win32',explicit=self.binary,
                                    runtime_cache_dir=self.cache)
        self.assertNotEqual(Path(first[0]).parent,self.bundle)
        self.host.unlink()  # Desktop removes host beside the original source.
        self.assertTrue(Path(first[0]).is_file())
        self.assertTrue((Path(first[0]).parent/'codex-code-mode-host.exe').is_file())
        try:
            second=resolve_codex_command(platform='win32',explicit=self.binary,
                                         runtime_cache_dir=self.cache)
        except FileNotFoundError as exc:
            self.fail(f'Intact verified cache was stranded by original-source cleanup: {exc}')
        self.assertEqual(second,first)

    def test_auto_source_cleanup_does_not_fall_back_to_unpinned_shim(self):
        first=resolve_codex_command(platform='win32',local_appdata=self.root,
                                    runtime_cache_dir=self.cache)
        self.host.unlink()
        self.assertTrue((Path(first[0]).parent/'codex-code-mode-host.exe').is_file())
        second=resolve_codex_command(platform='win32',local_appdata=self.root,
                                     runtime_cache_dir=self.cache)
        self.assertEqual(second,first)


if __name__=='__main__': unittest.main(verbosity=2)
