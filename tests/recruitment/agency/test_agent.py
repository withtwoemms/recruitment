from datetime import datetime
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from actionpack.actions import Call
from actionpack.actions import RetryPolicy
from actionpack.actions import Write
from actionpack.utils import Closure
from botocore.exceptions import ClientError
from botocore.stub import Stubber

from tests.recruitment.agency import client
from tests.recruitment.agency import fake_credentials
from tests.recruitment.agency import uncloseable
from recruitment.agency import Agent
from recruitment.agency import Broker
from recruitment.agency import Communicator
from recruitment.agency import Config


class AgentTest(TestCase):

    broker = Broker.sns
    region = 'some-region-1'
    sns = client(broker.name, region)
    expected_publish_response = {'MessageId': '00000000-0000-0000-0000-000000000000'}

    write_to_deadletter_file = Write(
        prefix=f'-> [{datetime.utcnow()}] -- ',
        filename=Agent.deadletter_file,
        to_write='failed',
        append=True,
        mkdir=True,
    )

    @patch('boto3.client')
    @patch('actionpack.actions.Write.perform')
    def test_can_retry_message_send(self, mock_write, mock_boto_client):
        mock_boto_client.return_value = self.sns
        with Stubber(self.sns) as stubber:
            stubber.add_client_error(self.broker.interface['send'], '500')  # attempt
            stubber.add_client_error(self.broker.interface['send'], '500')  # retry 1
            stubber.add_client_error(self.broker.interface['send'], '500')  # retry 2
            smith = Agent(
                config=Config(self.broker, **fake_credentials),
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
                config=Config(self.broker, **fake_credentials),
                retry_policy_provider=lambda action: retry_policy_provider(action),
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
            stubber.add_client_error(self.broker.interface['send'], '500')
            stubber.add_client_error(self.broker.interface['send'], '500')
            stubber.add_client_error(self.broker.interface['send'], '500')
            smith = Agent(
                config=Config(self.broker, **fake_credentials),
                retry_policy_provider=lambda action: retry_policy_provider(
                    action,
                    reaction=callback,  # called if the RetryPolicy expires
                ),
            )
            result, attempts = smith.publish(Message='Mr. Anderson...')

        self.assertFalse(result.successful)
        self.assertIsInstance(result.value, RetryPolicy.Expired)
        self.assertEqual(len(attempts), 3)
        for attempt in attempts:
            self.assertIsInstance(attempt.value, ClientError)
        self.assertEqual(vessel, [contents])  # evidence the fill callback was called

    @patch('boto3.client')
    @patch('pathlib.Path.open')
    def test_can_write_deadletter(self, mock_file, mock_boto_client):
        mock_boto_client.return_value = self.sns
        with uncloseable(StringIO()) as buffer:
            mock_file.return_value = buffer

            with Stubber(self.sns) as stubber:
                stubber.add_client_error(self.broker.interface['send'], '500')
                stubber.add_client_error(self.broker.interface['send'], '500')
                stubber.add_client_error(self.broker.interface['send'], '500')
                smith = Agent(
                    config=Config(self.broker, **fake_credentials),
                    retry_policy_provider=lambda action: retry_policy_provider(action),
                    record_failure_provider=lambda: self.write_to_deadletter_file,
                )
                result, attempts = smith.publish(Message='Mr. Anderson...')

        buffer_contents: str = buffer.read()
        self.assertTrue(buffer_contents.startswith('->'))
        self.assertTrue(buffer_contents.endswith('failed\n'))

        self.assertFalse(result.successful)
        self.assertIsInstance(result.value, RetryPolicy.Expired)
        self.assertEqual(len(attempts), 3)
        for attempt in attempts:
            self.assertIsInstance(attempt.value, ClientError)


def retry_policy_provider(action, max_retries=2, reaction=None) -> RetryPolicy:
    return RetryPolicy(
        action, reaction=reaction, max_retries=max_retries, should_record=True
    )
