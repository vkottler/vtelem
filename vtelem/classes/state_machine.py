"""
vtelem - A module for orchestrating state-machine implementation.
"""

# built-in
from collections import defaultdict
from contextlib import contextmanager
import logging
from typing import Dict, List, Iterator, Tuple, Optional

# internal
from . import METRIC_PRIM
from .channel_group import ChannelGroup
from .state import State
from .telemetry_environment import TelemetryEnvironment
from .time_entity import LockEntity

LOG = logging.getLogger(__name__)


class StateMachine(LockEntity):
    """
    A class that supports structuring execution of code as a state machine.
    """

    def __init__(
        self,
        name: str,
        states: List[State],
        initial_state: State = None,
        initial_data: dict = None,
        env: TelemetryEnvironment = None,
        rate: float = 1.0,
    ) -> None:
        """Construct a new state machine."""

        super().__init__()

        assert states

        if initial_state is None:
            initial_state = states[0]

        self.states: Dict[str, Optional[State]] = defaultdict(lambda: None)
        for state in states:
            self.states[state.name] = state

        self.current_state = initial_state.name
        assert self.current_state in self.states

        if initial_data is None:
            initial_data = {}

        self._data: dict = defaultdict(lambda: None)
        self._data.update(initial_data)

        # make sure we can enter the initial state
        init_state = self.states[self.current_state]
        assert init_state is not None
        init_state.is_initial_state = True
        assert init_state.entering(self.current_state, self._data)

        self.name = name
        self.metrics: Optional[ChannelGroup] = None
        if env is not None:
            self.metrics = ChannelGroup("machine." + self.name, env)
            self.metrics.add_channel("enter_fails", METRIC_PRIM, rate)
            self.metrics.add_channel("exit_fails", METRIC_PRIM, rate)
            self.metrics.add_channel("transitions", METRIC_PRIM, rate)
            self.metrics.add_channel("iterations", METRIC_PRIM, rate)

    @contextmanager
    def data(self) -> Iterator[dict]:
        """Acquire stateful data in a locked context."""

        with self.lock:
            yield self._data

    def run(self, new_data: dict = None) -> Tuple[State, State]:
        """
        Run an iteration of the state machine, return the starting and ending
        states.
        """

        if new_data is not None:
            with self.lock:
                self._data.update(new_data)

        curr = self.states[self.current_state]
        assert curr is not None

        with self.lock:
            new = curr.run(self._data)
            assert new in self.states

            # call edges
            enter_failed = False
            exit_failed = False
            transitioned = False
            if new != self.current_state:
                LOG.info(
                    "%s: attempting '%s' -> '%s'",
                    self.name,
                    self.current_state,
                    new,
                )
                if curr.leaving(new, self._data):
                    candidate = self.states[new]
                    assert candidate is not None
                    if candidate.entering(self.current_state, self._data):
                        self.current_state = new
                        LOG.info(
                            "%s: transition succeeded to '%s'", self.name, new
                        )
                        transitioned = True
                    else:
                        LOG.error("%s: couldn't enter '%s'", self.name, new)
                        enter_failed = True
                else:
                    LOG.error(
                        "%s: couldn't exit '%s'", self.name, self.current_state
                    )
                    exit_failed = True

        # increment metrics
        if self.metrics is not None:
            with self.metrics.data() as metrics_data:
                metrics_data["enter_fails"] += int(enter_failed)
                metrics_data["exit_fails"] += int(exit_failed)
                metrics_data["transitions"] += int(transitioned)
                metrics_data["iterations"] += 1

        actual_new = self.states[self.current_state]
        assert actual_new is not None
        return (curr, actual_new)
