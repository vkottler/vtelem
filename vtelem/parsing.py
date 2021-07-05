"""
vtelem - Parsing frames into runtime data.
"""

# internal
from .classes.byte_buffer import ByteBuffer
from .classes.channel_registry import ChannelRegistry
from .classes import TIMESTAMP_PRIM, ID_PRIM


def parse_data_frame(
    obj: dict, buf: ByteBuffer, registry: ChannelRegistry
) -> None:
    """
    From an object that contains frame-header data, parse the telemetry data.
    """

    assert obj["type"] == "data"

    # read channel IDs
    obj["channels"] = []
    for _ in range(obj["size"]):
        chan = {"id": buf.read(ID_PRIM)}
        chan["channel"] = registry.get_item(chan["id"])
        obj["channels"].append(chan)

    # read values
    for chan in obj["channels"]:
        chan["value"] = buf.read(chan["channel"].type)


def parse_event_frame(
    obj: dict, buf: ByteBuffer, registry: ChannelRegistry
) -> None:
    """
    From an object that contains frame-header data, parse the event data.
    """

    assert obj["type"] == "event"

    # read channel IDs
    obj["events"] = []
    for _ in range(obj["size"]):
        event = {"id": buf.read(ID_PRIM)}
        event["channel"] = registry.get_item(event["id"])
        obj["events"].append(event)

    # read events
    for event in obj["events"]:
        event["previous"] = {"value": buf.read(event["channel"].type)}
        event["previous"]["time"] = buf.read(TIMESTAMP_PRIM)
        event["current"] = {"value": buf.read(event["channel"].type)}
        event["current"]["time"] = buf.read(TIMESTAMP_PRIM)
