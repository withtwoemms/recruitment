from os import environ as envvars
from textwrap import dedent
from unittest import TestCase
from unittest.mock import patch

from tests.recruitment.agency import acceptable_broker_names
from tests.recruitment.agency import fake_credentials
from tests.recruitment.agency import fake_credentials_with_session_token
from recruitment.agency import Config


class ConfigTest(TestCase):

    broker_name = acceptable_broker_names[0]  # logs
    expected_serialization = dedent(
        f"""\
        service_name={broker_name}
        region_name=somewhere-in-the-world
        access_key_id=s3curityBadge!
        secret_access_key=p@ssw0rd!
        endpoint_url=some-computer.com"""
    )
    expected_serialization_missing_values = dedent(
        f"""\
        service_name={broker_name}
        region_name=
        access_key_id=
        secret_access_key=
        endpoint_url="""
    )

    def test_cannot_instantiate_given_invalid_Broker_type(self):
        with self.assertRaises(ValueError):
            Config('invalid Broker type')

    def test_can_instantiate(self):
        for name in acceptable_broker_names:
            config = Config(name, **fake_credentials)
            config_dict = dict(config)
            config_dict.pop('service_name')
            self.assertDictEqual(config_dict, fake_credentials)

    def test_can_instantiate_with_session_token(self):
        for name in acceptable_broker_names:
            config = Config(name, **fake_credentials_with_session_token)
            config_dict = dict(config)
            config_dict.pop('service_name')
            self.assertDictEqual(config_dict, fake_credentials_with_session_token)

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

    @patch.dict(
        envvars,
        {
            'AWS_SERVICE_NAME': broker_name,
            'AWS_REGION_NAME': fake_credentials['region_name'],
            'AWS_ACCESS_KEY_ID': fake_credentials['access_key_id'],
            'AWS_SECRET_ACCESS_KEY': fake_credentials['secret_access_key'],
            'AWS_ENDPOINT_URL': fake_credentials['endpoint_url'],
        },
        clear=True
    )
    def test_can_constitute_from_environment_variabiles(self):
        config = Config.fromenv()
        self.assertEqual(config.region_name, fake_credentials['region_name'])
        self.assertEqual(config.access_key_id, fake_credentials['access_key_id'])
        self.assertEqual(config.secret_access_key, fake_credentials['secret_access_key'])
        self.assertEqual(config.endpoint_url, fake_credentials['endpoint_url'])

    @patch.dict(
        envvars,
        {
            'AWS_SERVICE_NAME': broker_name,
            'AWS_REGION_NAME': fake_credentials['region_name'],
            'AWS_ACCESS_KEY_ID': fake_credentials['access_key_id'],
            'AWS_SECRET_ACCESS_KEY': fake_credentials['secret_access_key'],
            'AWS_ENDPOINT_URL': fake_credentials['endpoint_url'],
        },
        clear=True
    )
    def test_can_supplement_Config_instance_from_environment(self):
        some_service_name = 'kinesis'
        self.assertNotEqual(self.broker_name, some_service_name)
        config = Config(service_name=some_service_name)
        self.assertEqual(config.service_name, some_service_name)
        self.assertEqual(config.region_name, None)
        self.assertEqual(config.access_key_id, None)
        self.assertEqual(config.secret_access_key, None)
        self.assertEqual(config.endpoint_url, None)
        config = config.supplement('env')
        self.assertEqual(config.service_name, some_service_name)
        self.assertEqual(config.region_name, fake_credentials['region_name'])
        self.assertEqual(config.access_key_id, fake_credentials['access_key_id'])
        self.assertEqual(config.secret_access_key, fake_credentials['secret_access_key'])
        self.assertEqual(config.endpoint_url, fake_credentials['endpoint_url'])

    @patch.dict(
        envvars,
        {
            'AWS_SERVICE_NAME': broker_name,
            'AWS_REGION_NAME': fake_credentials_with_session_token['region_name'],
            'AWS_ACCESS_KEY_ID': fake_credentials_with_session_token['access_key_id'],
            'AWS_SECRET_ACCESS_KEY': fake_credentials_with_session_token['secret_access_key'],
            'AWS_SESSION_TOKEN': fake_credentials_with_session_token['session_token'],
            'AWS_ENDPOINT_URL': fake_credentials_with_session_token['endpoint_url'],
        },
        clear=True
    )
    def test_can_supplement_Config_instance_from_environment_with_session_token(self):
        some_service_name = 'kinesis'
        self.assertNotEqual(self.broker_name, some_service_name)
        config = Config(service_name=some_service_name)
        self.assertEqual(config.service_name, some_service_name)
        self.assertEqual(config.region_name, None)
        self.assertEqual(config.access_key_id, None)
        self.assertEqual(config.secret_access_key, None)
        self.assertEqual(config.session_token, None)
        self.assertEqual(config.endpoint_url, None)
        config = config.supplement('env')
        self.assertEqual(config.service_name, some_service_name)
        self.assertEqual(config.region_name, fake_credentials_with_session_token['region_name'])
        self.assertEqual(config.access_key_id, fake_credentials_with_session_token['access_key_id'])
        self.assertEqual(config.secret_access_key, fake_credentials_with_session_token['secret_access_key'])
        self.assertEqual(config.session_token, fake_credentials_with_session_token['session_token'])
        self.assertEqual(config.endpoint_url, fake_credentials_with_session_token['endpoint_url'])

    @patch.dict(
        envvars,
        {
            'AWS_SERVICE_NAME': broker_name,
            'AWS_SESSION_TOKEN': '',
        },
        clear=True
    )
    def test_session_token_attr_absent_if_envvar_is_empty(self):
        config = Config.fromenv()
        with self.assertRaises(AttributeError):
            config.session_token

    @patch.dict(
        envvars,
        {
            'AWS_SERVICE_NAME': broker_name,
            'AWS_SESSION_TOKEN': fake_credentials_with_session_token['session_token'],
        },
        clear=True
    )

    def test_session_token_attr_present_if_envvar_has_value(self):
        config = Config.fromenv()
        self.assertEqual(config.session_token, fake_credentials_with_session_token['session_token'])

    @patch.dict(
        envvars,
        {
            'AWS_SERVICE_NAME': broker_name,
            'AWS_REGION_NAME': fake_credentials_with_session_token['region_name'],
            'AWS_ACCESS_KEY_ID': fake_credentials_with_session_token['access_key_id'],
            'AWS_SECRET_ACCESS_KEY': fake_credentials_with_session_token['secret_access_key'],
            'AWS_SESSION_TOKEN': fake_credentials_with_session_token['session_token'],
            'AWS_ENDPOINT_URL': fake_credentials_with_session_token['endpoint_url'],
        },
        clear=True
    )
    def test___repr__(self):
        # sensitive to env ordering
        obj_repr = ('Config(service_name=logs, '
                    'region_name=somewhere-in-the-world, '
                    'access_key_id=s3curityBadge!, '
                    'secret_access_key=p@ssw0rd!, '
                    'endpoint_url=some-computer.com, '
                    'session_token=jamSesh3000!)')
        self.assertEqual(obj_repr, repr(Config.fromenv()))

    def test_cannot_instantiate_without_service_name(self):
        with self.assertRaises(Config.AttributeDeclaredIncorrectly):
            Config(None)

    def test_cannot_instantiate_with_invalid_service_name(self):
        with self.assertRaises(Config.AttributeDeclaredIncorrectly):
            Config(1)
