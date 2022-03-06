from contextlib import contextmanager
from io import IOBase as Buffer

from botocore.session import get_session


acceptable_broker_names = (
    'kinesis',
    's3',
    'sns',
    'sqs',
)

fake_credentials = {
    'region_name': 'somewhere-in-the-world',
    'aws_access_key_id': 's3curityBadge!',
    'aws_secret_access_key': 'p@ssw0rd!',
    'endpoint_url': 'some-computer.com',
}


def client(client_type: str, region_name: str):
    return get_session().create_client(client_type, region_name=region_name)


@contextmanager
def uncloseable(buffer: Buffer):
    """Context manager which makes the buffer's close operation a no-op"""
    close = buffer.close
    buffer.close = lambda: None
    yield buffer
    buffer.close = close
    buffer.seek(0)  # fake close
