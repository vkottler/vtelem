
"""
vtelem - Implements management of a synchronous task.
"""

# built-in
from typing import Callable

# internal
from .daemon_base import DaemonBase, DaemonState


class Daemon(DaemonBase):
    """
    A class for scheduling a task at a specified rate and providing metrics if
    desired.
    """

    def __init__(self, task: Callable, rate: float, get_time_fn: Callable,
                 sleep_fn: Callable, name: str = None,
                 iter_overrun_cb: Callable = None,
                 iter_metrics_cb: Callable = None,
                 state_change_cb: Callable = None) -> None:
        """ Create a new daemon. """

        super().__init__(name)
        self.function["task"] = task
        self.function["time"] = get_time_fn
        self.function["sleep"] = sleep_fn
        self.function["rate"] = rate
        self.function["overrun"] = iter_overrun_cb
        self.function["metrics"] = iter_metrics_cb
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
            self.increment_metric("count")

            # call the metrics callback if applicable
            if self.function["metrics"] is not None:
                with self.lock:
                    self.function["metrics"](iter_start, iter_end, rate,
                                             self.function["metrics_data"])

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
