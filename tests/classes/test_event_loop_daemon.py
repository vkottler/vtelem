"""
vtelem - Test the event-loop daemon's correctness.
"""

# built-in
import time

# module under test
from vtelem.classes.event_loop_daemon import EventLoopDaemon


def test_event_loop_daemon_basic():
    """Test that the event loop daemon can start and stop."""

    daemon = EventLoopDaemon("test")

    # make sure the loop can be started again
    for _ in range(5):
        with daemon.booted():
            time.sleep(0.01)
