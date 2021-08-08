"""
vtelem - A module implementing message frames.
"""

# built-in
from typing import Any, Dict

# internal
from vtelem.classes.byte_buffer import crc
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.enums.frame import MESSAGE_TYPES
from vtelem.frame import Frame
from vtelem.frame.fields import MESSAGE_FIELDS


class MessageFrame(Frame):
    """An implementation of a message frame."""

    def initialize(
        self, field_data: Dict[str, TypePrimitive], fragment: str
    ) -> None:
        """Perform one-time initialization of a message frame."""

        assert not self.initialized

        # write fields
        for field in MESSAGE_FIELDS:
            assert field.name in field_data
            assert field_data[field.name].type == field.type
            self.write(field_data[field.name])

        # write fragment
        msg_len = self.buffer.append(fragment.encode())
        self.used += msg_len
        self.increment_count(msg_len)
        self.initialized = True

    @staticmethod
    def messag_crc(message: str) -> int:
        """Compute a message checksum."""

        return crc(message.encode())

    @staticmethod
    def message_type(intended: str) -> int:
        """Convert a message type to an integer."""

        return MESSAGE_TYPES.get_value(intended)

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
