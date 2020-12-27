
"""
vtelem - Test the correctness of the daemon manager.
"""

# module under test
from vtelem.classes.daemon_base import DaemonOperation, DaemonState
from vtelem.classes.daemon_manager import DaemonManager
from vtelem.classes.time_keeper import TimeKeeper


def test_daemon_manager_basic():
    """ Test management of basic tasks. """

    manager = DaemonManager()
    manager.add_daemon(TimeKeeper("test1", 0.05))
    manager.add_daemon(TimeKeeper("test2", 0.05))
    manager.add_daemon(TimeKeeper("test3", 0.05))
    assert not manager.add_daemon(TimeKeeper("test3", 0.05))
    assert manager.perform_all(DaemonOperation.START)
    assert manager.perform_all(DaemonOperation.STOP)
    assert not manager.perform_all(DaemonOperation.STOP)
    assert manager.perform_str_all("start")
    assert manager.perform_str_all("stop")
    assert not manager.perform_str_all("stop")
    assert not manager.perform_str_all("not_an_action")
    assert not manager.perform_str("test1", "not_an_action")
    assert not manager.perform("not_a_daemon", DaemonOperation.START)
    assert manager.perform_str("test1", "start")
    assert manager.perform_str("test1", "stop")
    states_str = manager.states(False)
    assert states_str["test1"] == DaemonState.IDLE
    assert states_str["test2"] == DaemonState.IDLE
    assert states_str["test3"] == DaemonState.IDLE
    states_str = manager.states()
    assert states_str["test1"] == "idle"
    assert states_str["test2"] == "idle"
    assert states_str["test3"] == "idle"
