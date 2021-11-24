"""
vtelem - A module for generic test utilities.
"""

# built-in
from queue import Queue
from typing import Tuple, cast

# internal
from vtelem.classes.udp_client_manager import UdpClientManager
from vtelem.daemon.command_queue import CommandQueueDaemon
from vtelem.daemon.websocket_telemetry import queue_get
from vtelem.stream.writer import StreamWriter, default_writer
from vtelem.telemetry.environment import TelemetryEnvironment
from vtelem.types.command_queue_daemon import ResultCbType


def writer_environment(
    mtu: int = 64, basis: float = 0.5
) -> Tuple[StreamWriter, TelemetryEnvironment]:
    """
    Create a stream-writer and telemetry environment.
    """

    # create the environment and register its frame queue
    env = TelemetryEnvironment(mtu, metrics_rate=1.0, app_id_basis=basis)
    writer, _ = default_writer("frames", env=env, queue=env.frame_queue)
    return writer, env


def udp_client_environment(
    mtu: int = 64, basis: float = 0.5
) -> Tuple[UdpClientManager, TelemetryEnvironment]:
    """Create a udp-client manager and telemetry environment."""

    writer, env = writer_environment(mtu, basis)
    return UdpClientManager(writer), env


def make_queue_cb() -> Tuple[Queue, ResultCbType]:
    """Create a new queue and result-callback based on it."""

    result_queue: Queue = Queue()

    def result_consumer(result: bool, msg: str) -> None:
        """Example result consumer."""
        result_queue.put((result, msg))

    return result_queue, result_consumer


def command_result(
    cmd: dict, daemon: CommandQueueDaemon, result_queue: Queue
) -> Tuple[bool, str]:
    """Execute a command and get the result."""

    daemon.enqueue(cmd)
    return cast(Tuple[bool, str], queue_get(result_queue))
