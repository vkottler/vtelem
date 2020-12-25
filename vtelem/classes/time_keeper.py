
"""
vtelem - A class for managing application time.
"""

# built-in
import time
import threading
from typing import Callable, List

# internal
from .daemon import Daemon
from .time_entity import TimeEntity


class TimeKeeper(Daemon):
    """
    A class for managing a notion of time for an arbitrary number of slaves.
    """

    def __init__(self, rate: float, real_scalar: float = 1.0,
                 time_fn: Callable = None,
                 sleep_fn: Callable = None):
        """ Construct a new time keeper. """

        if time_fn is None:
            time_fn = time.time
        if sleep_fn is None:
            sleep_fn = time.sleep

        self.time_function = time_fn
        self.sleep_function = sleep_fn
        super().__init__(self.iteration, rate, self.time_function,
                         self.sleep_function, "time")
        self.slaves: List[TimeEntity] = []
        self.scalar = real_scalar
        assert self.scalar >= 0.0
        self.lock = threading.RLock()
        self.time_raw = self.time_function()

    def iteration(self) -> None:
        """ On every iteration, advance time for all slaves. """

        self.advance_slaves()

    def add_slave(self, slave: TimeEntity) -> None:
        """ Add a new slave under this keeper's management. """

        with self.lock:
            self.slaves.append(slave)
        self.set_slaves()

    def set_slaves(self) -> None:
        """ Set slave time. """

        curr_time = self.time()
        with self.lock:
            for slave in self.slaves:
                slave.set_time(curr_time)

    def advance_slaves(self) -> None:
        """ Advance slave time. """

        curr_time = self.time()
        with self.lock:
            for slave in self.slaves:
                slave.advance_time(curr_time - slave.get_time())

    def scale(self, scalar: float) -> None:
        """ Change the current time scaling. """

        if scalar >= 0.0:
            with self.lock:
                self.scalar = scalar

    def time(self) -> float:
        """
        Return time, scaled by 'scalar' with 'real' time. Truth is updated
        when this is called.
        """

        with self.lock:
            delta = self.time_function() - self.time_raw
            self.time_raw = delta * self.scalar
            return self.time_raw

    def sleep(self, amount: float) -> None:
        """ Sleep for the specified amount, scaled appropriately. """

        self.sleep_function(amount / self.scalar)
