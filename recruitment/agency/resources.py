from actionpack.actions import RetryPolicy
from actionpack.actions import Write
from actionpack import partialaction
from enum import auto
from enum import Enum
from typing import Dict
from typing import Optional


class NaturalEnum(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class Broker(NaturalEnum):
    """A repository for declaring services and their interfaces"""

    logs = auto()
    s3 = auto()
    sns = auto()
    sqs = auto()
    kinesis = auto()

    @property
    def interface(self) -> Dict[str, Optional[str]]:
        send = 'send'
        create_target = 'create_target'
        receive = 'receive'
        methods_for = {
            Broker.logs: {receive: 'get_log_events'},
            Broker.s3: {
                create_target: 'create_bucket',
                receive: 'get_object',
                send: 'upload_fileobj',
            },
            Broker.sns: {send: 'publish', create_target: 'create_topic'},
            Broker.sqs: {
                create_target: 'create_queue',
                receive: 'receive_message',
                send: 'send_message',
            },
            Broker.kinesis: {send: 'put_record', create_target: 'create_stream'},
        }
        return methods_for[self]  # KeyError should be contextualized as NotImplementedError


class From(NaturalEnum):
    env = auto()
    file = auto()


class CloudProvider(NaturalEnum):
    AWS = auto()


#- Custom Actions ---------------------------->>>
Append = partialaction('Append', Write, append=True)
RecordedRetryPolicy = partialaction('RecordedRetryPolicy', RetryPolicy, should_record=True)
    