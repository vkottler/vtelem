"""
vtelem - Test the stream-writer class's correctness.
"""

# built-in
import tempfile

# module under test
from vtelem.classes.stream_writer import default_writer
from vtelem.frame.framer import build_dummy_frame
from vtelem.mtu import DEFAULT_MTU


def test_stream_writer_basic():
    """Test basic functionality of a stream writer."""

    writer, frame_queue = default_writer("test_writer")
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
    queue_id = writer.registered_queue()[0]
    writer.remove_queue(writer.registered_queue()[0])

    # enqueue some frames
    for _ in range(100):
        frame_queue.put(build_dummy_frame(DEFAULT_MTU))

    # remove some streams
    assert writer.remove_stream(a_id)
    assert writer.remove_stream(b_id)
    assert not writer.remove_stream(a_id)

    # enqueue some frames
    for _ in range(100):
        frame_queue.put(build_dummy_frame(DEFAULT_MTU))

    assert writer.stop()

    # clean-up streams
    stream_a.close()
    stream_b.close()
    stream_c.close()

    writer.remove_queue(queue_id)
