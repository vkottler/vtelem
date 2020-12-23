
"""
vtelem - Unpack frames from raw bytes into coherent data.
"""

# internal
from . import TIMESTAMP_PRIM, COUNT_PRIM, ID_PRIM
from .byte_buffer import ByteBuffer
from .channel_registry import ChannelRegistry


def read_frame(data: bytearray, size: int, registry: ChannelRegistry) -> dict:
    """ Unpack a frame from an array of bytes. """

    result = {}
    buf = ByteBuffer(data, False, size)

    # read header
    result["timestamp"] = buf.read(TIMESTAMP_PRIM)
    result["size"] = buf.read(COUNT_PRIM)

    # read channel IDs
    result["channels"] = []
    for _ in range(result["size"]):
        chan = {"id": buf.read(ID_PRIM)}
        chan["channel"] = registry.get_item(chan["id"])
        result["channels"].append(chan)

    # read values
    for chan in result["channels"]:
        chan["value"] = buf.read(chan["channel"].type)

    return result
