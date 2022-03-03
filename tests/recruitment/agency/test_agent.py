from unittest import TestCase
from unittest.mock import patch

from actionpack.actions import Call
from actionpack.actions import RetryPolicy
from actionpack.utils import Closure
from botocore.exceptions import ClientError
from botocore.stub import Stubber

from tests.recruitment.agency import client
from tests.recruitment.agency import fake_credentials
from recruitment.agency import Agent
from recruitment.agency import Broker
from recruitment.agency import Communicator
from recruitment.agency import Config


class AgentTest(TestCase):

    broker = Broker.sns
    region = 'some-region-1'
    sns = client(broker.name, region)
    expected_publish_response = {'MessageId': '00000000-0000-0000-0000-000000000000'}

    @patch('boto3.client')
    @patch('actionpack.actions.Write.perform')
    def test_can_retry_message_send(self, mock_write, mock_boto_client):
        mock_boto_client.return_value = self.sns
        with Stubber(self.sns) as stubber:
            stubber.add_client_error(self.broker.interface['send'], '500')  # attempt
            stubber.add_client_error(self.broker.interface['send'], '500')  # retry 1
            stubber.add_client_error(self.broker.interface['send'], '500')  # retry 2
            smith = Agent(
                communicator=Communicator(Config(self.broker, **fake_credentials)),
                retry_policy_provider=lambda action: RetryPolicy(
                    action, max_retries=2, should_record=True
                ),
            )
            result, attempts = smith.publish(Message='Mr. Anderson...')

        self.assertFalse(result.successful)
        self.assertIsInstance(result.value, RetryPolicy.Expired)
        self.assertEqual(len(attempts), 3)
        for attempt in attempts:
            self.assertIsInstance(attempt.value, ClientError)

    @patch('boto3.client')
    @patch('actionpack.actions.Write.perform')
    def test_publish_can_eventually_succeed(self, mock_write, mock_boto_client):
        mock_boto_client.return_value = self.sns
        with Stubber(self.sns) as stubber:
            stubber.add_client_error(self.broker.interface['send'], '500')  # attempt
            stubber.add_client_error(self.broker.interface['send'], '500')  # retry 1
            stubber.add_response(
                self.broker.interface['send'], self.expected_publish_response
            )
            smith = Agent(
                communicator=Communicator(Config(self.broker, **fake_credentials)),
                retry_policy_provider=lambda action: RetryPolicy(
                    action, max_retries=2, should_record=True
                ),
            )
            result, attempts = smith.publish(Message='Mr. Anderson...')

        self.assertTrue(result.successful)
        self.assertEqual(result.value, self.expected_publish_response)
        self.assertEqual(len(attempts), 2)
        for attempt in attempts:
            self.assertIsInstance(attempt.value, ClientError)

    @patch('boto3.client')
    @patch('actionpack.actions.Write.perform')
    def test_can_define_failure_callback(self, mock_write, mock_boto_client):
        vessel = []
        contents = 'water'

        def fill(vessel: list, contents):
            vessel.append(contents)
            return vessel

        callback = Call(Closure(fill, vessel, contents))

        self.assertFalse(vessel)  # confirms the vessel has yet to be filled
        mock_boto_client.return_value = self.sns
        with Stubber(self.sns) as stubber:
            stubber.add_client_error(self.broker.interface['send'], '500')  # attempt
            stubber.add_client_error(self.broker.interface['send'], '500')  # retry 1
            smith = Agent(
                communicator=Communicator(Config(self.broker, **fake_credentials)),
                retry_policy_provider=lambda action: RetryPolicy(
                    action,
                    reaction=callback,  # called if the RetryPolicy expires
                    max_retries=1,
                    should_record=True
                ),
            )
            result, attempts = smith.publish(Message='Mr. Anderson...')

        self.assertFalse(result.successful)
        self.assertIsInstance(result.value, RetryPolicy.Expired)
        self.assertEqual(len(attempts), 2)
        for attempt in attempts:
            self.assertIsInstance(attempt.value, ClientError)
        self.assertEqual(vessel, [contents])  # evidence the fill callback was called
