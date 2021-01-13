
"""
vtelem - Test the correctness of the command-queue daemon.
"""

# built-in
from typing import Tuple

# module under test
from vtelem.classes.command_queue_daemon import CommandQueueDaemon


def test_command_queue_daemon_basic():
    """ Test the command queue's ability to correctly dispatch. """

    daemon = CommandQueueDaemon("test")

    iteration = 0

    def sample_handler(_: dict) -> Tuple[bool, str]:
        """ An example command handler. """
        nonlocal iteration
        iteration += 1
        return iteration % 2 == 0, str(iteration)

    def result_cb(result: bool, message: str) -> None:
        """ Sample result callback. """
        nonlocal iteration
        assert result == (iteration % 2 == 0)
        assert str(iteration) == message

    # register handlers
    daemon.register_consumer("test", sample_handler, result_cb)
    daemon.register_consumer("test", sample_handler)

    with daemon.booted():
        for _ in range(5):
            daemon.enqueue({})
            daemon.enqueue({"command": "test"})
            daemon.enqueue({"command": "test_bad"})
            daemon.enqueue({"command": "test", "data": {}})
