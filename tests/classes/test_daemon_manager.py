"""
vtelem - Test the correctness of the daemon manager.
"""

# built-in
import json

# module under test
from vtelem.classes.daemon_base import DaemonOperation, DaemonState
from vtelem.classes.daemon_manager import DaemonManager
from vtelem.classes.command_queue_daemon import CommandQueueDaemon
from vtelem.classes.time_keeper import TimeKeeper
from vtelem.factories.daemon_manager import create_daemon_manager_commander

# internal
from tests import make_queue_cb, command_result


def get_test_manager() -> DaemonManager:
    """Create a manager with some daemons for testing purposes."""

    manager = DaemonManager()
    manager.add_daemon(TimeKeeper("test1", 0.05))
    manager.add_daemon(TimeKeeper("test2", 0.05))
    manager.add_daemon(TimeKeeper("test3", 0.05))
    return manager


def test_daemon_manager_commands():
    """Test commanding the daemon manager via command queue."""

    manager = get_test_manager()
    daemon = CommandQueueDaemon("command")
    result_queue, result_consumer = make_queue_cb()
    create_daemon_manager_commander(manager, daemon, result_consumer)

    cmd_data = {}
    base_cmd = {"command": "daemon", "data": cmd_data}

    with daemon.booted():
        # test no params
        result = command_result(base_cmd, daemon, result_queue)
        assert not result[0]

        # test invalid operation
        cmd_data["operation"] = "strike"
        result = command_result(base_cmd, daemon, result_queue)
        assert not result[0]

        # test valid operation, no daemons
        cmd_data["operation"] = "start"
        result = command_result(base_cmd, daemon, result_queue)
        assert not result[0]

        # test starting all daemons
        cmd_data["daemons"] = ["all"]
        result = command_result(base_cmd, daemon, result_queue)
        assert result[0]

        # make sure daemons started
        cmd_data["operation"] = "states"
        result = command_result(base_cmd, daemon, result_queue)
        assert result[0]
        result_dict = json.loads(result[1])
        for state in result_dict.values():
            assert state != "idle"

        # test stopping all daemons
        cmd_data["operation"] = "stop"
        result = command_result(base_cmd, daemon, result_queue)
        assert result[0]


def test_daemon_manager_basic():
    """Test management of basic tasks."""

    manager = get_test_manager()
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
