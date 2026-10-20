"""Trusted stdlib-only exact-tree, receipt and latched audit boundaries.

These checks deliberately do not claim an OS security sandbox. Python/native
code in the same process can bypass or tamper with Python-level checks.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile

_NAMED_TEMPFILE_CODE = tempfile.NamedTemporaryFile.__code__

class PolicyError(RuntimeError):
    pass

def require(ok, reason):
    if not ok:
        raise PolicyError(reason)

def object_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode("utf-8")).hexdigest()

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def save_new(path, value):
    with Path(path).open("x", encoding="utf-8") as out:
        json.dump(value, out, indent=2, ensure_ascii=False)
        out.write("\n")
        out.flush()
        os.fsync(out.fileno())

def check_no_links(path, missing_ok=False):
    """Check every existing lexical ancestor before following any child path."""
    path = Path(os.path.abspath(path))
    for item in [*reversed(path.parents), path]:
        try:
            s = item.lstat()
        except FileNotFoundError:
            require(missing_ok, "missing path")
            continue
        require(not stat.S_ISLNK(s.st_mode), "symlink refused")
        require(not getattr(s, "st_file_attributes", 0) & 0x400, "reparse point refused")
        if stat.S_ISREG(s.st_mode):
            require(s.st_nlink == 1, "hard-linked file refused")
    return path

def safe_relative(name):
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name,
            "invalid relative path")
    path = PurePosixPath(name)
    require(not path.is_absolute() and all(p not in ("", ".", "..") for p in name.split("/")),
            "unsafe relative path")
    for part in path.parts:
        require(not part.endswith((".", " ")) and not any(ord(c) < 32 for c in part), "invalid component")
        require(not re.fullmatch(r"(?i)(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\..*)?", part),
                "reserved component")
    return path

def snapshot(root, *, max_entries=12000, max_bytes=805306368):
    root = check_no_links(root)
    require(root.is_dir(), "tree root missing")
    result, total = {}, 0
    stack = [root]
    while stack:
        directory = stack.pop()
        with os.scandir(directory) as entries:
            rows = sorted(entries, key=lambda e: e.name)
        folded = set()
        for entry in rows:
            name = Path(entry.path).relative_to(root).as_posix()
            safe_relative(name)
            require(entry.name.casefold() not in folded, "case collision")
            folded.add(entry.name.casefold())
            # Windows DirEntry.stat may return zero st_nlink/st_ino. lstat is
            # required for a real hard-link count, without following reparse.
            s = os.lstat(entry.path)
            require(not stat.S_ISLNK(s.st_mode) and not getattr(s, "st_file_attributes", 0) & 0x400,
                    "tree link/reparse refused")
            if stat.S_ISDIR(s.st_mode):
                result[name] = {"type": "directory"}
                stack.append(Path(entry.path))
            else:
                require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "nonregular/hardlink refused")
                total += s.st_size
                require(total <= max_bytes, "tree byte budget")
                result[name] = {"type": "file", "bytes": s.st_size, "sha256": file_hash(entry.path)}
            require(len(result) <= max_entries, "tree entry budget")
    return dict(sorted(result.items()))

def verify_exact(actual, expected):
    require(actual == expected, "exact inventory mismatch")

def verify_transition(before, after, mutable_files, mutable_dirs):
    files, dirs = set(mutable_files), set(mutable_dirs)
    for name in set(before) | set(after):
        row = after.get(name)
        if name in files:
            require(row is None or row["type"] == "file", "generated file type mismatch")
        elif name in dirs:
            require(row is None or row["type"] == "directory", "generated directory type mismatch")
        else:
            require(before.get(name) == row, "unreviewed input/output change")

def validate_predecessor(receipt, step, context, inventory, previous_hash):
    require(receipt.get("step") == step, "predecessor stage ID")
    require(receipt.get("status") == "success" and receipt.get("worker_status") == "success",
            "predecessor failure")
    require(type(receipt.get("exit_code")) is int and receipt["exit_code"] == 0, "predecessor actual exit")
    require(receipt.get("all_processes_terminated") is True, "predecessor process tree unresolved")
    require(receipt.get("context") == context, "predecessor fingerprint mismatch")
    require(receipt.get("previous_receipt_sha256") == previous_hash, "predecessor chain mismatch")
    require(receipt.get("inventory") == inventory, "predecessor output mismatch")
    require(receipt.get("inventory_sha256") == object_hash(inventory), "predecessor inventory hash")

def guarded_call(policy, callback, postcheck):
    """One hook/import boundary. Failure is data, never an exception-only flag."""
    result, failure = None, None
    sys.addaudithook(policy.audit)
    try:
        result = callback()
        policy.require_clean()
        policy.require_temporaries_removed()
        postcheck()
        policy.require_clean()
    except BaseException as exc:
        failure = type(exc).__name__
    finally:
        # Only trusted frontend finalization executes after this point.
        policy.active = False
    return {"status": "success" if failure is None and not policy.violation_count else "failed",
            "result": result if failure is None and not policy.violation_count else None,
            "failure_type": failure, "violations": policy.violations,
            "violation_count": policy.violation_count, "temporary_allocations": policy.allocations,
            "temporary_opener_events": policy.opener_events}

class AuditPolicy:
    def __init__(self, root, files, dirs, temp_rules, reporter=None):
        self.root = check_no_links(root)
        self.files, self.dirs = set(files), set(dirs)
        self.rules = temp_rules
        self.allocations = []
        self.opener_events = []
        self.violations = []
        self.violation_count = 0
        self.active = True
        self.reporter = reporter

    def deny(self, event, reason, path=None):
        # Latch first. Never store untrusted exception text, network addresses
        # or outside-path arguments. Limit the journal, not the failure latch.
        self.violation_count += 1
        if len(self.violations) < 32:
            row = {"event": str(event)[:80], "reason": reason}
            if path is not None:
                row["argument_sha256"] = hashlib.sha256(os.fsencode(path)).hexdigest()
            self.violations.append(row)
            if self.reporter is not None:
                # The reporter owns a file opened by the trusted frontend
                # before installing this hook; it receives sanitized data only.
                self.reporter(row)
        raise PolicyError("latched policy refusal: " + reason)

    def relative(self, path, event):
        if isinstance(path, int):
            self.deny(event, "unreviewed file descriptor")
        try:
            target = Path(os.path.abspath(os.fsdecode(path)))
            name = target.relative_to(self.root).as_posix()
            check_no_links(target, missing_ok=True)
            if name != ".":
                safe_relative(name)
            return name
        except (ValueError, OSError, PolicyError, TypeError):
            self.deny(event, "outside, link or invalid path", path)

    def write(self, path, event, kind=None):
        name = self.relative(path, event)
        allowed = self.files if kind == "file" else self.dirs if kind == "directory" else self.files | self.dirs
        if name not in allowed:
            self.deny(event, "unreviewed write path", path)

    def allocate(self, event, path):
        name = self.relative(path, event)
        parent, leaf = name.rsplit("/", 1) if "/" in name else ("", name)
        for i, rule in enumerate(self.rules):
            pattern = re.escape(rule["prefix"]) + "[a-z0-9_]{" + str(rule["random_chars"]) + "}" + re.escape(rule["suffix"])
            if event != rule["event"] or parent != rule["parent"] or not re.fullmatch(pattern, leaf):
                continue
            count = sum(a["rule_index"] == i for a in self.allocations)
            if rule.get("named_tempfile_opener"):
                intents = sum(a["rule_index"] == i for a in self.opener_events)
                if intents != count + 1:
                    self.deny(event, "missing trusted temporary opener", path)
            if count >= rule["limit"]:
                self.deny(event, "temporary allocation count", path)
            if os.path.lexists(self.root / name):
                self.deny(event, "temporary allocation already exists", path)
            row = {"rule_index": i, "event": event, "path": name, "kind": rule["kind"]}
            self.allocations.append(row)
            if rule["kind"] == "file":
                self.files.add(name)
            else:
                self.dirs.add(name)
                for child in rule["children"]:
                    safe_relative(child)
                    self.files.add(name + "/" + child)
            return
        self.deny(event, "unreviewed temporary allocation", path)

    def audit(self, event, args):
        if not self.active:
            return
        if event.startswith("socket.") or event in {
                "subprocess.Popen", "os.system", "os.posix_spawn", "os.exec",
                "os.spawn", "os.fork", "ctypes.dlopen", "ctypes.dlsym",
                "os.symlink", "os.link", "os.putenv", "os.unsetenv",
                "sys.addaudithook"}:
            self.deny(event, "forbidden operation")
        if event in ("tempfile.mkstemp", "tempfile.mkdtemp"):
            self.allocate(event, args[0])
        elif event == "open":
            path, mode, flags = args
            writing = (mode and any(c in mode for c in "wax+")) or flags & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            if writing:
                # CPython NamedTemporaryFile calls io.open(dir, opener=...)
                # before mkstemp allocates the real file. The dummy directory
                # argument grants no file write: only this pinned stdlib code
                # object, exact existing parent and one pending allocation.
                if mode == "w" and sys._getframe(1).f_code is _NAMED_TEMPFILE_CODE:
                    name = self.relative(path, event)
                    for i, rule in enumerate(self.rules):
                        if rule.get("named_tempfile_opener") and rule["parent"] == name:
                            count = sum(a["rule_index"] == i for a in self.opener_events)
                            if count >= rule["limit"] or not (self.root/name).is_dir():
                                self.deny(event, "temporary opener count or parent", path)
                            self.opener_events.append({"rule_index": i, "path": name})
                            return
                self.write(path, event, "file")
        elif event == "os.mkdir":
            if len(args) > 2 and args[2] not in (-1, None):
                self.deny(event, "dir_fd unsupported")
            self.write(args[0], event, "directory")
        elif event in ("os.remove", "os.rmdir", "os.chmod", "os.utime", "os.truncate"):
            if event in ("os.remove", "os.rmdir") and len(args) > 1 and args[1] not in (-1, None):
                self.deny(event, "dir_fd unsupported")
            self.write(args[0], event)
        elif event == "os.rename":
            if any(fd not in (-1, None) for fd in args[2:]):
                self.deny(event, "dir_fd unsupported")
            self.write(args[0], event)
            self.write(args[1], event)

    def require_clean(self):
        require(self.violation_count == 0, "policy failure was latched")

    def require_temporaries_removed(self):
        for i, rule in enumerate(self.rules):
            if rule.get("named_tempfile_opener"):
                intents = sum(a["rule_index"] == i for a in self.opener_events)
                allocated = sum(a["rule_index"] == i for a in self.allocations)
                if intents != allocated:
                    self.deny("stage.finalize", "unmatched temporary opener")
        for row in self.allocations:
            if os.path.lexists(self.root / row["path"]):
                self.deny("stage.finalize", "temporary output remains")
