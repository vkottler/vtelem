
"""
vtelem - Implements management of a synchronous task.
"""

# built-in
from collections import defaultdict
from enum import Enum
import threading
from typing import Callable, Any, Dict, Optional


class DaemonState(Enum):
    """ An enumeration of all valid daemon states. """

    ERROR = 0
    IDLE = 1
    STARTING = 2
    RUNNING = 3
    PAUSED = 4
    STOPPING = 5


class Daemon:
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

        self.state: DaemonState = DaemonState.IDLE
        self.name = name
        self.function: Dict[str, Any] = {}
        self.function["task"] = task
        self.function["time"] = get_time_fn
        self.function["sleep"] = sleep_fn
        self.function["rate"] = rate
        self.function["overrun"] = iter_overrun_cb
        self.function["metrics"] = iter_metrics_cb
        self.function["state_change"] = state_change_cb
        self.function["metrics_data"] = defaultdict(lambda: 0)
        self.lock = threading.RLock()
        self.thread: Optional[threading.Thread] = None

    def reset_metric(self, name: str) -> None:
        """ Set a metric back to zero. """

        if self.function["metrics"] is not None:
            with self.lock:
                self.function["metrics_data"][name] = 0

    def increment_metric(self, name: str) -> None:
        """ Increment a named metric. """

        if self.function["metrics"] is not None:
            with self.lock:
                self.function["metrics_data"][name] += 1

    def set_state(self, state: DaemonState) -> None:
        """ Assigns a new run-state to this daemon. """

        with self.lock:
            if self.state == state:
                return
            if self.function["state_change"] is not None:
                self.function["state_change"](self.state, state)
            self.state = state

    def get_state(self) -> DaemonState:
        """ Query this daemon's current state. """

        with self.lock:
            return self.state

    def run(self, *args, **kwargs) -> None:
        """ Runs this daemon's thread, until stop is requested. """

        self.set_state(DaemonState.RUNNING)

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

        # go back to idle when we stop iterating
        self.set_state(DaemonState.IDLE)

    def start(self, *args, **kwargs) -> bool:
        """ Attempt to start the daemon. """

        with self.lock:
            if self.state != DaemonState.IDLE:
                return False

            self.thread = threading.Thread(target=self.run, args=args,
                                           kwargs=kwargs, name=self.name)
            self.reset_metric("count")
            self.increment_metric("starts")
            self.set_state(DaemonState.STARTING)

        self.thread.start()
        return True

    def set_rate(self, rate: float) -> None:
        """ Set the rate for the daemon. """

        with self.lock:
            self.function["rate"] = rate

    def pause(self) -> bool:
        """ Attempt to pause the daemon. """

        with self.lock:
            if self.state == DaemonState.RUNNING:
                self.set_state(DaemonState.PAUSED)
                self.increment_metric("pauses")
                return True
        return False

    def unpause(self) -> bool:
        """ Attempt to un-pause the daemon. """

        with self.lock:
            if self.state == DaemonState.PAUSED:
                self.set_state(DaemonState.RUNNING)
                self.increment_metric("unpauses")
                return True
        return False

    def stop(self) -> bool:
        """ Attempt to stop the daemon. """

        # make sure we're in the correct state to attempt a stop
        wait_thread = False
        with self.lock:
            if self.state == DaemonState.RUNNING:
                self.set_state(DaemonState.STOPPING)
                wait_thread = True

        # if we should stop, wait for the thread to be joined
        if wait_thread:
            assert self.thread is not None
            self.thread.join()
            with self.lock:
                self.thread = None
                assert self.state == DaemonState.IDLE
            self.increment_metric("stops")

        return wait_thread
