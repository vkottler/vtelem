"""
vtelem - Test message framer correctness.
"""

# module under test
from vtelem.frame.fields import to_parsed

# internal
from tests.message import LONG_MESSAGE, create_env, parse_frames


def test_message_framer_basic():  # pylint: disable=too-many-locals
    """Test simple message serialization."""

    framer, env = create_env()
    long_message_bytes = LONG_MESSAGE.encode()

    frames, total_bytes = framer.serialize_message_str(LONG_MESSAGE)
    assert len(frames) > 1
    assert total_bytes > len(long_message_bytes)

    # attempt to de-serialize the message
    total_parsed = parse_frames(env, frames)

    # validate parsed results
    initial = total_parsed[0]
    assert to_parsed(initial.body) is not None
    curr_idx = initial.body["fragment_index"]
    message_bytes = initial.body["fragment_bytes"]
    should_match = [
        "message_type",
        "message_number",
        "message_crc",
        "total_fragments",
    ]
    for parsed in total_parsed[1:]:
        assert to_parsed(parsed.body) is not None
        for check in should_match:
            assert parsed.body[check] == initial.body[check]
        assert parsed.body["fragment_index"] == curr_idx + 1
        curr_idx = parsed.body["fragment_index"]

        message_bytes += parsed.body["fragment_bytes"]

    # verify overall correctness
    assert message_bytes == long_message_bytes
    assert message_bytes.decode() == LONG_MESSAGE
