from infi.execute import utils
import os
from .test_utils import TestCase

class NonblockingTest(TestCase):
    def test__nonblocking(self):
        if os.name == 'nt':
            raise unittest.SkipTest("Not available on Windows")
        fd_in, fd_out = os.pipe()
        file_in = os.fdopen(fd_in, "rb")
        file_out = os.fdopen(fd_out, "wb")
        self.assertTrue(self._is_blocking(file_in))
        utils.make_fd_non_blocking(file_in)
        self.assertFalse(self._is_blocking(file_in))
    def _is_blocking(self, f):
        return utils.is_blocking(f)

