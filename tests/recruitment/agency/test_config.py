from dataclasses import asdict
from unittest import TestCase

from tests.recruitment.agency import acceptable_broker_names
from tests.recruitment.agency import fake_credentials
from recruitment.agency import Config


class ConfigTest(TestCase):
    def test_cannot_instantiate_given_invalid_Broker_type(self):
        with self.assertRaises(ValueError):
            Config('invalid Broker type')

    def test_can_instantiate(self):
        for name in acceptable_broker_names:
            config = Config(name, **fake_credentials)
            config_dict = asdict(config)
            config_dict.pop('service_name')
            self.assertDictEqual(config_dict, fake_credentials)

    def test_can_serialize(self):
        config = Config(acceptable_broker_names[0], **fake_credentials)
        expected_string = (
            'service_name=kinesis, region_name=somewhere-in-the-world, '
            'aws_access_key_id=s3curityBadge!, aws_secret_access_key=p@ssw0rd!, '
            'endpoint_url=some-computer.com'
        )
        self.assertEqual(str(config), expected_string)
