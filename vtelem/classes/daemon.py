
"""
vtelem - Implements management of a synchronous task.
"""

# built-in
import time
from typing import Callable, Any

# internal
from .daemon_base import DaemonBase, DaemonState
from .telemetry_environment import TelemetryEnvironment


class Daemon(DaemonBase):
    """
    A class for scheduling a task at a specified rate and providing metrics if
    desired.
    """

    def __init__(self, name: str, task: Callable, rate: float,
                 iter_overrun_cb: Callable = None,
                 state_change_cb: Callable = None,
                 env: TelemetryEnvironment = None,
                 time_keeper: Any = None) -> None:
        """ Create a new daemon. """

        super().__init__(name, env, time_keeper)
        self.function["task"] = task
        self.function["sleep"] = time.sleep
        if time_keeper is not None:
            self.function["sleep"] = time_keeper.sleep
        self.function["rate"] = rate
        self.function["overrun"] = iter_overrun_cb
        if state_change_cb is not None:
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
            iter_start = self.get_time()
            self.function["task"](*args, **kwargs)
            iter_end = self.get_time()

            # await the next iteration
            sleep_amount = rate - (self.get_time() - iter_start)
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
