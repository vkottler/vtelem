
"""
vtelem - Test the daemon class's correctness.
"""

# built-in
import time

# module under test
from vtelem.classes.daemon import DaemonState, Daemon
from vtelem.classes.daemon_base import DaemonOperation


def test_daemon_callbacks():
    """ Test the daemon's callback functions. """

    curr_time = float()
    task_rate = 0.1

    def sleep(sleep_time: float) -> None:
        """ Example sleep function. """
        nonlocal curr_time
        curr_time += sleep_time
        time.sleep(0.1)

    def time_fn() -> float:
        """ Example time-get function. """

        return curr_time

    def daemon_task(*args, **kwargs) -> None:
        """ Example daemon task. """
        assert args[0] == "arg1"
        assert args[1] == "arg2"
        assert args[2] == "arg3"
        assert kwargs["kwarg1"] == 1
        assert kwargs["kwarg2"] == 2
        assert kwargs["kwarg3"] == 3
        nonlocal curr_time
        curr_time += 0.2
        time.sleep(0.2)

    def iter_overrun(start: float, end: float, rate: float,
                     _: dict) -> None:
        """ Example overrun function. """
        assert end >= start
        nonlocal task_rate
        assert rate == task_rate

    def iter_metrics(start: float, end: float, rate: float,
                     _: dict) -> None:
        """ Example metrics consumer. """
        assert end >= start
        nonlocal task_rate
        assert rate == task_rate

    daemon = Daemon("test", daemon_task, task_rate, time_fn, sleep,
                    iter_overrun, iter_metrics)
    assert daemon.get_state() == DaemonState.IDLE
    args = ["arg1", "arg2", "arg3"]
    kwargs = {"kwarg1": 1, "kwarg2": 2, "kwarg3": 3}
    assert daemon.start(*args, **kwargs)
    time.sleep(0.5)
    assert daemon.stop()


def basic_task():
    """ Sample daemon task. """

    print("test!")


def test_daemon_basic():
    """ Test basic daemon functionality. """

    daemon = Daemon("test", basic_task, 0.10, time.time, time.sleep)
    assert daemon.get_state() == DaemonState.IDLE
    daemon.set_state(DaemonState.IDLE)
    assert daemon.start()
    assert not daemon.start()
    time.sleep(0.1)
    assert daemon.pause()
    assert not daemon.pause()
    daemon.set_rate(0.05)
    time.sleep(0.1)
    assert daemon.unpause()
    assert not daemon.unpause()
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
