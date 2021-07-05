"""
vtelem - Test the channel-group registry's correctness.
"""

# module under test
from vtelem.enums.primitive import Primitive
from vtelem.classes.channel_group_registry import ChannelGroupRegistry
from vtelem.classes.telemetry_environment import TelemetryEnvironment

# internal
from . import EnumA


def test_group_registry_basic():
    """Test simple functionality of a group registry."""

    env = TelemetryEnvironment(2 ** 8)
    assert env.add_from_enum(EnumA) >= 0
    reg = ChannelGroupRegistry(env)
    groups = [
        reg.create_group("a"),
        reg.create_group("b"),
        reg.create_group("c"),
    ]

    # add channels to each group
    for group in groups:
        reg.add_channel(group, "a", Primitive.UINT32, 1.0)
        reg.add_channel(group, "b", Primitive.UINT32, 1.0)
        reg.add_channel(group, "c", Primitive.UINT32, 1.0)
        reg.add_enum_channel(group, "test_enum", "enum_a", 1.0)

    # write channels in each group
    for group in groups:
        with reg.group(group) as data:
            data["a"] = 1
            data["b"] = 2
            data["c"] = 3
            data["test_enum"] = "b"

    # read channels in each group to make sure correct values were written
    for group in groups:
        with reg.group(group) as data:
            assert data["a"] == 1
            assert data["b"] == 2
            assert data["c"] == 3
            assert data["test_enum"] == "b"
