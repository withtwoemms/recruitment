import boto3

from actionpack import Action
from actionpack.actions import Call
from actionpack.utils import Closure
from botocore.exceptions import NoRegionError
from dataclasses import asdict
from dataclasses import dataclass
from functools import reduce
from os import environ as envvars
from pathlib import Path
from typing import Callable
from typing import Optional
from typing import Union

from recruitment.agency.protocols import HasContingency
from recruitment.agency.resources import Append
from recruitment.agency.resources import Broker
from recruitment.agency.resources import CloudProvider
from recruitment.agency.resources import From
from recruitment.agency.resources import RecordedRetryPolicy


Reaction = Action

local_storage_dir = Path.home() / '.recruitment/agency/'
deadletters = local_storage_dir / 'deadletters'  # failures


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


class Commlink:
    """An object that hosts the Broker.interface"""

    def __init__(self, config: Config):
        broker = Broker(config.service_name)  # maybe redundant
        for alias, method in broker.interface.items():
            try:
                client = boto3.client(
                    service_name=config.service_name,
                    region_name=config.region_name,
                    aws_access_key_id=config.access_key_id,
                    aws_secret_access_key=config.secret_access_key,
                    endpoint_url=config.endpoint_url
                )
            except (ValueError, NoRegionError) as e:
                raise Commlink.FailedToInstantiate(given=config) from e
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


class Contingency:

    def __init__(
        self,
        retry_policy_provider: Optional[Callable[[Action, Optional[Reaction]], RecordedRetryPolicy]] = None
    ):
        if retry_policy_provider:
            self.retry_policy_provider = retry_policy_provider


class Coordinator:

    def __init__(
        self,
        commlink: Commlink,
        contingency: Optional[Contingency] = None
    ):
        self.commlink = commlink
        if contingency:
            self.retry_policy_provider = contingency.retry_policy_provider

    @property
    def has_contingency(self) -> bool:
        return isinstance(self, HasContingency)

    def do(self, action: Action, reaction: Optional[Reaction] = None):
        if self.has_contingency:
            retry_policy = self.retry_policy_provider(action, reaction) if reaction else self.retry_policy_provider(action)
            return retry_policy.perform(), retry_policy.attempts  # Effort type
        else:
            return action.perform()


class Publisher:
    """A namespace for publishing messages"""

    def __init__(self, coordinator: Coordinator):
        self.coordinator = coordinator

    def publish(self, *args, **kwargs):
        send_communique = Call(Closure(self.coordinator.commlink.send, *args, **kwargs))
        return self.coordinator.do(send_communique)


class Consumer:
    """A namespace for consuming messages

    TODO (withtwoemms) -- add error logfile header for simpler parsing
    """

    def __init__(self, coordinator: Coordinator):
        self.coordinator = coordinator

    def consume(self, *args, **kwargs):
        receive_communique = Call(Closure(self.coordinator.commlink.receive, *args, **kwargs))
        return self.coordinator.do(receive_communique)


class Agent:
    """A namespace for consuming and/or publishing messages"""

    def __init__(self, consumer: Consumer, publisher: Publisher):
        if not isinstance(consumer, Consumer):
            raise TypeError(f'{self.__class__.__name__} consumer must be of type {Consumer.__name__} not {type(consumer).__name__}')
        if not isinstance(publisher, Publisher):
            raise TypeError(f'{self.__class__.__name__} publisher must be of type {Publisher.__name__} not {type(publisher).__name__}')

        setattr(self, consumer.consume.__name__, consumer.consume)
        setattr(self, publisher.publish.__name__, publisher.publish)
