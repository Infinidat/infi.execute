from .test_utils import TestCase
import forge
from infi.execute import runner

class PopenTest(TestCase):
    kwargs = dict(kwargs="here", and_another="there")
    args = (1, 2, 3, 4, object())
    def setUp(self):
        super(PopenTest, self).setUp()
        self.forge = forge.Forge()
        self.fake_popen = self.forge.create_wildcard_function_stub()
        self.forge.replace_with(runner, "Popen", self.fake_popen)
    def tearDown(self):
        self.forge.verify()
        self.forge.restore_all_replacements()
        super(PopenTest, self).tearDown()

class TestLocalPopen(PopenTest):
    def test__popen_passthrough(self):
        expected_result = self.forge.create_sentinel()
        self.fake_popen(*self.args, **self.kwargs).and_return(expected_result)
        with self.forge.verified_replay_context():
            result = runner.local.popen(*self.args, **self.kwargs)
        self.assertIs(expected_result, result)

class TestSSHPopen(PopenTest):
    SSH = '/usr/bin/ssh'
    def setUp(self):
        super(TestSSHPopen, self).setUp()
        self.host = "some_host"
        self.runner = self.forge.create_mock(runner.Runner)
        self.ssh_runner = runner.through_ssh(self.host, base_runner=self.runner)
    def test__default_goes_to_local(self):
        self.forge.replace(runner, "local")
        expected_result = runner.local.popen([self.SSH, self.host, "command"], shell=True).and_return(self.forge.create_sentinel())
        with self.forge.verified_replay_context():
            result = runner.through_ssh(self.host).popen(["command"])
        self.assertIs(result, expected_result)
    def test__list_command(self):
        self._test__popen_execution(["echo", "hello"], [self.SSH, self.host, "echo hello"])
    def test__string_command(self):
        self._test__popen_execution("echo hello", "{} {} \"echo hello\"".format(self.SSH, self.host))
    def test__list_command_with_quoting(self):
        self._test__popen_execution(["echo", "hello there"], [self.SSH, self.host, "echo \"hello there\""])
    def test__string_command_with_quoting(self):
        self._test__popen_execution("echo \"hello there\"", "{} {} \"echo \\\"hello there\\\"\"".format(self.SSH, self.host))
    def _test__popen_execution(self, cmd, expected_translation):
        expected_result = self.forge.create_sentinel()
        self.runner.popen(expected_translation, shell=True, *self.args, **self.kwargs).and_return(expected_result)
        with self.forge.verified_replay_context():
            result = self.ssh_runner.popen(cmd, *self.args, **self.kwargs)
        self.assertEquals(result, expected_result)

