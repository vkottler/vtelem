"""
vtelem - A module containing generic utilities for building frames.
"""

# built-in
from collections import defaultdict
import logging
from typing import Callable, Dict, Type

# internal
from vtelem.classes import DEFAULTS
from vtelem.classes.type_primitive import TypePrimitive, new_default
from vtelem.enums.frame import FRAME_TYPES
from vtelem.enums.primitive import random_integer
from vtelem.frame import Frame, time_to_int
from vtelem.frame.channel import ChannelFrame
from vtelem.frame.message import MessageFrame

LOG = logging.getLogger(__name__)
FRAME_CLASS_MAP: Dict[str, Type] = defaultdict(lambda: Frame)
FRAME_CLASS_MAP["data"] = ChannelFrame
FRAME_CLASS_MAP["event"] = ChannelFrame
FRAME_CLASS_MAP["message"] = MessageFrame


def basis_to_int(basis: float) -> int:
    """
    Convert some basis floating-point number into a valid integer for an
    application identifier.
    """

    basis = abs(basis)
    if basis > 1.0:
        basis = 1.0 / basis
    return int(float(DEFAULTS["id"].value.max) * basis)


class Framer:
    """A class capable of building frames of a specified type."""

    def __init__(
        self,
        mtu: int,
        app_id_basis: float = None,
        use_crc: bool = True,
    ) -> None:
        """Construct a new framer."""

        self.mtu = mtu
        self.timestamp = new_default("timestamp")
        self.frame_types = FRAME_TYPES

        # build primitives to hold the frame types and timestamps
        self.timestamps: Dict[str, TypePrimitive] = {}
        self.primitives: Dict[str, TypePrimitive] = {}
        for name in self.frame_types:
            self.timestamps[name] = new_default("timestamp")
            self.primitives[name] = self.frame_types.get_primitive(name)
        self.primitives["app_id"] = Framer.create_app_id(app_id_basis)
        self.use_crc = use_crc
        LOG.info(
            "using application identifier '%d'",
            self.primitives["app_id"].get(),
        )

    def new_frame(self, frame_type: str, time: float = None) -> Frame:
        """Construct a new frame object."""

        timestamp = self.timestamps[frame_type]
        if time is not None:
            assert timestamp.set(time_to_int(time))
        return FRAME_CLASS_MAP[frame_type](
            self.mtu,
            self.primitives["app_id"],
            self.primitives[frame_type],
            timestamp,
            self.use_crc,
        )

    @staticmethod
    def create_app_id(basis: float = None) -> TypePrimitive:
        """
        Create a new application identifier, use a provided basis value if
        provided.
        """

        result = new_default("id")
        if basis is None:
            new_id = random_integer(DEFAULTS["id"])
        else:
            new_id = basis_to_int(basis)
        assert result.set(new_id)
        return result


def build_dummy_frame(
    overall_size: int,
    frame_type: str = "invalid",
    frame_builder: Callable[[Frame], None] = None,
    app_id_basis: float = None,
    bad_crc: bool = False,
) -> ChannelFrame:
    """Build an empty frame of a specified size."""

    frame = ChannelFrame(
        overall_size,
        Framer.create_app_id(app_id_basis),
        FRAME_TYPES.get_primitive(frame_type),
        new_default("timestamp"),
    )

    if frame_builder is not None:
        frame_builder(frame)

    frame.finalize(not bad_crc)
    frame.pad_to_mtu()
    assert frame.finalize() == overall_size
    return frame
