from unittest import TestCase
from unittest.mock import patch

from recruitment.agency import Agent
from recruitment.agency import Config
from recruitment.agency import Consumer
from recruitment.agency import Publisher
from recruitment.agency.protocols import HasContingency

from tests.recruitment.agency import acceptable_broker_names


class HasContingencyTest(TestCase):

    @patch('boto3.client')
    def test_fully_implemented_entities_follow_protol(self, mock_boto_client):
        broker_name = acceptable_broker_names[0]
        config = Config(broker_name)
        self.assertIsInstance(Agent(config), HasContingency)
        self.assertIsInstance(Publisher(config), HasContingency)

    @patch('boto3.client')
    def test_partial_entity_violates_protocol(self, mock_boto_client):
        self.assertNotIsInstance(Consumer(), HasContingency)
