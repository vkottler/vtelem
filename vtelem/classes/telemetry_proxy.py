
"""
vtelem - TODO.
"""

# built-in
import errno
import logging
from queue import Queue
import socket
import time
from typing import Any, Callable, Tuple, Optional

# internal
from vtelem.enums.primitive import Primitive, get_size
from vtelem.mtu import create_udp_socket
from . import TIMESTAMP_PRIM, COUNT_PRIM, ENUM_TYPE
from .byte_buffer import primitive_from_buffer
from .channel_framer import FRAME_TYPES
from .daemon_base import DaemonBase, DaemonState
from .type_primitive import TypePrimitive

LOG = logging.getLogger(__name__)


def into_primitive_from_buffer(buf: bytearray, inst: TypePrimitive,
                               order: str = "!", _time: float = None) -> None:
    """ Read a primitive directly into storage. """

    assert inst.set(primitive_from_buffer(buf, inst.type, order), _time)


class TelemetryProxy(DaemonBase):
    """ TODO """

    def __init__(self, host: Tuple[str, int], output_stream: Queue,
                 app_id: TypePrimitive, poll_rate: float = 0.01,
                 sleep_fn: Callable = None) -> None:
        """ TODO """

        self.socket = create_udp_socket(host, False)
        name = self.socket.getsockname()
        super().__init__("{}:{}".format(name[0], name[1]))
        self.frames = output_stream
        self.expected_id = app_id
        self.curr_id = TypePrimitive(self.expected_id.type)
        self.poll_rate = poll_rate
        self.read_flags = socket.MSG_DONTWAIT
        self.function["sleep"] = sleep_fn
        if self.function["sleep"] is None:
            self.function["sleep"] = time.sleep

        def stop_server() -> None:
            """ TODO """

            name = self.socket.getsockname()
            LOG.info("closing udp listener on '%s:%d'", name[0], name[1])
            self.socket.close()

        self.function["inject_stop"] = stop_server

    def read_and_store(self, prim: TypePrimitive,
                       append_buf: bytearray = None) -> bool:
        """ TODO """

        try:
            data = self.socket.recv(prim.size(), self.read_flags)
            if append_buf is not None:
                append_buf.extend(data)
            into_primitive_from_buffer(data, prim)
            LOG.info("%s -> %s", data, prim)
            return True
        except OSError as exc:
            if exc.errno != errno.EAGAIN:
                LOG.error(exc)

        return False

    def read_primitive(self, prim: Primitive,
                       append_buf: bytearray = None) -> Optional[Any]:
        """ TODO """

        try:
            data = self.socket.recv(get_size(prim), self.read_flags)
            if append_buf is not None:
                append_buf.extend(data)
            result = primitive_from_buffer(data, prim)
            LOG.info("%s -> %s", data, result)
            return result
        except OSError as exc:
            if exc.errno != errno.EAGAIN:
                LOG.error(exc)

        return None

    def run(self, *_, **__) -> None:
        """ TODO """

        while self.state != DaemonState.STOPPING:

            # always sleep for the poll interval
            self.function["sleep"](self.poll_rate)

            frame_buf = bytearray()

            # attempt to read a frame identifier
            if not self.read_and_store(self.curr_id, frame_buf):
                continue

            # make sure we read the expected identifier, which makes it likely
            # that a real frame is to follow
            if self.curr_id != self.expected_id:
                LOG.debug("id mismatch %s != %s", self.curr_id,
                          self.expected_id)
                continue

            frame = {"app_id": self.curr_id.get()}

            # read type
            frame_type = self.read_primitive(ENUM_TYPE)
            if frame_type is None:
                continue
            frame["type"] = FRAME_TYPES.get_str(frame_type)

            # read timestamp
            frame["timestamp"] = self.read_primitive(TIMESTAMP_PRIM)
            if frame["timestamp"] is None:
                continue

            # read size
            frame["size"] = self.read_primitive(COUNT_PRIM)
            if frame["size"] is None:
                continue
