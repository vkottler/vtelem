"""
vtelem - A module that helps aggregate command-consuming entities and dispatch
         commands destined for them from a queue.
"""

# built-in
from collections import defaultdict
import json
import logging
from queue import Queue
from threading import Semaphore
from typing import Any, Dict, List, Tuple, Optional

# internal
from vtelem.types.command_queue_daemon import (
    ConsumerType,
    ResultCbType,
    HandlersType,
)
from .queue_daemon import QueueDaemon
from .telemetry_environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)


class CommandQueueDaemon(QueueDaemon):
    """
    A class for consuming any arbitrary form of commands that other other
    entities can register handlers for.
    """

    def __init__(
        self,
        name: str,
        env: TelemetryEnvironment = None,
        time_keeper: Any = None,
    ) -> None:
        """Construct a new command-queue daemon."""

        self.handlers: HandlersType = defaultdict(list)

        def elem_handle(data: Tuple[Any, Optional[ResultCbType]]) -> None:
            """Handle an individual command from the queue."""

            self.increment_metric("command_count")
            elem = data[0]
            cmd_cb = data[1]

            # make sure the element is a dictionary, has "command", has a
            # handler registered
            if not isinstance(elem, dict) or "command" not in elem:
                err = (
                    "{}: unknown or malformed command, " + "rejected"
                ).format(self.name)
                LOG.error(err)
                self.increment_metric("rejected_count")
                if cmd_cb is not None:
                    cmd_cb(False, err)
                return None
            if not self.handlers[elem["command"]]:
                err = (
                    "{}: command '{}' has no handlers, " + "rejected"
                ).format(self.name, elem["command"])
                LOG.error(err)
                self.increment_metric("rejected_count")
                if cmd_cb is not None:
                    cmd_cb(False, err)
                return None

            # provide data as a defaultdict no matter what
            cmd_data: dict = defaultdict(lambda: None)
            if "data" in elem and isinstance(elem["data"], dict):
                cmd_data.update(elem["data"])

            # execute command
            handlers = self.handlers[elem["command"]]
            for handler, result_cb, _ in handlers:
                result, message = handler(cmd_data)
                if result_cb is not None:
                    result_cb(result, message)
                if cmd_cb is not None:
                    cmd_cb(result, message)
                status = "success" if result else "failure"
                self.increment_metric("{}_count".format(status))

                # log result
                log_fn = LOG.info if result else LOG.warning
                log_fn(
                    "%s: command '%s' '%s' %s, '%s'",
                    self.name,
                    elem["command"],
                    json.dumps(cmd_data),
                    status,
                    message,
                )
            return None

        super().__init__(name, Queue(), elem_handle, env, time_keeper)
        self.reset_metric("command_count")
        self.reset_metric("success_count")
        self.reset_metric("failure_count")
        self.reset_metric("rejected_count")

        def help_handler(data: dict) -> Tuple[bool, str]:
            """A useful command for viewing what commands are available."""

            cmd_help: Dict[str, List[str]] = {}
            commands = []
            for key, handler in self.handlers.items():
                if handler:
                    commands.append(key)
            if data["command"] is not None:
                # make sure the specified command exists
                if data["command"] not in self.handlers:
                    msg = "Unknown command '{}'".format(data["command"])
                    return False, msg
                commands = [data["command"]]

            # build result
            for command in commands:
                cmd_help[command] = []
                for _, __, help_msg in self.handlers[command]:
                    cmd_help[command].append(help_msg)

            indented = data["indent"] is not None
            return True, json.dumps(cmd_help, indent=(4 if indented else None))

        # add a 'help' handler
        help_msg = "inquire about available command usages"
        self.register_consumer("help", help_handler, help_msg=help_msg)

    def register_consumer(
        self,
        command: str,
        handler: ConsumerType,
        result_cb: ResultCbType = None,
        help_msg: str = "",
    ) -> None:
        """Register a command handler for a given command name."""
        self.handlers[command].append((handler, result_cb, help_msg))

    def enqueue(self, command: Any, result_cb: ResultCbType = None) -> None:
        """Put a command into our queue."""
        self.queue.put((command, result_cb))

    def execute(self, command: Any) -> Tuple[bool, str]:
        """Execute a command and block until it's complete."""

        result, msg = False, "Command result not known."
        signal = Semaphore(0)

        def cmd_cb(status: bool, message: str) -> None:
            """Update the result when we get it."""

            nonlocal result
            nonlocal msg
            result = status
            msg = message
            signal.release()

        self.enqueue(command, cmd_cb)
        signal.acquire()  # pylint:disable=consider-using-with
        return result, msg
