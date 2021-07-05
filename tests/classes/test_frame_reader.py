"""
vtelem - Test the frame-reader class's correctness.
"""

# built-in
import time

# module under test
from vtelem.classes.telemetry_environment import TelemetryEnvironment
from vtelem.enums.primitive import Primitive


def test_read_frame_basic():
    """Test that frames can be correctly read."""

    start_time = time.time()
    env = TelemetryEnvironment(2 ** 8, start_time)

    chan_ids = []
    for i in range(10):
        chan = env.add_channel("chan{}".format(i), Primitive.INT32, 0.1, True)
        chan_ids.append(chan)

    # build some frames
    total_frames = 0
    for i in range(10):
        if i > 8:
            env.write_crc = False
        for chan in chan_ids:
            env.set_now(chan, i * (-(1 ** i)))
        env.advance_time(0.1)
        total_frames += env.dispatch_now()
    assert total_frames > 0

    # parse the frames
    frames = []
    for _ in range(total_frames):
        frame, size = env.get_next_frame().raw()
        frames.append(env.decode_frame(frame, size))
    assert len(frames) == total_frames

    # check correctness of frames
    result = frames[0]
    assert result["type"] == "data"
    assert result["size"] == len(chan_ids)
