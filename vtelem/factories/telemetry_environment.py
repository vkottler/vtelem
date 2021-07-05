"""
vtelem - A module for creating functions based on telemetry environment
         instances.
"""

# built-in
from typing import Tuple

# internal
from vtelem.classes.channel import Channel
from vtelem.classes.telemetry_environment import TelemetryEnvironment
from vtelem.classes.command_queue_daemon import CommandQueueDaemon
from vtelem.types.command_queue_daemon import ResultCbType


def channel_set(
    chan: Tuple[Channel, int],
    cmd: dict,
    time: float,
    env: TelemetryEnvironment,
) -> Tuple[bool, str]:
    """Attempt to set a channel from a command."""

    if "value" not in cmd:
        return False, "no value provided to set '{}'".format(str(chan[0]))

    if env.is_enum_channel(chan[1]):
        result = env.command_enum_channel_id(chan[1], cmd["value"])
    else:
        result = chan[0].command(cmd["value"], time, False)

    msg = "success" if result else "failure"
    return result, "{}: set '{}' to '{}'".format(
        msg, str(chan[0]), str(cmd["value"])
    )


def channel_get(
    chan: Tuple[Channel, int], _: dict, __: float, env: TelemetryEnvironment
) -> Tuple[bool, str]:
    """Return the value of a channel."""

    if env.is_enum_channel(chan[1]):
        return True, env.get_enum_value(chan[1])
    return True, str(chan[0].get())


def channel_increment(
    chan: Tuple[Channel, int],
    cmd: dict,
    time: float,
    env: TelemetryEnvironment,
) -> Tuple[bool, str]:
    """Attempt to increment a channel by a certain amount."""

    if env.is_enum_channel(chan[1]):
        return False, "can't increment enum channel '{}'".format(str(chan[0]))

    to_inc = 1
    if "value" in cmd:
        to_inc = cmd["value"]
    result = chan[0].command(to_inc, time, True)
    msg = "success" if result else "failure"
    return result, "{}: incremented '{}' by '{}'".format(
        msg, str(chan[0]), str(to_inc)
    )


def channel_decrement(
    chan: Tuple[Channel, int],
    cmd: dict,
    time: float,
    env: TelemetryEnvironment,
) -> Tuple[bool, str]:
    """Attempt to decrement a channel by a certain amount."""

    if env.is_enum_channel(chan[1]):
        return False, "can't decrement enum channel '{}'".format(str(chan[0]))

    to_dec = 1
    if "value" in cmd:
        to_dec = cmd["value"]
    result = chan[0].command(to_dec * -1, time, True)
    msg = "success" if result else "failure"
    return result, "{}: decremented '{}' by '{}'".format(
        msg, str(chan[0]), str(to_dec)
    )


def create_channel_commander(
    env: TelemetryEnvironment,
    daemon: CommandQueueDaemon,
    result_cb: ResultCbType = None,
    command_name: str = "channel",
) -> None:
    """Register a handler to a command queue for a telemetry environment."""

    supported_ops = {
        "set": channel_set,
        "get": channel_get,
        "increment": channel_increment,
        "decrement": channel_decrement,
    }

    def channel_commander(cmd: dict) -> Tuple[bool, str]:
        """Attempt to command a channel in this environment"""

        # validate input keys
        required_keys = [["operation"], ["channel_name", "channel_id"]]
        for key_list in required_keys:
            found = 0
            for key in key_list:
                if key in cmd:
                    found += 1
            if not found:
                return False, "missing key from '{}'".format(str(key_list))

        # validate channel name, id, or both provided
        if "channel_name" in cmd:
            chan_name = cmd["channel_name"]
            if not env.has_channel(chan_name):
                return False, "no channel '{}' known".format(chan_name)
            chan_id = env.channel_registry.get_id(chan_name)
            assert chan_id is not None
            if "channel_id" in cmd and cmd["channel_id"] != chan_id:
                msg = "id mismatch, '{}' != '{}'"
                return False, msg.format(cmd["channel_id"], chan_id)
        elif "channel_id" in cmd:
            chan_id = cmd["channel_id"]

        # get the channel
        assert chan_id is not None
        chan = env.channel_registry.get_item(chan_id)
        if chan is None:
            return False, "no channel with id '{}'".format(chan_id)

        # check the operation
        if cmd["operation"] not in supported_ops:
            msg = "operation '{}' not supported"
            return False, msg.format(cmd["operation"])

        # return the result of the operation
        return supported_ops[cmd["operation"]](
            (chan, chan_id), cmd, env.get_time(), env
        )

    ops_str = ", ".join("'{}'".format(val) for val in supported_ops)
    daemon.register_consumer(
        command_name,
        channel_commander,
        result_cb,
        "{} channels".format(ops_str),
    )
