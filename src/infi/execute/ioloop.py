import os
try:
    from gevent.select import select as select_unix
    from gevent import sleep
except:
    from select import select as select_unix
    from time import sleep
from .utils import _get_named_pipe_from_fileno

from time import time
from infi.monotonic_time import monotonic_time, is_supported
if is_supported():
    time = monotonic_time


def select_windows(rlist, wlist, xlist, timeout, retry=True):
    """ on Windows, select() works only on sockets
    work of anonymous pipes is done as follows:
        PeekNamedPipe returns the amount of data avaialble.
        ReadFile calls with a higher size will be blocked

    so, in order to support size-limited reads, this function doesn't return list of file descriptors,
    but a list of tuples: (fd, bytes_available,)

    since IOLoop.do_iterations calls select with xlist=[], I do not iterate over xlist at all

    since PeekNamedPipe does not have a timeout, we will try run two iterations
    over all the fds in rlist
    """
    from ctypes import windll, byref, c_ulong, c_void_p, WinError, GetLastError
    PIPE_ENDED = 109
    read_ready = []
    rlist = [item for item in rlist]
    for i in range(2):
        for fd in rlist:
            bytes_available = c_ulong(0)
            handle = _get_named_pipe_from_fileno(fd.fileno())
            result = windll.kernel32.PeekNamedPipe(c_void_p(handle), 0, c_ulong(0), 0, byref(bytes_available), 0)
            if not result:
                last_error = GetLastError()
                if last_error != PIPE_ENDED:
                    raise WinError(last_error)
                continue
            if bytes_available.value:
                read_ready.append((fd, bytes_available.value, ))
                rlist.remove(fd)
        sleep(timeout)
    return read_ready, wlist, xlist

def select(rlist, wlist, xlist, timeout):
    if os.name != 'nt':
        return select_unix(rlist, wlist, xlist, timeout)
    else:
        return select_windows(rlist, wlist, xlist, timeout)

class IOLoop(object):
    def __init__(self):
        super(IOLoop, self).__init__()
        self.reset()

    def reset(self):
        self._reads = {}
        self._writes = {}

    def register_read(self, fd, handler):
        self._register(self._reads, fd, handler)

    def register_write(self, fd, handler):
        self._register(self._writes, fd, handler)

    def _register(self, collection, fd, handler):
        if fd in collection:
            raise NotImplementedError("Multiple registrations on single file")
        collection[fd] = handler

    def unregister_read(self, fd):
        self._unregister(self._reads, fd)

    def unregister_write(self, fd):
        self._unregister(self._writes, fd)

    def _unregister(self, collection, fd):
        if fd not in collection:
            raise NotImplementedError("Unregistering non-registered file")
        collection.pop(fd)

    def do_iteration(self, timeout=None):
        reads, writes, _ = select(self._reads.keys(), self._writes.keys(), [], timeout)
        for readable in reads:
            self._handle_readable(readable)
        for writeable in writes:
            self._handle_writeable(writeable)
        return reads or writes

    def flush(self):
        # read from the pipes until the end
        # the process is finished (or killed) when this function is called
        # we don't use do_iteration and instead call directly to the read handlers anyway -
        # this is because PeekNamedPipe won't work now (the pipe is closed), and it's safe to
        # read now that the pipes are closed, read will always finish and will never block
        # The read handles will not be re-registered when they are exhausted
        while self._reads:
            [self._handle_readable(r) for r in self._reads.keys()]

    def _handle_readable(self, f):
        """ because anonymous pipes in windows can be blocked, we need to pay attention
        on how much we read
        """
        count = -1
        if isinstance(f, tuple):
            f, count = f
        handler = self._reads.pop(f, None)
        if handler is not None:
            handler(self, f, count=count)

    def _handle_writeable(self, f):
        handler = self._writes.pop(f, None)
        if handler is not None:
            handler(self, f)

