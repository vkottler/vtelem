
"""
vtelem - Test the daemon class's correctness.
"""

# built-in
import time

# module under test
from vtelem.classes.daemon import DaemonState, Daemon


def basic_task():
    """ Sample daemon task. """

    print("test!")


def test_daemon_basic():
    """ Test basic daemon functionality. """

    daemon = Daemon(basic_task, 0.10, time.time, time.sleep, "test")
    assert daemon.get_state() == DaemonState.IDLE
    daemon.set_state(DaemonState.IDLE)
    assert daemon.start()
    assert not daemon.start()
    time.sleep(0.2)
    assert daemon.pause()
    assert not daemon.pause()
    daemon.set_rate(0.05)
    time.sleep(0.2)
    assert daemon.unpause()
    assert not daemon.unpause()
    time.sleep(0.2)
    assert daemon.stop()
    assert not daemon.stop()
