import os
import time
import errno


INVALID_HANDLE_VALUE = -1
PIPE_NOWAIT = 1
BUFSIZE = 4096


def _make_fd_non_blocking_unix(fd):
    import fcntl
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

def _get_named_pipe_from_fileno(fileno):
    import msvcrt
    from ctypes import WinError
    result = msvcrt.get_osfhandle(fileno)
    if result == INVALID_HANDLE_VALUE:
        raise WinError(result)
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

def retry_loop_on_eagain(func, *args, **kwargs):
    while True:
        try:
            return func(*args, **kwargs)
        except IOError as error:
            if error.errno == errno.EAGAIN:
                time.sleep(0.1)
            else:
                raise

def non_blocking_read(file_obj, count):
    try:
        from gevent.os import nb_read
        return nb_read(file_obj.fileno(), count if count >= 0 else BUFSIZE)
    except ImportError:
        return retry_loop_on_eagain(file_obj.read, count)

def non_blocking_write(file_obj, input_buffer):
    if not input_buffer:
        return
    try:
        from gevent.os import nb_write
        nb_write(file_obj.fileno(), input_buffer)
    except ImportError:
        return retry_loop_on_eagain(file_obj.write, input_buffer)
