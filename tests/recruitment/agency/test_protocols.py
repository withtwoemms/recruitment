from unittest import TestCase
from unittest.mock import patch

from recruitment.agency import Config
from recruitment.agency import Publisher
from recruitment.agency.protocols import HasContingency

from tests.recruitment.agency import acceptable_broker_names


class HasContingencyTest(TestCase):

    @patch('boto3.client')
    def test_can_follow_protocol(self, mock_boto_client):
        broker_name = acceptable_broker_names[0]
        self.assertIsInstance(Publisher(Config(broker_name)), HasContingency)
