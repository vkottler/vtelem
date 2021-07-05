"""
vtelem - Implements an interface for getting and setting time on an object.
"""

# built-in
import threading


class LockEntity:  # pylint: disable=too-few-public-methods
    """A simple mix-in for adding a lock attribute to a class."""

    def __init__(self) -> None:
        """Construct a new locked entity."""

        if not hasattr(self, "lock"):
            self.lock = threading.RLock()


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
