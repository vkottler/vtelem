"""
vtelem - A generic element that can be read from and written to buffers.
"""

# built-in
import logging
from typing import Any, Callable
import threading

# internal
from vtelem.enums.primitive import Primitive, default_val, get_size
from .byte_buffer import ByteBuffer

LOG = logging.getLogger(__name__)


class TypePrimitive:
    """
    A class for storing primitive data types that can be read from and written
    into buffers.
    """

    def __init__(
        self, instance: Primitive, changed_cb: Callable = None
    ) -> None:
        """Construct a new primitive storage of a certain type."""

        self.type = instance
        self.data: Any = default_val(self.type)
        self.changed_cb = changed_cb
        self.last_set: float = float()
        self.lock = threading.RLock()

    def __eq__(self, other) -> bool:
        """Generic equality check for primitives."""

        if not self.type == other.type:
            return False
        return abs(float(self.data) - float(other.data)) < 0.001

    def __str__(self) -> str:
        """Conver this type primitive into a String."""

        return "({}) {}".format(self.type.name, self.data)

    def add(self, data: Any, time: float = None) -> bool:
        """Safely add some amount to the primitive."""

        with self.lock:
            result = self.set(self.get() + data, time)
        return result

    def set(self, data: Any, time: float = None) -> bool:
        """Set this primitive's data manually."""

        if time is None:
            time = float()

        expected_type = self.type.value["type"]
        if isinstance(data, expected_type):

            # validate the desired value
            if not self.type.value["validate"](self.type, data):
                LOG.warning(
                    "value '%s' not valid for type '%s'", data, self.type
                )
                return False

            with self.lock:
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

    def get(self) -> Any:
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

    def read(self, buf: ByteBuffer, pos: int = None) -> Any:
        """
        Read this primitive out of a buffer, assign its data and return the
        result.
        """

        with buf.with_pos(pos):
            result = buf.read(self.type)
        self.data = result
        return result
