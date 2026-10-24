"""One viewer-private DLC1 request, one checked Windows leaf call, one DLR1 result.

The caller binds this file and its fixed sibling through an explicitly pinned
bundle. Layout bytes are opaque data. There is no provider/control registration,
retry, path cleanup, or external process operation here.
"""
import os
import threading

# Start before bundle/leaf loading or any stdin read. A trusted bootstrap may
# already own the same timer. Never cancel it while this process is alive.
if "_layout_watchdog" not in globals():
    _layout_watchdog = threading.Timer(6.0, lambda: os._exit(124))
    _layout_watchdog.daemon = True
    _layout_watchdog.start()

import hashlib
import json
import re
import struct
import sys

_PROTOCOL = "deepeye-layout-commit/1"
_LEAF_SHA256 = "521cfcea011d462b4b69641f33fbb6f3f7baca16eac7bb4e0b9ee8f1d932ed1f"
_MAX_PAYLOAD = 1048576


class _Rejected(Exception):
    pass


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _Rejected("duplicate_key")
        result[key] = value
    return result


def _constant(value):
    raise _Rejected("invalid_number")


def _json(raw):
    return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_unique,
                      parse_constant=_constant)


def _read_file(path, limit):
    with open(path, "rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise _Rejected("binding_size")
    return raw


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _checked_bundle():
    if (len(sys.argv) != 5 or sys.argv[1] != "--bundle"
            or sys.argv[3] != "--bundle-sha256"):
        raise _Rejected("arguments")
    path, digest = sys.argv[2], sys.argv[4]
    if (not os.path.isabs(path) or type(digest) is not str
            or not re.fullmatch(r"[0-9a-f]{64}", digest)):
        raise _Rejected("bundle_binding")
    raw = _read_file(path, 8192)
    if _hash(raw) != digest:
        raise _Rejected("bundle_pin")
    bundle = _json(raw)
    if (type(bundle) is not dict or set(bundle) != {"schema", "helper", "leaf"}
            or type(bundle["schema"]) is not int or bundle["schema"] != 1):
        raise _Rejected("bundle_schema")
    for name, filename in (("helper", "layout_commit_cli.py"),
                           ("leaf", "layout_commit_windows.py")):
        entry = bundle[name]
        if (type(entry) is not dict or set(entry) != {"path", "sha256"}
                or entry["path"] != filename or type(entry["sha256"]) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])):
            raise _Rejected("bundle_entry")
    directory = os.path.dirname(path)
    helper_path = os.path.join(directory, bundle["helper"]["path"])
    # Recheck the explicitly bound source even when invoked by checked bootstrap.
    if (os.path.normcase(os.path.abspath(__file__)) != os.path.normcase(helper_path)
            or _hash(_read_file(helper_path, 131072)) != bundle["helper"]["sha256"]):
        raise _Rejected("helper_pin")
    if bundle["leaf"]["sha256"] != _LEAF_SHA256:
        raise _Rejected("leaf_binding")
    return os.path.join(directory, bundle["leaf"]["path"])


def _read_exact(count):
    raw = bytearray(count)
    offset = 0
    while offset < count:
        read = sys.stdin.buffer.readinto(memoryview(raw)[offset:])
        if not read:
            raise _Rejected("incomplete_frame")
        offset += read
    return bytes(raw)


def _target(value):
    if type(value) is not str or not re.match(r"^[A-Za-z]:\\", value):
        raise _Rejected("invalid_target")
    if len(value.encode("utf-16-le")) // 2 >= 260 or "/" in value:
        raise _Rejected("invalid_target")
    for part in value[3:].split("\\"):
        if (not part or part in (".", "..") or part.endswith((".", " "))
                or len(part.encode("utf-16-le")) // 2 > 255
                or any(ord(ch) < 32 or ch in '<>:"/\\|?*' for ch in part)):
            raise _Rejected("invalid_target")
        stem = part.split(".", 1)[0].rstrip(" ").upper()
        if (stem in ("CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$")
                or re.fullmatch(r"(?:COM|LPT)[1-9¹²³]", stem)):
            raise _Rejected("invalid_target")
    parent = value.rsplit("\\", 1)[0]
    if len(parent) == 2:
        parent += "\\"
    if len(parent.encode("utf-16-le")) // 2 + 41 >= 260:
        raise _Rejected("invalid_target")


def _request():
    if _read_exact(4) != b"DLC1":
        raise _Rejected("frame_magic")
    count = struct.unpack(">I", _read_exact(4))[0]
    if not 1 <= count <= 4096:
        raise _Rejected("metadata_size")
    meta = _json(_read_exact(count))
    if (type(meta) is not dict or set(meta) != {"protocol", "operation_id", "target",
                                             "payload_bytes", "payload_sha256"}):
        raise _Rejected("metadata_keys")
    if meta["protocol"] != _PROTOCOL:
        raise _Rejected("protocol")
    if (type(meta["operation_id"]) is not str
            or not re.fullmatch(r"[0-9a-f]{32}", meta["operation_id"])):
        raise _Rejected("operation_id")
    if (type(meta["payload_bytes"]) is not int
            or not 0 <= meta["payload_bytes"] <= _MAX_PAYLOAD):
        raise _Rejected("payload_size")
    if (type(meta["payload_sha256"]) is not str
            or not re.fullmatch(r"[0-9a-f]{64}", meta["payload_sha256"])):
        raise _Rejected("payload_digest")
    _target(meta["target"])
    payload = _read_exact(meta["payload_bytes"])
    payload.decode("utf-8", "strict")
    if payload.startswith(b"\xef\xbb\xbf"):
        raise _Rejected("payload_bom")
    if _hash(payload) != meta["payload_sha256"]:
        raise _Rejected("payload_digest")
    return meta, payload


def _load_leaf(path):
    raw = _read_file(path, 131072)
    if _hash(raw) != _LEAF_SHA256:
        raise _Rejected("leaf_pin")
    namespace = {"__name__": "_deepeye_layout_commit_windows", "__file__": path}
    exec(compile(raw, path, "exec"), namespace)
    return namespace["commit_new"]


def main():
    leaf_called = False
    try:
        path = _checked_bundle()
        meta, payload = _request()
        commit_new = _load_leaf(path)
        leaf_called = True
        result = commit_new(meta["target"], payload)
        result.update({key: meta[key] for key in ("protocol", "operation_id", "payload_bytes", "payload_sha256")})
        result["leaf_called"] = True
        raw = json.dumps(result, ensure_ascii=False, allow_nan=False,
                         separators=(",", ":")).encode("utf-8", "strict")
        if not 1 <= len(raw) <= 16384:
            raise _Rejected("result_size")
        # Unbuffered -u stdout, exactly one frame, no incidental output.
        sys.stdout.buffer.write(b"DLR1" + struct.pack(">I", len(raw)) + raw)
        return 0
    except BaseException as exc:
        # Fixed diagnostics never include a target, layout, exception text or traceback.
        code = str(exc) if isinstance(exc, _Rejected) else "invalid_input_or_binding"
        label = "outcome_unknown" if leaf_called else "pre_leaf_rejected"
        sys.stderr.write(label + ":" + code + "; leaf_called=" + ("true" if leaf_called else "false") + "\n")
        return 3 if leaf_called else 2


if __name__ == "__main__":
    sys.exit(main())
