import subprocess
import functools
import time
from .result import ExecuteResult
from .exceptions import *
from .result import wait_for_many_results
from .utils import quote
from .utils import make_fd_non_blocking

class Runner(object):
    def execute_async(self, *args, **kwargs):
        return self.execute(async=True, *args, **kwargs)
    def execute_assert_success(self, *args, **kwargs):
        return self.execute(assert_success=True, *args, **kwargs)
    def execute_async_assert_success(self, *args, **kwargs):
        return self.execute(assert_success=True, async=True, *args, **kwargs)
    def execute(self, *args, **kwargs):
        raise NotImplementedError()
    def through_ssh(self, host):
        return SSHRunner(host, self)

class LocalRunner(Runner):
    def execute(self, command, *args, **kwargs):
        stdin=kwargs.pop('stdin', '')
        async = kwargs.pop('async', False)
        assert_success = kwargs.pop('assert_success', False)
        timeout = kwargs.pop('timeout', None)
        if kwargs:
            raise TypeError("Unknown arguments: %s" % (kwargs,))
        if args:
            raise NotImplementedError()
        popen = subprocess.Popen(command, shell=True,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        for fd in [popen.stdout,
                   popen.stdin,
                   popen.stderr]:
            make_fd_non_blocking(fd)
        returned =  ExecuteResult(command, popen, stdin, assert_success=assert_success, timeout=timeout)
        assert returned._popen.stdin is not None
        assert returned._popen.stdout is not None
        if not async:
            returned.wait()
        return returned

class SSHRunner(Runner):
    def __init__(self, host, base_runner=None):
        super(SSHRunner, self).__init__()
        self._host = host
        if base_runner is None:
            base_runner = LocalRunner()
        self._runner = base_runner
    def execute(self, cmd, *args, **kwargs):
        cmd = "ssh {} {}".format(self._host, quote(cmd))
        return self._runner.execute(cmd, *args, **kwargs)
