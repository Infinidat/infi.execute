from .waiting import wait_for_many_results
from .exceptions import CommandTimeout
from .exceptions import ExecutionError
from .utils import make_fd_non_blocking
from cStringIO import StringIO
import os
import select
import signal
import time

MAX_INPUT_CHUNK_SIZE = 1024
RESOURCE_TEMPORARILY_UNAVAILABLE = 11

class Result(object):
    def __init__(self, command, popen, stdin, assert_success, timeout):
        super(Result, self).__init__()
        self._command = command
        self._popen = popen
        self._output = StringIO()
        self._input  = StringIO(stdin or '')
        self._error  = StringIO()
        self._assert_success = assert_success
        self._deadline = None
        if timeout is not None:
            self._deadline = time.time() + timeout
        make_fd_non_blocking(self._popen.stdout.fileno())
        make_fd_non_blocking(self._popen.stderr.fileno())
    def get_deadline(self):
        return self._deadline
    def get_returncode(self):
        return self._popen.returncode
    def kill(self, sig=signal.SIGTERM):
        if not self.is_finished():
            os.kill(self.get_pid(), sig)

    def register_to_ioloop(self, ioloop):
        if self._popen.stdout is not None:
            self._register_stdout(ioloop)
        if self._popen.stderr is not None:
            self._register_stderr(ioloop)
        if self._popen.stdin is not None:
            self._register_stdin(ioloop)
    def _register_stdin(self, ioloop):
        ioloop.register_write(self._popen.stdin, self._handle_stdin)
    def _register_stdout(self, ioloop):
        ioloop.register_read(self._popen.stdout, self._handle_stdout)
    def _register_stderr(self, ioloop):
        ioloop.register_read(self._popen.stderr, self._handle_stderr)
    def _handle_stdout(self, ioloop, _, **kwargs):
        """ because anonymous pipes in windows can be blocked, we need to pay attention
        on how much we read
        """
        count = kwargs.get('count', -1)
        output = self._popen.stdout.read(count)
        if not output:
            self._popen.stdout.close()
            self._popen.stdout = None
        else:
            self._output.write(output)
            self._register_stdout(ioloop)
    def _handle_stdin(self, ioloop, _):
        input = self._input.read(MAX_INPUT_CHUNK_SIZE)
        if input:
            self._popen.stdin.write(input)
        if len(input) <  MAX_INPUT_CHUNK_SIZE:
            self._popen.stdin.close()
            self._popen.stdin = None
        else:
            self._register_stdin(ioloop)
    def _handle_stderr(self, ioloop, _, **kwargs):
        """ because anonymous pipes in windows can be blocked, we need to pay attention
        on how much we read
        """
        count = kwargs.get('count', -1)
        output = self._popen.stderr.read(count)
        if not output:
            self._popen.stderr.close()
            self._popen.stderr = None
        else:
            self._error.write(output)
            self._register_stderr(ioloop)
    def poll(self):
        self._popen.poll()
        self._check_return_code()
        return self.get_returncode()
    def _check_return_code(self):
        returncode = self.get_returncode()
        if returncode is not None:
            # Although the process died, there may be some data in the pipes left.
            self._flush_pipes()
        if self._assert_success and returncode is not None and returncode != 0:
            raise ExecutionError(self)
    def _read_from_pipe(self, pipe):
        try:
            return pipe.read(-1)
        except IOError, io_error:
            if io_error.errno == RESOURCE_TEMPORARILY_UNAVAILABLE:
                return self._read_from_pipe(pipe)
            raise
    def _flush_pipes(self):
        for string_io, pipe in ((self._output, self._popen.stdout), (self._error, self._popen.stderr)):
            if pipe:
                data = self._read_from_pipe(pipe)
                if data:
                    string_io.write(data)
    def wait(self, timeout=None):
        returned_results = wait_for_many_results([self], timeout=timeout)
        returned = self in returned_results
        if not returned and (self.get_deadline() or timeout):
            raise CommandTimeout(self)
        return returned
    def is_finished(self):
        return self.get_returncode() is not None
    def __repr__(self):
        return "<pid %s: %s>" % (self.get_pid(), self._command)
    def get_pid(self):
        return self._popen.pid
    def get_stdout(self):
        return self._output.getvalue()
    def get_stderr(self):
        return self._error.getvalue()
