"""
vtelem - Parsing specific frame payloads.
"""

# built-in
import logging

# internal
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes import DEFAULTS
from vtelem.classes.byte_buffer import ByteBuffer
from vtelem.frame.fields import MESSAGE_FIELDS
from vtelem.types.frame import FrameHeader

LOG = logging.getLogger(__name__)


def parse_invalid_frame(
    header: FrameHeader, buf: ByteBuffer, ___: ChannelRegistry
) -> dict:
    """A default parser for frames we can't interpret."""

    LOG.warning("can't decode frame type '%s'", header.type)
    buf.advance(buf.remaining)
    return {"valid": False}


def parse_data_frame(
    header: FrameHeader, buf: ByteBuffer, registry: ChannelRegistry
) -> dict:
    """
    Attempt to parse a data frame from the remaining byte-buffer.
    """

    # read channel IDs
    obj: dict = {"channels": []}
    for _ in range(header.size):
        chan = {"id": buf.read(DEFAULTS["id"])}
        chan["channel"] = registry.get_item(chan["id"])
        assert not chan["channel"].is_stream
        obj["channels"].append(chan)

    # read values
    for chan in obj["channels"]:
        chan["value"] = buf.read(chan["channel"].type)

    return obj


def parse_event_frame(
    header: FrameHeader, buf: ByteBuffer, registry: ChannelRegistry
) -> dict:
    """
    Attempt to parse an event frame from the remaining byte-buffer.
    """

    # read channel IDs
    obj: dict = {"events": []}
    for _ in range(header.size):
        event = {"id": buf.read(DEFAULTS["id"])}
        event["channel"] = registry.get_item(event["id"])
        assert not event["channel"].is_stream
        obj["events"].append(event)

    # read events
    for event in obj["events"]:
        event["previous"] = {"value": buf.read(event["channel"].type)}
        event["previous"]["time"] = buf.read(DEFAULTS["timestamp"])
        event["current"] = {"value": buf.read(event["channel"].type)}
        event["current"]["time"] = buf.read(DEFAULTS["timestamp"])

    return obj


def parse_message_frame(
    header: FrameHeader, buf: ByteBuffer, _: ChannelRegistry
) -> dict:
    """
    Attempt to parse a message frame from the remaining byte-buffer.
    """

    obj = {field.name: buf.read(field.type) for field in MESSAGE_FIELDS}
    obj["fragment_bytes"] = buf.read_bytes(header.size)
    return obj


def parse_stream_frame(
    header: FrameHeader, buf: ByteBuffer, registry: ChannelRegistry
) -> dict:
    """
    Attempt to parse a stream frame from the remaining byte-buffer.
    """

    obj = {"id": buf.read(DEFAULTS["id"])}
    obj["channel"] = registry.get_item(obj["id"])
    assert obj["channel"].is_stream
    obj["index"] = buf.read(DEFAULTS["count"])
    obj["data"] = buf.read_bytes(header.size * obj["channel"].size())
    return obj
