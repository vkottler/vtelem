"""
vtelem - Allows singleton management of application daemons.
"""

# built-in
from collections import defaultdict
import logging
from typing import Dict, Optional, List

# internal
from vtelem.enums.daemon import (
    DaemonOperation,
    str_to_operation,
    operation_str,
)
from .daemon_base import DaemonBase
from .time_entity import LockEntity

LOG = logging.getLogger(__name__)
NAME_DENYLIST = ["all"]


class DaemonManager(LockEntity):
    """A class for managing a group of daemon tasks."""

    def __init__(self):
        """Construct a new daemon manager."""

        super().__init__()
        self.daemons: Dict[str, DaemonBase] = defaultdict(lambda: None)
        opt_dict = defaultdict(lambda: None)
        self.depends_on: Dict[str, Optional[List[str]]] = opt_dict

    def get(self, name: str) -> Optional[DaemonBase]:
        """Get a daemon object by name."""

        assert name not in NAME_DENYLIST
        return self.daemons[name]

    def add_daemon(
        self, daemon: DaemonBase, depends_on: List[str] = None
    ) -> bool:
        """Add a daemon to this manager."""

        name = daemon.name
        assert name not in NAME_DENYLIST
        with self.lock:
            if name in self.daemons:
                LOG.error(
                    "can't register daemon '%s', name is registered.", name
                )
                return False
            self.daemons[name] = daemon
            self.depends_on[name] = depends_on
        return True

    def perform_stack(
        self,
        name_stack: List[str],
        executed: List[str],
        results: Dict[str, bool],
        operation: DaemonOperation,
        *args,
        **kwargs
    ) -> None:
        """
        Execute an operation on daemons, respecting the dependency order.
        """

        if not name_stack:
            return

        curr = name_stack.pop()
        if curr not in executed:

            # determine if we can execute yet
            to_execute: List[str] = []
            curr_deps = self.depends_on[curr]
            if curr_deps:
                for dep in curr_deps:
                    if dep not in executed:
                        to_execute.append(dep)

            # if we have dependencies, put them in front of us, otherwise
            # run against the current entry
            if to_execute:
                name_stack = to_execute + [curr] + name_stack
            else:
                results[curr] = self.perform(curr, operation, *args, **kwargs)
                executed.append(curr)

        self.perform_stack(
            name_stack, executed, results, operation, *args, **kwargs
        )

    def perform_all(self, operation: DaemonOperation, *args, **kwargs) -> bool:
        """Attempt to perform an action on all daemons."""

        failures = 0
        with self.lock:
            results: Dict[str, bool] = {}
            self.perform_stack(
                list(self.daemons.keys()),
                [],
                results,
                operation,
                *args,
                **kwargs
            )
            for result_key, result_val in results.items():
                if not result_val:
                    LOG.error(
                        "'%s' on '%s' failed.",
                        operation_str(operation),
                        result_key,
                    )
                    failures += 1
        return failures == 0

    def perform_str_all(self, operation: str, *args, **kwargs) -> bool:
        """Attempt to perform a String action on all daemons."""

        action = str_to_operation(operation)
        if action is None:
            LOG.error("No such action '%s' for daemons.", operation)
            return False
        return self.perform_all(action, *args, **kwargs)

    def perform(
        self, name: str, operation: DaemonOperation, *args, **kwargs
    ) -> bool:
        """Perform an action on one or more managed daemons."""

        if name not in self.daemons:
            LOG.error(
                "can't '%s' daemon '%s', unknown daemon.",
                operation_str(operation),
                name,
            )
            return False
        with self.lock:
            result = self.daemons[name].perform(operation, *args, **kwargs)
        return result

    def perform_str(self, name: str, operation: str, *args, **kwargs) -> bool:
        """Perform an action on one or more daemons by String."""

        action = str_to_operation(operation)
        if action is None:
            LOG.error("No such action '%s' for daemons.", operation)
            return False
        return self.perform(name, action, *args, **kwargs)

    def states(self, as_str: bool = True) -> dict:
        """Get all daemon states as a dictionary."""

        states_dict = {}
        with self.lock:
            for name, daemon in self.daemons.items():
                state_fn = daemon.get_state_str if as_str else daemon.get_state
                states_dict[name] = state_fn()
        return states_dict
