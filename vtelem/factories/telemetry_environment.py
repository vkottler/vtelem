"""
vtelem - A module for creating functions based on telemetry environment
         instances.
"""

# built-in
from typing import Tuple

# internal
from vtelem.channel import Channel
from vtelem.daemon.command_queue import CommandQueueDaemon
from vtelem.telemetry.environment import TelemetryEnvironment
from vtelem.types.command_queue_daemon import ResultCbType


def channel_set(
    chan: Tuple[Channel, int],
    cmd: dict,
    time: float,
    env: TelemetryEnvironment,
) -> Tuple[bool, str]:
    """Attempt to set a channel from a command."""

    if "value" not in cmd:
        return False, f"no value provided to set '{chan[0]}'"

    if env.is_enum_channel(chan[1]):
        result = env.command_enum_channel_id(chan[1], cmd["value"])
    else:
        result = chan[0].command(cmd["value"], time, False)

    msg = "success" if result else "failure"
    return result, f"{msg}: set '{chan[0]}' to '{cmd['value']}'"


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
        return False, f"can't increment enum channel '{chan[0]}'"

    to_inc = 1
    if "value" in cmd:
        to_inc = cmd["value"]
    result = chan[0].command(to_inc, time, True)
    msg = "success" if result else "failure"
    return result, f"{msg}: incremented '{chan[0]}' by '{to_inc}'"


def channel_decrement(
    chan: Tuple[Channel, int],
    cmd: dict,
    time: float,
    env: TelemetryEnvironment,
) -> Tuple[bool, str]:
    """Attempt to decrement a channel by a certain amount."""

    if env.is_enum_channel(chan[1]):
        return False, f"can't decrement enum channel '{chan[0]}'"

    to_dec = 1
    if "value" in cmd:
        to_dec = cmd["value"]
    result = chan[0].command(to_dec * -1, time, True)
    msg = "success" if result else "failure"
    return result, f"{msg}: decremented '{chan[0]}' by '{to_dec}'"


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
                return False, f"missing key from '{key_list}'"

        # validate channel name, id, or both provided
        if "channel_name" in cmd:
            chan_name = cmd["channel_name"]
            if not env.has_channel(chan_name):
                return False, f"no channel '{chan_name}' known"
            chan_id = env.channel_registry.get_id(chan_name)
            assert chan_id is not None
            if "channel_id" in cmd and cmd["channel_id"] != chan_id:
                msg = f"id mismatch, '{cmd['channel_id']}' != '{chan_id}'"
                return False, msg
        elif "channel_id" in cmd:
            chan_id = cmd["channel_id"]

        # get the channel
        assert chan_id is not None
        chan = env.channel_registry.get_item(chan_id)
        if chan is None:
            return False, f"no channel with id '{chan_id}'"

        # check the operation
        if cmd["operation"] not in supported_ops:
            return False, f"operation '{cmd['operation']}' not supported"

        # return the result of the operation
        return supported_ops[cmd["operation"]](
            (chan, chan_id), cmd, env.get_time(), env
        )

    ops_str = ", ".join(f"'{val}'" for val in supported_ops)
    daemon.register_consumer(
        command_name,
        channel_commander,
        result_cb,
        f"{ops_str} channels",
    )
