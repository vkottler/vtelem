
"""
vtelem - A module that helps aggregate command-consuming entities and dispatch
         commands destined for them from a queue.
"""

# built-in
from collections import defaultdict
import json
import logging
from queue import Queue
from typing import Any

# internal
from vtelem.types.command_queue_daemon import (
    ConsumerType, ResultCbType, HandlersType
)
from .queue_daemon import QueueDaemon
from .telemetry_environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)


class CommandQueueDaemon(QueueDaemon):
    """
    A class for consuming any arbitrary form of commands that other other
    entities can register handlers for.
    """

    def __init__(self, name: str, env: TelemetryEnvironment = None,
                 time_keeper: Any = None) -> None:
        """ Construct a new command-queue daemon. """

        self.handlers: HandlersType = defaultdict(list)

        def elem_handle(elem: Any) -> None:
            """ Handle an individual command from the queue. """

            self.increment_metric("command_count")

            # make sure the element is a dictionary, has "command", has a
            # handler registered
            if not isinstance(elem, dict) or "command" not in elem:
                LOG.error("%s: unknown or malformed command, rejected",
                          self.name)
                self.increment_metric("rejected_count")
                return None
            if not self.handlers[elem["command"]]:
                LOG.error("%s: command '%s' has no handlers, rejected",
                          self.name, elem["command"])
                self.increment_metric("rejected_count")
                return None

            # provide data as a defaultdict no matter what
            cmd_data: dict = defaultdict(lambda: None)
            if "data" in elem and isinstance(elem["data"], dict):
                cmd_data.update(elem["data"])

            # execute command
            handlers = self.handlers[elem["command"]]
            for handler, result_cb in handlers:
                result, message = handler(cmd_data)
                if result_cb is not None:
                    result_cb(result, message)
                status = "success" if result else "failure"
                self.increment_metric("{}_count".format(status))

                # log result
                log_fn = LOG.info if result else LOG.warning
                log_fn("%s: command '%s' '%s' %s, '%s'", self.name,
                       elem["command"], json.dumps(cmd_data), status, message)
            return None

        super().__init__(name, Queue(), elem_handle, env, time_keeper)
        self.reset_metric("command_count")
        self.reset_metric("success_count")
        self.reset_metric("failure_count")
        self.reset_metric("rejected_count")

    def register_consumer(self, command: str, handler: ConsumerType,
                          result_cb: ResultCbType = None) -> None:
        """ Register a command handler for a given command name. """
        self.handlers[command].append((handler, result_cb))

    def enqueue(self, command: Any) -> None:
        """ Put a command into our queue. """
        self.queue.put(command)
