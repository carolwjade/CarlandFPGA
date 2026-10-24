"""Strict JSON reports, serialized before exclusive file creation.

NumPy is optional: supported scalars are converted only if the caller has
already loaded NumPy. Arrays and nonfinite values are never silently encoded.
"""
import json
from pathlib import Path
import sys


def _scalar(value):
    numpy = sys.modules.get("numpy")
    if numpy is not None and isinstance(value, numpy.generic):
        if value.dtype.kind in "biufU":
            native = value.item()
            if type(native) in (bool, int, float, str):
                return native
    raise TypeError(f"Unsupported report value: {type(value).__name__}")


def dumps_report(value):
    """Return strict, readable JSON; reject unsupported values before any I/O."""
    return json.dumps(value, ensure_ascii=False, indent=2,
                      allow_nan=False, default=_scalar) + "\n"


def write_new_report(path, value):
    """Create a new UTF-8 report without replacing existing evidence.

    Serialization errors create no file. An actual disk write failure may
    leave a partial new file; callers must preserve it as failure evidence.
    """
    encoded = dumps_report(value).encode("utf-8")
    with Path(path).open("xb") as stream:
        stream.write(encoded)
