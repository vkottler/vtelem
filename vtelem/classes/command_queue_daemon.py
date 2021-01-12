
"""
vtelem - A module that helps aggregate command-consuming entities and dispatch
         commands destined for them from a queue.
"""

# built-in
from collections import defaultdict
import logging
from queue import Queue
from typing import Any, Callable, Dict, Optional

# internal
from .queue_daemon import QueueDaemon
from .telemetry_environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)
ConsumerType = Callable[[dict], bool]
HandlersType = Dict[str, Optional[ConsumerType]]


class CommandQueueDaemon(QueueDaemon):
    """
    A class for consuming any arbitrary form of commands that other other
    entities can register handlers for.
    """

    def __init__(self, name: str, env: TelemetryEnvironment = None,
                 time_keeper: Any = None) -> None:
        """ Construct a new command-queue daemon. """

        self.handlers: HandlersType = defaultdict(lambda: None)

        def elem_handle(elem: Any) -> None:
            """ Handle an individual command from the queue. """

            self.increment_metric("command_count")

            # make sure the element is a dictionary, has "command", has a
            # handler registered
            if not isinstance(elem, dict) or "command" not in elem:
                self.increment_metric("rejected_count")
                return None
            if self.handlers[elem["command"]] is None:
                self.increment_metric("rejected_count")
                return None

            # provide data as a defaultdict no matter what
            cmd_data: dict = defaultdict(lambda: None)
            if "data" in elem and isinstance(elem["data"], dict):
                cmd_data.update(elem["data"])

            # execute command
            handler = self.handlers[elem["command"]]
            assert handler is not None
            result = handler(cmd_data)
            status = "success" if result else "failure"
            self.increment_metric("{}_count".format(status))

            # log result
            log_fn = LOG.info if result else LOG.warning
            log_fn("%s: command '%s' '%s' %s", self.name, elem["command"],
                   cmd_data, status)
            return None

        super().__init__(name, Queue(), elem_handle, env, time_keeper)
        self.reset_metric("command_count")
        self.reset_metric("success_count")
        self.reset_metric("failure_count")
        self.reset_metric("rejected_count")

    def register_consumer(self, command: str,
                          handler: ConsumerType) -> None:
        """ Register a command handler for a given command name. """
        self.handlers[command] = handler

    def enqueue(self, command: Any) -> None:
        """ Put a command into our queue. """
        self.queue.put(command)
