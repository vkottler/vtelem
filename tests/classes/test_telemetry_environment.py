"""
vtelem - Test the telemetry environment's correctness.
"""

# built-in
import time

# module under test
from vtelem.classes.channel import Channel
from vtelem.classes.channel_framer import create_app_id
from vtelem.classes.telemetry_environment import TelemetryEnvironment
from vtelem.classes.user_enum import UserEnum
from vtelem.enums.primitive import Primitive

# internal
from . import EnumA


def test_environment_commanding():
    """Test that channels can be commanded when expected to be."""

    start_time = time.time()
    env = TelemetryEnvironment(2 ** 8, start_time, 1.0)

    env.add_channel("a", Primitive.FLOAT, 0.1)
    env.add_channel("b", Primitive.FLOAT, 0.1)
    env.add_channel("c", Primitive.FLOAT, 0.1, commandable=False)
    assert env.command_channel("a", 1.0)
    assert env.command_channel("b", 2.0)
    assert not env.command_channel("c", 3.0)
    assert not env.command_channel("d", 4.0)

    assert env.add_from_enum(EnumA) >= 0
    env.add_enum_channel("enum_chan", "enum_a", 1.0)
    assert env.command_enum_channel("enum_chan", "b")
    assert not env.command_enum_channel("enum_chan2", "b")


def test_app_id_from_basis():
    """Test application-identifer creation."""

    create_app_id(2.0)


def test_environment_with_metrics():
    """Test that metrics channels are present when initialized."""

    start_time = time.time()
    env = TelemetryEnvironment(2 ** 8, start_time, 1.0)
    env.dispatch_now()
    env.advance_time(1.0)
    env.dispatch_now()
    frame = env.get_next_frame().raw()
    frame_data = env.decode_frame(frame[0], frame[1])
    assert frame_data["type"] == "data"

    # make sure all the metrics can be found in the frame
    expected_metrics = [
        "metrics_rate",
        "channel_count",
        "events_captured",
        "emits_captured",
        "frame_queue.elements",
        "frame_queue.total_enqueued",
        "frame_queue.total_dequeued",
    ]
    for metric in expected_metrics:
        found = False
        for chan in frame_data["channels"]:
            if metric == chan["channel"].name:
                found = True
                break
        assert found

    assert env.add_from_enum(EnumA) >= 0

    chan = env.add_enum_channel(
        "enum_chan", "enum_a", 1.0, True, ("b", float())
    )
    assert env.get_enum_value(chan) == "b"


def test_create_environment():
    """Test that an environment can be created successfully."""

    start_time = time.time()
    TelemetryEnvironment(2 ** 8, start_time)


def test_create_many_channels():
    """Test an environment with many channels."""

    start_time = time.time()
    env = TelemetryEnvironment(2 ** 8, start_time)

    chan_ids = []
    for i in range(1000):
        chan_ids.append(
            env.add_channel("chan{}".format(i), Primitive.FLOAT, 0.1)
        )

    # set all channels and dispatch
    for _ in range(5):
        for chan in chan_ids:
            env.set_now(chan, start_time)
        start_time += 0.1
        env.advance_time(0.1)
        env.dispatch_now()


def test_telemetry_environment_basic():
    """Exercise some basic telemetry-environment operations."""

    start_time = time.time()
    chan_1 = Channel("chan_1", Primitive.BOOL, 0.5)
    chan_2 = Channel("chan_2", Primitive.FLOAT, 0.25)
    env = TelemetryEnvironment(2 ** 8, start_time, None, [chan_1, chan_2])

    # add some basic enums
    env.add_enum(UserEnum("a", {0: "a", 1: "b", 2: "c"}))
    env.add_enum(UserEnum("b", {0: "a", 1: "b", 2: "c"}))
    env.add_enum(UserEnum("c", {0: "a", 1: "b", 2: "c"}))

    # add some enum channels
    a_tok = env.add_enum_channel("enum_chan_a", "a", 1.0, True)
    b_tok = env.add_enum_channel("enum_chan_b", "b", 1.0, True)
    c_tok = env.add_enum_channel("enum_chan_c", "c", 1.0, False)

    # advance time and set some values
    env.advance_time(1.0)
    env.set_enum_now(a_tok, "a")
    env.set_enum_now(b_tok, "b")
    env.set_enum_now(c_tok, "c")

    env.dispatch_now()
    env.dispatch_now()

    frame = env.get_next_frame()
    assert frame.finalize() > 0
    assert not frame.add_event(
        0, Primitive.BOOL, (False, float()), (False, float())
    )
    assert not frame.add(0, Primitive.BOOL, False)

    # set channel 'a' over and over
    for _ in range(100):
        env.advance_time(1.0)
        env.set_enum_now(a_tok, "a")
        env.advance_time(1.0)
        env.set_enum_now(a_tok, "b")
        env.advance_time(1.0)
        env.set_enum_now(a_tok, "c")

    env.dispatch_now()
