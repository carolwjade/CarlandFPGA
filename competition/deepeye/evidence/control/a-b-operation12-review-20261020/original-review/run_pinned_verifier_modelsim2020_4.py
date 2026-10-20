"""Execute the pinned verifier with two disclosed ModelSim-host adaptations.

1. Preserve the review-owned ASCII subst drive through Path.absolute(); Python's
   Path.resolve() expands it to the repository's non-ASCII path, which this
   ModelSim 2020.4 installation cannot use for its SQLite work database.
2. Translate each vsim launch from interactive `-c -onfinish stop` to
   `-batch -syncio`. On this installation the former stops at $finish without
   flushing $display and raises `FileWatch(fileName)`, yielding a false negative
   even though the testbench reached its pass statement. Batch mode with syncio
   emits the real marker and final error/warning counts.

The pinned verifier, vectors, RTL, testbench and assertions remain byte-identical.
Every translated launch is printed to stderr for the enclosing raw log.
"""
import pathlib
import runpy
import subprocess
import sys


def main():
    marker = sys.argv.index("--")
    verifier = sys.argv[1]
    forwarded = sys.argv[marker + 1:]
    if not forwarded:
        raise SystemExit("missing verifier arguments after --")

    pathlib.Path.resolve = pathlib.Path.absolute
    real_run = subprocess.run

    def compatible_run(command, *args, **kwargs):
        command = list(command)
        if pathlib.Path(command[0]).name.lower() == "vsim.exe":
            translated = []
            skip = False
            for item in command[1:]:
                if skip:
                    skip = False
                    continue
                if item == "-onfinish":
                    skip = True
                    continue
                if item == "-c":
                    continue
                translated.append(item)
            command = [command[0], "-batch", "-syncio", *translated]
            print("COMPAT_VSIM " + repr(command), file=sys.stderr, flush=True)
        return real_run(command, *args, **kwargs)

    subprocess.run = compatible_run
    sys.argv = [verifier] + forwarded
    runpy.run_path(verifier, run_name="__main__")


if __name__ == "__main__":
    main()
