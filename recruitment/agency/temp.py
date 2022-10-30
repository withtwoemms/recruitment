from typing import Iterable
from typing import Optional
from unittest.mock import patch

from recruitment.agency import Commlink as ActualCommlink
from recruitment.agency import Config


class Commlink(ActualCommlink):

    def __init__(
        self,
        config: Config,
        expected_payload: Optional[dict] = None,
        expected_args: Optional[Iterable] = None,
        expected_kwargs: Optional[dict] = None
    ):
        super().__init__(config)
        self.response_provider = lambda: expected_payload or {}
        self.args_provider = lambda: expected_args or ()
        self.kwargs_provider = lambda: expected_kwargs or {}

    def __enter__(self):
        self.patcher = patch('botocore.client.BaseClient._make_api_call')
        self.mock = self.patcher.start()
        self.mock.return_value = self.response_provider()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Given a call signature for `botocore.client.BaseClient._make_api_call` as follows:
            def _make_api_call(self, operation_name, api_params):
                ...
        where, for example, operation_name and api_params could be:
            * GetLogEvents
            * {'logGroupName': ..., 'logStreamName': ...}
        """
        self.mock.assert_called_with(*self.args_provider(), **self.kwargs_provider())
        self.patcher.stop()
