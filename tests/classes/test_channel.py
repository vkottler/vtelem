"""
vtelem - Test the channel class's correctness.
"""

# module under test
from vtelem.classes.channel import Channel
from vtelem.classes.event_queue import EventQueue
from vtelem.enums.primitive import Primitive


def test_channel_basic():
    """Test that emitting and the changed callbacks work."""

    queue = EventQueue()
    chan_a = Channel("a", Primitive.FLOAT, 1.0)
    chan_b = Channel("b", Primitive.UINT8, 1.0, queue)
    chan_c = Channel("c", Primitive.BOOL, 1.0, queue, False)

    time = float()

    assert chan_a.emit(time) is None
    assert chan_b.emit(time) is None
    assert chan_c.emit(time) is None

    time += 1.0

    assert chan_a.emit(time) is not None
    assert chan_b.emit(time) is not None
    assert chan_c.emit(time) is not None

    assert chan_a.set(1.0, time)
    assert chan_b.set(1, time)
    assert chan_c.set(True, time)

    events = queue.consume()
    assert len(events) == 2

    assert chan_b.command(1)
    assert not chan_c.command(True)
