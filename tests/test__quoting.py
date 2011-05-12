import unittest
from ast import literal_eval
from infi.execute.utils import quote

class QuotingTest(unittest.TestCase):
    def test__quoting(self):
        strings = [
            'hey"there', 'hello world', 'this is a quote: \'', 'this is a $ dollar sign', '"quoted string"'
            ]
        for string in strings:
            quoted = quote(string)
            if " " not in string:
                self.assertFalse(quoted.startswith('"') or quoted.endswith('"'))
                quoted = '"' + quoted + '"'
            self.assertEquals(literal_eval(quoted.replace("\\$", "$")), string)
