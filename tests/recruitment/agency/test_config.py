from dataclasses import asdict
from textwrap import dedent
from unittest import TestCase

from tests.recruitment.agency import acceptable_broker_names
from tests.recruitment.agency import fake_credentials
from recruitment.agency import Config


class ConfigTest(TestCase):

    broker_name = acceptable_broker_names[0]  # kinesis
    expected_serialization = dedent(
        f"""\
        service_name={broker_name}
        region_name=somewhere-in-the-world
        aws_access_key_id=s3curityBadge!
        aws_secret_access_key=p@ssw0rd!
        endpoint_url=some-computer.com"""
    )
    expected_serialization_missing_values = dedent(
        f"""\
        service_name={broker_name}
        region_name=
        aws_access_key_id=
        aws_secret_access_key=
        endpoint_url="""
    )

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
        config = Config(self.broker_name, **fake_credentials)
        self.assertEqual(str(config), self.expected_serialization)

    def test_can_serialize_given_absent_values(self):
        config = Config(self.broker_name)
        self.assertEqual(str(config), self.expected_serialization_missing_values)

    def test_can_serialize_asfile(self):
        profile_name = 'testing'
        config = Config(self.broker_name, **fake_credentials)
        self.assertEqual(
            config.asfile(profile=profile_name),
            f'[{profile_name}]\n' + self.expected_serialization,
        )
        config_missing_values = Config(self.broker_name)
        self.assertEqual(
            config_missing_values.asfile(profile=profile_name),
            f'[{profile_name}]\n' + self.expected_serialization_missing_values,
        )
