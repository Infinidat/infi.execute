from select import select

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
    def do_iteration(self, timeout=None):
        reads, writes, _ = select(self._reads.keys(), self._writes.keys(), [], timeout)
        for readable in reads:
            self._handle_readable(readable)
        for writeable in writes:
            self._handle_writeable(writeable)
    def _handle_readable(self, f):
        handler = self._reads.pop(f, None)
        if handler is not None:
            handler(self, f)
    def _handle_writeable(self, f):
        handler = self._writes.pop(f, None)
        if handler is not None:
            handler(self, f)

