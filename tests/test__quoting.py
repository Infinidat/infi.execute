from unittest import TestCase
from infi.execute import execute_assert_success
from infi.execute.utils import quote

_PROBLEMATIC_STRINGS = [
    'hey"there', 'hello world', 'this is a quote: \'', 'this is a $ dollar sign', '"quoted string"'
    ]

class QuotingTest(TestCase):
    def test__quoting(self):
        for string in _PROBLEMATIC_STRINGS:
            output = execute_assert_success("echo {0}".format(quote(string))).stdout.rstrip()
            self.assertEquals(string, output)
