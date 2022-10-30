from typing import Callable
from typing import Optional
from typing import Protocol
from typing import runtime_checkable

from actionpack import Action
from actionpack.actions import RetryPolicy
from actionpack.actions import Write


@runtime_checkable
class HasContingency(Protocol):
    retry_policy_provider: Callable[[Action], RetryPolicy]
