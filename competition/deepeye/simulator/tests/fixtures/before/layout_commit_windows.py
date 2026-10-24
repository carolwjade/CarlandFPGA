"""One-shot Windows no-replace file publication, stdlib only.

Public API: commit_new(target: str, payload: bytes) -> dict.
Import performs no native calls, filesystem mutation, or background work.
Only ordinary absolute drive paths on fixed local NTFS are supported. The
existing ancestry is first retained without write/delete sharing. After its
owned temp pins the final parent nonempty, an identity-checked handover permits
write sharing while continuously denying delete sharing. NTFS cannot establish
a reparse point on these nonempty directories. This is a bounded
ordinary-writer operation, not a defense against privileged handle/volume/ACL
manipulation, and FlushFileBuffers is not a power-loss durability guarantee.
"""
import ctypes as C
from ctypes import wintypes as W
import re
import secrets

__all__ = ["commit_new"]

_MAX_PAYLOAD = 1048576
_TEMP_ATTEMPTS = 8
_TEMP_NAME_UNITS = 40  # .lc- + 32 hex + .tmp
_INVALID = C.c_void_p(-1).value
_READ = 0x80000000
_WRITE = 0x40000000
_DELETE = 0x10000
_LIST_DIRECTORY = 0x1
_READ_ATTRIBUTES = 0x80
_SHARE_READ = 0x1
_SHARE_WRITE = 0x2
_CREATE_NEW = 1
_OPEN_EXISTING = 3
_NORMAL = 0x80
_BACKUP_SEMANTICS = 0x02000000
_OPEN_REPARSE = 0x00200000
_DIRECTORY = 0x10
_REPARSE = 0x400
_COLLISIONS = (80, 183)


class _RenameUnion(C.Union):
    _fields_ = [("ReplaceIfExists", C.c_ubyte), ("Flags", W.DWORD)]


class _RenameInfo(C.Structure):
    _anonymous_ = ("choice",)
    _fields_ = [("choice", _RenameUnion), ("RootDirectory", W.HANDLE),
                ("FileNameLength", W.DWORD), ("FileName", W.WCHAR * 1)]


class _DispositionInfo(C.Structure):
    _fields_ = [("DeleteFile", C.c_ubyte)]


class _FileInfo(C.Structure):
    _fields_ = [("attributes", W.DWORD), ("creation", W.FILETIME),
                ("access", W.FILETIME), ("write", W.FILETIME),
                ("volume", W.DWORD), ("size_high", W.DWORD),
                ("size_low", W.DWORD), ("links", W.DWORD),
                ("index_high", W.DWORD), ("index_low", W.DWORD)]


class _Failure(Exception):
    def __init__(self, code, winerror=None):
        super().__init__(code)
        self.code = code
        self.winerror = winerror


def _validate(target, payload):
    if not isinstance(payload, bytes) or len(payload) > _MAX_PAYLOAD:
        raise _Failure("invalid_payload")
    if not isinstance(target, str) or not re.match(r"^[A-Za-z]:\\", target):
        raise _Failure("invalid_path")
    try:
        units = len(target.encode("utf-16-le")) // 2
    except UnicodeEncodeError:
        raise _Failure("invalid_path") from None
    if units >= 260 or "/" in target:
        raise _Failure("invalid_path")
    components = target[3:].split("\\")
    for part in components:
        if (not part or part in (".", "..") or part.endswith((".", " "))
                or len(part.encode("utf-16-le")) // 2 > 255
                or any(ord(ch) < 32 or ch in '<>:"/\\|?*' for ch in part)):
            raise _Failure("invalid_path")
        stem = part.split(".", 1)[0].rstrip(" ").upper()
        if (stem in ("CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$")
                or re.fullmatch(r"(?:COM|LPT)[1-9¹²³]", stem)):
            raise _Failure("invalid_path")
    parent = target.rsplit("\\", 1)[0]
    if len(parent) == 2:
        parent += "\\"
    # Source temp uses this same parent; fail before any I/O if it cannot fit.
    if len(parent.encode("utf-16-le")) // 2 + 1 + _TEMP_NAME_UNITS >= 260:
        raise _Failure("invalid_path")
    return parent, components[-1]


class _Api:
    def __init__(self):
        if C.sizeof(W.WCHAR) != 2 or C.sizeof(W.DWORD) != 4:
            raise _Failure("unsupported_abi")
        offsets = (8, 16, 20) if C.sizeof(W.HANDLE) == 8 else (4, 8, 12)
        if (C.sizeof(W.HANDLE) not in (4, 8)
                or (_RenameInfo.RootDirectory.offset, _RenameInfo.FileNameLength.offset,
                    _RenameInfo.FileName.offset) != offsets
                or C.sizeof(_FileInfo) != 52 or C.sizeof(_DispositionInfo) != 1):
            raise _Failure("unsupported_abi")
        self.k = C.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateFileW": ([W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p,
                             W.DWORD, W.DWORD, W.HANDLE], W.HANDLE),
            "CloseHandle": ([W.HANDLE], W.BOOL),
            "GetFileInformationByHandle": ([W.HANDLE, C.POINTER(_FileInfo)], W.BOOL),
            "GetDriveTypeW": ([W.LPCWSTR], W.UINT),
            "QueryDosDeviceW": ([W.LPCWSTR, W.LPWSTR, W.DWORD], W.DWORD),
            "GetVolumeInformationByHandleW": ([W.HANDLE, W.LPWSTR, W.DWORD,
                C.POINTER(W.DWORD), C.POINTER(W.DWORD), C.POINTER(W.DWORD),
                W.LPWSTR, W.DWORD], W.BOOL),
            "WriteFile": ([W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD),
                           C.c_void_p], W.BOOL),
            "FlushFileBuffers": ([W.HANDLE], W.BOOL),
            "SetFilePointerEx": ([W.HANDLE, C.c_longlong, C.POINTER(C.c_longlong),
                                  W.DWORD], W.BOOL),
            "ReadFile": ([W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD),
                          C.c_void_p], W.BOOL),
            "SetFileInformationByHandle": ([W.HANDLE, C.c_int, C.c_void_p,
                                             W.DWORD], W.BOOL),
        }
        for name, (argtypes, restype) in signatures.items():
            function = getattr(self.k, name)
            function.argtypes = argtypes
            function.restype = restype

    def _check(self, ok, code):
        if not ok:
            raise _Failure(code, C.get_last_error())

    def create(self, path, access, share, disposition, flags):
        handle = self.k.CreateFileW(path, access, share, None, disposition, flags, None)
        if handle == _INVALID:
            raise _Failure("create_failed", C.get_last_error())
        return handle

    def info(self, handle):
        value = _FileInfo()
        self._check(self.k.GetFileInformationByHandle(handle, C.byref(value)), "info_failed")
        return value

    def check_volume(self, root, root_handle):
        if self.k.GetDriveTypeW(root) != 3:  # DRIVE_FIXED only
            raise _Failure("unsupported_drive")
        mapping = C.create_unicode_buffer(32768)
        self._check(self.k.QueryDosDeviceW(root[:2], mapping, len(mapping)), "drive_query_failed")
        # Exclude SUBST, mapped-network and device aliases even if they look local.
        if not re.fullmatch(r"\\Device\\HarddiskVolume[0-9]+", mapping.value):
            raise _Failure("unsupported_drive_mapping")
        fs = C.create_unicode_buffer(32)
        self._check(self.k.GetVolumeInformationByHandleW(root_handle, None, 0,
                    None, None, None, fs, len(fs)), "volume_query_failed")
        if fs.value != "NTFS":
            raise _Failure("unsupported_filesystem")

    def write(self, handle, payload):
        count = W.DWORD()
        buffer = C.create_string_buffer(payload, max(1, len(payload)))
        self._check(self.k.WriteFile(handle, buffer, len(payload), C.byref(count), None),
                    "write_failed")
        if count.value != len(payload):
            raise _Failure("short_write")

    def flush(self, handle):
        self._check(self.k.FlushFileBuffers(handle), "flush_failed")

    def read(self, handle, count):
        buffer = C.create_string_buffer(max(1, count))
        actual = W.DWORD()
        self._check(self.k.ReadFile(handle, buffer, count, C.byref(actual), None), "read_failed")
        return buffer.raw[:actual.value]

    def verify(self, handle, payload):
        self._check(self.k.SetFilePointerEx(handle, 0, None, 0), "seek_failed")
        if self.read(handle, len(payload)) != payload or self.read(handle, 1) != b"":
            raise _Failure("readback_mismatch")

    def rename(self, handle, target):
        encoded = target.encode("utf-16-le")
        size = max(C.sizeof(_RenameInfo), _RenameInfo.FileName.offset + len(encoded) + 2)
        # A ctypes structure array provides pointer alignment; no _pack_ override.
        count = (size + C.sizeof(_RenameInfo) - 1) // C.sizeof(_RenameInfo)
        buffer = (_RenameInfo * count)()
        value = buffer[0]
        value.Flags = 0
        value.ReplaceIfExists = 0
        # This host's Kernel32 rejects a non-NULL RootDirectory (native 87).
        # One absolute-target call is used; there is no relative/absolute retry.
        value.RootDirectory = None
        value.FileNameLength = len(encoded)
        C.memmove(C.addressof(buffer) + _RenameInfo.FileName.offset, encoded, len(encoded))
        self._check(self.k.SetFileInformationByHandle(handle, 3, C.byref(buffer), size),
                    "rename_failed")

    def dispose(self, handle):
        disposition = _DispositionInfo(1)
        self._check(self.k.SetFileInformationByHandle(handle, 4, C.byref(disposition),
                                                     C.sizeof(disposition)), "disposition_failed")

    def close(self, handle):
        self._check(self.k.CloseHandle(handle), "close_failed")


class _Operation:
    """Private stage/publish split; each instance attempts publication at most once."""
    def __init__(self, target, payload):
        self.target = target
        self.payload = payload
        self.api = None
        self.handle = None
        self.directories = []
        self.temp_path = None
        self.identity = None
        self.state = "failed_before_publish"
        self.code = "not_started"
        self.winerror = None
        self.publish_attempted = False
        self.publication_confirmed = False
        self.handover_close_errors = []
        self.result = None

    def _stage(self):
        parent, self.name = _validate(self.target, self.payload)
        self.api = _Api()
        root = self.target[:3]
        paths = [root]
        if parent != root:
            parts = parent[3:].split("\\")
            paths.extend(root + "\\".join(parts[:i]) for i in range(1, len(parts) + 1))
        root_volume = None
        for path in paths:
            handle = self.api.create(path, _READ_ATTRIBUTES | _LIST_DIRECTORY,
                                     _SHARE_READ, _OPEN_EXISTING, _BACKUP_SEMANTICS | _OPEN_REPARSE)
            self.directories.append(handle)
            info = self.api.info(handle)
            if info.attributes & _REPARSE:
                raise _Failure("reparse_ancestor")
            if not info.attributes & _DIRECTORY:
                raise _Failure("not_directory")
            if root_volume is None:
                root_volume = info.volume
                self.api.check_volume(root, handle)
            elif info.volume != root_volume:
                raise _Failure("volume_changed")
        for _ in range(_TEMP_ATTEMPTS):
            name = ".lc-" + secrets.token_hex(16) + ".tmp"
            temp_path = parent.rstrip("\\") + "\\" + name
            try:
                handle = self.api.create(temp_path, _READ | _WRITE | _DELETE, 0,
                                         _CREATE_NEW, _NORMAL | _OPEN_REPARSE)
            except _Failure as exc:
                if exc.winerror in _COLLISIONS:
                    continue
                raise
            self.handle = handle  # establish ownership before any further native call
            self.temp_path = temp_path
            break
        if self.handle is None:
            raise _Failure("temp_names_exhausted")
        info = self.api.info(self.handle)
        self.identity = {"volume_serial": info.volume,
                         "file_index": (info.index_high << 32) | info.index_low}
        if info.volume != root_volume or info.attributes & (_REPARSE | _DIRECTORY):
            raise _Failure("invalid_source")
        self.api.write(self.handle, self.payload)
        self.api.flush(self.handle)
        self.api.verify(self.handle, self.payload)
        self._handover_ancestry(paths)

    def _handover_ancestry(self, paths):
        # The exclusive source now makes the parent nonempty, and each held
        # child directory makes its ancestor nonempty. Keep EVERY strict handle
        # until all second handles are acquired and matched. A failed handover
        # never publishes, and all cleanup still uses the original source handle.
        strict = self.directories.copy()
        for path, original in zip(paths, strict):
            second = self.api.create(path, _READ_ATTRIBUTES | _LIST_DIRECTORY,
                                     _SHARE_READ | _SHARE_WRITE, _OPEN_EXISTING,
                                     _BACKUP_SEMANTICS | _OPEN_REPARSE)
            self.directories.append(second)
            before = self.api.info(original)
            after = self.api.info(second)
            if (before.volume, before.index_high, before.index_low) != (
                    after.volume, after.index_high, after.index_low):
                raise _Failure("ancestor_identity_changed")
            if after.attributes & _REPARSE or not after.attributes & _DIRECTORY:
                raise _Failure("invalid_ancestor_handover")
        for original in reversed(strict):
            # Remove ownership before attempting CloseHandle: an uncertain close
            # is never retried, and causes a pre-publication failure.
            self.directories.remove(original)
            try:
                self.api.close(original)
            except BaseException as exc:
                self.handover_close_errors.append({"resource": "strict_ancestor",
                    "code": getattr(exc, "code", type(exc).__name__),
                    "winerror": getattr(exc, "winerror", None)})
                raise _Failure("ancestor_handover_close_failed") from None

    def _publish(self):
        self.publish_attempted = True
        # Any exception without a trusted native FALSE remains unknown. Cleanup
        # must never disposition a handle that might now name the published file.
        self.state = "outcome_unknown"
        self.code = "publish_response_unknown"
        try:
            self.api.rename(self.handle, self.target)
        except _Failure as exc:
            self.state = "already_exists" if exc.winerror in _COLLISIONS else "failed_before_publish"
            self.code = "target_exists" if self.state == "already_exists" else exc.code
            self.winerror = exc.winerror
            return
        self.publication_confirmed = True
        self.state = "committed"
        self.code = "committed"

    def _finish(self):
        cleanup = {"attempted": False, "disposition_marked": False, "close_ok": None,
                   "orphan_possible": False, "source_path_at_creation": self.temp_path,
                   "identity": self.identity, "errors": []}
        close_errors = self.handover_close_errors.copy()
        if self.handle is not None:
            if self.state not in ("committed", "outcome_unknown"):
                cleanup["attempted"] = True
                try:
                    self.api.dispose(self.handle)
                    cleanup["disposition_marked"] = True
                except BaseException as exc:
                    cleanup["errors"].append({"code": getattr(exc, "code", type(exc).__name__),
                                               "winerror": getattr(exc, "winerror", None)})
            try:
                self.api.close(self.handle)
                cleanup["close_ok"] = True
            except BaseException as exc:
                cleanup["close_ok"] = False
                close_errors.append({"resource": "source", "code": getattr(exc, "code", type(exc).__name__),
                                     "winerror": getattr(exc, "winerror", None)})
            if self.state == "outcome_unknown":
                cleanup["orphan_possible"] = True  # could be old temp OR published target
            elif cleanup["attempted"]:
                cleanup["orphan_possible"] = not (cleanup["disposition_marked"] and cleanup["close_ok"])
            self.handle = None  # never retry an ambiguous CloseHandle
        for handle in reversed(self.directories):
            try:
                self.api.close(handle)
            except BaseException as exc:
                close_errors.append({"resource": "ancestor", "code": getattr(exc, "code", type(exc).__name__),
                                     "winerror": getattr(exc, "winerror", None)})
        self.directories.clear()
        if close_errors and self.state == "committed":
            self.state = "outcome_unknown"
            self.code = "close_after_publish_failed"
            cleanup["orphan_possible"] = True
        result = {"state": self.state, "ok": self.state == "committed", "code": self.code,
                  "publish_attempted": self.publish_attempted,
                  "publication_confirmed": self.publication_confirmed,
                  "cleanup": cleanup, "close_errors": close_errors}
        if self.winerror is not None:
            result["winerror"] = self.winerror
        if hasattr(self, "exception_type"):
            result["exception_type"] = self.exception_type
        return result

    def run(self):
        if self.result is not None:
            return self.result.copy()
        try:
            self._stage()
            self._publish()
        except _Failure as exc:
            self.code = exc.code
            self.winerror = exc.winerror
        except BaseException as exc:
            self.code = "exception_after_publish_attempt" if self.publish_attempted else "exception_before_publish"
            self.exception_type = type(exc).__name__
        self.result = self._finish()
        return self.result.copy()


def commit_new(target: str, payload: bytes) -> dict:
    """Publish new opaque bytes once. Never replace, adopt, sweep, or replay.

    outcome_unknown requires caller reconciliation without automatic replay.
    cleanup source_path_at_creation is diagnostic only, never deletion authority.
    """
    return _Operation(target, payload).run()
