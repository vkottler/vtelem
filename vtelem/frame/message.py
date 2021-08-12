"""
vtelem - A module implementing message frames.
"""

# built-in
from math import ceil
from typing import Any, Dict, Tuple

# internal
from vtelem.classes.byte_buffer import crc
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.frame import Frame
from vtelem.frame.fields import MESSAGE_FIELDS

HEADER_SIZE: int = 0
for _field in MESSAGE_FIELDS:
    HEADER_SIZE += _field.type.value.size


class MessageFrame(Frame):
    """An implementation of a message frame."""

    def initialize(
        self, field_data: Dict[str, TypePrimitive], fragment: bytes
    ) -> None:
        """Perform one-time initialization of a message frame."""

        assert not self.initialized

        # write fields
        for field in MESSAGE_FIELDS:
            assert field.name in field_data
            assert field_data[field.name].type == field.type
            self.write(field_data[field.name])

        # write fragment
        msg_len = self.buffer.append(fragment)
        self.used += msg_len
        self.increment_count(msg_len)
        self.initialized = True

    def initialize_str(
        self, field_data: Dict[str, TypePrimitive], fragment: str
    ) -> None:
        """Initialize a message with a String fragment."""

        return self.initialize(field_data, fragment.encode())

    @property
    def frame_overhead(self) -> int:
        """
        Compute the overhead required to serialize a message for this frame.
        """

        return HEADER_SIZE + self.overhead

    def frame_size(self, message: bytes) -> int:
        """Compute the size of a potential frame."""

        return self.frame_overhead + len(message)

    def frame_size_str(self, message: str) -> int:
        """Compute the size of a potential frame with a String payload."""

        return self.frame_size(message.encode())

    @staticmethod
    def messag_crc(message: bytes) -> int:
        """Compute a message checksum."""

        return crc(message)

    @staticmethod
    def messag_crc_str(message: str) -> int:
        """Compute a message checksum for a String message."""

        return MessageFrame.messag_crc(message.encode())

    @staticmethod
    def create_fields(
        values: Dict[str, Any] = None
    ) -> Dict[str, TypePrimitive]:
        """
        Create a dictionary for message-field data, optionally initialize it.
        """

        result = {}
        for field in MESSAGE_FIELDS:
            prim = TypePrimitive(field.type)
            if values is not None and field.name in values:
                prim.set(values[field.name])
            result[field.name] = prim
        return result


def frames_required(
    prototype: MessageFrame, message_len: int
) -> Tuple[int, int]:
    """
    Compute the number of frames required to completely transfer a message
    via message frames.
    """

    len_per_mtu = prototype.mtu - prototype.frame_overhead
    return ceil(message_len / len_per_mtu), len_per_mtu
