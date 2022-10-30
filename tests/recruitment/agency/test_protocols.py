from unittest import TestCase
from unittest.mock import patch

from recruitment.agency import Config
from recruitment.agency import Commlink
from recruitment.agency import Contingency
from recruitment.agency import Coordinator
from recruitment.agency.protocols import HasContingency

from tests.recruitment.agency import client
from tests.recruitment.agency import fake_credentials
from tests.recruitment.agency import retry_policy_provider


class HasContingencyTest(TestCase):

    def setUp(self):
        broker_name = 'sns'
        region = 'us-east-1'

        patcher = patch('boto3.client')
        self.addCleanup(patcher.stop)
        self.mock_boto_client = patcher.start()
        self.mock_boto_client.return_value = client(broker_name, region)

        self.commlink = Commlink(Config(broker_name, **fake_credentials))

    def test_arbitrary_class_can_adhere_to_HasContingency_protocol(self):
        class Conformer:
            def __init__(self):
                self.retry_policy_provider = 'has requisite attributes'
        self.assertIsInstance(Conformer(), HasContingency)

    def test_arbitrary_class_cannot_adhere_to_HasContingency_protocol(self):
        class NonConformer:
            pass
        self.assertNotIsInstance(NonConformer(), HasContingency)

    def test_fully_implemented_entities_follow_protol(self):
        coordinator = Coordinator(
            commlink=self.commlink,
            contingency=Contingency(retry_policy_provider=retry_policy_provider)
        )
        self.assertIsInstance(coordinator, HasContingency)

    def test_partial_entity_violates_protocol(self):
        self.assertNotIsInstance(Coordinator(commlink=self.commlink), HasContingency)


class ContingencyTest(TestCase):

    def test_can_adhere_to_HasContingency_protocol(self):
        contingency = Contingency(retry_policy_provider=retry_policy_provider)
        self.assertIsInstance(contingency, HasContingency)

    def test_cannot_adhere_to_HasContingency_protocol(self):
        contingency = Contingency()
        self.assertNotIsInstance(contingency, HasContingency)
