"""
vtelem - A daemon that provides decoded telemetry frames into a queue, from a
         file.
"""

# built-in
from contextlib import contextmanager
import logging
from pathlib import Path
from queue import Queue
from tempfile import NamedTemporaryFile
from typing import Iterator, List, NamedTuple, Optional, Tuple

# internal
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.type_primitive import TypePrimitive, new_default
from vtelem.client import TelemetryClient
from vtelem.daemon import DaemonBase, DaemonState
from vtelem.mtu import DEFAULT_MTU
from vtelem.stream.writer import StreamWriter
from vtelem.telemetry.environment import TelemetryEnvironment

LOG = logging.getLogger(__name__)
TELEM_SUFFIX = ".vtelem"


class FileDecodeTask(NamedTuple):
    """Attributes for a frame-decoding task to complete for a given file."""

    path: Path
    byte_index: int = 0
    max_frames: Optional[int] = None


class FileClient(DaemonBase, TelemetryClient):
    """A class for decoding telemetry frames found in files."""

    def __init__(
        self,
        task: FileDecodeTask,
        output_stream: Queue,
        channel_registry: ChannelRegistry,
        app_id: TypePrimitive = None,
        env: TelemetryEnvironment = None,
        mtu: int = DEFAULT_MTU,
    ) -> None:
        """Construct a new file client."""

        TelemetryClient.__init__(
            self, task.path.name, output_stream, channel_registry, app_id, mtu
        )
        DaemonBase.__init__(self, task.path.name, env)
        self.task = task
        self.frame_count: int = 0
        self.to_process: List[bytes] = []

    def process_raw_frames(self, task: FileDecodeTask) -> bool:
        """
        Process all staged byte payloads, but ensure that we don't process
        (and export via queue) more frames than were requested.
        """

        # Determine how many frames to process, we can either process them all
        # or we want to truncate so we don't process more than was requested.
        process_count = len(self.to_process)
        if task.max_frames is not None:
            process_count = min(
                process_count, task.max_frames - self.frame_count
            )

        # Consume the desired number of payloads from our process list.
        if process_count:
            to_process = [self.to_process.pop(0) for _ in range(process_count)]
            self.frame_count += self.handle_frames(to_process)

        # Determine if we've reached the limit of desired frames, if one was
        # provided.
        keep_reading = True
        if task.max_frames is not None:
            keep_reading = self.frame_count < task.max_frames
            if not keep_reading:
                LOG.info(
                    "%s: decoded %d frames (max: %d)",
                    self.name,
                    self.frame_count,
                    task.max_frames,
                )

        return keep_reading

    def run(self, *_, **__) -> None:
        """Read from the file and enqueue decoded frames."""

        with self.task.path.open("rb") as stream:
            stream.seek(self.task.byte_index)

            frame_size = new_default("count")
            assert self.env is not None

            while self.state != DaemonState.STOPPING:
                try:
                    data = stream.read(self.mtu + frame_size.type.value.size)
                    if not data:
                        LOG.info("%s: reached end-of-file", self.name)
                        self.frames.put(None)
                        break

                    # Accumulate new frames to process.
                    self.to_process.extend(
                        self.processor.process(data, frame_size, self.mtu)
                    )

                    # Stop processing frames (and reading) if we reached the
                    # maximum desired.
                    if not self.process_raw_frames(self.task):
                        break
                finally:
                    pass

            # Update the byte index.
            self.task = FileDecodeTask(
                self.task.path, stream.tell(), self.task.max_frames
            )


@contextmanager
def create(
    writer: StreamWriter,
    env: TelemetryEnvironment,
    mtu: int = DEFAULT_MTU,
    max_frames: int = None,
) -> Iterator[Tuple[FileClient, Queue]]:
    """
    Using a temporary file, create a file-client and register the file to the
    stream-writer.
    """

    queue = writer.get_queue()
    with NamedTemporaryFile(suffix=TELEM_SUFFIX) as output:
        path = Path(output.name)
        task = FileDecodeTask(path, 0, max_frames)
        client = FileClient(
            task, queue, env.channel_registry, env.app_id, env, mtu
        )
        with writer.add_file(path, flush=True):
            yield client, queue
