from textwrap import dedent
from unittest import TestCase
from unittest.mock import ANY
from unittest.mock import patch

from botocore.exceptions import NoRegionError
from botocore.stub import Stubber

from tests.recruitment.agency import fake_credentials
from tests.recruitment.agency import client
from tests.recruitment.agency import raise_this
from recruitment.agency import Broker
from recruitment.agency import Config
from recruitment.agency import Commlink
from recruitment.agency.temp import Commlink as FakeCommunicator


class CommunicatorTest(TestCase):

    @patch('boto3.client')
    def test_cannot_instantiate_with_invalid_Config(self, mock_boto_client):
        mock_boto_client.side_effect = raise_this(exception=ValueError)
        with self.assertRaises(Commlink.FailedToInstantiate):
            Commlink(config=Config(Broker.sns))

        mock_boto_client.side_effect = raise_this(exception=NoRegionError)
        with self.assertRaises(Commlink.FailedToInstantiate):
            Commlink(config=Config(Broker.sns))

    @patch('boto3.client')
    def test_communicator_instantiation_failure_redacts_secrets(self, mock_boto_client):
        expected_serialization = dedent(
            """\
            service_name=sns
            region_name=
            access_key_id=**********
            secret_access_key=**********
            endpoint_url="""
        )

        mock_boto_client.side_effect = raise_this(exception=ValueError)
        with self.assertRaises(Commlink.FailedToInstantiate) as error_ctx:
            Commlink(config=Config(Broker.sns))

        self.assertEqual(str(error_ctx.exception), expected_serialization)

    @patch('boto3.client')
    def test_can_create_topic_and_send_message(self, mock_boto_client):
        region = 'some-region-1'
        topic_name = 'some-topic'
        broker = Broker.sns

        expected_topic_response = {
            'TopicArn': f'arn:aws:sns:{region}:12345:{topic_name}'
        }
        expected_publish_response = {
            'MessageId': '00000000-0000-0000-0000-000000000000'
        }

        sns = client(broker.name, region)
        mock_boto_client.return_value = sns
        with Stubber(sns) as stubber:
            stubber.add_response(
                broker.interface['create_target'], expected_topic_response
            )
            stubber.add_response(broker.interface['send'], expected_publish_response)

            commlink = Commlink(Config(broker, **fake_credentials))
            topic_creation = commlink.create_target(
                Name='string',
                Attributes={'string': 'string'},
                Tags=[
                    {'Key': 'string', 'Value': 'string'},
                ],
            )
            message_receipt = commlink.send(Message='some message!')

        self.assertEqual(topic_creation, expected_topic_response)
        self.assertEqual(message_receipt, expected_publish_response)

    @patch('boto3.client')
    def test_can_receive_logs_message(self, mock_boto_client):
        region = 'some-region-1'
        broker = Broker.logs

        expected_response = {
            'events': [
                    {
                    'timestamp': 1663600455651,
                    'message': '  File "/usr/local/lib/python3.7/http/client.py", line 1026, in _send_output',
                    'ingestionTime': 1663600458020
                }
            ],
            'nextForwardToken': '-->',
            'nextBackwardToken': '<--',
            'ResponseMetadata': {
                'RequestId': 'b14a4a55-5ab1-4da0-aa90-eafaa721fdaa',
                'HTTPStatusCode': 200,
                'HTTPHeaders': {
                    'x-amzn-requestid': 'b14a4a55-5ab1-4da0-aa90-eafaa721fdaa',
                    'content-type': 'application/x-amz-json-1.1',
                    'content-length': '1057709',
                    'date': 'Mon, 19 Sep 2022 15:59:05 GMT'
                },
                'RetryAttempts': 0
            }
        }

        logs = client(broker.name, region)
        mock_boto_client.return_value = logs
        with Stubber(logs) as stubber:
            stubber.add_response(
                broker.interface['receive'], expected_response
            )

            commlink = Commlink(Config(broker, **fake_credentials))
            message_receipt = commlink.receive(logGroupName='someLogGroupName', logStreamName='someLogStreamName')

        self.assertEqual(message_receipt, expected_response)


class TempCommunicatorTest(TestCase):

    def test_context(self):
        config = Config('logs', 'us-east-1','some-acces-key-id', 'some-secret', 'https://some-endpoint.com')
        payload_items = [('testing', 123)]
        logGroupName, logStreamName = 'testing', '123'
        expectations = {
            'expected_payload': dict(payload_items),
            'expected_args': (
                ANY,
                {
                    'logGroupName': logGroupName,
                    'logStreamName': logStreamName
                }
            )
        }
        with FakeCommunicator(config, **expectations) as fake_commlink:
            received = fake_commlink.receive(logGroupName=logGroupName, logStreamName=logStreamName)

        self.assertCountEqual(payload_items, received.items())
