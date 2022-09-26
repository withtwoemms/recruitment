from typing import Iterable
from typing import Optional

from recruitment.agency import Communicator as ActualCommunicator
from recruitment.agency import Config


class Communicator(ActualCommunicator):

    def __init__(
        self,
        config: Config,
        expected_payload: Optional[dict] = None,
        expected_args: Optional[Iterable] = None,
        expected_kwargs: Optional[dict] = None
    ):
        self.response_provider = lambda: expected_payload or {}
        self.args_provider = lambda: expected_args or {}
        self.kwargs_provider = lambda: expected_kwargs or {}
        super().__init__(config)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Given a call signature for `botocore.client.BaseClient._make_api_call` as follows:
            def _make_api_call(self, operation_name, api_params):
                ...
        where, for example, operation_name and api_params could be:
            * GetLogEvents
            * {'logGroupName': ..., 'logStreamName': ...}
        """
        return
