
"""
vtelem - A base for building runtime tasks.
"""

# built-in
from collections import defaultdict
from enum import Enum
import logging
import threading
import time
from typing import Any, Dict, Optional

# internal
from vtelem.names import class_to_snake
from . import METRIC_PRIM
from .telemetry_environment import TelemetryEnvironment
from .time_entity import TimeEntity

LOG = logging.getLogger(__name__)


class DaemonState(Enum):
    """ An enumeration of all valid daemon states. """

    ERROR = 0
    IDLE = 1
    STARTING = 2
    RUNNING = 3
    PAUSED = 4
    STOPPING = 5


class DaemonOperation(Enum):
    """ A declaration of the actions that can be performed on a daemon. """

    NONE = 0
    START = 1
    STOP = 2
    PAUSE = 3
    UNPAUSE = 4
    RESTART = 5


def operation_str(operation: DaemonOperation) -> str:
    """ Convert an operation enum to a String. """
    return operation.name.lower()


def str_to_operation(operation: str) -> Optional[DaemonOperation]:
    """ Find an operation enum based on the provided stream. """

    for known_op in DaemonOperation:
        if operation_str(known_op) == operation.lower():
            return known_op
    return None


class DaemonBase(TimeEntity):
    """ A base class for building worker threads. """

    def __init__(self, name: str, env: TelemetryEnvironment = None,
                 time_keeper: Any = None):
        """
        Construct a base daemon, supports implementations of tasks that can
        be started, stopped, paused etc. at runtime.
        """

        super().__init__()
        if time_keeper is not None:
            time_keeper.add_slave(self)
        self.state: DaemonState = DaemonState.ERROR
        assert name != ""
        self.name = name
        self.env = env
        self.function: Dict[str, Any] = {}
        self.function["track_metric_changes"] = False
        self.function["metrics_data"] = defaultdict(lambda: 0)
        self.thread: Optional[threading.Thread] = None

        # register and reset standard metrics
        self.reset_metric("starts")
        self.reset_metric("stops")
        self.reset_metric("pauses")
        self.reset_metric("unpauses")
        self.reset_metric("count")

        def default_state_change(prev_state: DaemonState, state: DaemonState,
                                 time_val: float) -> None:
            """ By default, log state changes for a daemon. """
            LOG.info("%s: %s -> %s", time.ctime(time_val),
                     prev_state.name.lower(), state.name.lower())

        self.function["state_change"] = default_state_change

        # add a metric channel for the overall state
        if self.env is not None:
            self.env.add_from_enum(DaemonState)
            self.env.add_enum_metric(self.get_metric_name("state"),
                                     class_to_snake(DaemonState), True)

        self.set_state(DaemonState.IDLE)

        # set up the actions data
        default: dict = defaultdict(lambda: {"action": lambda: False,
                                             "takes_args": False})
        self.daemon_ops: Dict[DaemonOperation, dict] = default
        self.daemon_ops[DaemonOperation.START] = {"action": self.start,
                                                  "takes_args": True}
        self.daemon_ops[DaemonOperation.STOP] = {"action": self.stop,
                                                 "takes_args": False}
        self.daemon_ops[DaemonOperation.PAUSE] = {"action": self.pause,
                                                  "takes_args": False}
        self.daemon_ops[DaemonOperation.UNPAUSE] = {"action": self.unpause,
                                                    "takes_args": False}
        self.daemon_ops[DaemonOperation.RESTART] = {"action": self.restart,
                                                    "takes_args": True}

    def perform(self, action: DaemonOperation, *args, **kwargs) -> bool:
        """ Perform an action by enum. """

        operation = self.daemon_ops[action]
        if not operation["takes_args"]:
            return operation["action"]()
        return operation["action"](*args, **kwargs)

    def perform_str(self, action: str, *args, **kwargs) -> bool:
        """ Perform an action on this daemon by String. """

        operation = str_to_operation(action)
        if operation is None:
            return False
        return self.perform(operation, *args, **kwargs)

    def get_metric_name(self, channel_name: str) -> str:
        """ Build the name of a metric channel for this daemon. """

        return "{}.{}".format(self.name, channel_name)

    def set_state(self, state: DaemonState) -> None:
        """ Assigns a new run-state to this daemon. """

        with self.lock:
            if self.state == state:
                return
            self.function["state_change"](self.state, state, self.get_time())
            self.state = state

            # set the metric channel
            if self.env is not None:
                self.env.set_enum_metric(self.get_metric_name("state"),
                                         self.get_state_str(), self.get_time())

    def set_env_metric(self, name: str, value: Any) -> None:
        """ Set a metric channel value if an environment is registered. """

        if self.env is not None:
            metric_name = self.get_metric_name(name)
            if not self.env.has_metric(metric_name):
                self.env.add_metric(metric_name, METRIC_PRIM,
                                    self.function["track_metric_changes"])
            self.env.set_metric(metric_name, value, self.get_time())

    def reset_metric(self, name: str) -> None:
        """ Set a metric back to zero. """

        with self.lock:
            self.function["metrics_data"][name] = 0
            self.set_env_metric(name, self.function["metrics_data"][name])

    def increment_metric(self, name: str, value: int = 1) -> None:
        """ Increment a named metric. """

        with self.lock:
            self.function["metrics_data"][name] += value
            self.set_env_metric(name, self.function["metrics_data"][name])

    def decrement_metric(self, name: str, value: int = 1) -> None:
        """ Decrement a named metric. """

        with self.lock:
            self.function["metrics_data"][name] -= value
            self.set_env_metric(name, self.function["metrics_data"][name])

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
        self.increment_metric("count")
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
        should_stop = False
        with self.lock:
            if self.state == DaemonState.RUNNING:
                self.set_state(DaemonState.STOPPING)
                should_stop = True

        if should_stop:
            try:
                self.function["inject_stop"]()
            except KeyError:
                pass

        return should_stop

    def restart(self, *args, **kwargs) -> bool:
        """ Attempt to restart this daemon. """

        if self.stop():
            return self.start(*args, **kwargs)
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
