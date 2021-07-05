"""
vtelem - Test the channel group class's correctness.
"""

# module under test
from vtelem.enums.primitive import Primitive
from vtelem.classes.channel_group import ChannelGroup
from vtelem.classes.telemetry_environment import TelemetryEnvironment

# internal
from . import EnumA


def test_channel_group_basic():
    """Test basic channel-group operations."""

    env = TelemetryEnvironment(2 ** 8)
    group = ChannelGroup("test_group", env)
    assert env.add_from_enum(EnumA) >= 0
    assert group.add_channel("test_chan", Primitive.UINT32, 1.0)
    assert not group.add_channel("test_chan", Primitive.UINT32, 1.0)
    assert group.add_enum_channel("test_enum", "enum_a", 1.0)
    assert not group.add_enum_channel("test_enum", "enum_a", 1.0)
    assert not group.add_enum_channel("test_new_enum", "not_an_enum", 1.0)

    with group.data() as data:
        data["test_chan"] = 1
        data["test_enum"] = "b"

    with group.data() as data:
        assert data["test_chan"] == 1
        assert data["test_enum"] == "b"

    assert env.has_channel("test_group.test_chan")
    assert env.has_channel("test_group.test_enum")
