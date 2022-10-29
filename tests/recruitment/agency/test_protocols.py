from unittest import TestCase

from recruitment.agency import Config
from recruitment.agency import Commlink
from recruitment.agency import Contingency
from recruitment.agency import Coordinator
from recruitment.agency.protocols import HasContingency

from tests.recruitment.agency import acceptable_broker_names
from tests.recruitment.agency import retry_policy_provider


class HasContingencyTest(TestCase):

    broker_name = acceptable_broker_names[0]
    commlink = Commlink(Config(broker_name))

    def test_arbitrary_class_can_adhere_to_HasContingency_protocol(self):
        class Conformer:
            def __init__(self):
                self.retry_policy_provider = 'has requisite'
                self.record_failure_provider = 'attributes'
        self.assertIsInstance(Conformer(), HasContingency)

    def test_fully_implemented_entities_follow_protol(self):
        coordinator = Coordinator(
            commlink=self.commlink,
            contingency=Contingency(
                retry_policy_provider=retry_policy_provider
            )
        )
        self.assertIsInstance(coordinator, HasContingency)

    def test_partial_entity_violates_protocol(self):
        self.assertNotIsInstance(Coordinator(commlink=self.commlink), HasContingency)
