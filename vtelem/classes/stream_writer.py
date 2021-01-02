
"""
vtelem - Uses daemon machinery to build the task that can consume outgoing
         telemetry frames.
"""

# built-in
from io import BytesIO
import logging
from queue import Queue
from typing import Callable, Dict

# internal
from .channel_frame import ChannelFrame
from .queue_daemon import QueueDaemon

LOG = logging.getLogger(__name__)


class StreamWriter(QueueDaemon):
    """
    Implements a daemon for writing frames to an arbitrary number of client
    streams.
    """

    def __init__(self, name: str, frame_queue: Queue,
                 error_handle: Callable[[int], None] = None) -> None:
        """ Construct a new stream-writer daemon. """

        self.curr_id: int = 0
        self.streams: Dict[int, BytesIO] = {}
        self.error_handle = error_handle

        def frame_handle(frame: ChannelFrame) -> None:
            """ Write this frame to all registered streams. """

            array, size = frame.raw()
            with self.lock:
                to_remove = []
                for stream_id, stream in self.streams.items():
                    try:
                        assert stream.write(array) == size
                        self.increment_metric("stream_writes")
                        self.increment_metric("bytes_written", size)
                    except OSError as exc:
                        LOG.error("stream '%s' (%d) error: %s (%d)",
                                  stream.name, stream_id, exc.strerror,
                                  exc.errno)
                        to_remove.append((stream_id, stream))

                # remove streams that errored when writing
                for stream_id, stream in to_remove:
                    LOG.warning("removing stream '%s' (%d) errors writing",
                                stream.name, stream_id)

                    # signal parent that their stream may be broken
                    if self.error_handle is not None:
                        self.error_handle(stream_id)

                    assert self.remove_stream(stream_id)

        super().__init__(name, frame_queue, frame_handle)

        # register and reset additional metrics
        self.reset_metric("stream_writes")
        self.reset_metric("stream_count")

    def add_stream(self, stream: BytesIO) -> int:
        """ Add a stream and return its integer identifier. """

        with self.lock:
            result = self.curr_id
            self.streams[result] = stream
            self.curr_id += 1
        self.increment_metric("stream_count")
        return result

    def remove_stream(self, stream_id: int) -> bool:
        """ Remove a stream, if one is present with this identifier. """

        with self.lock:
            result = stream_id in self.streams
            if result:
                del self.streams[stream_id]
        if result:
            self.decrement_metric("stream_count")
        return result
