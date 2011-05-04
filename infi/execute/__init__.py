__version__ = "0.0.1"

from .runners import LocalRunner, SSHRunner
from .runners import wait_for_many_results
from .exceptions import *

local_runner = LocalRunner()
execute = local_runner.execute
execute_async = local_runner.execute_async
execute_assert_success = local_runner.execute_assert_success
execute_async_assert_success = local_runner.execute_async_assert_success
through_ssh = local_runner.through_ssh
