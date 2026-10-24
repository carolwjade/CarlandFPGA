"""Run the pinned verifier without Python resolving an ASCII subst drive.

ModelSim 2020.4 cannot open its SQLite work database under this repository's
non-ASCII absolute path. The pinned verifier calls Path.resolve(), which expands
review-owned subst drive R: back to that path before CreateProcess. This wrapper
replaces only that path-normalization operation with Path.absolute(); it does
not alter the verifier file, vectors, RTL, testbench, or assertions.
"""
import pathlib
import runpy
import sys


def main():
    marker = sys.argv.index("--")
    verifier = sys.argv[1]
    forwarded = sys.argv[marker + 1:]
    if not forwarded:
        raise SystemExit("missing verifier arguments after --")
    pathlib.Path.resolve = pathlib.Path.absolute
    sys.argv = [verifier] + forwarded
    runpy.run_path(verifier, run_name="__main__")


if __name__ == "__main__":
    main()
