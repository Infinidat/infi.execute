from .exceptions import CommandTimeout
from .exceptions import ExecutionError
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
    def _burst(self, stdoutReadable, stderrReadable, stdinWritable):
        if stdoutReadable:
            output = self._popen.stdout.read()
            if not output:
                self._popen.stdout.close()
                self._popen.stdout = None
            else:
                self._output.write(output)
        if stderrReadable:
            output = self._popen.stderr.read()
            if not output:
                self._popen.stderr.close()
                self._popen.stderr = None
            else:
                self._error.write(output)
        if stdinWritable:
            input = self._input.read(MAX_INPUT_CHUNK_SIZE)
            if input:
                self._popen.stdin.write(input)
            if len(input) <  MAX_INPUT_CHUNK_SIZE:
                self._popen.stdin.close()
                self._popen.stdin = None
    def poll(self):
        # the following calls _check_return_code
        _poll_and_wait_for_io([self], timeout=0)
        return self.result
    def poll_without_checking_io(self):
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
    results = list(results)
    timeout = kwargs.pop('timeout', None)
    deadline = _get_deadline(results, timeout)
    returned = [None for result in results]
    while _should_still_wait(results, deadline=deadline):
        current_time = time.time()
        _poll_and_wait_for_io(results, timeout=_get_wait_interval(current_time, deadline))
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
        result.poll_without_checking_io()
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

def _poll_and_wait_for_io(results, timeout=0):
    read_fds = []
    write_fds = []
    for result in results:
        if result is None:
            continue
        if result._popen.stdin is not None:
            write_fds.append(result._popen.stdin)
        if result._popen.stdout is not None:
            read_fds.append(result._popen.stdout)
        if result._popen.stderr is not None:
            read_fds.append(result._popen.stderr)
    #print "selecting, r=%s, w=%s, timeout=%s" % (read_fds, write_fds, timeout)
    readables = writables = []
    if read_fds or write_fds:
        readables, writables, _ = select.select(read_fds, write_fds, [], timeout)
    for result in results:
        if result is None:
            continue
        result._burst(stdoutReadable=result._popen.stdout in readables,
                      stderrReadable=result._popen.stderr in readables,
                      stdinWritable=result._popen.stdin in writables)
        result.poll_without_checking_io()
