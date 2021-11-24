"""
vtelem - Implements an interface for getting and setting time on an object.
"""

# built-in
from contextlib import AbstractContextManager
from threading import RLock
from typing import Any, Optional, Type

from typing_extensions import Literal


class OptionalRLock(AbstractContextManager):
    """
    A class allowing easy transitions from using actual locking mechanisms or
    opting out, but keeping the context-manager semantics.
    """

    def __init__(
        self,
        make_lock: bool,
        item: Optional[Any] = None,
        lock_cls: Type[RLock] = RLock,
    ) -> None:
        """Construct a new optional lock."""

        assert not hasattr(self, "lock")
        self.lock: Optional[RLock] = None
        if make_lock:
            self.lock = lock_cls()
        self.item = item

    def __enter__(self) -> Optional[Any]:
        """Acquire the lock (if we have one) and return the locked item."""

        if self.lock is not None:
            self.lock.acquire()
        return self.item

    def __exit__(self, exc_type, __, ___) -> Literal[False]:
        """Release the lock if no exception was raised."""

        if exc_type is None and self.lock is not None:
            self.lock.release()
        return False


class LockEntity:  # pylint: disable=too-few-public-methods
    """A simple mix-in for adding a lock attribute to a class."""

    def __init__(self, make_lock: bool = True) -> None:
        """Construct a new locked entity."""

        if not hasattr(self, "lock"):
            self.lock: OptionalRLock = OptionalRLock(make_lock)


class TimeEntity(LockEntity):
    """A simple class for adding time-keeping to a parent."""

    def __init__(self, init_time: float = None) -> None:
        """Construct a new time entity."""

        super().__init__()
        self.time: float = init_time if init_time is not None else float()

    def advance_time(self, amount: float) -> None:
        """Advance this entity's time by a specified amount."""

        with self.lock:
            self.time += amount

    def set_time(self, time: float) -> None:
        """Set this entity's current time."""

        with self.lock:
            self.time = time

    def get_time(self) -> float:
        """Return this entity's current time."""

        return self.time
