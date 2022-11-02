from botocore.stub import Stubber
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from recruitment.agency import Job
from recruitment.agency import Coordinator
from recruitment.agency.resources import Broker
from tests.recruitment.agency import client


class JobTest(TestCase):

    broker = Broker.s3
    region = 'some-region-1'
    boto_client = client(broker.name, region)

    expected_create_target_response = {
        'ResponseMetadata': {
            'RequestId': 'MV004T58ZZ31T6TP',
            'HostId': 'pdeFdK6Uqq4yTyG4j+TdtrrG66PV8kc69qUHcj6cW7sIjpzjKYDFoy2acnO3TCAuVlX6qTbR1blyt+eM4C5nNg==',
            'HTTPStatusCode': 200,
            'HTTPHeaders': {
                'x-amz-id-2': 'pdeFdK6Uqq4yTyG4j+TdtrrG66PV8kc69qUHcj6cW7sIjpzjKYDFoy2acnO3TCAuVlX6qTbR1blyt+eM4C5nNg==',
                'x-amz-request-id': 'MV004T58ZZ31T6TP',
                'date': 'Sun, 30   Oct 2022 15:55:02 GMT',
                'location': '/test-bucket',
                'server': 'AmazonS3',
                'content-length': '0'
            },
            'RetryAttempts': 0
        },
        'Location': '/test-bucket'
    }

    @patch('boto3.client')
    def test_can_create_target(self, mock_boto_client):
        mock_boto_client.return_value = self.boto_client
        mock_commlink = MagicMock()
        mock_commlink.create_target.__name__ = 'create_target'
        mock_commlink.create_target.return_value = self.expected_create_target_response
        with Stubber(self.boto_client) as stubber:
            stubber.add_response(
                self.broker.interface['create_target'], self.expected_create_target_response
            )
            job = Job(Coordinator(mock_commlink))
            result = job.create_target(Bucket='test-bucket')

        self.assertTrue(result.successful)
        self.assertDictEqual(result.value, self.expected_create_target_response)
