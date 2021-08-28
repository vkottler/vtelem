"""
vtelem - Constants for tests related to messages.
"""

# built-in
from typing import List, Tuple, Sequence

# module under test
from vtelem.frame.message import MessageFrame
from vtelem.message.framer import MessageFramer
from vtelem.telemetry.environment import TelemetryEnvironment
from vtelem.types.frame import ParsedFrame

LONG_MESSAGE = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
commodo consequat. Duis aute irure dolor in reprehenderit in voluptate
velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat
cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id
est laborum.
"""


def create_env(
    mtu: int = 64, basis: float = 0.5, use_crc: bool = False
) -> Tuple[MessageFramer, TelemetryEnvironment]:
    """Create a message framer and telemetry environment."""

    framer = MessageFramer(mtu, basis, use_crc)
    env = TelemetryEnvironment(mtu, 0.0, app_id_basis=basis, use_crc=use_crc)
    return framer, env


def parse_frames(
    env: TelemetryEnvironment, frames: Sequence[MessageFrame]
) -> List[ParsedFrame]:
    """Parse message frames."""

    total_parsed = []
    for frame in frames:
        result = env.decode_frame(*frame.raw)
        assert result is not None
        total_parsed.append(result)
    return total_parsed
