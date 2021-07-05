"""
vtelem - Test the telemetry-environment factory functions.
"""

# built-in
from queue import Queue

# module under test
from vtelem.classes.telemetry_environment import TelemetryEnvironment
from vtelem.classes.command_queue_daemon import CommandQueueDaemon
from vtelem.enums.primitive import Primitive, get_name
from vtelem.factories.telemetry_environment import create_channel_commander

# internal
from tests import command_result, make_queue_cb
from tests.classes import EnumA


def assert_get_id(
    results: Queue, daemon: CommandQueueDaemon, chan_id: int, value: str
):
    """A simple function for asserting the result of a 'get' command."""

    cmd_data = {"operation": "get", "channel_id": chan_id}
    base_cmd = {"command": "channel", "data": cmd_data}
    result = command_result(base_cmd, daemon, results)
    assert result[0]
    assert result[1] == value


def test_channel_commander():  # pylint: disable=too-many-statements
    """Test all of the traversable paths for commanding channels."""

    env = TelemetryEnvironment(1024, metrics_rate=0.5)
    daemon = CommandQueueDaemon("test", env)
    result_queue, result_consumer = make_queue_cb()
    create_channel_commander(env, daemon, result_consumer)

    # add channels
    assert env.add_from_enum(EnumA) >= 0
    enum_ids = []
    for i in range(5):
        enum_ids.append(
            env.add_enum_channel("echan{}".format(i), "enum_a", 1.0)
        )
    prim_ids = {}
    for prim in Primitive:
        prim_list = []
        for i in range(5):
            chan_name = "{}_chan{}".format(get_name(prim), i)
            prim_list.append(env.add_channel(chan_name, prim, 1.0))
        prim_ids[get_name(prim)] = prim_list

    cmd_data = {}
    base_cmd = {"command": "channel", "data": cmd_data}
    with daemon.booted():
        # test no channel name
        cmd_data["operation"] = "get"
        result = command_result(base_cmd, daemon, result_queue)
        assert not result[0]

        # test unknown channel name
        cmd_data["channel_name"] = "not_a_channel"
        result = command_result(base_cmd, daemon, result_queue)
        assert not result[0]

        # test channel name, id mismatch
        cmd_data["channel_name"] = "echan0"
        cmd_data["channel_id"] = enum_ids[1]
        result = command_result(base_cmd, daemon, result_queue)
        assert not result[0]
        del cmd_data["channel_name"]

        # test bad channel id
        cmd_data["channel_id"] = 999
        result = command_result(base_cmd, daemon, result_queue)
        assert not result[0]
        del cmd_data["channel_id"]

        # test get - enum
        cmd_data["channel_name"] = "echan1"
        result = command_result(base_cmd, daemon, result_queue)
        assert result[0]
        assert result[1] == "a"

        # test bad operation
        cmd_data["operation"] = "destroy"
        result = command_result(base_cmd, daemon, result_queue)
        assert not result[0]

        # test get - bool
        del cmd_data["channel_name"]
        cmd_data["channel_id"] = prim_ids["boolean"][0]
        assert_get_id(result_queue, daemon, cmd_data["channel_id"], str(False))

        # test increment
        cmd_data["operation"] = "increment"
        cmd_data["value"] = 5
        cmd_data["channel_id"] = prim_ids["uint32"][0]
        result = command_result(base_cmd, daemon, result_queue)
        assert result[0]
        assert_get_id(result_queue, daemon, cmd_data["channel_id"], str(5))

        # test increment, decrement fail
        del cmd_data["channel_id"]
        cmd_data["channel_name"] = "echan1"
        cmd_data["operation"] = "increment"
        result = command_result(base_cmd, daemon, result_queue)
        assert not result[0]
        cmd_data["operation"] = "decrement"
        result = command_result(base_cmd, daemon, result_queue)
        assert not result[0]

        # test decrement
        del cmd_data["channel_name"]
        cmd_data["operation"] = "decrement"
        cmd_data["channel_id"] = prim_ids["uint32"][0]
        result = command_result(base_cmd, daemon, result_queue)
        assert result[0]
        assert_get_id(result_queue, daemon, cmd_data["channel_id"], str(0))

        # test set
        cmd_data["operation"] = "set"
        del cmd_data["value"]
        result = command_result(base_cmd, daemon, result_queue)
        assert not result[0]
        cmd_data["value"] = 5
        result = command_result(base_cmd, daemon, result_queue)
        assert result[0]
        assert_get_id(result_queue, daemon, cmd_data["channel_id"], str(5))

        # test set - enum
        cmd_data["operation"] = "set"
        del cmd_data["channel_id"]
        cmd_data["channel_name"] = "echan1"
        cmd_data["value"] = "b"
        result = command_result(base_cmd, daemon, result_queue)
        assert result[0]
        assert_get_id(result_queue, daemon, enum_ids[1], "b")
