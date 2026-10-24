"""New Windows-only filesystem tests; all retained artifacts live under author/runs."""
import importlib
import importlib.util
import ctypes
import json
import multiprocessing
import os
import pathlib
import subprocess
import struct
import sys
import tempfile
import unittest
from unittest import mock


def competing_writer(target, payload, channel):
    import layout_commit_windows as leaf

    class Rendezvous(leaf._Operation):
        def _stage(self):
            super()._stage()
            channel.send({"ready": True, "pid": os.getpid(), "source": self.temp_path})
            if not channel.poll(20) or channel.recv() != "publish":
                raise RuntimeError("test rendezvous timed out")

    result = Rendezvous(target, payload).run()
    channel.send({"result": result, "pid": os.getpid()})
    channel.close()


class CommitWindowsTests(unittest.TestCase):
    def setUp(self):
        # Explicit test-only environment keeps released tests independent of
        # this author evidence directory. No source contains an absolute root.
        runs = pathlib.Path(os.environ["LAYOUT_COMMIT_TEST_ROOT"]).resolve(strict=True)
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="t-", dir=runs))

    def record(self, **evidence):
        (self.root / "evidence.json").write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")

    def leaf(self):
        return importlib.import_module("layout_commit_windows")

    def assert_failed_clean(self, result, target):
        self.assertEqual(result["state"], "failed_before_publish", result)
        self.assertFalse(result["ok"], result)
        self.assertFalse(target.exists())
        self.assertEqual(list(self.root.glob(".lc-*.tmp")), [])
        self.assertFalse(result["cleanup"]["orphan_possible"], result)

    def test_empty_new_file_is_committed_and_existing_file_is_preserved(self):
        # Catches publication that overwrites an existing target or claims success early.
        spec = importlib.util.find_spec("layout_commit_windows")
        self.assertIsNotNone(spec, "the retained-HANDLE commit leaf is absent")
        leaf = importlib.import_module("layout_commit_windows")
        target = self.root / "empty.json"
        result = leaf.commit_new(str(target), b"")
        self.assertEqual(result["state"], "committed", result)
        self.assertTrue(result["ok"], result)
        self.assertEqual(target.read_bytes(), b"")
        before = target.stat().st_ino
        collision = leaf.commit_new(str(target), b"must not replace")
        self.assertEqual(collision["state"], "already_exists", collision)
        self.assertFalse(collision["ok"])
        self.assertEqual(target.read_bytes(), b"")
        self.assertEqual(target.stat().st_ino, before)
        self.record(first=result, collision=collision, inode_before=before,
                    inode_after=target.stat().st_ino)

    def test_unicode_and_binary_payload_roundtrip_and_limit(self):
        # Catches wrong UTF-16 byte lengths, payload decoding, or a missing bound.
        leaf = self.leaf()
        parent = self.root / "中文😀"
        parent.mkdir()
        payload = "水层🛠️\u0000红门".encode("utf-8") + bytes(range(256))
        target = parent / "布局🚀.json"
        result = leaf.commit_new(str(target), payload)
        self.assertEqual(result["state"], "committed", result)
        self.assertEqual(target.read_bytes(), payload)
        full = self.root / "one-mib.bin"
        self.assertTrue(leaf.commit_new(str(full), b"x" * 1048576)["ok"])
        self.assertEqual(full.stat().st_size, 1048576)
        oversized = self.root / "over.bin"
        self.assert_failed_clean(leaf.commit_new(str(oversized), b"x" * 1048577), oversized)
        wrong = self.root / "type.bin"
        self.assert_failed_clean(leaf.commit_new(str(wrong), bytearray(b"x")), wrong)
        self.record(result=result, exact_payload_hex=payload.hex())

    def test_two_real_processes_no_replace_race_has_one_complete_winner(self):
        # Catches check-then-replace, shared source names, or incomplete winners.
        target = self.root / "race.bin"
        ctx = multiprocessing.get_context("spawn")
        payloads = [b"A" * 8193, b"B" * 16387]
        children, channels, ready, results = [], [], [], []
        try:
            for payload in payloads:
                parent, child = ctx.Pipe()
                proc = ctx.Process(target=competing_writer, args=(str(target), payload, child))
                proc.start()
                child.close()
                children.append(proc)
                channels.append(parent)
            for channel in channels:
                self.assertTrue(channel.poll(20), "child failed to rendezvous")
                ready.append(channel.recv())
            self.assertTrue(all(item.get("ready") for item in ready), ready)
            self.assertEqual(len({item["pid"] for item in ready}), 2)
            self.assertFalse(target.exists())
            for channel in channels:
                channel.send("publish")
            for channel in channels:
                self.assertTrue(channel.poll(20), "child failed to finish")
                results.append(channel.recv()["result"])
            for proc in children:
                proc.join(20)
                self.assertEqual(proc.exitcode, 0)
            self.assertEqual(sorted(r["state"] for r in results),
                             ["already_exists", "committed"], results)
            winner = next(i for i, r in enumerate(results) if r["ok"])
            self.assertEqual(target.read_bytes(), payloads[winner])
            self.assertEqual(list(self.root.glob(".lc-*.tmp")), [])
            self.record(ready=ready, results=results, winner=winner,
                        process_exitcodes=[p.exitcode for p in children])
        finally:
            for channel in channels:
                channel.close()
            for proc in children:
                if proc.is_alive():
                    proc.terminate()
                    proc.join(10)
                    self.fail("test worker needed termination; inspect retained evidence")

    def test_external_sentinel_created_after_absent_check_keeps_bytes_and_identity(self):
        # Catches replacing a target created by an uncooperative external writer.
        leaf = self.leaf()
        target = self.root / "sentinel.bin"
        self.assertFalse(target.exists())
        original_stage = leaf._Operation._stage
        before = {}

        def stage_then_external_create(op):
            original_stage(op)
            with target.open("xb") as f:
                f.write(b"external sentinel\x00\xff")
            before["ino"] = target.stat().st_ino

        with mock.patch.object(leaf._Operation, "_stage", stage_then_external_create):
            result = leaf.commit_new(str(target), b"caller losing payload")
        self.assertEqual(result["state"], "already_exists", result)
        self.assertEqual(target.read_bytes(), b"external sentinel\x00\xff")
        self.assertEqual(target.stat().st_ino, before["ino"])
        self.assertFalse(result["cleanup"]["orphan_possible"])
        self.record(result=result, inode_before=before["ino"], inode_after=target.stat().st_ino)

    def test_occupied_temp_name_is_not_opened_and_retry_is_bounded(self):
        # Catches temp adoption/truncation and unbounded CREATE_NEW collisions.
        leaf = self.leaf()
        occupied = self.root / (".lc-" + "a" * 32 + ".tmp")
        occupied.write_bytes(b"not owned")
        before = occupied.stat().st_ino
        target = self.root / "occupied.bin"
        with mock.patch.object(leaf.secrets, "token_hex", return_value="a" * 32):
            result = leaf.commit_new(str(target), b"new")
        self.assertEqual(result["state"], "failed_before_publish", result)
        self.assertEqual(result["code"], "temp_names_exhausted", result)
        self.assertEqual(occupied.read_bytes(), b"not owned")
        self.assertEqual(occupied.stat().st_ino, before)
        self.assertFalse(target.exists())
        with mock.patch.object(leaf.secrets, "token_hex", side_effect=["a" * 32, "b" * 32]):
            retried = leaf.commit_new(str(target), b"new")
        self.assertTrue(retried["ok"], retried)
        self.assertEqual(occupied.read_bytes(), b"not owned")
        self.record(exhausted=result, then_new_name=retried, occupied_inode=before)

    def test_retained_source_denies_external_truncate_delete_and_ancestor_rename(self):
        # Catches closing/reopening the source or releasing ancestry too early.
        leaf = self.leaf()
        parent = self.root / "ordinary"
        parent.mkdir()
        target = parent / "owned.bin"
        original_stage = leaf._Operation._stage
        denied = {}

        def stage_then_external_attempts(op):
            original_stage(op)
            for name, action in [
                ("truncate", lambda: op.api.create(op.temp_path, 0x40000000, 7, 5, 0x80)),
                ("delete", lambda: os.unlink(op.temp_path)),
                ("rename_parent", lambda: os.rename(parent, self.root / "moved")),
            ]:
                try:
                    unexpected = action()
                    if hasattr(unexpected, "close"):
                        unexpected.close()
                    elif name == "truncate":
                        op.api.close(unexpected)
                    denied[name] = "unexpected_success"
                except leaf._Failure as exc:
                    denied[name] = exc.winerror
                except OSError as exc:
                    denied[name] = exc.winerror

        with mock.patch.object(leaf._Operation, "_stage", stage_then_external_attempts):
            result = leaf.commit_new(str(target), b"original retained bytes")
        self.assertTrue(result["ok"], result)
        self.assertTrue(all(isinstance(x, int) for x in denied.values()), denied)
        self.assertEqual(len(denied), 3)
        self.assertEqual(target.read_bytes(), b"original retained bytes")
        self.record(result=result, actual_win32_denials=denied)

    def test_preexisting_write_handle_on_ancestor_fails_closed(self):
        # Catches accepting mutable ancestry when a write-sharing conflict exists.
        leaf = self.leaf()
        api = leaf._Api()
        parent = self.root / "busy"
        parent.mkdir()
        target = parent / "x"
        handle = api.create(str(parent), 0x40000000, 7, 3, 0x02000000)
        try:
            result = leaf.commit_new(str(target), b"x")
        finally:
            api.close(handle)
        self.assertEqual(result["state"], "failed_before_publish", result)
        self.assertEqual(result.get("winerror"), 32, result)
        self.assertFalse(target.exists())
        self.record(actual_directory_write_sharing_conflict=result)

    def test_handover_keeps_owned_parent_and_ancestor_nonempty_and_unredirectable(self):
        # Catches opening ancestry for writes before its children/source are pinned.
        leaf = self.leaf()
        holder = self.root / "holder"
        parent = holder / "parent"
        parent.mkdir(parents=True)
        redirect = self.root / "redirect"
        redirect.mkdir()
        target = parent / "new.bin"
        original_stage = leaf._Operation._stage
        attempts = []

        def stage_then_try_reparse(op):
            original_stage(op)
            for path in (parent, holder):
                attempt = {"path": str(path)}
                attempts.append(attempt)
                try:
                    handle = op.api.create(str(path), 0x40000000, 3, 3, 0x02200000)
                    attempt["write_open_error"] = None
                except leaf._Failure as exc:
                    attempt["write_open_error"] = exc.winerror
                    continue
                try:
                    substitute = ("\\??\\" + str(redirect)).encode("utf-16-le")
                    printed = str(redirect).encode("utf-16-le")
                    names = substitute + b"\0\0" + printed + b"\0\0"
                    raw = struct.pack("<LHHHHHH", 0xa0000003, 8 + len(names), 0,
                                      0, len(substitute), len(substitute) + 2, len(printed)) + names
                    buffer = ctypes.create_string_buffer(raw)
                    returned = leaf.W.DWORD()
                    native = op.api.k.DeviceIoControl
                    native.argtypes = [leaf.W.HANDLE, leaf.W.DWORD, ctypes.c_void_p, leaf.W.DWORD,
                                       ctypes.c_void_p, leaf.W.DWORD,
                                       ctypes.POINTER(leaf.W.DWORD), ctypes.c_void_p]
                    native.restype = leaf.W.BOOL
                    ok = native(handle, 0x900a4, buffer, len(raw), None, 0,
                                ctypes.byref(returned), None)
                    attempt["reparse_bool"] = bool(ok)
                    attempt["reparse_error"] = None if ok else ctypes.get_last_error()
                    if ok:
                        raise RuntimeError("unexpected owned-directory redirect; do not publish")
                finally:
                    op.api.close(handle)

        with mock.patch.object(leaf._Operation, "_stage", stage_then_try_reparse):
            result = leaf.commit_new(str(target), b"protected handover")
        self.assertEqual([x["write_open_error"] for x in attempts], [None, None], attempts)
        self.assertEqual([x["reparse_error"] for x in attempts], [145, 145], attempts)
        self.assertTrue(result["ok"], result)
        self.assertEqual(target.read_bytes(), b"protected handover")
        self.assertEqual(list(redirect.iterdir()), [])
        self.record(result=result, actual_owned_directory_reparse_attempts=attempts)

    def test_directory_target_collision_keeps_directory_and_cleans_source(self):
        leaf = self.leaf()
        target = self.root / "directory"
        target.mkdir()
        marker = target / "keep"
        marker.write_bytes(b"directory contents")
        inode = target.stat().st_ino
        result = leaf.commit_new(str(target), b"cannot replace dir")
        self.assertIn(result["state"], ["already_exists", "failed_before_publish"], result)
        self.assertEqual(target.stat().st_ino, inode)
        self.assertEqual(marker.read_bytes(), b"directory contents")
        self.assertEqual(list(self.root.glob(".lc-*.tmp")), [])
        self.record(result=result, directory_inode=inode)

    def test_rejects_namespace_aliases_and_missing_parent_without_creating_files(self):
        # Catches normalization before validation or accepting unsupported namespaces.
        leaf = self.leaf()
        base = str(self.root)
        bad = ["relative.bin", "C:relative.bin", "\\\\server\\share\\x",
               "\\\\?\\" + base + "\\x", "\\\\.\\C:\\x", "\\??\\C:\\x",
               base + "\\x:stream", base + "\\..\\x", base + "\\.\\x",
               base + "\\x.", base + "\\x ", base + "\\CON.txt", base + "\\NUL",
               base + "\\COM¹.txt", base + "\\LPT9", base + "\\a<b", base + "\\a?b",
               base + "\\a\x00b", base + "\\a\x01b", base + "\\\ud800",
               base + "\\" + "z" * 260, base + "\\\\x", base + "/x"]
        outcomes = []
        for value in bad:
            with self.subTest(path=repr(value)):
                result = leaf.commit_new(value, b"x")
                self.assertEqual(result["state"], "failed_before_publish", result)
                self.assertEqual(result["code"], "invalid_path", result)
                outcomes.append({"path": repr(value), "state": result["state"], "code": result["code"]})
        missing = self.root / "missing" / "x"
        result = leaf.commit_new(str(missing), b"x")
        self.assertEqual(result["state"], "failed_before_publish", result)
        self.assertFalse(missing.parent.exists())
        self.assertEqual(list(self.root.iterdir()), [])
        self.record(rejected=outcomes, missing_parent=result)

    def test_actual_junction_ancestry_is_rejected(self):
        # Catches following a preexisting reparse parent into another location.
        leaf = self.leaf()
        real = self.root / "real"
        link = self.root / "junction"
        real.mkdir()
        # cmd is used only to CREATE this local junction; no cmd deletion/move.
        proc = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(real)],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        result = leaf.commit_new(str(link / "x"), b"never follow")
        self.assertEqual(result["state"], "failed_before_publish", result)
        self.assertEqual(result["code"], "reparse_ancestor", result)
        self.assertEqual(list(real.iterdir()), [])
        self.record(result=result, junction_create_exit=proc.returncode,
                    junction_create_stdout=proc.stdout)

    def test_actual_write_and_rename_api_failure_clean_owned_source(self):
        # Actual OS errors, not synthetic success/error values.
        leaf = self.leaf()
        write = leaf._Api.write
        rename = leaf._Api.rename
        target = self.root / "real-errors.bin"

        def real_bad_write(api, handle, payload):
            return write(api, ctypes.c_void_p(-1).value, payload)

        with mock.patch.object(leaf._Api, "write", real_bad_write):
            write_result = leaf.commit_new(str(target), b"x")
        self.assert_failed_clean(write_result, target)
        self.assertEqual(write_result.get("winerror"), 6, write_result)

        def real_bad_rename(api, handle, target):
            return rename(api, handle, str(self.root / "absent-subdirectory" / "x"))

        with mock.patch.object(leaf._Api, "rename", real_bad_rename):
            rename_result = leaf.commit_new(str(target), b"x")
        self.assert_failed_clean(rename_result, target)
        self.assertIsInstance(rename_result.get("winerror"), int)
        self.record(actual_os_error_with_injected_invalid_argument={
            "write": write_result, "rename": rename_result})

    def test_injected_short_write_flush_and_readback_fail_before_publish(self):
        # Explicit software fault injection; these are not physical OS faults.
        leaf = self.leaf()
        target = self.root / "injected.bin"
        outcomes = {}

        real_write = leaf._Api.write

        def short_write(api, handle, payload):
            native_write = api.k.WriteFile

            def report_short_count(*args):
                ok = native_write(*args)  # actual bytes are written once
                if ok:
                    ctypes.cast(args[3], ctypes.POINTER(leaf.W.DWORD)).contents.value = len(payload) - 1
                return ok

            with mock.patch.object(api.k, "WriteFile", report_short_count):
                return real_write(api, handle, payload)

        def flush_error(api, handle):
            raise leaf._Failure("flush_failed", 1117)

        for name, method, replacement in [
            ("short_write", "write", short_write),
            ("flush_failure", "flush", flush_error),
            ("readback_mismatch", "read", lambda *args: b"wrong"),
            ("readback_extra", "read", lambda api, handle, count: b"X" if count == 1 else b"payload"),
        ]:
            with self.subTest(injection=name):
                with mock.patch.object(leaf._Api, method, replacement):
                    result = leaf.commit_new(str(target), b"payload")
                self.assert_failed_clean(result, target)
                outcomes[name] = result
        self.record(software_fault_injections=outcomes)

    def test_injected_uncertain_call_before_native_does_not_delete_or_replay(self):
        # Unknown call boundary may leave the original temp; preserve its identity.
        leaf = self.leaf()
        target = self.root / "uncertain.bin"

        def response_unknown(api, handle, target):
            raise RuntimeError("software injection at rename call boundary")

        with mock.patch.object(leaf._Api, "rename", response_unknown):
            op = leaf._Operation(str(target), b"uncertain source")
            result = op.run()
            again = op.run()
        self.assertEqual(result["state"], "outcome_unknown", result)
        self.assertEqual(again, result)
        self.assertFalse(target.exists())
        self.assertFalse(result["cleanup"]["attempted"])
        orphan = pathlib.Path(result["cleanup"]["source_path_at_creation"])
        self.assertEqual(orphan.read_bytes(), b"uncertain source")
        self.assertEqual(orphan.stat().st_ino, result["cleanup"]["identity"]["file_index"])
        self.record(software_call_boundary_fault=result, retained_source=str(orphan))

    def test_injected_close_response_after_real_success_keeps_published_file(self):
        # Close uncertainty after publication must not become pre-publish failure.
        leaf = self.leaf()
        target = self.root / "close-response.bin"
        real_close = leaf._Api.close
        real_publish = leaf._Operation._publish
        first = [True]
        published = [False]

        def publish_then_flag(op):
            real_publish(op)
            published[0] = op.publication_confirmed

        def close_then_response_lost(api, handle):
            real_close(api, handle)
            if first[0] and published[0]:
                first[0] = False
                raise leaf._Failure("close_failed", 6)

        with mock.patch.object(leaf._Api, "close", close_then_response_lost), \
                mock.patch.object(leaf._Operation, "_publish", publish_then_flag):
            result = leaf.commit_new(str(target), b"keep after close")
        self.assertEqual(result["state"], "outcome_unknown", result)
        self.assertTrue(result["publication_confirmed"], result)
        self.assertFalse(result["cleanup"]["attempted"])
        self.assertEqual(target.read_bytes(), b"keep after close")
        self.record(real_close_then_software_response_fault=result)

    def test_windows_abi_and_noninherited_source_handle(self):
        # Catches pointer truncation, duplicate union fields, or inherited ownership.
        leaf = self.leaf()
        offsets = (leaf._RenameInfo.RootDirectory.offset,
                   leaf._RenameInfo.FileNameLength.offset, leaf._RenameInfo.FileName.offset)
        self.assertEqual(offsets, (8, 16, 20) if ctypes.sizeof(ctypes.c_void_p) == 8 else (4, 8, 12))
        original_stage = leaf._Operation._stage
        flags = leaf.W.DWORD(0xffffffff)

        def stage_then_handle_flag_check(op):
            original_stage(op)
            native = op.api.k.GetHandleInformation
            native.argtypes = [leaf.W.HANDLE, ctypes.POINTER(leaf.W.DWORD)]
            native.restype = leaf.W.BOOL
            self.assertTrue(native(op.handle, ctypes.byref(flags)))

        with mock.patch.object(leaf._Operation, "_stage", stage_then_handle_flag_check), \
                mock.patch.object(leaf._Api, "rename", side_effect=RuntimeError("test-only stage boundary")):
            result = leaf.commit_new(str(self.root / "abi.bin"), b"noninherited")
        self.assertEqual(flags.value & 1, 0)
        self.assertEqual(result["state"], "outcome_unknown", result)
        self.record(pointer_bytes=ctypes.sizeof(ctypes.c_void_p), offsets=offsets,
                    source_handle_flags=flags.value, retained_unknown_source=result)

    def test_injected_lost_response_after_real_publish_is_unknown_and_not_replayed(self):
        # Real successful rename followed by a synthetic lost wrapper response.
        leaf = self.leaf()
        target = self.root / "response.bin"
        real_rename = leaf._Api.rename
        publications = []

        def published_then_response_lost(api, handle, target):
            real_rename(api, handle, target)
            publications.append("actual_SetFileInformationByHandle_success")
            raise RuntimeError("injected response loss after OS success")

        with mock.patch.object(leaf._Api, "rename", published_then_response_lost):
            op = leaf._Operation(str(target), b"actually published")
            result = op.run()
            repeated_private_run = op.run()
        self.assertEqual(result["state"], "outcome_unknown", result)
        self.assertFalse(result["ok"])
        self.assertEqual(target.read_bytes(), b"actually published")
        self.assertEqual(publications, ["actual_SetFileInformationByHandle_success"])
        self.assertEqual(repeated_private_run, result)
        self.assertFalse(result["cleanup"]["attempted"])
        self.record(real_success_then_software_response_loss=result,
                    native_success_evidence=publications,
                    repeated_private_run=repeated_private_run)

    def test_injected_cleanup_failure_reports_retained_orphan_identity(self):
        leaf = self.leaf()
        target = self.root / "cleanup.bin"

        def bad_flush(api, handle):
            raise leaf._Failure("flush_failed", 1117)

        def bad_dispose(api, handle):
            raise leaf._Failure("disposition_failed", 5)

        with mock.patch.object(leaf._Api, "flush", bad_flush), \
                mock.patch.object(leaf._Api, "dispose", bad_dispose):
            result = leaf.commit_new(str(target), b"owned orphan")
        self.assertEqual(result["state"], "failed_before_publish", result)
        self.assertTrue(result["cleanup"]["orphan_possible"], result)
        orphan = pathlib.Path(result["cleanup"]["source_path_at_creation"])
        self.assertEqual(orphan.read_bytes(), b"owned orphan")
        self.assertEqual(orphan.stat().st_ino, result["cleanup"]["identity"]["file_index"])
        self.assertFalse(target.exists())
        # The orphan remains preserved as evidence; tests do not sweep/adopt it.
        self.record(software_cleanup_fault=result, retained_orphan=str(orphan))

    def test_import_has_no_file_or_native_library_io(self):
        # Catches accidental native load, output creation, or service startup at import.
        script = """
import ctypes, sys
def forbidden(*args, **kwargs):
    raise AssertionError('import performed native I/O')
ctypes.WinDLL = forbidden
def audit(event, args):
    if event in ('os.mkdir', 'os.remove', 'os.rename', 'subprocess.Popen', 'socket.connect'):
        raise AssertionError('import side effect: ' + event)
sys.addaudithook(audit)
import layout_commit_windows
print('import_without_native_or_filesystem_mutation')
"""
        proc = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", script],
                              cwd=pathlib.Path(__file__).parent, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.record(exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
