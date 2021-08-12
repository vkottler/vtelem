"""
vtelem - Test message framer correctness.
"""

# module under test
from vtelem.message.framer import MessageFramer
from vtelem.telemetry.environment import TelemetryEnvironment


def test_message_framer_basic():  # pylint: disable=too-many-locals
    """Test simple message serialization."""

    basis = 0.5
    framer = MessageFramer(64, basis, False)
    long_message = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
    tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
    veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
    commodo consequat. Duis aute irure dolor in reprehenderit in voluptate
    velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat
    cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id
    est laborum.
    """
    long_message_bytes = long_message.encode()

    frames, total_bytes = framer.serialize_message_str(long_message)
    assert len(frames) > 1
    assert total_bytes > len(long_message_bytes)

    # attempt to de-serialize the message
    env = TelemetryEnvironment(2 ** 8, 0.0, app_id_basis=basis, use_crc=False)
    total_parsed = []
    for frame in frames:
        result = env.decode_frame(*frame.raw())
        assert result is not None
        total_parsed.append(result)

    # validate parsed results
    initial = total_parsed[0]
    curr_idx = initial.body["fragment_index"]
    message_bytes = initial.body["fragment_bytes"]
    should_match = [
        "message_type",
        "message_number",
        "message_crc",
        "total_fragments",
    ]
    for parsed in total_parsed[1:]:
        for check in should_match:
            assert parsed.body[check] == initial.body[check]
        assert parsed.body["fragment_index"] == curr_idx + 1
        curr_idx = parsed.body["fragment_index"]

        message_bytes += parsed.body["fragment_bytes"]

    # verify overall correctness
    assert message_bytes == long_message_bytes
    assert message_bytes.decode() == long_message
