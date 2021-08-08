"""
vtelem - Parsing frames into runtime data.
"""

# built-in
import logging
from typing import cast, Optional

# internal
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes import DEFAULTS
from vtelem.classes.byte_buffer import ByteBuffer
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.enums.frame import PARSERS, FRAME_TYPES
from vtelem.enums.primitive import get_size

LOG = logging.getLogger(__name__)


def parse_frame_header(
    result: dict, buf: ByteBuffer, expected_id: Optional[TypePrimitive] = None
) -> bool:
    """Attempt to parse a channel frame from a buffer."""

    # read header
    result["app_id"] = buf.read(DEFAULTS["id"])
    id_valid = True
    if expected_id is not None:
        id_valid = result["app_id"] == expected_id.get()
    result["type"] = FRAME_TYPES.get_str(buf.read(DEFAULTS["enum"]))
    result["timestamp"] = buf.read(DEFAULTS["timestamp"])
    result["size"] = buf.read(DEFAULTS["count"])
    return id_valid


def parse_frame_footer(result: dict, buf: ByteBuffer) -> bool:
    """Attempt to parse a channel fram footer from a buffer."""

    if buf.can_read(DEFAULTS["crc"]):
        result["crc"] = buf.read(DEFAULTS["crc"])
        buf.size = buf.get_pos()
        buf.size -= get_size(DEFAULTS["crc"])
        return result["crc"] == buf.crc32()

    return True


def decode_frame(
    channel_registry: ChannelRegistry,
    data: bytes,
    size: int,
    expected_id: Optional[TypePrimitive] = None,
) -> dict:
    """Unpack a frame from an array of bytes."""

    result: dict = {"valid": False, "crc": None}
    buf = ByteBuffer(cast(bytearray, data), False, size)

    if parse_frame_header(result, buf, expected_id):
        result["valid"] = True
        PARSERS.get(result["type"], PARSERS["invalid"])(
            result, buf, channel_registry
        )

        result["valid"] = parse_frame_footer(result, buf)
        if not result["valid"]:
            LOG.error(
                "invalid crc on frame: %d != %d",
                result["crc"],
                buf.crc32(),
            )
    else:
        assert expected_id is not None
        LOG.error("id mismatch: %d != %d", result["app_id"], expected_id.get())

    return result
