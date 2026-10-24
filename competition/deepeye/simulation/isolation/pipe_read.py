"""Diagnostic observations of a caller-owned, single-reader anonymous pipe.

No endpoint acquisition, authentication, completion proof or elapsed-time bound.
The production actor and authority paths do not import this inactive leaf.
"""
from dataclasses import dataclass
import struct

_MAX_HANDLE=(1 << (8*struct.calcsize('P'))) - 1


@dataclass(frozen=True)
class PipeReadResult:
    """Plain diagnostic state/bytes; constructing one grants no authority."""
    state: str
    data: bytes


def _native():
    # Invalid arguments must not even reach native module initialization.
    from . import win32
    return win32


def poll_output(handle, max_bytes=8192):
    """One peek and at most one bounded read: data, empty, or observed EOF.

    Caller supplies its original owned endpoint and ensures no competing reader.
    Native calls have OS scheduling behavior, not hard cancellation deadlines.
    Errors other than Win32 ERROR_BROKEN_PIPE remain errors. This function never
    closes handles, writes, waits for data or invokes authority/lifecycle code.
    """
    if type(handle) is not int or not 0 < handle <= _MAX_HANDLE:
        raise ValueError('positive native-width exact integer handle required')
    if type(max_bytes) is not int or not 1 <= max_bytes <= 8192:
        raise ValueError('exact integer max_bytes in 1..8192 required')
    w=_native()
    count=w.W.DWORD()
    try:
        if not w.PeekNamedPipe(handle,None,0,None,w.C.byref(count),None):
            raise w.C.WinError(w.C.get_last_error(),'PeekNamedPipe')
        if count.value==0:
            return PipeReadResult('empty',b'')
        requested=min(count.value,max_bytes)
        raw=w.read(handle,requested)
    except OSError as error:
        if getattr(error,'winerror',None)==109:
            return PipeReadResult('eof',b'')
        raise
    if type(raw) is not bytes or not 0 < len(raw) <= requested:
        raise ValueError('native pipe read returned unexpected bytes')
    return PipeReadResult('data',raw)


__all__=['PipeReadResult','poll_output']
