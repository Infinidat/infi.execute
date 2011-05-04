from .exceptions import CommandTimeout
from .exceptions import ExecutionError
from .ioloop import IOLoop
from cStringIO import StringIO
import itertools
import os
import select
import signal
import time

MAX_INPUT_CHUNK_SIZE = 1024

class ExecuteResult(object):
    def __init__(self, command, popen, stdin=None, assert_success=False, timeout=None):
        super(ExecuteResult, self).__init__()
        self._command = command
        self._popen = popen
        self._output = StringIO()
        self._input  = StringIO(stdin or '')
        self._error  = StringIO()
        self._assert_success = assert_success
        self._deadline = None
        if timeout is not None:
            self._deadline = time.time() + timeout
    def get_deadline(self):
        return self._deadline
    @property
    def result(self):
        return self._popen.returncode
    @property
    def finished(self):
        return self.result is not None
    def kill(self, sig=signal.SIGKILL):
        if not self.finished:
            os.kill(self.pid, sig)

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
    def _handle_stdout(self, ioloop, _):
        output = self._popen.stdout.read()
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
    def _handle_stderr(self, ioloop, _):
        output = self._popen.stderr.read()
        if not output:
            self._popen.stderr.close()
            self._popen.stderr = None
        else:
            self._error.write(output)
            self._register_stderr(ioloop)
    def poll(self):
        self._popen.poll()
        self._check_return_code()
        return self.result
    def _check_return_code(self):
        if self._assert_success and self.result is not None and self.result != 0:
            raise ExecutionError(self)
    def wait(self, timeout=None):
        returned_results = wait_for_many_results([self], timeout=timeout)
        returned = self in returned_results
        if not returned and (self.get_deadline() or timeout):
            raise CommandTimeout(self)
        return returned
    def is_finished(self):
        return self.result is not None
    def __int__(self):
        return self.result
    def __repr__(self):
        return "<pid %s: %s>" % (self.pid, self._command)
    @property
    def pid(self):
        return self._popen.pid
    @property
    def stdout(self):
        return self._output.getvalue()
    @property
    def stderr(self):
        return self._error.getvalue()

def wait_for_many_results(results, **kwargs):
    ioloop = IOLoop()
    results = list(results)
    for result in results:
        result.register_to_ioloop(ioloop)
    timeout = kwargs.pop('timeout', None)
    deadline = _get_deadline(results, timeout)
    returned = [None for result in results]
    while _should_still_wait(results, deadline=deadline):
        current_time = time.time()
        ioloop.do_iteration(_get_wait_interval(current_time, deadline))
        _sweep_finished_results(results, returned)
    _sweep_finished_results(results, returned)
    return returned

DEFAULT_SAMPLE_INTERVAL = 0.05

def _get_deadline(results, deadline):
    returned = None
    for d in itertools.chain([deadline], (result.get_deadline() for result in results)):
        if d is None:
            continue
        if returned is None or d < returned:
            returned = d
    return returned

def _get_wait_interval(current_time, deadline):
    if deadline is None:
        return DEFAULT_SAMPLE_INTERVAL
    return max(0, min(DEFAULT_SAMPLE_INTERVAL, (deadline - current_time)))

def _sweep_finished_results(results, returned):
    for index, result in enumerate(results):
        if result is None:
            continue
        result.poll()
        if result.is_finished():
            returned[index] = result
            results[index] = None

def _should_still_wait(results, deadline):
    if all(r is None for r in results):
        return False
    current_time = time.time()
    if deadline is not None and deadline < time.time():
        return False
    return True
