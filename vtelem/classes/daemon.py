"""
vtelem - Implements management of a synchronous task.
"""

# built-in
import logging
import time
from typing import Callable, Any

# internal
from vtelem.enums.primitive import Primitive
from . import LOG_PERIOD
from .daemon_base import DaemonBase, DaemonState
from .telemetry_environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)


class Daemon(DaemonBase):
    """
    A class for scheduling a task at a specified rate and providing metrics if
    desired.
    """

    def __init__(
        self,
        name: str,
        task: Callable,
        rate: float,
        iter_overrun_cb: Callable = None,
        state_change_cb: Callable = None,
        env: TelemetryEnvironment = None,
        time_keeper: Any = None,
        init: Callable = None,
    ) -> None:
        """Create a new daemon."""

        super().__init__(name, env, time_keeper)
        self.function["task"] = task
        self.function["init"] = init
        self.function["sleep"] = time.sleep
        if time_keeper is not None:
            self.function["sleep"] = time_keeper.sleep
        self.function["rate"] = rate
        if state_change_cb is not None:
            self.function["state_change"] = state_change_cb

        def default_overrun(
            start: float, end: float, rate: float, metrics_data: dict
        ) -> None:
            """A default handler for overrun conditions."""

            last_log_delta = end - metrics_data["last_overrun_time"]
            if last_log_delta >= metrics_data["overrun_throttle"]:
                over = (end - start) - rate
                log_str = (
                    "%-10s - %.3f: most recent overrun was %.3f over "
                    + "(%d overruns)"
                )
                LOG.warning(
                    log_str, self.name, rate, over, metrics_data["overruns"]
                )

            metrics_data["last_overrun_time"] = end

        if iter_overrun_cb is None:
            self.function["metrics_data"]["overrun_throttle"] = LOG_PERIOD
            self.function["overrun"] = default_overrun
        else:
            self.function["overrun"] = iter_overrun_cb

        self.reset_metric("overruns")
        self.set_env_metric("uptime", 0.0, Primitive.FLOAT)
        self.set_env_metric("cycle_time", 0.0, Primitive.FLOAT)

    def get_rate(self) -> float:
        """Get the current daemon-iteration rate."""

        return self.function["rate"]

    def run(self, *args, **kwargs) -> None:
        """Runs this daemon's thread, until stop is requested."""

        # call an initialization routine if provided
        if self.function["init"] is not None:
            self.function["init"](*args, **kwargs)

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

            # keep runtime metrics
            self.increment_metric("uptime", iter_end - iter_start)
            self.set_env_metric(
                "cycle_time", iter_end - iter_start, Primitive.FLOAT
            )

            # await the next iteration
            sleep_amount = rate - (self.get_time() - iter_start)
            if sleep_amount > 0.0:
                self.function["sleep"](sleep_amount)
            elif self.function["overrun"] is not None:
                self.increment_metric("overruns")
                self.function["overrun"](
                    iter_start, iter_end, rate, self.function["metrics_data"]
                )

    def set_rate(self, rate: float) -> None:
        """Set the rate for the daemon."""

        if rate > 0.0:
            with self.lock:
                self.function["rate"] = rate
