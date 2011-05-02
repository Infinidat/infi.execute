__version__ = "0.0.1"
import subprocess
import functools
import time
from .result import ExecuteResult
from .exceptions import *
from .result import wait_for_many_results
from .utils import quote
from .utils import make_fd_non_blocking

def _execute(command, *args, **kwargs):
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

execute = _execute
execute_async = functools.partial(_execute, async=True)
execute_assert_success = functools.partial(_execute, assert_success=True)
execute_async_assert_success = functools.partial(_execute, async=True, assert_success=True)
