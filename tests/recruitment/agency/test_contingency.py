from unittest import TestCase
from unittest.mock import MagicMock

from recruitment.agency import Contingency


class ContingencyTest(TestCase):

    def test_can_have_0_max_retries(self):
        self.assertIsInstance(Contingency, type)
        self.assertIsInstance(Contingency(max_retries=0), Contingency)
        self.assertIsInstance(Contingency(max_retries=0, reaction=MagicMock()), Contingency)
