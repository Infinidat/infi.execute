__version__ = "0.0.1"
from .runner import local, through_ssh
execute = local.execute
execute_async = local.execute_async
execute_assert_success = local.execute_assert_success

from .waiting import wait_for_many_results
from .exceptions import *
