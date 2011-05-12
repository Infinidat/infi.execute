import sys
from time import time
import unittest
from infi.execute import (
    local,
    execute,
    execute_assert_success,
    execute_async,
    wait_for_many_results,
    execute_async,
    ExecutionError,
    CommandTimeout,
    )
from contextlib import contextmanager

class TestCase(unittest.TestCase):
    def assertImmediate(self):
        return self.assertTakesAlmost(0)
    @contextmanager
    def assertTakesAlmost(self, secs):
        start_time = time()
        yield None
        self.assertAlmostEquals(time(), start_time + secs, places=1)

class MiscTest(TestCase):
    def test__invalid_kwargs(self):
        with self.assertRaises(TypeError):
            local.execute("command", bla=2, bloop=3)
    def test__repr_doesnt_fail(self):
        representation = repr(local.execute("echo hello", shell=True))
        self.assertGreater(len(representation), 0)
    def test__shortcuts(self):
        self.assertIs(execute.im_func, local.execute.im_func)
        self.assertIs(execute_assert_success.im_func, local.execute_assert_success.im_func)
        self.assertIs(execute_async.im_func, local.execute_async.im_func)

class SimpleExecution(TestCase):
    def test__sync_execute_shell(self):
        result = local.execute("echo hello", shell=True)
        self.assertEquals(result.get_returncode(), 0)
        for i in range(3):
            self.assertEquals(result.get_stderr(), "")
            self.assertEquals(result.get_stdout(), "hello\n")
    def test__sync_execute_stderr(self):
        produce_stderr_command = ["-c",
                                  "import sys;sys.stderr.write('hello')"]
        produce_stderr_command.insert(0,sys.executable)

        result = local.execute(produce_stderr_command)
        self.assertEquals(result.get_stderr(), "hello")
    def test__sync_execute_stdin_through_string(self):
        result = execute("cat | cat", stdin="hello", shell=True)
        self.assertEquals(result.get_stdout(), "hello")
    def test__async_execute(self):
        num_secs = 1
        with self.assertTakesAlmost(num_secs):
            with self.assertImmediate():
                result = execute_async("sleep {}".format(num_secs), shell=True)
            self.assertIsNone(result.get_returncode())
            self.assertFalse(result.is_finished())
            self.assertIsNone(result.poll())
            self.assertEquals(result.wait(), True)
        self.assertEquals(0, result.poll())
    def test__multiple_executes(self):
        num_secs = 3
        commands = ["sleep {0}".format(num_secs) for i in range(10)]
        with self.assertImmediate():
            results = [local.execute_async(command, shell=True) for command in commands]
        with self.assertTakesAlmost(num_secs):
            results = wait_for_many_results(results)
        self.assertTrue(all(results))
        self.assertEquals(len(results), len(commands))
        self.assertEquals(set(result.get_returncode() for result in results), set([0]))
class ErrorExitTest(TestCase):
    FALSE_RETURN_CODE = 1
    def test__ignore_exit_code(self):
        result = local.execute("false", shell=True)
        self.assertEquals(result.get_returncode(), self.FALSE_RETURN_CODE)
    def test__sync_failure(self):
        with self.assertRaises(ExecutionError) as caught:
            local.execute_assert_success("false", shell=True)
        self.assertEquals(caught.exception.result.get_stderr(), "")
        self.assertEquals(caught.exception.result.get_stdout(), "")
        self.assertEquals(caught.exception.result.get_returncode(), self.FALSE_RETURN_CODE)
    def test__timeout_sync(self):
        with self.assertRaises(CommandTimeout) as caught:
            local.execute("sleep 100", timeout=1, shell=True)
        self.assertFalse(caught.exception.result.is_finished())
        caught.exception.result.kill()
    def test__timeout_async(self):
        result = execute_async("sleep 100", shell=True, timeout=1)
        with self.assertRaises(CommandTimeout) as caught:
            result.wait()
        self.assertFalse(caught.exception.result.is_finished())
        caught.exception.result.kill()
    def test__timeout_is_absolute(self):
        timeout = 2
        with self.assertTakesAlmost(timeout):
            result = local.execute_async("sleep 100", shell=True, timeout=timeout)
            with self.assertRaises(CommandTimeout) as caught:
                result.wait()

