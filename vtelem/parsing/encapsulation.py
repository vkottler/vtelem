"""
vtelem - Parsing frames into runtime data.
"""

# built-in
import logging
from typing import Optional, Tuple, cast

# internal
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes import DEFAULTS
from vtelem.classes.byte_buffer import ByteBuffer
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.enums.frame import PARSERS
from vtelem.enums.primitive import get_size
from vtelem.types.frame import FrameFooter, FrameHeader, FrameType, ParsedFrame

LOG = logging.getLogger(__name__)


def parse_frame_header(
    buf: ByteBuffer, expected_id: Optional[TypePrimitive] = None
) -> Tuple[int, Optional[FrameHeader]]:
    """Attempt to parse a channel frame from a buffer."""

    # read header
    app_id = buf.read(DEFAULTS["id"])

    if expected_id is not None:
        if app_id != expected_id.get():
            return app_id, None

    return app_id, FrameHeader(
        buf.size,
        app_id,
        FrameType(buf.read(DEFAULTS["enum"])),
        buf.read(DEFAULTS["timestamp"]),
        buf.read(DEFAULTS["count"]),
    )


def parse_frame_footer(buf: ByteBuffer) -> FrameFooter:
    """Attempt to parse a channel fram footer from a buffer."""

    crc = None
    if buf.can_read(DEFAULTS["crc"]):
        crc = buf.read(DEFAULTS["crc"])
    return FrameFooter(crc)


def decode_frame(
    channel_registry: ChannelRegistry,
    data: bytes,
    size: int,
    expected_id: Optional[TypePrimitive] = None,
) -> Optional[ParsedFrame]:
    """Unpack a frame from an array of bytes."""

    buf = ByteBuffer(cast(bytearray, data), False, size)
    app_id, header = parse_frame_header(buf, expected_id)

    if header is None:
        assert expected_id is not None
        LOG.error("id mismatch: %d != %d", app_id, expected_id.get())
        return None

    result = PARSERS.get(header.type, PARSERS[FrameType.INVALID])(
        header, buf, channel_registry
    )

    footer = parse_frame_footer(buf)
    if footer.crc is not None:
        buf.size = buf.get_pos()
        buf.size -= get_size(DEFAULTS["crc"])
        if footer.crc != buf.crc32():
            LOG.error(
                "invalid crc on frame: %d != %d",
                footer.crc,
                buf.crc32(),
            )
            return None

    return ParsedFrame(header, result, footer)
