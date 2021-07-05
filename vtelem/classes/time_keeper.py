"""
vtelem - A class for managing application time.
"""

# built-in
import time
from typing import Callable, List, Any

# internal
from .daemon import Daemon


class TimeKeeper(Daemon):
    """
    A class for managing a notion of time for an arbitrary number of slaves.
    """

    def __init__(
        self,
        name: str,
        rate: float,
        real_scalar: float = 1.0,
        time_fn: Callable = None,
        sleep_fn: Callable = None,
    ):
        """Construct a new time keeper."""

        if time_fn is None:
            time_fn = time.time
        if sleep_fn is None:
            sleep_fn = time.sleep

        self.time_function = time_fn
        self.sleep_function = sleep_fn
        self.scalar = real_scalar
        assert self.scalar >= 0.0
        self.time = self.time_function()
        self.last_time_eval = self.time
        super().__init__(name, self.iteration, rate)
        self.time = self.last_time_eval
        self.function["sleep"] = self.sleep_function
        self.slaves: List[Any] = []

    def iteration(self, *_, **__) -> None:
        """On every iteration, advance time for all slaves."""

        with self.lock:
            curr = self.time_function()
            self.advance_time((curr - self.last_time_eval) * self.scalar)
            self.last_time_eval = curr

        self.set_slaves()

    def add_slave(self, slave: Any) -> None:
        """Add a new slave under this keeper's management."""

        with self.lock:
            slave.set_time(self.get_time())
            self.slaves.append(slave)

    def set_slaves(self) -> None:
        """Set slave time."""

        with self.lock:
            curr_time = self.get_time()
            for slave in self.slaves:
                slave.set_time(curr_time)

    def scale(self, scalar: float) -> None:
        """Change the current time scaling."""

        if scalar >= 0.0:
            with self.lock:
                self.scalar = scalar

    def sleep(self, amount: float) -> None:
        """Sleep for the specified amount, scaled appropriately."""

        self.sleep_function(amount / self.scalar)
