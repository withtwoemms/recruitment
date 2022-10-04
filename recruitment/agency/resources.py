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
        declare_receiver = 'declare_receiver'
        receive = 'receive'
        methods_for = {
            Broker.logs: {receive: 'get_log_events'},
            Broker.s3: {send: 'upload_fileobj', declare_receiver: 'create_bucket'},
            Broker.sns: {send: 'publish', declare_receiver: 'create_topic'},
            Broker.sqs: {send: 'send_message', declare_receiver: 'create_queue'},
            Broker.kinesis: {send: 'put_record', declare_receiver: 'create_stream'},
        }
        return methods_for[self]


class From(NaturalEnum):
    env = auto()
    file = auto()


class CloudProvider(NaturalEnum):
    AWS = auto()
    