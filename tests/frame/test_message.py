"""
vtelem - Test message frame correctness.
"""

# module under test
from vtelem.frame.message import MessageFrame, frames_required
from vtelem.frame.framer import Framer
from vtelem.telemetry.environment import TelemetryEnvironment


def test_message_frame_basic():
    """Test simple message-frame operations."""

    basis = 0.5
    env = TelemetryEnvironment(2 ** 8, 0.0, app_id_basis=basis, use_crc=False)
    framer = Framer(64, basis, False)
    frame = framer.new_frame("message", 0.0)
    assert isinstance(frame, MessageFrame)

    # initialize frame
    message = "Hello, world!"
    assert frames_required(frame, len(message.encode())) == 1
    frame_values = {
        "message_type": MessageFrame.message_type("text"),
        "message_number": 0,
        "message_crc": MessageFrame.messag_crc(message),
        "fragment_index": 0,
        "total_fragments": 1,
    }
    frame.initialize(MessageFrame.create_fields(frame_values), message)
    assert frame.finalize(False) > 0

    frame_bytes, frame_size = frame.raw()
    assert frame_size == frame.frame_size(message)
    parsed = env.decode_frame(frame_bytes, frame_size)

    for key, val in frame_values.items():
        assert parsed[key] == val
