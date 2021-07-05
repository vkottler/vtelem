"""
vtelem - A base for building runtime tasks.
"""

# built-in
from collections import defaultdict
from contextlib import contextmanager
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional, Iterator

# internal
from vtelem.enums.daemon import DaemonState, DaemonOperation, str_to_operation
from vtelem.enums.primitive import Primitive
from vtelem.names import class_to_snake
from . import METRIC_PRIM
from .telemetry_environment import TelemetryEnvironment
from .time_entity import TimeEntity
from .user_enum import from_enum

LOG = logging.getLogger(__name__)
MainThread = Callable[..., int]


def dummy_thread(*args, **kwargs) -> int:
    """
    For applications that don't do work in the main thread outside of daemons,
    just sleep until we're interrupted.
    """

    LOG.debug(
        "'dummy_thread' invoked: [%s], %s", ", ".join(args[1:]), str(kwargs)
    )
    try:
        while True:
            # just use native time since we're not doing any time-keeping
            time.sleep(2 ** 32)
    except KeyboardInterrupt:
        pass
    return 0


class DaemonBase(TimeEntity):
    """A base class for building worker threads."""

    states = from_enum(DaemonState)
    operations = from_enum(DaemonOperation)

    def __init__(
        self,
        name: str,
        env: TelemetryEnvironment = None,
        time_keeper: Any = None,
    ):
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

        # add daemon enum definitions to the environment
        if self.env is not None:
            if not self.env.has_enum(DaemonBase.states):
                self.env.add_enum(DaemonBase.states)
            if not self.env.has_enum(DaemonBase.operations):
                self.env.add_enum(DaemonBase.operations)

        # register and reset standard metrics
        self.reset_metric("starts")
        self.reset_metric("stops")
        self.reset_metric("pauses")
        self.reset_metric("unpauses")
        self.reset_metric("count")

        def default_state_change(
            prev_state: DaemonState, state: DaemonState, time_val: float
        ) -> None:
            """By default, log state changes for a daemon."""
            LOG.info(
                "%-10s - %s: %s -> %s",
                self.name,
                time.ctime(time_val),
                prev_state.name.lower(),
                state.name.lower(),
            )

        self.function["state_change"] = default_state_change

        # add a metric channel for the overall state
        if self.env is not None:
            self.env.add_from_enum(DaemonState)
            self.env.add_enum_metric(
                self.get_metric_name("state"),
                class_to_snake(DaemonState),
                True,
            )

        self.set_state(DaemonState.IDLE)

        # set up the actions data
        default: dict = defaultdict(
            lambda: {"action": lambda: False, "takes_args": False}
        )
        self.daemon_ops: Dict[DaemonOperation, dict] = default
        self.daemon_ops[DaemonOperation.START] = {
            "action": self.start,
            "takes_args": True,
        }
        self.daemon_ops[DaemonOperation.STOP] = {
            "action": self.stop,
            "takes_args": False,
        }
        self.daemon_ops[DaemonOperation.PAUSE] = {
            "action": self.pause,
            "takes_args": False,
        }
        self.daemon_ops[DaemonOperation.UNPAUSE] = {
            "action": self.unpause,
            "takes_args": False,
        }
        self.daemon_ops[DaemonOperation.RESTART] = {
            "action": self.restart,
            "takes_args": True,
        }

    def perform(self, action: DaemonOperation, *args, **kwargs) -> bool:
        """Perform an action by enum."""

        operation = self.daemon_ops[action]
        if not operation["takes_args"]:
            return operation["action"]()
        return operation["action"](*args, **kwargs)

    def perform_str(self, action: str, *args, **kwargs) -> bool:
        """Perform an action on this daemon by String."""

        operation = str_to_operation(action)
        if operation is None:
            return False
        return self.perform(operation, *args, **kwargs)

    def get_metric_name(self, channel_name: str) -> str:
        """Build the name of a metric channel for this daemon."""

        return "{}.{}".format(self.name, channel_name)

    def set_state(self, state: DaemonState) -> None:
        """Assigns a new run-state to this daemon."""

        with self.lock:
            if self.state == state:
                return
            self.function["state_change"](self.state, state, self.get_time())
            self.state = state

            # set the metric channel
            if self.env is not None:
                self.env.set_enum_metric(
                    self.get_metric_name("state"),
                    self.get_state_str(),
                    self.get_time(),
                )

    def set_env_metric(
        self, name: str, value: Any, prim: Primitive = METRIC_PRIM
    ) -> None:
        """Set a metric channel value if an environment is registered."""

        if self.env is not None:
            metric_name = self.get_metric_name(name)
            if not self.env.has_metric(metric_name):
                self.env.add_metric(
                    metric_name, prim, self.function["track_metric_changes"]
                )
            self.env.set_metric(metric_name, value, self.get_time())

    def reset_metric(self, name: str) -> None:
        """Set a metric back to zero."""

        with self.lock:
            self.function["metrics_data"][name] = 0
            self.set_env_metric(name, self.function["metrics_data"][name])

    def increment_metric(self, name: str, value: Any = 1) -> None:
        """Increment a named metric."""

        with self.lock:
            self.function["metrics_data"][name] += value
            self.set_env_metric(name, self.function["metrics_data"][name])

    def decrement_metric(self, name: str, value: Any = 1) -> None:
        """Decrement a named metric."""

        with self.lock:
            self.function["metrics_data"][name] -= value
            self.set_env_metric(name, self.function["metrics_data"][name])

    def get_state(self) -> DaemonState:
        """Query this daemon's current state."""

        with self.lock:
            return self.state

    def get_state_str(self) -> str:
        """Get the current state as a String."""

        return self.get_state().name.lower()

    def run_harness(self, *args, **kwargs) -> None:
        """
        Execute 'run' and ensure that the correct state transitions occur.
        """

        try:
            self.set_state(DaemonState.RUNNING)
            self.run(*args, **kwargs)
        except KeyboardInterrupt:
            LOG.warning("%s: interrupted", self.name)
        finally:
            self.increment_metric("count")
            self.set_state(DaemonState.IDLE)

    def run(self, *_, **__) -> None:
        """To be implemented by parent."""

    @contextmanager
    def booted(self, *args, **kwargs) -> Iterator[None]:
        """
        Provide a context manager that yields when this daemon is running and
        automatically stops it.
        """

        try:
            assert self.start(*args, **kwargs)
            yield
        finally:
            assert self.stop()

    def serve(self, *args, main_thread: MainThread = None, **kwargs) -> int:
        """
        Run this daemon with an optionally-provided main-thread function,
        return the main-thread function's result and shut down the daemon when
        it returns.
        """

        result = -1
        if main_thread is None:
            main_thread = dummy_thread
        with self.booted(*args, **kwargs):
            result = main_thread(self, *args, **kwargs)
        return result

    def start(self, *args, **kwargs) -> bool:
        """Attempt to start the daemon."""

        with self.lock:
            if self.state != DaemonState.IDLE:
                return False

            self.thread = threading.Thread(
                target=self.run_harness,
                args=args,
                kwargs=kwargs,
                name=self.name,
            )
            self.reset_metric("count")
            self.increment_metric("starts")
            self.set_state(DaemonState.STARTING)

        self.thread.start()
        return True

    @contextmanager
    def paused(self) -> Iterator[None]:
        """Exposes pausing and unpausing while yielded."""

        try:
            assert self.pause()
            yield
        finally:
            assert self.unpause()

    def pause(self) -> bool:
        """Attempt to pause the daemon."""

        with self.lock:
            if self.state == DaemonState.RUNNING:
                self.set_state(DaemonState.PAUSED)
                self.increment_metric("pauses")
                return True
        return False

    def unpause(self) -> bool:
        """Attempt to un-pause the daemon."""

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
        """Attempt to restart this daemon."""

        if self.stop():
            return self.start(*args, **kwargs)
        return False

    def stop(self) -> bool:
        """Attempt to stop the daemon."""

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
