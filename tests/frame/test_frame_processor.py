"""
vtelem - Test the frame processor's correctness.
"""

# built-in

# module under test
from vtelem.classes.type_primitive import new_default
from vtelem.frame.framer import build_dummy_frame
from vtelem.frame.processor import FrameProcessor


def test_frame_processor_bogus_size():
    """
    Test that the frame processor fails to parse a frame that's too large.
    """

    proc = FrameProcessor()
    mtu = 64
    frame_size = new_default("count")
    data = build_dummy_frame(mtu).with_size_header()[0]
    assert len(proc.process(data, frame_size, mtu)) == 1

    # with a modified buffer, ensure we can't process a frame
    temp = new_default("count")
    temp.set(mtu * 2)
    data = temp.buffer() + build_dummy_frame(mtu).with_size_header()[0]
    assert len(proc.process(data, frame_size, mtu)) == 0
