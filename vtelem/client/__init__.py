"""
vtelem - A module exposing a common interface for telemetry clients.
"""

# built-in
import logging
from queue import Queue
from typing import List

# internal
from vtelem.channel.registry import ChannelRegistry
from vtelem.classes.type_primitive import TypePrimitive
from vtelem.frame.processor import FrameProcessor
from vtelem.mtu import DEFAULT_MTU
from vtelem.parsing.encapsulation import decode_frame

LOG = logging.getLogger(__name__)


class TelemetryClient:
    """A class implementing a few stubs for basic telemetry clients."""

    def __init__(
        self,
        name: str,
        output_stream: Queue,
        channel_registry: ChannelRegistry,
        app_id: TypePrimitive = None,
        mtu: int = DEFAULT_MTU,
    ) -> None:
        """Construct a new telemetry client."""

        self.name = name
        self.mtu = mtu
        self.channel_registry = channel_registry
        self.frames = output_stream
        self.expected_id = app_id
        self.processor = FrameProcessor()

    def update_mtu(self, new_mtu: int) -> None:
        """
        Update this proxy's understanding of the maximum transmission-unit
        size.
        """

        self.mtu = new_mtu
        LOG.info("%s: mtu set to %d", self.name, new_mtu)

    def handle_frames(self, new_frames: List[bytes]) -> int:
        """
        Attempt to decode any new frames and publish them to the upstream
        consumer.

        Return the number of successfully decoded frames.
        """

        count = 0
        for frame in new_frames:
            new_frame = decode_frame(
                self.channel_registry,
                frame,
                len(frame),
                self.expected_id,
            )
            if new_frame is not None:
                self.frames.put(new_frame)
                count += 1
        return count
