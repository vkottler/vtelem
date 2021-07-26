"""
vtelem - Parsing specific frame payloads.
"""

# built-in
import logging

# internal
from vtelem.classes import DEFAULTS
from vtelem.classes.byte_buffer import ByteBuffer
from vtelem.classes.channel_registry import ChannelRegistry

LOG = logging.getLogger(__name__)


def parse_invalid_frame(
    obj: dict, __: ByteBuffer, ___: ChannelRegistry
) -> None:
    """A default parser for frames we can't interpret."""

    LOG.warning("can't decode frame type '%s'", obj["type"])
    obj["valid"] = False


def parse_data_frame(
    obj: dict, buf: ByteBuffer, registry: ChannelRegistry
) -> None:
    """
    Attempt to parse a data frame from the remaining byte-buffer.
    """

    # read channel IDs
    obj["channels"] = []
    for _ in range(obj["size"]):
        chan = {"id": buf.read(DEFAULTS["id"])}
        chan["channel"] = registry.get_item(chan["id"])
        obj["channels"].append(chan)

    # read values
    for chan in obj["channels"]:
        chan["value"] = buf.read(chan["channel"].type)


def parse_event_frame(
    obj: dict, buf: ByteBuffer, registry: ChannelRegistry
) -> None:
    """
    Attempt to parse an event frame from the remaining byte-buffer.
    """

    # read channel IDs
    obj["events"] = []
    for _ in range(obj["size"]):
        event = {"id": buf.read(DEFAULTS["id"])}
        event["channel"] = registry.get_item(event["id"])
        obj["events"].append(event)

    # read events
    for event in obj["events"]:
        event["previous"] = {"value": buf.read(event["channel"].type)}
        event["previous"]["time"] = buf.read(DEFAULTS["timestamp"])
        event["current"] = {"value": buf.read(event["channel"].type)}
        event["current"]["time"] = buf.read(DEFAULTS["timestamp"])


def parse_message_frame(
    obj: dict, buf: ByteBuffer, registry: ChannelRegistry
) -> None:
    """
    Attempt to parse a message frame from the remaining byte-buffer.
    """

    return parse_invalid_frame(obj, buf, registry)


def parse_stream_frame(
    obj: dict, buf: ByteBuffer, registry: ChannelRegistry
) -> None:
    """
    Attempt to parse a stream frame from the remaining byte-buffer.
    """

    return parse_invalid_frame(obj, buf, registry)
