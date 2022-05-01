"""
vtelem - Uses daemon machinery to build the task that can consume outgoing
         telemetry frames.
"""

# built-in
from contextlib import contextmanager
from io import BytesIO
import logging
from pathlib import Path
from queue import Queue
from threading import Semaphore
from typing import (
    Any,
    BinaryIO,
    Callable,
    DefaultDict,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

# internal
from vtelem.classes import DEFAULTS
from vtelem.classes.metered_queue import MAX_SIZE, create
from vtelem.classes.time_entity import LockEntity
from vtelem.classes.type_primitive import new_default
from vtelem.daemon.queue import QueueDaemon
from vtelem.frame.channel import ChannelFrame
from vtelem.mtu import Host
from vtelem.telemetry.environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)
Stream = Union[BinaryIO, BytesIO]


class StreamWriter(QueueDaemon):
    """
    Implements a daemon for writing frames to an arbitrary number of client
    streams.
    """

    def __init__(
        self,
        name: str,
        frame_queue: Queue,
        error_handle: Callable[[int], None] = None,
        env: TelemetryEnvironment = None,
        time_keeper: Any = None,
    ) -> None:
        """Construct a new stream-writer daemon."""

        self.curr_id: int = 0
        self.queue_id: int = 0
        self.streams: Dict[int, Stream] = {}
        self.stream_attrs: Dict[int, Dict[str, bool]] = DefaultDict(
            lambda: DefaultDict(bool)
        )
        self.stream_closers: Dict[int, Optional[Callable]] = {}
        self.queues: Dict[int, Queue] = {}
        self.error_handle = error_handle

        frame_size = new_default("count")

        def frame_handle(frame: Optional[ChannelFrame]) -> None:
            """Write this frame to all registered streams."""

            if frame is not None:
                array, size = frame.with_size_header(frame_size)

                with self.lock:
                    to_remove = []
                    for stream_id, stream in self.streams.items():
                        try:
                            assert stream.write(array) == size
                            if self.stream_attrs[stream_id]["flush"]:
                                stream.flush()
                            self.increment_metric("stream_writes")
                            self.increment_metric("bytes_written", size)
                        except OSError as exc:
                            msg = (
                                "stream '%s' (%d) error writing %d "
                                + "bytes: %s (%d)"
                            )
                            LOG.error(
                                msg,
                                stream.name,
                                stream_id,
                                len(array),
                                exc.strerror,
                                exc.errno,
                            )
                            to_remove.append((stream_id, stream))

                    # remove streams that errored when writing
                    for stream_id, stream in to_remove:
                        LOG.warning(
                            "removing stream '%s' (%d) errors writing",
                            stream.name,
                            stream_id,
                        )

                        # signal parent that their stream may be broken
                        if self.error_handle is not None:
                            self.error_handle(stream_id)

                        assert self.remove_stream(stream_id)

            # add to queues
            with self.lock:
                queues = list(self.queues.values())
            for queue in queues:
                queue.put(frame)
            self.increment_metric("queue_writes", len(queues))

        super().__init__(name, frame_queue, frame_handle, env, time_keeper)

        # register and reset additional metrics
        self.reset_metric("stream_writes")
        self.reset_metric("stream_count")
        self.reset_metric("queue_writes")
        self.reset_metric("queue_count")

    @property
    def overhead(self) -> int:
        """Get the amount of overhead bytes introduced by the framer."""

        return DEFAULTS["count"].value.size

    def get_queue(self, name: str = None, maxsize: int = MAX_SIZE) -> Queue:
        """Get a default queue."""

        env: Any = None
        if name is not None:
            env = self.env
        return create(name, env, maxsize)

    def add_queue(self, queue: Queue) -> int:
        """Add a queue and return its integer identifier."""

        with self.lock:
            result = self.queue_id
            self.queues[result] = queue
            self.queue_id += 1
        self.increment_metric("queue_count")
        return result

    def registered_queue(
        self,
        name: str = None,
        maxsize: int = MAX_SIZE,
    ) -> Tuple[int, Queue]:
        """Construct a default queue, register it and return the result."""

        queue = self.get_queue(name, maxsize)
        return self.add_queue(queue), queue

    def add_stream(
        self,
        stream: Stream,
        stream_closer: Callable = None,
        flush: bool = False,
    ) -> int:
        """Add a stream and return its integer identifier."""

        with self.lock:
            result = self.curr_id
            self.streams[result] = stream
            self.stream_closers[result] = stream_closer
            self.stream_attrs[result]["flush"] = flush
            self.curr_id += 1
        self.increment_metric("stream_count")
        return result

    @contextmanager
    def stream_added(
        self,
        stream: Stream,
        stream_closer: Callable = None,
        flush: bool = False,
    ) -> Iterator[None]:
        """Provide an added-stream as a context."""

        stream_id = self.add_stream(stream, stream_closer, flush)
        try:
            yield
        finally:
            self.remove_stream(stream_id, stream_closer is not None)

    @contextmanager
    def add_file(
        self, path: Path, flush: bool = False, append: bool = True
    ) -> Iterator[None]:
        """Add a file as an output."""

        mode = f"{'a' if append else 'w'}b"
        with path.open(mode) as stream:
            with self.stream_added(cast(BinaryIO, stream), flush=flush):
                yield

    def add_semaphore_stream(self, stream: Stream) -> Tuple[int, Semaphore]:
        """
        Add a stream that waits for a semaphore to increment when closing.
        """

        sem = Semaphore(0)
        return self.add_stream(stream, sem.release), sem

    def remove_stream(self, stream_id: int, call_closer: bool = True) -> bool:
        """Remove a stream, if one is present with this identifier."""

        closer = None
        with self.lock:
            result = stream_id in self.streams
            if result:
                del self.streams[stream_id]
                closer = self.stream_closers[stream_id]
                del self.stream_closers[stream_id]
        if closer is not None and call_closer:
            closer()
        if result:
            self.decrement_metric("stream_count")
        return result

    def remove_queue(self, queue_id: int, inject_none: bool = True) -> bool:
        """Remove a stream, if one is present with this identifier."""

        with self.lock:
            result = queue_id in self.queues
            if result:
                if inject_none:
                    self.queues[queue_id].put(None)
                del self.queues[queue_id]
        if result:
            self.decrement_metric("queue_count")
        return result


class QueueClientManager(LockEntity):
    """
    A class for exposing common stream-writer queue registration operations.
    """

    def __init__(self, name: str, writer: StreamWriter) -> None:
        """Construct a new queue-client manager."""

        LockEntity.__init__(self)
        self.name = name
        self.writer = writer
        self.active_client_queues: List[int] = []

    def add_client_queue(self, addr: Host = None) -> Tuple[int, Queue]:
        """Register a new frame queue for a connected client."""

        name = None
        if addr is not None:
            name = f"{self.name}.{addr.address}:{addr.port}"
        queue_id, frame_queue = self.writer.registered_queue(name)
        with self.lock:
            self.active_client_queues.append(queue_id)
        return queue_id, frame_queue

    def close_clients(self) -> int:
        """
        Attempt to remove all active client-writing queues from the stream
        writer. This should initiate our side of the connections to begin
        closing.
        """

        closed = 0
        with self.lock:
            for queue_id in self.active_client_queues:
                if self.writer.remove_queue(queue_id):
                    closed += 1
        return closed


def default_writer(
    name: str = "writer",
    error_handle: Callable[[int], None] = None,
    env: TelemetryEnvironment = None,
    time_keeper: Any = None,
    maxsize: int = MAX_SIZE,
    queue: Queue = None,
) -> Tuple[StreamWriter, Queue]:
    """Construct a queue and a stream writer, return both."""

    if queue is None:
        queue = create(name + ".queue", env, maxsize)
    return StreamWriter(name, queue, error_handle, env, time_keeper), queue
