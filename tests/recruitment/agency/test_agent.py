from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from actionpack import Action
from actionpack.actions import Call
from actionpack.actions import RetryPolicy
from actionpack.utils import Closure
from botocore.exceptions import ClientError
from botocore.stub import Stubber
from typing import Callable
from typing import Optional

from recruitment.agency import Agent
from recruitment.agency import Broker
from recruitment.agency import Commlink
from recruitment.agency import Config
from recruitment.agency import Consumer
from recruitment.agency import Contingency
from recruitment.agency import Coordinator
from recruitment.agency import Publisher
from recruitment.agency import Reaction
from tests.recruitment.agency import client
from tests.recruitment.agency import fake_credentials
from tests.recruitment.agency import uncloseable
from tests.recruitment.agency import write_to_deadletter_file



class AgentTest(TestCase):

    region = 'some-region-1'
    sns = client(Broker.sns.value, region)
    logs = client(Broker.logs.value, region)

    expected_publish_response = {'MessageId': '00000000-0000-0000-0000-000000000000'}
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

    def publisher_provider(self, commlink: Commlink, contingency: Optional[Contingency] = None) -> Publisher:
        return Publisher(Coordinator(commlink=commlink, contingency=contingency))

    def consumer_provider(self, commlink: Commlink, contingency: Optional[Contingency] = None) -> Consumer:
        return Consumer(Coordinator(commlink=commlink, contingency=contingency))

    def commlink_provider(self, broker: Broker):
        return Commlink(Config(broker, **fake_credentials))

    def client_selector(self, *args, **kwargs):
        service_name = kwargs.get('service_name')
        if service_name == 'sns':
            return self.sns
        if service_name == 'logs':
            return self.logs

    @patch('boto3.client')
    def test_can_proceed_without_contingency(self, mock_boto_client):
        mock_boto_client.side_effect = self.client_selector
        with Stubber(self.logs) as logs_stubber, \
             Stubber(self.sns) as sns_stubber:
            sns_stubber.add_client_error(Broker.sns.interface['send'], '500')
            logs_stubber.add_client_error(Broker.logs.interface['receive'], '500')  # retry 2
            smith = Agent(
                consumer=self.consumer_provider(commlink=self.commlink_provider(Broker.logs)),
                publisher=self.publisher_provider(commlink=self.commlink_provider(Broker.sns))
            )
            consume_result = smith.consume(logGroupName='the-construct', logStreamName='the-training-program')
            publish_result = smith.publish(Message='Mr. Anderson...')

        self.assertFalse(consume_result.successful)
        self.assertIsInstance(consume_result.value, ClientError)

        self.assertFalse(publish_result.successful)
        self.assertIsInstance(publish_result.value, ClientError)

    @patch('boto3.client')
    def test_cannot_instantiate_agent_given_invalid_suboordinates(self, mock_boto_client):
        valid_consumer = self.consumer_provider(commlink=self.commlink_provider(Broker.logs))
        valid_publisher = self.publisher_provider(commlink=self.commlink_provider(Broker.sns))
        with self.assertRaises(TypeError):
            Agent(consumer='Invalid Suboordinate.', publisher=valid_publisher)
        with self.assertRaises(TypeError):
            Agent(consumer=valid_consumer, publisher='Invalid Suboordinate.')

    @patch('boto3.client')
    @patch('actionpack.actions.Write.perform')
    def test_can_retry_message_send(self, mock_write, mock_boto_client):
        mock_boto_client.side_effect = self.client_selector
        with Stubber(self.logs) as logs_stubber, \
             Stubber(self.sns) as sns_stubber:
            sns_stubber.add_client_error(Broker.sns.interface['send'], '500')  # attempt
            sns_stubber.add_client_error(Broker.sns.interface['send'], '500')  # retry 1
            sns_stubber.add_client_error(Broker.sns.interface['send'], '500')  # retry 2
            logs_stubber.add_client_error(Broker.logs.interface['receive'], '500')  # attempt
            logs_stubber.add_client_error(Broker.logs.interface['receive'], '500')  # retry 1
            logs_stubber.add_client_error(Broker.logs.interface['receive'], '500')  # retry 2
            smith = Agent(
                consumer=self.consumer_provider(
                    commlink=self.commlink_provider(Broker.logs),
                    contingency=Contingency
                ),
                publisher=self.publisher_provider(
                    commlink=self.commlink_provider(Broker.sns),
                    contingency=Contingency
                )
            )
            publish_result, publish_attempts = smith.publish(Message='Mr. Anderson...')
            consume_result, consume_attempts = smith.consume(logGroupName='the construct', logStreamName='the-training-program')

        self.assertFalse(publish_result.successful)
        self.assertIsInstance(publish_result.value, RetryPolicy.Expired)
        self.assertEqual(len(publish_attempts), 3)
        for attempt in publish_attempts:
            self.assertIsInstance(attempt.value, ClientError)

        self.assertFalse(consume_result.successful)
        self.assertIsInstance(consume_result.value, RetryPolicy.Expired)
        self.assertEqual(len(consume_attempts), 3)
        for attempt in consume_attempts:
            self.assertIsInstance(attempt.value, ClientError)

    @patch('boto3.client')
    @patch('actionpack.actions.Write.perform')
    def test_publish_can_eventually_succeed(self, mock_write, mock_boto_client):
        mock_boto_client.side_effect = self.client_selector
        consumer_max_retries = 1
        with Stubber(self.logs) as logs_stubber, \
             Stubber(self.sns) as sns_stubber:
            sns_stubber.add_client_error(Broker.sns.interface['send'], '500')  # attempt
            sns_stubber.add_client_error(Broker.sns.interface['send'], '500')  # retry 1
            sns_stubber.add_response(Broker.sns.interface['send'], self.expected_publish_response)  # retry 2
            logs_stubber.add_client_error(Broker.logs.interface['receive'], '500')  # attempt
            logs_stubber.add_response(Broker.logs.interface['receive'], self.expected_consume_response)  # retry 1
            smith = Agent(
                consumer=self.consumer_provider(
                    commlink=self.commlink_provider(Broker.logs),
                    contingency=Contingency(max_retries=consumer_max_retries)
                ),
                publisher=self.publisher_provider(
                    commlink=self.commlink_provider(Broker.sns),
                    contingency=Contingency
                )
            )
            publish_result, publish_attempts = smith.publish(Message='Mr. Anderson...')
            consume_result, consume_attempts = smith.consume(logGroupName='the-construct', logStreamName='the-training-program')

        self.assertTrue(publish_result.successful)
        self.assertEqual(publish_result.value, self.expected_publish_response)
        self.assertEqual(len(publish_attempts), 3)
        self.assertIsInstance(publish_attempts.pop().value, type(self.expected_publish_response))
        for attempt in publish_attempts:
            self.assertIsInstance(attempt.value, ClientError)

        self.assertTrue(consume_result.successful)
        self.assertEqual(consume_result.value, self.expected_consume_response)
        self.assertEqual(len(consume_attempts), consumer_max_retries + 1)
        self.assertIsInstance(consume_attempts.pop().value, type(self.expected_consume_response))
        for attempt in consume_attempts:
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
        mock_boto_client.side_effect = self.client_selector
        publisher_max_retries, consumer_max_retries = 2, 1
        with Stubber(self.logs) as logs_stubber, \
             Stubber(self.sns) as sns_stubber:
            [sns_stubber.add_client_error(Broker.sns.interface['send'], '500') for _ in range(publisher_max_retries + 1)]
            [logs_stubber.add_client_error(Broker.logs.interface['receive'], '500') for _ in range(consumer_max_retries + 1)]
            smith = Agent(
                consumer=self.consumer_provider(
                    commlink=self.commlink_provider(Broker.logs),
                    contingency=Contingency(
                        reaction=callback,  # called if the RetryPolicy fails for any reason
                        max_retries=consumer_max_retries
                    )
                ),
                publisher=self.publisher_provider(
                    commlink=self.commlink_provider(Broker.sns),
                    contingency=Contingency
                )
            )
            publish_result, publish_attempts = smith.publish(Message='Mr. Anderson...')
            consume_result, consume_attempts = smith.consume(logGroupName='the-construct', logStreamName='the-training-program')

        self.assertFalse(publish_result.successful)
        self.assertIsInstance(publish_result.value, RetryPolicy.Expired)
        self.assertEqual(len(publish_attempts), publisher_max_retries + 1)
        for attempt in publish_attempts:
            self.assertIsInstance(attempt.value, ClientError)

        self.assertFalse(consume_result.successful)
        self.assertIsInstance(consume_result.value, RetryPolicy.Expired)
        self.assertEqual(len(consume_attempts), consumer_max_retries + 1)
        for attempt in consume_attempts:
            self.assertIsInstance(attempt.value, ClientError)

        self.assertEqual(vessel, [contents])  # evidence the fill callback was called

    @patch('boto3.client')
    @patch('pathlib.Path.open')
    def test_can_write_deadletter(self, mock_file, mock_boto_client):
        mock_boto_client.side_effect = self.client_selector
        with uncloseable(StringIO()) as buffer:
            mock_file.return_value = buffer

            with Stubber(self.sns) as sns_stubber:
                sns_stubber.add_client_error(Broker.sns.interface['send'], '500')
                sns_stubber.add_client_error(Broker.sns.interface['send'], '500')
                sns_stubber.add_client_error(Broker.sns.interface['send'], '500')
                smith = Agent(
                    consumer=self.consumer_provider(self.commlink_provider(Broker.logs)),
                    publisher=self.publisher_provider(
                        commlink=self.commlink_provider(Broker.sns),
                        contingency=Contingency(reaction=write_to_deadletter_file)
                    )
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
