from actionpack.action import Result
from actionpack.actions import RetryPolicy
from actionpack.actions import Write
from actionpack import partialaction
from enum import auto
from enum import Enum
from typing import Dict
from typing import List
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


#- Helpful Types ----------------------------->>>


class Effort:

    def __init__(self, culmination: Result, *attempts: List[Result]):
        self.culmination: Result = culmination
        self.attempts: List[Result] = list(attempts)
        self.initial_attempt: Result
        self.retries: List[Result]
        if any(attempts):
            self.initial_attempt, *self.retries = attempts
        else:
            self.initial_attempt, self.retries = culmination, []
            self.attempts.append(self.initial_attempt)
        self.final_attempt = self.retries[-1] if any(self.retries) else self.initial_attempt

    def __repr__(self) -> str:
        name = self.__class__.__name__
        retries = ':retries' if self.retries else ''
        status = 'succeeded' if self.culmination.successful else 'failed'

        return f'<{name}:{status}{retries}>'


#- Custom Actions ---------------------------->>>


Append = partialaction('Append', Write, append=True)
RecordedRetryPolicy = partialaction('RecordedRetryPolicy', RetryPolicy, should_record=True)
    