
"""
vtelem - Uses daemon machinery to build the task that can consume outgoing
         telemetry frames.
"""

# built-in
from io import BytesIO
from queue import Queue
from typing import Dict

# internal
from .channel_frame import ChannelFrame
from .queue_daemon import QueueDaemon


class StreamWriter(QueueDaemon):
    """
    Implements a daemon for writing frames to an arbitrary number of client
    streams.
    """

    def __init__(self, name: str, frame_queue: Queue) -> None:
        """ Construct a new stream-writer daemon. """

        self.curr_id: int = 0
        self.streams: Dict[int, BytesIO] = {}

        def frame_handle(frame: ChannelFrame) -> None:
            """ Write this frame to all registered streams. """
            array, size = frame.raw()
            raw_frame = array[0:size]
            with self.lock:
                for stream in self.streams.values():
                    stream.write(raw_frame)
                    self.increment_metric("stream_writes")

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
            self.decrement_metric("stream_count")
        return result
