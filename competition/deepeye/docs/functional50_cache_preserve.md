# Functional50 vendor state preservation

The A-only loader refuses an existing or symlinked vendor global state before PYNQ import and again immediately before download. It copies existing vendor metadata as bounded raw bytes into the exclusive operation directory, verifies its length and SHA-256 by readback, and records absence explicitly. It never unpickles old metadata. Metadata identity is checked again before import and download.

An incomplete operation or missing return remains an unknown effect; do not retry. These checks rely on the original exclusive board owner and do not provide a filesystem lock against another process changing state between the last check and vendor code.
