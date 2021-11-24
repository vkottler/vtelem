"""
vtelem - Test the telemetry proxy's correctness.
"""

# built-in
import time

# internal
from tests import udp_client_environment

# module under test
from vtelem.channel.framer import Framer, build_dummy_frame
from vtelem.classes.udp_client_manager import UdpClientManager
from vtelem.client.udp import UdpClient, create
from vtelem.mtu import DEFAULT_MTU, Host
from vtelem.stream import queue_get, queue_get_none
from vtelem.stream.writer import default_writer
from vtelem.telemetry.environment import TelemetryEnvironment


def test_udp_client_create():
    """Test that a just-created telemetry client can decode telemetry."""

    manager, env = udp_client_environment()
    with create(manager, env) as (client, queue):
        with client.booted(), manager.writer.booted():
            time.sleep(0.5)
            for _ in range(10):
                env.advance_time(10)
                frame_count = env.dispatch_now()
                for _ in range(frame_count):
                    assert queue_get(queue) is not None


def test_udp_client_restart():
    """Test that a just-created telemetry client can decode telemetry."""

    manager, env = udp_client_environment()
    with create(manager, env) as (client, queue):
        with manager.writer.booted():
            for _ in range(5):
                with client.booted():
                    time.sleep(0.2)
                    for _ in range(10):
                        env.advance_time(10)
                        frame_count = env.dispatch_now()
                        for _ in range(frame_count):
                            assert queue_get(queue) is not None
                queue_get_none(queue)


def setup_environment() -> dict:
    """
    Test that unexpectedly closing a reading socket is handled correctly.
    """

    result: dict = {}
    # set up an environment
    app_basis = 0.5
    env = TelemetryEnvironment(
        DEFAULT_MTU, metrics_rate=1.0, app_id_basis=app_basis, use_crc=False
    )

    # set up a stream-writer
    writer, frame_queue = default_writer("test_writer", env=env)

    # set up the proxy
    proxy = UdpClient(
        Host("localhost", 0),
        writer.get_queue("proxy"),
        env.channel_registry,
        Framer.create_app_id(app_basis),
        env,
        DEFAULT_MTU,
    )

    manager = UdpClientManager(writer)
    client = manager.add_client(
        Host("localhost", proxy.socket.getsockname()[1])
    )
    proxy.update_mtu(client[1])
    env.handle_new_mtu(client[1])

    result["proxy"] = proxy
    result["writer"] = writer
    result["client"] = client
    result["app_basis"] = app_basis
    result["manager"] = manager
    result["frame_queue"] = frame_queue
    return result


def test_telemetry_proxy_read_error():
    """
    Test how the proxy handles its file-descriptor being closed mid operation.
    """

    testenv = setup_environment()
    assert testenv["proxy"].start()

    frame_count = 5
    with testenv["writer"].booted():
        # write some frames
        for _ in range(frame_count):
            testenv["frame_queue"].put(
                build_dummy_frame(testenv["proxy"].mtu, testenv["app_basis"])
            )

        # read expected number of frames
        for _ in range(frame_count):
            frame = queue_get(testenv["proxy"].frames)
            assert frame is not None

        # close the server unexpectedly
        testenv["proxy"].function["inject_stop"]()

        # write more frames
        for _ in range(frame_count):
            testenv["frame_queue"].put(
                build_dummy_frame(testenv["client"][1], testenv["app_basis"])
            )

    testenv["proxy"].stop()


def test_telemetry_proxy_basic():
    """Test that valid frames can be decoded."""

    testenv = setup_environment()
    assert testenv["proxy"].start()

    # write some frames
    frame_count = 5
    with testenv["writer"].booted():
        for i in range(frame_count):
            crc_type = i % 2 == 0
            testenv["frame_queue"].put(
                build_dummy_frame(
                    testenv["client"][1], testenv["app_basis"], crc_type
                )
            )
    testenv["manager"].remove_client(testenv["client"][0])

    # read frames from proxy
    for _ in range(frame_count):
        frame = queue_get(testenv["proxy"].frames)
        assert frame is not None

    assert testenv["proxy"].stop()
