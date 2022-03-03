from logging import exception
from unittest import TestCase
from unittest.mock import patch

from botocore.exceptions import NoRegionError
from botocore.stub import Stubber

from tests.recruitment.agency import fake_credentials
from tests.recruitment.agency import client
from recruitment.agency import Broker
from recruitment.agency import Config
from recruitment.agency import Communicator


class CommunicatorTest(TestCase):

    @patch('boto3.client')
    def test_cannot_instantiate_with_invalid_Config(self, mock_boto_client):
        def raise_this(**kwargs):
            exception = kwargs['exception']
            def will_raise(**kwargs):
                raise exception
            return will_raise
        
        mock_boto_client.side_effect = raise_this(exception=ValueError)
        with self.assertRaises(Communicator.FailedToInstantiate):
            Communicator(config=Config(Broker.sns))  # all credentials are missing

    @patch('boto3.client')
    def test_can_create_topic_and_publish_message(self, mock_boto_client):
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
                broker.interface['declare_receiver'], expected_topic_response
            )
            stubber.add_response(broker.interface['send'], expected_publish_response)

            commlink = Communicator(Config(broker, **fake_credentials))
            topic_creation = commlink.declare_receiver(
                Name='string',
                Attributes={'string': 'string'},
                Tags=[
                    {'Key': 'string', 'Value': 'string'},
                ],
            )
            message_receipt = commlink.send(Message='some message!')

        self.assertEqual(topic_creation, expected_topic_response)
        self.assertEqual(message_receipt, expected_publish_response)
