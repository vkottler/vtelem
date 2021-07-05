"""
vtelem - A module for encapsulating software states.
"""

# built-in
from typing import Callable, Optional

# internal
from . import METRIC_PRIM
from .channel_group import ChannelGroup
from .telemetry_environment import TelemetryEnvironment


class State:
    """
    A class for encapsulating a single state to be used in a state machine.
    """

    def __init__(
        self,
        name: str,
        run: Callable = None,
        entering: Callable = None,
        leaving: Callable = None,
        env: TelemetryEnvironment = None,
        rate: float = 1.0,
    ) -> None:
        """Construct a new state."""

        self.name = name
        self.run_fn: Optional[Callable] = run
        self.entering_fn: Optional[Callable] = entering
        self.leaving_fn: Optional[Callable] = leaving
        self.metrics: Optional[ChannelGroup] = None
        if env is not None:
            self.metrics = ChannelGroup("state." + self.name, env)
            self.metrics.add_channel("enter_attempts", METRIC_PRIM, rate)
            self.metrics.add_channel("enter_successes", METRIC_PRIM, rate)
            self.metrics.add_channel("exit_attempts", METRIC_PRIM, rate)
            self.metrics.add_channel("exit_successes", METRIC_PRIM, rate)
            self.metrics.add_channel("iterations", METRIC_PRIM, rate)
        self.is_initial_state = False

    def __eq__(self, other) -> bool:
        """Generic equality check for state instances."""

        return self.name == other.name

    def entering(self, prev_state_name: str, data: dict) -> bool:
        """
        Call this state's entrance routine, return whether or not this state
        can (or should) be entered.
        """

        result = True

        if self.entering_fn is not None:
            if not self.is_initial_state:
                assert prev_state_name != self.name
            result = self.entering_fn(prev_state_name, data)

        # increment metrics
        if self.metrics is not None:
            with self.metrics.data() as metrics_data:
                metrics_data["enter_attempts"] += 1
                metrics_data["enter_successes"] += int(result)

        return result

    def run(self, data: dict) -> str:
        """Run an iteration for this state."""

        result = self.name
        if self.run_fn is not None:
            result = self.run_fn(data)

        # increment metrics
        if self.metrics is not None:
            with self.metrics.data() as metrics_data:
                metrics_data["iterations"] += 1

        return result

    def leaving(self, next_state_name: str, data: dict) -> bool:
        """
        Call this state's exit routine, return whether or not this state
        can (or should) be exited.
        """

        result = True

        if self.leaving_fn is not None:
            assert next_state_name != self.name
            result = self.leaving_fn(next_state_name, data)

        # increment metrics
        if self.metrics is not None:
            with self.metrics.data() as metrics_data:
                metrics_data["exit_attempts"] += 1
                metrics_data["exit_successes"] += int(result)

        return result
