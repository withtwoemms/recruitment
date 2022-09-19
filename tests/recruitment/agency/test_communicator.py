import json
from pathlib import Path
import boto3
import placebo

from pprint import pprint as pp
from textwrap import dedent
from unittest import TestCase
from unittest.mock import patch

from botocore.exceptions import NoRegionError
from botocore.stub import Stubber

from tests.recruitment.agency import fake_credentials
from tests.recruitment.agency import client
from tests.recruitment.agency import raise_this
from recruitment.agency import Broker
from recruitment.agency import Config
from recruitment.agency import Communicator


class CommunicatorTest(TestCase):

    fixtures = Path(__file__).parent.parent / 'fixtures'

    @patch('boto3.client')
    def test_cannot_instantiate_with_invalid_Config(self, mock_boto_client):
        mock_boto_client.side_effect = raise_this(exception=ValueError)
        with self.assertRaises(Communicator.FailedToInstantiate):
            Communicator(config=Config(Broker.sns))

        mock_boto_client.side_effect = raise_this(exception=NoRegionError)
        with self.assertRaises(Communicator.FailedToInstantiate):
            Communicator(config=Config(Broker.sns))

    @patch('boto3.client')
    def test_communicator_instantiation_failure_redacts_secrets(self, mock_boto_client):
        expected_serialization = dedent(
            """\
            service_name=sns
            region_name=
            aws_access_key_id=**********
            aws_secret_access_key=**********
            endpoint_url="""
        )

        mock_boto_client.side_effect = raise_this(exception=ValueError)
        with self.assertRaises(Communicator.FailedToInstantiate) as error_ctx:
            Communicator(config=Config(Broker.sns))

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

    # @patch('boto3.client')
    # def test_can_send_message_to_s3(self, mock_boto_client):
    def test_can_send_message_to_s3(self):
        region = 'some-region-1'
        bucket_name = 'some-bucket'
        broker = Broker.s3

        expected_topic_response = {
            "ResponseMetadata": {
                "RequestId": "5OCA6D1TNFTJ7X25XBG5UHXGE0NCJJX15H1XVPXQMY84T60M3AV4",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {
                "content-type": "application/xml; charset=utf-8",
                "content-length": "161",
                "x-amzn-requestid": "5OCA6D1TNFTJ7X25XBG5UHXGE0NCJJX15H1XVPXQMY84T60M3AV4",
                "access-control-allow-origin": "*",
                "location": "/testing",
                "last-modified": "Mon, 23 May 2022 04:45:35 GMT",
                "x-amz-request-id": "B41674D8F42B4EB0",
                "x-amz-id-2": "MzRISOwyjmnupB41674D8F42B4EB07/JypPGXLh0OVFGcJaaO3KW/hRAqKOpIEEp",
                "access-control-allow-methods": "HEAD,GET,PUT,POST,DELETE,OPTIONS,PATCH",
                "access-control-allow-headers": "authorization,cache-control,content-length,content-md5,content-type,etag,location,x-amz-acl,x-amz-content-sha256,x-amz-date,x-amz-request-id,x-amz-security-token,x-amz-tagging,x-amz-target,x-amz-user-agent,x-amz-version-id,x-amzn-requestid,x-localstack-target,amz-sdk-invocation-id,amz-sdk-request",
                "access-control-expose-headers": "etag,x-amz-version-id",
                "connection": "close",
                "date": "Mon, 23 May 2022 04:45:35GMT",
                "server": "hypercorn-h11"
                },
                "RetryAttempts": 0
            },
            "Location": f"/{bucket_name}"
        }
        expected_publish_response = None

        session = boto3.Session()
        pill = placebo.attach(session, data_path='./')
        pill.record(services='s3')
        boto3.setup_default_session()
        session = boto3.DEFAULT_SESSION
        # pill = placebo.attach(session, data_path='/path/to/response/directory')
        pill = placebo.attach(session, data_path='/Users/withtwoemms/programming/python/recruitment')
        pill.record()
        # s3 = client(broker.name, region)
        # s3 = client = boto3.client('s3')
        s3 = boto3.client('s3')
        #client.describe_images(DryRun=False)
        # s3 = client(broker.name, region)
        # from boto3 import client
        # s3 = client(broker.name, region)
        # mock_boto_client.return_value = s3

        print(s3)
        pp(dir(s3))
        pp(s3.list_buckets())
        bucket = 'chicago-community-bond-fund-inmates-scraper'
        key = 'inmates/dekalb.json'
        pp(s3.get_object(Bucket=bucket, Key=key))
        # bucket = s3.Bucket('testing')
        with Stubber(s3) as stubber:
            stubber.add_response(
                broker.interface['declare_receiver'], expected_topic_response
            )
            stubber.add_response(broker.interface['send'], expected_publish_response)

            commlink = Communicator(Config(broker, **fake_credentials))
            topic_creation = commlink.declare_receiver(
                Bucket=bucket_name,
            )
            message_receipt = commlink.send(Message='some message!')

        self.assertEqual(topic_creation, expected_topic_response)
        self.assertEqual(message_receipt, expected_publish_response)
    
    def test_older(self):
        session = boto3.Session()
        pill = placebo.attach(session, data_path='/Users/withtwoemms/programming/python/recruitment')
        pill.playback()
        s3 = boto3.client('s3')
        # pp(s3.list_buckets())
        bucket = 'chicago-community-bond-fund-inmates-scraper'
        key = 'inmates/dekalb.json'
        object = s3.get_object(Bucket=bucket, Key=key)
        contents = object['Body'].read().decode('utf-8')
        pp(json.loads(contents))
    
    def test_old(self):
        session = boto3.Session()
        pill = placebo.attach(session, data_path='/Users/withtwoemms/programming/python/recruitment')
        pill.save_response(
            service='s3',
            operation='GetObject',
            response_data={'testing': True},
            http_response=200
        )
        pill.playback()
        s3 = boto3.client('s3')
    
    @patch('boto3.client')
    def test(self, mock_boto_client):
    # def test(self):
        region = 'some-region-1'
        broker = Broker.s3
        session = boto3.Session()
        pill = placebo.attach(session, data_path=self.fixtures)
        pill.playback()
        s3 = boto3.client('s3')
        bucket_name = 'chicago-community-bond-fund-inmates-scraper'
        key = 'inmates/dekalb.json'
        # object = s3.get_object(Bucket=bucket, Key=key)
        # contents = object['Body'].read().decode('utf-8')
        # pp(json.loads(contents))
        with Stubber(s3) as stubber:
            # stubber.add_response(
            #     broker.interface['declare_receiver'], expected_topic_response
            # )
            # stubber.add_response(broker.interface['send'], expected_publish_response)

            commlink = Communicator(Config(broker, **fake_credentials))
            topic_creation = commlink.declare_receiver(
                Bucket=bucket_name,
            )
            message_receipt = commlink.send(Message='some message!')

        self.assertEqual(topic_creation, {})
        self.assertEqual(message_receipt, {})
