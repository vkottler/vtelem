
"""
vtelem - A base for building runtime tasks.
"""

# built-in
from collections import defaultdict
from enum import Enum
import threading
from typing import Any, Dict, Optional


class DaemonState(Enum):
    """ An enumeration of all valid daemon states. """

    ERROR = 0
    IDLE = 1
    STARTING = 2
    RUNNING = 3
    PAUSED = 4
    STOPPING = 5


class DaemonBase:
    """ A base class for building worker threads. """

    def __init__(self, name: str = None):
        """
        Construct a base daemon, supports implementations of tasks that can
        be started, stopped, paused etc. at runtime.
        """

        self.state: DaemonState = DaemonState.IDLE
        self.name = name
        self.function: Dict[str, Any] = {}
        self.function["metrics_data"] = defaultdict(lambda: 0)
        self.lock = threading.RLock()
        self.thread: Optional[threading.Thread] = None

    def set_state(self, state: DaemonState) -> None:
        """ Assigns a new run-state to this daemon. """

        with self.lock:
            if self.state == state:
                return
            try:
                self.function["state_change"](self.state, state,
                                              self.function["time"]())
            except (KeyError, TypeError):
                pass
            self.state = state

    def reset_metric(self, name: str) -> None:
        """ Set a metric back to zero. """

        with self.lock:
            self.function["metrics_data"][name] = 0

    def increment_metric(self, name: str) -> None:
        """ Increment a named metric. """

        with self.lock:
            self.function["metrics_data"][name] += 1

    def get_state(self) -> DaemonState:
        """ Query this daemon's current state. """

        with self.lock:
            return self.state

    def get_state_str(self) -> str:
        """ Get the current state as a String. """

        return self.get_state().name.lower()

    def run_harness(self, *args, **kwargs) -> None:
        """
        Execute 'run' and ensure that the correct state transitions occur.
        """

        self.set_state(DaemonState.RUNNING)
        self.run(*args, **kwargs)
        self.set_state(DaemonState.IDLE)

    def run(self, *_, **__) -> None:
        """ To be implemented by parent. """

    def start(self, *args, **kwargs) -> bool:
        """ Attempt to start the daemon. """

        with self.lock:
            if self.state != DaemonState.IDLE:
                return False

            self.thread = threading.Thread(target=self.run_harness, args=args,
                                           kwargs=kwargs, name=self.name)
            self.reset_metric("count")
            self.increment_metric("starts")
            self.set_state(DaemonState.STARTING)

        self.thread.start()
        return True

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

    def begin_stop(self) -> bool:
        """
        Determine if we're in the correct state to stop, mutate state if so.
        """

        # make sure we're in the correct state to attempt a stop
        with self.lock:
            if self.state == DaemonState.RUNNING:
                self.set_state(DaemonState.STOPPING)
                try:
                    self.function["inject_stop"]()
                except KeyError:
                    pass
                return True
        return False

    def stop(self) -> bool:
        """ Attempt to stop the daemon. """

        if not self.begin_stop():
            return False

        # if we should stop, wait for the thread to be joined
        assert self.thread is not None
        self.thread.join()
        with self.lock:
            self.thread = None
            assert self.state == DaemonState.IDLE
        self.increment_metric("stops")

        return True
