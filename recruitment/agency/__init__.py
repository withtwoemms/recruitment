import boto3

from dataclasses import asdict
from dataclasses import dataclass
from enum import Enum
from enum import auto
from functools import reduce
from functools import partial
from os import environ as envvars
from pathlib import Path
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Union

from botocore.exceptions import NoRegionError
from actionpack import Action
from actionpack.actions import Call
from actionpack.actions import Remove
from actionpack.actions import RetryPolicy
from actionpack.actions import Write
from actionpack.utils import Closure


class Broker(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

    s3 = auto()
    sns = auto()
    sqs = auto()
    kinesis = auto()

    @property
    def interface(self) -> Dict[str, Optional[str]]:
        send = 'send'
        declare_receiver = 'declare_receiver'
        methods_for = {
            Broker.s3: {send: 'upload_file', declare_receiver: 'create_bucket'},
            Broker.sns: {send: 'publish', declare_receiver: 'create_topic'},
            Broker.sqs: {send: 'send_message', declare_receiver: 'create_queue'},
            Broker.kinesis: {send: 'put_record', declare_receiver: 'create_stream'},
        }
        return methods_for[self]


@dataclass
class Config:
    service_name: Union[str, Broker]
    region_name: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    endpoint_url: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.service_name, Broker):
            self.service_name = self.service_name.value
        else:
            self.service_name = Broker(self.service_name).value

    def __str__(self):
        return reduce(
            lambda a, b: f'{a}' + f'{b[0]}={b[1]}, ', asdict(self).items(), ''
        ).strip(', ')


class Communicator:

    # send messages
    # declare receivers
    # list receivers

    def __init__(
        self,
        config: Config,
        # client_provider: Callable[[], boto3.Session.client]
    ):
        broker = Broker(config.service_name)  # maybe redundant
        _client = partial(boto3.client, service_name=broker.name)
        for alias, method in broker.interface.items():
            # TODO (withtwoemms) -- validate config.region_name and .endpoint_url
            try:
                client = _client(
                    region_name=config.region_name, endpoint_url=config.endpoint_url
                )
            except (ValueError, NoRegionError) as e:
                # NOTE: can replace `from` with 'dispatch across exceptions' for nuance
                raise Communicator.FailedToInstantiate(given=config) from e
            setattr(self, alias, getattr(client, method))

    class FailedToInstantiate(Exception):
        def __init__(self, given: Config):
            super().__init__(str(given))


class Agent:

    # perform actions
    # TODO (withtwoemms) -- add error logfile header for simpler parsing

    local_storage_dir = Path.home() / '.recruitment/agency/'
    deadletters = local_storage_dir / envvars.get('DEADLETTER_FILE', 'dead.letters')

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


class Janitor(Agent):
    """Will read from local storage and retry failed Agent.publish Actions"""
    
    def consume(self):
        _consume = Remove(filename=self.local_storage_dir / self.error_logfilename)
        result = _consume.perform()
        if result.successful:
            return result.value
        else:
            raise result.value
