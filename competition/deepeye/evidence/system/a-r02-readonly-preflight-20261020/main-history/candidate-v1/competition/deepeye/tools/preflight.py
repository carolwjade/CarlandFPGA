"""Bounded metadata/CIM inventory. This command cannot accept R02 or hardware."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import struct
import subprocess
import sys
import threading

PINNED_REQUIREMENTS_SHA256 = "c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804"
CONTRACT_PATH = Path(__file__).resolve().parents[3] / "docs/competition/deepeye-2026/immutable_scope.json"
COLLECTOR_PATH = Path(__file__).with_name("preflight_windows.ps1")
MAX_JSON_BYTES = 1048576
TIMEOUT_SECONDS = 20
PACKAGES = ("torch", "onnxruntime", "onnxruntime-directml", "onnx", "rocm",
            "rocm-bootstrap", "numpy", "setuptools", "typing-extensions")
GROUP_FIELDS = {
    "cpu": {"name": str, "architecture": str, "address_width": int,
            "cores": int, "logical_processors": int},
    "os": {"name": str, "version": str, "build": str, "architecture": str,
           "total_memory_bytes": int},
    "gpu": {"name": str, "device_id": str, "adapter_ram_bytes": int,
            "driver_version": str, "driver_date": str},
    "npu_candidates": {"name": str, "device_id": str, "status": str},
    "drivers": {"device_id": str, "device_name": str, "driver_version": str, "driver_date": str},
    "disks": {"device_id": str, "filesystem": str, "total_bytes": int, "free_bytes": int},
}


class CollectionError(Exception):
    def __init__(self, code, message, **details):
        super().__init__(message)
        self.code = code
        self.details = details


def decode_json(raw):
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("JSON exceeds 1 MiB")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("nonfinite JSON value: " + value)
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("nonfinite JSON number: " + value)
        return number
    try:
        result = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs,
                            parse_constant=invalid_constant, parse_float=finite_float)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError(str(exc)) from exc
    if not isinstance(result, dict):
        raise ValueError("JSON root must be an object")
    return result


def verify_contract():
    result = {"contract_id": "DEEPEYE-HUMAN-LOCK-20261014/revision1",
              "expected_requirements_sha256": PINNED_REQUIREMENTS_SHA256,
              "actual_requirements_sha256": None, "valid": False}
    try:
        contract = decode_json(CONTRACT_PATH.read_bytes())
        requirements = contract.get("requirements")
        canonical = json.dumps(requirements, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
        result["actual_requirements_sha256"] = hashlib.sha256(canonical).hexdigest()
        ids = [item.get("id") for item in requirements if isinstance(item, dict)] if isinstance(requirements, list) else []
        result["valid"] = (
            contract.get("contract_id") == "DEEPEYE-HUMAN-LOCK-20261014"
            and type(contract.get("revision")) is int and contract["revision"] == 1
            and len(ids) == 15 and set(ids) == {f"H{i:02}" for i in range(1, 16)}
            and isinstance(requirements, list) and len(requirements) == 15
            and result["actual_requirements_sha256"] == PINNED_REQUIREMENTS_SHA256
            and contract.get("requirements_sha256") == PINNED_REQUIREMENTS_SHA256)
        if not result["valid"]:
            result["error"] = "Contract identity, revision, H01-H15 membership or pinned digest mismatch"
    except (OSError, ValueError, TypeError) as exc:
        result["error"] = str(exc)
    return result


def is_npu_candidate(name, device_id):
    return bool(re.search(r"\b(?:NPU|Neural|IPU)\b", name, re.IGNORECASE)
                or re.match(r"^PCI\\VEN_1022&DEV_(?:1502|17F0)(?:&|$)", device_id, re.IGNORECASE))


def validate_inventory(data):
    errors = []
    def problem(message):
        errors.append({"code": "inventory_invalid", "message": message})
    if set(data) != {"schema", "observed_at_utc", "groups"} or type(data.get("schema")) is not int or data["schema"] != 1:
        problem("Invalid collector root/schema")
    try:
        observed = datetime.fromisoformat(data["observed_at_utc"].replace("Z", "+00:00"))
        if observed.utcoffset() is None or observed.utcoffset().total_seconds() != 0:
            raise ValueError("UTC required")
    except (KeyError, TypeError, AttributeError, ValueError):
        problem("Invalid observation UTC timestamp")
    groups = data.get("groups")
    if not isinstance(groups, dict) or set(groups) != set(GROUP_FIELDS):
        problem("Missing or unexpected inventory groups")
        return errors
    for name, fields in GROUP_FIELDS.items():
        group = groups[name]
        if not isinstance(group, dict) or set(group) != {"status", "rows", "error"}:
            problem(name + ": invalid group shape")
            continue
        if group["status"] == "error":
            problem(name + ": query failed: " + str(group["error"]))
        elif group["status"] != "ok" or group["error"] is not None:
            problem(name + ": invalid status/error")
        rows = group["rows"]
        if not isinstance(rows, list):
            problem(name + ": rows must be an array")
            continue
        if name in ("cpu", "os", "disks") and not rows:
            problem(name + ": required group is empty")
        for row in rows:
            if not isinstance(row, dict) or set(row) != set(fields):
                problem(name + ": invalid row shape")
                continue
            valid = True
            for key, kind in fields.items():
                value = row[key]
                if type(value) is not kind or (kind is int and value < 0):
                    problem(name + ": invalid field " + key)
                    valid = False
                elif kind is str and not value.strip() and key not in ("driver_version", "driver_date", "status", "device_name", "filesystem"):
                    problem(name + ": empty field " + key)
                    valid = False
            if not valid:
                continue
            if name == "cpu" and (row["address_width"] not in (32, 64) or row["cores"] < 1 or row["logical_processors"] < 1):
                problem("cpu: invalid width/core counts")
            if name == "os" and row["total_memory_bytes"] < 1:
                problem("os: invalid memory size")
            if name == "disks" and (row["total_bytes"] < 1 or row["free_bytes"] > row["total_bytes"]):
                problem("disks: invalid total/free bytes")
            if name == "npu_candidates" and not is_npu_candidate(row["name"], row["device_id"]):
                problem("npu_candidates: row does not match candidate rules")
    return errors


def package_metadata():
    result = {"scope": "metadata only; selected distributions in current interpreter, not all environments",
              "complete": True, "packages": {}}
    for name in PACKAGES:
        try:
            version = metadata.version(name)
            if not isinstance(version, str) or not version.strip():
                raise ValueError("missing/non-string version")
            result["packages"][name] = {"status": "installed", "version": version}
        except metadata.PackageNotFoundError:
            result["packages"][name] = {"status": "not_installed", "version": None}
        except Exception as exc:
            result["complete"] = False
            result["packages"][name] = {"status": "metadata_error", "version": None, "error": str(exc)}
    return result


def collect_windows():
    executable = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    command = [str(executable), "-NoLogo", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-File", str(COLLECTOR_PATH)]
    try:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, creationflags=0x08004000)
    except OSError as exc:
        raise CollectionError("collector_start", str(exc)) from exc
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    overflow = threading.Event()
    read_errors = []
    def read_pipe(name, pipe, limit):
        try:
            while True:
                chunk = pipe.read(8192)
                if not chunk:
                    break
                remaining = limit - len(buffers[name])
                buffers[name].extend(chunk[:max(remaining, 0)])
                if len(chunk) > remaining:
                    overflow.set()
                    process.kill()
                    break
        except (OSError, ValueError) as exc:
            read_errors.append(str(exc))
        finally:
            pipe.close()
    readers = [threading.Thread(target=read_pipe, args=(name, pipe, limit), daemon=True)
               for name, pipe, limit in (("stdout", process.stdout, MAX_JSON_BYTES),
                                         ("stderr", process.stderr, 65536))]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        process.wait(timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        process.wait(timeout=5)
    for reader in readers:
        reader.join(timeout=1)
    details = {"exit_code": process.returncode,
               "stdout": bytes(buffers["stdout"]).decode("utf-8", errors="replace"),
               "stderr": bytes(buffers["stderr"]).decode("utf-8", errors="replace")}
    if timed_out:
        raise CollectionError("collector_timeout", "Collector exceeded 20 seconds; owned process killed and waited", **details)
    if overflow.is_set():
        raise CollectionError("collector_output_limit", "Collector output exceeded bounded pipe limit", **details)
    if read_errors or any(reader.is_alive() for reader in readers):
        raise CollectionError("collector_read", "Incomplete pipe read: " + "; ".join(read_errors), **details)
    if process.returncode != 0:
        raise CollectionError("collector_exit", "Collector exited unsuccessfully", **details)
    try:
        return decode_json(bytes(buffers["stdout"]))
    except ValueError as exc:
        raise CollectionError("collector_json", str(exc), **details) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--output", type=Path, help="exclusively create a new JSON file; parent must exist")
    args = parser.parse_args(argv)
    result = {"schema": 1, "R02": "not_run", "formal_acceptance": False,
              "inventory_complete": False, "errors": [], "observations": None,
              "gates": {"physical_board": "not_run", "calibration": "not_run",
                        "rocm_project": "not_run", "npu_runtime": "not_run",
                        "device_compatibility": "unknown", "trained_model_benefit": "not_run"},
              "interpreter": {"version": platform.python_version(), "architecture_bits": struct.calcsize("P") * 8,
                              "executable": sys.executable},
              "interpretation": "Empty device query lists mean no matching rows, not proven absence or support. NPU rows are candidates only."}
    output = None
    try:
        if args.output is not None:
            try:
                output = args.output.open("x", encoding="utf-8", newline="\n")
            except OSError as exc:
                raise CollectionError("output_refused", str(exc)) from exc
        result["contract"] = verify_contract()
        if not result["contract"]["valid"]:
            raise CollectionError("contract_invalid", result["contract"].get("error", "invalid contract"))
        try:
            result["collector_source_sha256"] = hashlib.sha256(COLLECTOR_PATH.read_bytes()).hexdigest()
        except OSError as exc:
            raise CollectionError("collector_source", str(exc)) from exc
        if platform.system() != "Windows":
            raise CollectionError("unsupported_platform", "Only Windows CIM inventory is implemented")
        result["package_metadata"] = package_metadata()
        result["observations"] = collect_windows()
        result["errors"].extend(validate_inventory(result["observations"]))
        if not result["package_metadata"]["complete"]:
            result["errors"].append({"code": "metadata_error", "message": "Selected package metadata collection incomplete"})
        result["inventory_complete"] = not result["errors"]
    except CollectionError as exc:
        result["errors"].append({"code": exc.code, "message": str(exc), **exc.details})
    payload = json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2) + "\n"
    if output is not None:
        try:
            output.write(payload)
            output.close()
        except OSError as exc:
            result["inventory_complete"] = False
            result["errors"].append({"code": "output_write", "message": str(exc)})
            payload = json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2) + "\n"
    sys.stdout.write(payload)
    return 0 if args.inventory_only and result["inventory_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
