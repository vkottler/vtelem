
"""
vtelem - Allows singleton management of application daemons.
"""

# built-in
import logging
from typing import Dict

# internal
from vtelem.enums.daemon import (
    DaemonOperation, str_to_operation, operation_str
)
from .daemon_base import DaemonBase

LOG = logging.getLogger(__name__)


class DaemonManager:
    """ A class for managing a group of daemon tasks. """

    def __init__(self):
        """ Construct a new daemon manager. """

        self.daemons: Dict[str, DaemonBase] = {}

    def add_daemon(self, daemon: DaemonBase) -> bool:
        """ Add a daemon to this manager. """

        name = daemon.name
        if name in self.daemons:
            LOG.error("can't register daemon '%s', name is registered.", name)
            return False
        self.daemons[name] = daemon
        return True

    def perform_all(self, operation: DaemonOperation, *args, **kwargs) -> bool:
        """ Attempt to perform an action on all daemons. """

        failures = 0
        for daemon_name in self.daemons:
            if not self.perform(daemon_name, operation, *args, **kwargs):
                LOG.error("'%s' on '%s' failed.", operation_str(operation),
                          daemon_name)
                failures += 1
        return failures == 0

    def perform_str_all(self, operation: str, *args, **kwargs) -> bool:
        """ Attempt to perform a String action on all daemons. """

        action = str_to_operation(operation)
        if action is None:
            LOG.error("No such action '%s' for daemons.", operation)
            return False
        return self.perform_all(action, *args, **kwargs)

    def perform(self, name: str, operation: DaemonOperation, *args,
                **kwargs) -> bool:
        """ Perform an action on one or more managed daemons. """

        if name not in self.daemons:
            LOG.error("can't '%s' daemon '%s', unknown daemon.",
                      operation_str(operation), name)
            return False
        return self.daemons[name].perform(operation, *args, **kwargs)

    def perform_str(self, name: str, operation: str, *args, **kwargs) -> bool:
        """ Perform an action on one or more daemons by String. """

        action = str_to_operation(operation)
        if action is None:
            LOG.error("No such action '%s' for daemons.", operation)
            return False
        return self.perform(name, action, *args, **kwargs)

    def states(self, as_str: bool = True) -> dict:
        """ Get all daemon states as a dictionary. """

        states_dict = {}
        for name, daemon in self.daemons.items():
            get_state = daemon.get_state_str if as_str else daemon.get_state
            states_dict[name] = get_state()
        return states_dict
