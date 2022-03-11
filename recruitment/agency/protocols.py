from typing import Callable
from typing import Optional
from typing import Protocol
from typing import runtime_checkable

from actionpack import Action
from actionpack.actions import RetryPolicy
from actionpack.actions import Write


@runtime_checkable
class HasContingency(Protocol):
    retry_policy_provider: Optional[Callable[[Action], RetryPolicy]] = None
    record_failure_provider: Optional[Callable[[], Write]] = None
