import os

INVALID_HANDLE_VALUE = -1
PIPE_NOWAIT = 1

def _make_fd_non_blocking_unix(fd):
    import fcntl
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

def _get_named_pipe_from_fileno(fileno):
    import msvcrt
    result = msvcrt.get_osfhandle(fileno)
    if result == INVALID_HANDLE_VALUE:
        raise WinError()
    return result

def _make_fd_non_blocking_windows(fd):
    """ We tried using GetNamedPipehandleStateA and SetNamedPipeHandle, but it always returns 0
    If you PeekNamedPipe and read only as much as available, it will not be blocked
    """
    return

def make_fd_non_blocking(fd):
    if os.name != 'nt':
        _make_fd_non_blocking_unix(fd)
    else:
        _make_fd_non_blocking_windows(fd)

def _is_blocking_unix(fd):
    import fcntl
    return not bool(fcntl.fcntl(fd, fcntl.F_GETFL, os.O_NONBLOCK))

def _is_blocking_windows(fd):
    """ We tried using GetNamedPipehandleStateA and SetNamedPipeHandle, but it always returns 0
    """
    raise NotImplementedError

def is_blocking(fd):
    if os.name != 'nt':
        return _is_blocking_unix(fd)
    else:
        return _is_blocking_windows(fd)

def quote(s):
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    if " " in s:
        s = '"{0}"'.format(s)
    else:
        s = s.replace("'", "\\'")
    return s

