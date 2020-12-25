
"""
vtelem - Implements management of a synchronous task.
"""

# built-in
from typing import Callable

# internal
from .daemon_base import DaemonBase, DaemonState
from .telemetry_environment import TelemetryEnvironment


class Daemon(DaemonBase):
    """
    A class for scheduling a task at a specified rate and providing metrics if
    desired.
    """

    def __init__(self, name: str, task: Callable, rate: float,
                 get_time_fn: Callable, sleep_fn: Callable,
                 iter_overrun_cb: Callable = None,
                 state_change_cb: Callable = None,
                 env: TelemetryEnvironment = None) -> None:
        """ Create a new daemon. """

        super().__init__(name, get_time_fn, env)
        self.function["task"] = task
        self.function["sleep"] = sleep_fn
        self.function["rate"] = rate
        self.function["overrun"] = iter_overrun_cb
        self.function["state_change"] = state_change_cb

    def run(self, *args, **kwargs) -> None:
        """ Runs this daemon's thread, until stop is requested. """

        while self.state != DaemonState.STOPPING:
            with self.lock:
                rate = self.function["rate"]

            # just sleep while we're paused
            if self.state == DaemonState.PAUSED:
                self.function["sleep"](rate)
                continue

            # run the iteration
            iter_start = self.function["time"]()
            self.function["task"](*args, **kwargs)
            iter_end = self.function["time"]()

            # await the next iteration
            sleep_amount = rate - (self.function["time"]() - iter_start)
            if sleep_amount > 0.0:
                self.function["sleep"](sleep_amount)
            elif self.function["overrun"] is not None:
                with self.lock:
                    self.function["overrun"](iter_start, iter_end, rate,
                                             self.function["metrics_data"])

    def set_rate(self, rate: float) -> None:
        """ Set the rate for the daemon. """

        with self.lock:
            self.function["rate"] = rate
