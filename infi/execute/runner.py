from subprocess import Popen
from .utils import quote
from .result import Result
from .exceptions import *
from subprocess import PIPE

class Runner(object):
    def popen(self, *args, **kwargs):
        raise NotImplementedError()
    def execute_async(self, command, shell=False, assert_success=False, stdin=None, timeout=None):
        popen = self.popen(command, shell=shell, stderr=PIPE, stdout=PIPE, stdin=PIPE)
        return Result(command, popen,
                      stdin=stdin,
                      assert_success=assert_success,
                      timeout=timeout)
    def execute(self, *args, **kwargs):
        returned = self.execute_async(*args, **kwargs)
        returned.wait()
        return returned
    def execute_assert_success(self, *args, **kwargs):
        kwargs.update(assert_success=True)
        return self.execute(*args, **kwargs)
class LocalRunner(Runner):
    def popen(self, *args, **kwargs):
        return Popen(*args, **kwargs)
local = LocalRunner()

class SSHRunner(Runner):
    def __init__(self, host, base_runner=None):
        super(SSHRunner, self).__init__()
        if base_runner is None:
            base_runner = local
        self.host = host
        self._base_runner = base_runner
    def popen(self, cmd, *args, **kwargs):
        cmd = self._fix_cmd(cmd)
        kwargs['shell'] = True
        return self._base_runner.popen(cmd, *args, **kwargs)
    def _fix_cmd(self, cmd):
        if isinstance(cmd, list) or isinstance(cmd, tuple):
            cmd = [self._get_ssh_command(), self.host] + [" ".join(map(quote, cmd))]
        else:
            cmd = "{0} {1} {2}".format(self._get_ssh_command(), self.host, quote(cmd))
        return cmd
    def _get_ssh_command(self):
        return "/usr/bin/ssh"
through_ssh = SSHRunner