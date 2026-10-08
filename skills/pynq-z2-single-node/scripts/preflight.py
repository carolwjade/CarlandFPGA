"""Report local FPGA tool discovery without implying access to a PYNQ-Z2 board.

The probe is intentionally static: vendor tools are never launched.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Callable, Mapping


def _tool_path(
    names: tuple[str, ...],
    env_names: tuple[str, ...],
    subpaths: tuple[str, ...],
    which: Callable[[str], str | None],
    environ: Mapping[str, str],
    explicit_home: str | Path | None = None,
) -> str | None:
    valid_names = {name.lower() for name in names}
    if explicit_home is not None:
        base_path = Path(explicit_home)
        candidates = (base_path, *(base_path / subpath for subpath in subpaths))
        for candidate in candidates:
            if candidate.is_file() and candidate.name.lower() in valid_names:
                return str(candidate.resolve())
    for name in names:
        found = which(name)
        if found:
            return str(found)
    for env_name in env_names:
        base = environ.get(env_name)
        if not base:
            continue
        base_path = Path(base)
        candidates = (base_path, *(base_path / subpath for subpath in subpaths))
        for candidate in candidates:
            if candidate.is_file() and candidate.name.lower() in valid_names:
                return str(candidate.resolve())
    return None


def collect_preflight(
    *,
    which: Callable[[str], str | None] | None = None,
    environ: Mapping[str, str] | None = None,
    vivado_home: str | Path | None = None,
    modelsim_home: str | Path | None = None,
) -> dict:
    """Return a deterministic, JSON-compatible local availability report."""
    which = shutil.which if which is None else which
    environ = os.environ if environ is None else environ
    vivado = _tool_path(
        ("vivado", "vivado.bat", "vivado.exe"),
        ("XILINX_VIVADO", "VIVADO_HOME"),
        ("bin/vivado.bat", "bin/vivado.exe", "bin/vivado"),
        which,
        environ,
        vivado_home,
    )
    modelsim = _tool_path(
        ("vsim", "vsim.exe"),
        ("MODELSIM_HOME", "QUESTA_HOME", "MGC_HOME"),
        ("win64/vsim.exe", "win32/vsim.exe", "bin/vsim.exe", "bin/vsim"),
        which,
        environ,
        modelsim_home,
    )
    return {
        "schema_version": 1,
        "tools": {
            "vivado": {"available": vivado is not None, "path": vivado},
            "modelsim": {"available": modelsim is not None, "path": modelsim},
        },
        "board": {"status": "not_checked"},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Report local Vivado and ModelSim executable discovery as JSON. "
            "Board access is not checked."
        )
    )
    parser.add_argument("--vivado-home", type=Path, help="Vivado installation directory or executable")
    parser.add_argument("--modelsim-home", type=Path, help="ModelSim installation directory or executable")
    args = parser.parse_args(argv)
    print(json.dumps(
        collect_preflight(vivado_home=args.vivado_home, modelsim_home=args.modelsim_home),
        ensure_ascii=False,
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
