from actionpack.actions import RetryPolicy
from actionpack.actions import Write
from contextlib import contextmanager
from datetime import datetime
from io import IOBase as Buffer

from botocore.session import get_session


acceptable_broker_names = (
    'logs',
    'kinesis',
    's3',
    'sns',
    'sqs',
)

fake_credentials = {
    'region_name': 'somewhere-in-the-world',
    'access_key_id': 's3curityBadge!',
    'secret_access_key': 'p@ssw0rd!',
    'endpoint_url': 'some-computer.com',
}

write_to_deadletter_file = Write(
    prefix=f'-> [{datetime.utcnow()}] -- ',
    filename='some.file',
    to_write='failed',
    append=True,
    mkdir=True,
)


def client(client_type: str, region_name: str):
    return get_session().create_client(
        client_type,
        region_name=region_name,
    )


def raise_this(**kwargs):
    exception = kwargs['exception']
    def will_raise(**kwargs):
        raise exception
    return will_raise


@contextmanager
def uncloseable(buffer: Buffer):
    """Context manager which makes the buffer's close operation a no-op"""
    close = buffer.close
    buffer.close = lambda: None
    yield buffer
    buffer.close = close
    buffer.seek(0)  # fake close
