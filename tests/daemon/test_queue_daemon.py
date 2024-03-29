"""
vtelem - Test the queue-daemon class's correctness.
"""

# built-in
from typing import Any

# module under test
from vtelem.classes.metered_queue import create
from vtelem.daemon.queue import QueueDaemon


def test_queue_daemon_basic():
    """Test basic queue-daemon correctness."""

    count = 0

    def handle_elem(queue_elem: Any) -> None:
        """Accumulate a count with provided elements."""

        nonlocal count
        count += queue_elem

    test_queue = create()
    daemon = QueueDaemon("queue_test", test_queue, handle_elem)
    assert daemon.start()
    test_queue.put(1)
    test_queue.put(2)
    test_queue.put(3)
    test_queue.put(4)
    assert daemon.stop()
    assert count == 10
