from infi.execute import utils
import os
import fcntl
import unittest

class NonblockingTest(unittest.TestCase):
    def test__nonblocking(self):
        fd_in, fd_out = os.pipe()
        file_in = os.fdopen(fd_in, "rb")
        file_out = os.fdopen(fd_out, "wb")
        self.assertTrue(self._is_blocking(file_in))
        utils.make_fd_non_blocking(file_in)
        self.assertFalse(self._is_blocking(file_in))
    def _is_blocking(self, f):
        return not bool(fcntl.fcntl(f, fcntl.F_GETFL, os.O_NONBLOCK))

