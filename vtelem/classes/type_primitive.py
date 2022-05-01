"""
vtelem - A generic element that can be read from and written to buffers.
"""

# built-in
import logging
import struct
from typing import Callable, Tuple

# internal
from vtelem.enums.primitive import (
    Primitive,
    PrimitiveValue,
    default_val,
    get_size,
)

from . import DEFAULTS
from .byte_buffer import ByteBuffer

LOG = logging.getLogger(__name__)
ChangeCallback = Callable[
    [Tuple[PrimitiveValue, float], Tuple[PrimitiveValue, float]], None
]


class TypePrimitive:
    """
    A class for storing primitive data types that can be read from and written
    into buffers.
    """

    def __init__(
        self, instance: Primitive, changed_cb: ChangeCallback = None
    ) -> None:
        """Construct a new primitive storage of a certain type."""

        self.type = instance
        self.data: PrimitiveValue = default_val(self.type)
        self.changed_cb = changed_cb
        self.last_set: float = float()

    def __eq__(self, other) -> bool:
        """Generic equality check for primitives."""

        if not self.type == other.type:
            return False
        return abs(float(self.data) - float(other.data)) < 0.001

    def __str__(self) -> str:
        """Conver this type primitive into a String."""

        return f"({self.type.name}) {self.data}"

    def add(self, data: PrimitiveValue, time: float = None) -> bool:
        """Safely add some amount to the primitive."""

        return self.set(self.get() + data, time)

    def set(self, data: PrimitiveValue, time: float = None) -> bool:
        """Set this primitive's data manually."""

        if time is None:
            time = float()

        expected_type = self.type.value.type
        if isinstance(data, expected_type):

            # validate the desired value
            if not self.type.value.validate(self.type.value, data):
                LOG.warning(
                    "value '%s' not valid for type '%s'", data, self.type
                )
                return False

            # setup changed-callback if necessary
            if self.changed_cb is not None:
                cb_args = [(self.data, self.last_set), (data, time)]
                prev_data = self.data

            # set the new value
            self.data = expected_type(data)
            if time is not None:
                self.last_set = time

            # call changed-callback
            if self.changed_cb is not None and prev_data != data:
                self.changed_cb(*cb_args)
            return True

        LOG.warning(
            "can't assign '%s', expected type '%s' got '%s'",
            str(data),
            type(data),
            expected_type,
        )
        return False

    def get(self) -> PrimitiveValue:
        """Get this primitive's data."""

        return self.data

    def size(self) -> int:
        """Get the size of this primitive type."""

        return get_size(self.type)

    def write(self, buf: ByteBuffer, pos: int = None) -> int:
        """Write this primitive into a buffer."""

        with buf.with_pos(pos):
            result = buf.write(self.type, self.data)
        return result

    def read(
        self, buf: ByteBuffer, pos: int = None, chomp: bool = False
    ) -> PrimitiveValue:
        """
        Read this primitive out of a buffer, assign its data and return the
        result.
        """

        with buf.with_pos(pos):
            result = buf.read(self.type, chomp)
        self.data = result
        return result

    def buffer(self, order: str = "!") -> bytes:
        """Get this primitive as a buffer of bytes."""

        return struct.pack(order + self.type.value.fmt, self.data)


def new_default(
    default: str, changed_cb: ChangeCallback = None
) -> TypePrimitive:
    """Construct a new type primitive from a default type alias."""

    assert default in DEFAULTS
    return TypePrimitive(DEFAULTS[default], changed_cb)
