from unittest import TestCase
from unittest.mock import patch

from recruitment.agency import Publisher
from recruitment.agency.protocols import HasContingency


class HasContingencyTest(TestCase):

    @patch('boto3.client')
    def test_can_follow_protocol(self, mock_boto_client):
        self.assertIsInstance(Publisher(), HasContingency)
