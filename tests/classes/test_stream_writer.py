"""
vtelem - Test the stream-writer class's correctness.
"""

# built-in
from queue import Queue
import random
import sys
import tempfile
from typing import Tuple

# module under test
from vtelem.classes.stream_writer import StreamWriter


class DummyFrame:
    """Class for mocking a channel frame."""

    def __init__(self) -> None:
        """Construct an empty frame."""
        self.data = bytearray()

    def add_byte(self, val: int) -> None:
        """Add a single byte to the frame."""
        self.data.extend(val.to_bytes(1, sys.byteorder))

    def raw(self) -> Tuple[bytearray, int]:
        """Required to match the channel-frame interface."""
        return self.data, len(self.data)


def random_garbage_factory() -> DummyFrame:
    """Create a dummy frame, containing a random number of random bytes."""

    frame = DummyFrame()
    for _ in range(int(random.random() * 1000.0)):
        frame.add_byte(int(random.random() * 255.0))
    return frame


def test_stream_writer_basic():
    """Test basic functionality of a stream writer."""

    frame_queue = Queue()
    writer = StreamWriter("test_writer", frame_queue)
    assert writer.start()

    # add streams
    # pylint:disable=consider-using-with
    stream_a = tempfile.TemporaryFile()
    stream_b = tempfile.TemporaryFile()
    stream_c = tempfile.TemporaryFile()
    a_id = writer.add_stream(stream_a)
    b_id = writer.add_stream(stream_b)
    writer.add_stream(stream_c)

    # add a queue
    queue_id = writer.add_queue(Queue())
    writer.remove_queue(writer.add_queue(Queue()))

    # enqueue some frames
    for _ in range(100):
        frame_queue.put(random_garbage_factory())

    # remove some streams
    assert writer.remove_stream(a_id)
    assert writer.remove_stream(b_id)
    assert not writer.remove_stream(a_id)

    # enqueue some frames
    for _ in range(100):
        frame_queue.put(random_garbage_factory())

    assert writer.stop()

    # clean-up streams
    stream_a.close()
    stream_b.close()
    stream_c.close()

    writer.remove_queue(queue_id)
