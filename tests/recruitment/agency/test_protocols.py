from unittest import TestCase

from recruitment.agency import Publisher
from recruitment.agency.protocols import HasContingency


class HasContingencyTest(TestCase):

    def test_can_follow_protocol(self):
        self.assertIsInstance(Publisher(), HasContingency)
