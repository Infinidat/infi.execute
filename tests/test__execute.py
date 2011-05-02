from time import time
import unittest
from infi.execute import (
    execute,
    execute_assert_success,
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
            execute("command", bla=2, bloop=3)
    def test__repr_doesnt_fail(self):
        representation = repr(execute("echo hello"))
        self.assertGreater(len(representation), 0)

class SimpleExecution(TestCase):
    def test__sync_execute(self):
        result = execute("echo hello")
        self.assertEquals(result.result, 0)
        self.assertEquals(int(result), 0)
        self.assertEquals(result.stderr, "")
        self.assertEquals(result.stdout, "hello\n")
    def test__sync_execute_stderr(self):
        result = execute("echo hello > /dev/stderr")
        self.assertEquals(result.stderr, "hello\n")
    def test__sync_execute_stdin_through_string(self):
        result = execute("cat | cat", stdin="hello")
        self.assertEquals(result.stdout, "hello")
    def test__async_execute(self):
        num_secs = 1
        with self.assertTakesAlmost(num_secs):
            with self.assertImmediate():
                result = execute_async("sleep {}".format(num_secs))
            self.assertIsNone(result.result)
            self.assertFalse(result.is_finished())
            self.assertIsNone(result.poll())
            result.wait()
        self.assertEquals(0, result.poll())
    def test__multiple_executes(self):
        num_secs = 3
        commands = ["sleep {0}".format(num_secs) for i in range(10)]
        with self.assertImmediate():
            results = [execute_async(command) for command in commands]
        with self.assertTakesAlmost(num_secs):
            results = wait_for_many_results(results)
        self.assertTrue(all(results))
        self.assertEquals(len(results), len(commands))
        self.assertEquals(set(result.result for result in results), set([0]))
class ErrorExitTest(TestCase):
    FALSE_RETURN_CODE = 1
    def test__ignore_exit_code(self):
        result = execute("false")
        self.assertEquals(result.result, self.FALSE_RETURN_CODE)
        self.assertEquals(int(result), self.FALSE_RETURN_CODE)
    def test__sync_failure(self):
        with self.assertRaises(ExecutionError) as caught:
            execute_assert_success("false")
        self.assertEquals(caught.exception.result.stderr, "")
        self.assertEquals(caught.exception.result.stdout, "")
        self.assertEquals(caught.exception.result.result, self.FALSE_RETURN_CODE)
    def test__timeout_sync(self):
        with self.assertRaises(CommandTimeout) as caught:
            execute("sleep 100", timeout=1)
        self.assertFalse(caught.exception.result.is_finished())
        caught.exception.result.kill()
    def test__timeout_async(self):
        result = execute_async("sleep 100", timeout=1)
        with self.assertRaises(CommandTimeout) as caught:
            result.wait()
        self.assertFalse(caught.exception.result.is_finished())
        caught.exception.result.kill()
    def test__timeout_is_absolute(self):
        timeout = 2
        with self.assertTakesAlmost(timeout):
            result = execute_async("sleep 100", timeout=timeout)
            with self.assertRaises(CommandTimeout) as caught:
                result.wait()

