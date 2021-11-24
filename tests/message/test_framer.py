"""
vtelem - Test message framer correctness.
"""

# built-in
import json
from typing import List

# internal
from tests.message import LONG_MESSAGE, create_env, parse_frames

# module under test
from vtelem.classes.user_enum import UserEnum, user_enum
from vtelem.frame.fields import to_parsed
from vtelem.message.cache import from_temp_dir
from vtelem.types.frame import MessageType, ParsedFrame


def cache_message_str(
    frames: List[ParsedFrame],
    mtype: MessageType,
) -> str:
    """Use a temporary message cache to decode a String-based message."""

    with from_temp_dir() as cache:
        # Load the message and verify we collect it.
        for message in frames:
            cache.ingest(message)
        messages = cache.complete(mtype)
        assert len(messages) == 1

        # Return the contents.
        result = cache.content_str(mtype, messages[0])
        assert result is not None
        return result[1]


def test_message_framer_object():
    """Test that a UserEnum object can be transferred."""

    framer, env = create_env()

    # Serialize an enum.
    enum = user_enum("test", {0: "a", 1: "b", 2: "c"})
    frames, _ = framer.serialize_object(enum, message_type=MessageType.ENUM)

    # Verify the enum loaded is equivalent to the one sent..
    message = cache_message_str(parse_frames(env, frames), MessageType.ENUM)
    new_enum = enum.load_str(message)
    assert new_enum == enum
    assert isinstance(new_enum, UserEnum)


def test_message_framer_json():
    """Test that a JSON message can be transferred."""

    framer, env = create_env()

    # Serialize some data into message frames.
    data = {"a": 1, "b": 2, "c": 3}
    frames, _ = framer.serialize_message_json(data)

    # Verify the message loaded is equivalent to the one sent.
    message = cache_message_str(parse_frames(env, frames), MessageType.JSON)
    new_data = json.loads(message)
    assert new_data == data


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
