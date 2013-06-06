import os
import sys
from time import time, sleep
from . import test_utils
from infi.execute import (
    local,
    execute,
    execute_assert_success,
    execute_async,
    wait_for_many_results,
    make_fd_non_blocking,
    execute_async,
    ExecutionError,
    CommandTimeout,
    )
from contextlib import contextmanager

class TestCase(test_utils.TestCase):
    def assertImmediate(self):
        return self.assertTakesAlmost(0)
    @contextmanager
    def assertTakesAlmost(self, secs, delta=0.5):
        start_time = time()
        yield None
        self.assertLess(abs(time()-(start_time + secs)), delta)

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
        self.assertEquals(result.get_stderr(), "")
        newline = "\r\n" if os.name == 'nt' else "\n"
        self.assertEquals(result.get_stdout(), "hello%s" % newline)
    def test__execute_with_env(self):
        key = "some_key"
        value = "some_value"
        output = local.execute("set", shell=True, env={key:value}).get_stdout()
        self.assertIn(key, output)
        self.assertIn(value, output)
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
        num_secs = 3
        with self.assertTakesAlmost(num_secs, 1):
            with self.assertImmediate():
                result = execute_async("sleep {0}".format(num_secs), shell=True)
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
    def test__async_execute_with_little_output(self):
        try:
            import gevent.subprocess
            raise test_utils.SkipTest()
        except ImportError:
            pass

        part_a = 'legen'
        part_b = 'wait for it'
        part_c = 'dary'
        command = ["-c", "from sys import stdout; from time import sleep; stdout.write('%s');stdout.flush(); sleep(2); stdout.write('%s');stdout.flush(); sleep(2); stdout.write('%s'); stdout.flush(); sleep(2)" % \
                        (part_a, part_b, part_c)]
        command.insert(0,sys.executable)
        num_secs = 6
        with self.assertTakesAlmost(num_secs, 1):
            with self.assertImmediate():
                result = execute_async(command)
            with self.assertTakesAlmost(1):
                self.assertRaises(CommandTimeout, result.wait, **{'timeout':1})
                self.assertIn(part_a, result.get_stdout())
                #self.assertNotIn(part_b, result.get_stdout())
            with self.assertTakesAlmost(2):
                self.assertRaises(CommandTimeout, result.wait, **{'timeout':2})
                self.assertIn(part_a, result.get_stdout())
                self.assertIn(part_b, result.get_stdout())
                self.assertNotIn(part_c, result.get_stdout())
            with self.assertTakesAlmost(2):
                self.assertRaises(CommandTimeout, result.wait, **{'timeout':2})
                self.assertIn(part_a, result.get_stdout())
                self.assertIn(part_b, result.get_stdout())
                self.assertIn(part_c, result.get_stdout())
            result.wait()
    def test__sync_execute_with_huge_output(self):
        part_a = 'legen'
        part_b = 'wait for it'
        part_c = 'dary'
        number = 65536
        command = ["-c", "from sys import stdout; from time import sleep; stdout.write('%s'*%s);stdout.flush(); sleep(2); stdout.write('%s'*%s);stdout.flush(); sleep(2); stdout.write('%s'*%s); stdout.flush(); sleep(2)" % \
                        (part_a, number, part_b, number, part_c, number)]
        command.insert(0,sys.executable)
        result = execute(command)
        self.assertIn(part_a * number, result.get_stdout())
        self.assertIn(part_b * number, result.get_stdout())
        self.assertIn(part_c * number, result.get_stdout())

    def test__sync_execute_with_huge_output_one_shot(self):
        part_a = 'legen'
        part_b = 'wait for it'
        part_c = 'dary'
        number = 65536
        command = ["-c", "from sys import stdout; from time import sleep; stdout.write('%s'*%s); stdout.write('%s'*%s); stdout.write('%s'*%s);" % \
                        (part_a, number, part_b, number, part_c, number)]
        command.insert(0,sys.executable)
        result = execute(command)
        self.assertIn(part_a * number, result.get_stdout())
        self.assertIn(part_b * number, result.get_stdout())
        self.assertIn(part_c * number, result.get_stdout())

    def test__async_wait_periods(self):
        num_secs = 3
        with self.assertTakesAlmost(num_secs):
            with self.assertImmediate():
                result = execute_async("sleep {0}".format(num_secs), shell=True)
            self.assertFalse(result.is_finished())
            with self.assertTakesAlmost(1):
                self.assertRaises(CommandTimeout, result.wait, **{'timeout':1})
                self.assertFalse(result.is_finished())
            with self.assertTakesAlmost(1):
                self.assertRaises(CommandTimeout, result.wait, **{'timeout':1})
                self.assertFalse(result.is_finished())
            result.wait()
            self.assertTrue(result.is_finished())

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


def is_gevent_importable():
    try:
        import gevent.subprocess
    except ImportError:
        return False
    return True


class GeventTestCase(test_utils.TestCase):
    def setUp(self):
        if os.name == 'nt' or not is_gevent_importable():
            raise test_utils.SkipTest("available on posix systems with gevent.subprocess")

    def test_async_with_another_greenlet_running(self):
        import gevent
        event = gevent.event.Event()
        def func():
            event.set()
        result = execute_async("sleep 1", shell=True)
        greenlet = gevent.spawn(func)
        self.assertFalse(event.is_set())
        result.wait()
        self.assertTrue(event.is_set())
        greenlet.join()

    def test_sync_with_another_greenlet_running(self):
        import gevent
        event = gevent.event.Event()
        def func():
            event.set()
        greenlet = gevent.spawn(func)
        execute("sleep 1", shell=True)
        self.assertTrue(event.is_set())
        greenlet.join()
