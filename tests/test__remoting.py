from forge import Forge
import unittest
from infi import execute as execute_module
from infi.execute.utils import quote

class RemotingTest(unittest.TestCase):
    def setUp(self):
        super(RemotingTest, self).setUp()
        self.forge = Forge()
        self.forge.replace(execute_module.local_runner, "execute")
    def tearDown(self):
        self.forge.verify()
        self.forge.reset()
        self.forge.restore_all_replacements()
        super(RemotingTest, self).tearDown()
    def test__through_ssh_global(self):
        self._test__through_ssh(execute_module.through_ssh)
    def test__through_ssh_local_runner(self):
        self._test__through_ssh(execute_module.local_runner.through_ssh)
    def _test__through_ssh(self, through_ssh_method):
        host = "some_host_name"
        command = "some complex 'command with' \"all sorts of $ quoting\""
        args = ('a', 'b', 'c')
        kwargs = dict(d=2, e=3, f=4)
        expected_obj = object()
        execute_module.local_runner.execute("ssh {} {}".format(host, quote(command)), *args, **kwargs).and_return(expected_obj)
        self.forge.replay()
        self.assertIs(expected_obj, through_ssh_method(host).execute(command, *args, **kwargs))
