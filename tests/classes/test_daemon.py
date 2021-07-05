"""
vtelem - Test the daemon class's correctness.
"""

# built-in
import time

# module under test
from vtelem.classes.daemon import DaemonState, Daemon
from vtelem.classes.daemon_base import DaemonOperation
from vtelem.classes.time_keeper import TimeKeeper


def test_daemon_callbacks():
    """Test the daemon's callback functions."""

    keeper = TimeKeeper("time", 0.05)
    assert keeper.start()

    def daemon_task(*args, **kwargs) -> None:
        """Example daemon task."""
        assert args[0] == "arg1"
        assert args[1] == "arg2"
        assert args[2] == "arg3"
        assert kwargs["kwarg1"] == 1
        assert kwargs["kwarg2"] == 2
        assert kwargs["kwarg3"] == 3
        keeper.sleep(0.2)

    def state_change_cb(
        prev_state: DaemonState, state: DaemonState, _: float
    ) -> None:
        """Example state-change function."""
        assert prev_state != state

    task_rate = 0.1

    def iter_overrun(start: float, end: float, rate: float, _: dict) -> None:
        """Example overrun function."""
        assert end >= start
        nonlocal task_rate
        assert rate == task_rate

    daemon = Daemon(
        "test",
        daemon_task,
        task_rate,
        iter_overrun,
        state_change_cb,
        None,
        keeper,
    )
    assert daemon.get_rate() == task_rate
    assert daemon.get_state() == DaemonState.IDLE
    args = ["arg1", "arg2", "arg3"]
    kwargs = {"kwarg1": 1, "kwarg2": 2, "kwarg3": 3}
    assert daemon.start(*args, **kwargs)
    keeper.sleep(1.0)
    assert daemon.stop()
    assert keeper.stop()


def basic_task():
    """Sample daemon task."""

    print("test!")


def test_daemon_basic():
    """Test basic daemon functionality."""

    keeper = TimeKeeper("time", 0.05)
    assert keeper.start()
    daemon = Daemon("test", basic_task, 0.10, time.sleep, time_keeper=keeper)
    assert daemon.get_state() == DaemonState.IDLE
    daemon.set_state(DaemonState.IDLE)
    assert daemon.start()
    assert not daemon.start()
    time.sleep(0.1)
    assert daemon.pause()
    assert not daemon.pause()
    time.sleep(0.1)
    daemon.set_rate(0.05)
    time.sleep(0.1)
    assert daemon.unpause()
    assert not daemon.unpause()
    with daemon.paused():
        time.sleep(0.1)
    assert daemon.stop()
    assert not daemon.stop()
    assert daemon.start()
    time.sleep(0.1)
    assert daemon.restart()
    time.sleep(0.1)
    assert daemon.stop()
    assert not daemon.restart()

    assert daemon.perform(DaemonOperation.START)
    time.sleep(0.1)
    assert daemon.perform(DaemonOperation.STOP)

    assert daemon.perform_str("start")
    time.sleep(0.1)
    assert daemon.perform_str("stop")
    assert not daemon.perform_str("not_an_op")
    assert keeper.stop()
