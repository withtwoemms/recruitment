import boto3

from actionpack import Action
from actionpack.actions import Call
from actionpack.actions import Remove
from actionpack.actions import RetryPolicy
from actionpack.actions import Write
from actionpack.utils import Closure
from botocore.exceptions import NoRegionError
from dataclasses import asdict
from dataclasses import dataclass
from functools import reduce
from functools import partial
from os import environ as envvars
from pathlib import Path
from typing import Callable
from typing import Optional
from typing import Union

from recruitment.agency.resources import Broker
from recruitment.agency.resources import CloudProvider
from recruitment.agency.resources import From


local_storage_dir = Path.home() / '.recruitment/agency/'
deadletters = local_storage_dir / 'deadletters'


@dataclass
class Config:
    """An object for conveying configuration info"""

    service_name: Union[str, Broker]
    region_name: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    endpoint_url: Optional[str] = None

    @staticmethod
    def fromenv():
        return Config(
            service_name=envvars.get('AWS_SERVICE_NAME'),
            region_name=envvars.get('AWS_REGION_NAME'),
            access_key_id=envvars.get('AWS_ACCESS_KEY_ID'),
            secret_access_key=envvars.get('AWS_SECRET_ACCESS_KEY'),
            endpoint_url=envvars.get('AWS_ENDPOINT_URL')
        )

    def supplement(self, fromhere: str):
        fromwhere = From(fromhere)
        unset = {}
        if fromwhere == From.env:
            for k, v in asdict(self).items():
                if v is None:
                    unset[k] = envvars.get(f'{CloudProvider.AWS.value}_{k.upper()}')
        if fromwhere == From.file:
            raise NotImplementedError('Coming soon.')

        return Config(**{**asdict(self), **unset})

    def asfile(self, profile: str = 'default'):
        return f'[{profile}]\n{str(self)}'

    def __post_init__(self):
        if self.service_name is None:
            raise Config.AttributeDeclaredIncorrectly('Missing service_name.')

        if isinstance(self.service_name, Broker):
            self.service_name = self.service_name.value
        elif isinstance(self.service_name, str):
            self.service_name = Broker(self.service_name).value
        else:
            service_name_type = type(self.service_name).__name__
            raise Config.AttributeDeclaredIncorrectly(
                f'Service name must be a <Broker> or <str>. Received <{service_name_type}>.'
            )

    def __str__(self):
        """Produces a string compatible with the AWS CLI tool
        (see documentation for details:
         https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
        """
        return reduce(
            lambda a, b: f'{a}' + f'{b[0]}={b[1] if b[1] else ""}\n',
            asdict(self).items(),
            '',
        ).strip()

    class AttributeDeclaredIncorrectly(Exception):
        pass


class Communicator:
    """An object that hosts the Broker.interface"""

    def __init__(self, config: Config):
        broker = Broker(config.service_name)  # maybe redundant
        _client = partial(boto3.client, service_name=broker.name)
        for alias, method in broker.interface.items():
            try:
                client = _client(
                    region_name=config.region_name, endpoint_url=config.endpoint_url
                )
            except (ValueError, NoRegionError) as e:
                raise Communicator.FailedToInstantiate(given=config) from e
            setattr(self, alias, getattr(client, method))

    class FailedToInstantiate(Exception):
        def __init__(self, given: Config):
            redaction = '*' * 10
            redacted_config = Config(
                service_name=given.service_name,
                region_name=given.region_name,
                access_key_id=redaction,
                secret_access_key=redaction,
                endpoint_url=given.endpoint_url
            )
            super().__init__(str(redacted_config))


class Publisher:
    """A namespace for publishing messages"""

    def __init__(
        self,
        communicator: Communicator,
        retry_policy_provider: Optional[Callable[[Action], RetryPolicy]] = None,
        record_failure_provider: Optional[Callable[[], Write]] = None,
    ):
        self.communicator = communicator
        self.retry_policy_provider = retry_policy_provider
        self.record_failure_provider = record_failure_provider

    def publish(self, *args, **kwargs):
        send_communique = Call(Closure(self.communicator.send, *args, **kwargs))
        if self.retry_policy_provider:
            retry_policy = self.retry_policy_provider(send_communique)
            result = retry_policy.perform()

            if not result.successful and self.record_failure_provider:
                record_failure = self.record_failure_provider()
                record_failure.perform()

            return result, retry_policy.attempts
        else:
            return send_communique.perform()


class Consumer:
    """A namespace for consuming messages

    TODO (withtwoemms) -- add error logfile header for simpler parsing
    """

    deadletter_file = deadletters / 'consumer' / 'letters'

    def consume(self):
        """Consume from message bus"""
        raise NotImplementedError()

    def take_deadletter(self):
        _consume = Remove(filename=self.deadletter_file)
        return _consume.perform()


class Agent(Consumer, Publisher):
    """A namespace for consuming and/or publishing messages"""

    def __init__(
        self,
        communicator: Communicator,
        retry_policy_provider: Optional[Callable[[Action], RetryPolicy]] = None,
        record_failure_provider: Optional[Callable[[], Write]] = None,
    ):
        Publisher.__init__(self, communicator, retry_policy_provider, record_failure_provider)
