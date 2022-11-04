from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from actionpack.actions import Call
from actionpack.actions import RetryPolicy
from actionpack.utils import Closure
from botocore.exceptions import ClientError
from botocore.stub import Stubber

from recruitment.agency import Commlink
from recruitment.agency import Config
from recruitment.agency import Consumer
from recruitment.agency import Contingency
from recruitment.agency import Coordinator
from recruitment.agency.resources import Broker
from tests.recruitment.agency import client
from tests.recruitment.agency import fake_credentials
from tests.recruitment.agency import uncloseable
from tests.recruitment.agency import write_to_deadletter_file


class ConsumerTest(TestCase):

    broker = Broker.logs
    region = 'some-region-1'
    botoclient = client(broker.name, region)

    expected_consume_response = {
        'events': [
            {
                'timestamp': 123,
                'message': 'string',
                'ingestionTime': 123
            },
        ],
        'nextForwardToken': 'string',
        'nextBackwardToken': 'string'
    }

    @patch('boto3.client')
    @patch('actionpack.actions.Write.perform')
    def test_can_retry_message_send(self, mock_write, mock_boto_client):
        mock_boto_client.return_value = self.botoclient
        max_retries = 2
        with Stubber(self.botoclient) as stubber:
            stubber.add_client_error(self.broker.interface['receive'], '500')  # attempt
            stubber.add_client_error(self.broker.interface['receive'], '500')  # retry 1
            stubber.add_client_error(self.broker.interface['receive'], '500')  # retry 2
            consumer = Consumer(
                coordinator=Coordinator(
                    commlink=Commlink(Config(self.broker, **fake_credentials)),
                    contingency=Contingency
                )
            )
            effort = consumer.consume(logGroupName='the construct', logStreamName='the-training-program')

        self.assertFalse(effort.culmination.successful)
        self.assertIsInstance(effort.culmination.value, RetryPolicy.Expired)
        self.assertEqual(len(effort.retries), max_retries)
        self.assertIsInstance(effort.initial_attempt.value, ClientError)
        for retry in effort.retries:
            self.assertIsInstance(retry.value, ClientError)

    @patch('boto3.client')
    @patch('actionpack.actions.Write.perform')
    def test_consume_can_eventually_succeed(self, mock_write, mock_boto_client):
        mock_boto_client.return_value = self.botoclient
        max_retries = 2
        with Stubber(self.botoclient) as stubber:
            stubber.add_client_error(self.broker.interface['receive'], '500')  # attempt
            stubber.add_client_error(self.broker.interface['receive'], '500')  # retry 1
            stubber.add_response(
                self.broker.interface['receive'], self.expected_consume_response
            )
            consumer = Consumer(
                coordinator=Coordinator(
                    commlink=Commlink(Config(self.broker, **fake_credentials)),
                    contingency=Contingency  # 2 max_retries by default
                )
            )
            effort = consumer.consume(logGroupName='the construct', logStreamName='the-training-program')

        self.assertTrue(effort.culmination.successful)
        self.assertEqual(effort.culmination.value, self.expected_consume_response)
        self.assertEqual(len(effort.retries), max_retries)
        self.assertIsInstance(effort.initial_attempt.value, ClientError)
        self.assertIsInstance(effort.final_attempt.value, type(self.expected_consume_response))
        for retry in effort.retries[:-1]:
            self.assertIsInstance(retry.value, ClientError)

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
        mock_boto_client.return_value = self.botoclient
        max_retries = 2
        with Stubber(self.botoclient) as stubber:
            stubber.add_client_error(self.broker.interface['receive'], '500')
            stubber.add_client_error(self.broker.interface['receive'], '500')
            stubber.add_client_error(self.broker.interface['receive'], '500')
            consumer = Consumer(
                coordinator=Coordinator(
                    commlink=Commlink(Config(self.broker, **fake_credentials)),
                    contingency=Contingency(
                        reaction=callback,  # called if the RetryPolicy expires
                    )
                )
            )
            effort = consumer.consume(logGroupName='the construct', logStreamName='the-training-program')

        self.assertFalse(effort.culmination.successful)
        self.assertIsInstance(effort.culmination.value, RetryPolicy.Expired)
        self.assertEqual(len(effort.retries), max_retries)
        for retry in effort.retries:
            self.assertIsInstance(retry.value, ClientError)
        self.assertEqual(vessel, [contents])  # evidence the fill callback was called

    @patch('boto3.client')
    @patch('pathlib.Path.open')
    def test_can_write_deadletter(self, mock_file, mock_boto_client):
        mock_boto_client.return_value = self.botoclient
        max_retries = 2
        with uncloseable(StringIO()) as buffer:
            mock_file.return_value = buffer

            with Stubber(self.botoclient) as stubber:
                stubber.add_client_error(self.broker.interface['receive'], '500')
                stubber.add_client_error(self.broker.interface['receive'], '500')
                stubber.add_client_error(self.broker.interface['receive'], '500')
                consumer = Consumer(
                    coordinator=Coordinator(
                        commlink=Commlink(Config(self.broker, **fake_credentials)),
                        contingency=Contingency(reaction=write_to_deadletter_file)
                    )
                )
                effort = consumer.consume(logGroupName='the construct', logStreamName='the-training-program')

        buffer_contents: str = buffer.read()
        self.assertTrue(buffer_contents.startswith('->'))
        self.assertTrue(buffer_contents.endswith('failed\n'))

        self.assertFalse(effort.culmination.successful)
        self.assertIsInstance(effort.culmination.value, RetryPolicy.Expired)
        self.assertEqual(len(effort.retries), max_retries)
        for retry in effort.retries:
            self.assertIsInstance(retry.value, ClientError)