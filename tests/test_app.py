"""
vtelem - Test this package in the context of additional application tasks.
"""

# built-in
import time
from typing import Any, Dict

# module under test
from vtelem.classes.telemetry_server import TelemetryServer
from vtelem.classes.channel_group_registry import ChannelGroupRegistry
from vtelem.enums.primitive import Primitive


def test_telemetry_server_app_basic():
    """
    Test a basic use case for integrating telemetry into an application.
    """

    instance = 0

    def app_setup(groups: ChannelGroupRegistry, data: Dict[str, Any]) -> None:
        """Set up a channel group."""

        nonlocal instance
        data["a"] = "a"
        data["group_a"] = groups.create_group("channels_{}".format(instance))
        instance += 1
        groups.add_channel(data["group_a"], "a", Primitive.UINT32, 0.1)
        groups.add_channel(data["group_a"], "b", Primitive.UINT32, 0.1)
        groups.add_channel(data["group_a"], "c", Primitive.UINT32, 0.1, True)

    def app_loop(groups: ChannelGroupRegistry, data: Dict[str, Any]) -> None:
        """Update telemetry values."""

        with groups.group(data["group_a"]) as chan_data:
            chan_data["a"] += 1
            chan_data["b"] += 1
            chan_data["c"] += 1

        assert data["a"] == "a"

    server = TelemetryServer(0.01, 0.10, ("0.0.0.0", 0), 0.25)
    server.register_application("test1", 0.10, app_setup, app_loop)
    with server.booted():
        server.register_application("test2", 0.10, app_setup, app_loop)
        time.sleep(1.0)
