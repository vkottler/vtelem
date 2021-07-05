"""
vtelem - A module for generic test utilities.
"""

# built-in
from queue import Queue
from typing import Tuple

# internal
from vtelem.classes.command_queue_daemon import CommandQueueDaemon
from vtelem.types.command_queue_daemon import ResultCbType


def make_queue_cb() -> Tuple[Queue, ResultCbType]:
    """Create a new queue and result-callback based on it."""

    result_queue: Queue = Queue()

    def result_consumer(result: bool, msg: str) -> None:
        """Example result consumer."""
        result_queue.put((result, msg))

    return result_queue, result_consumer


def command_result(
    cmd: dict, daemon: CommandQueueDaemon, result_queue: Queue
) -> Tuple[bool, str]:
    """Execute a command and get the result."""

    daemon.enqueue(cmd)
    return result_queue.get()
