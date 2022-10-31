from unittest import TestCase

from recruitment.agency import Broker
from tests.recruitment.agency import acceptable_broker_names


class BrokerTest(TestCase):

    broker_interface_method_names = {'receive', 'create_target', 'send'}

    def test_cannot_instantiate_invalid_Broker(self):
        with self.assertRaises(ValueError):
            Broker('invalid broker type')

    def test_can_instantiate_valid_Brokers(self):
        for name in acceptable_broker_names:
            broker = Broker(name)
            self.assertEqual(broker.name, name)
            self.assertEqual(broker.value, name)

    def test_brokers_have_defined_interfaces(self):
        for broker in [Broker(name) for name in acceptable_broker_names]:
            self.assertTrue(
                set(broker.interface.keys()).issubset(self.broker_interface_method_names)
            )
