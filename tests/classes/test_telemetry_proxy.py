"""
vtelem - Test the telemetry proxy's correctness.
"""

# module under test
from vtelem.channel.framer import Framer, build_dummy_frame
from vtelem.classes.stream_writer import default_writer
from vtelem.classes.telemetry_environment import TelemetryEnvironment
from vtelem.classes.telemetry_proxy import TelemetryProxy
from vtelem.classes.udp_client_manager import UdpClientManager
from vtelem.mtu import DEFAULT_MTU


def setup_environment() -> dict:
    """
    Test that unexpectedly closing a reading socket is handled correctly.
    """

    result: dict = {}
    # set up an environment
    env = TelemetryEnvironment(DEFAULT_MTU, metrics_rate=1.0)

    # set up a stream-writer
    writer, frame_queue = default_writer("test_writer", env=env)

    # set up the proxy
    app_basis = 0.5
    proxy = TelemetryProxy(
        ("localhost", 0),
        writer.get_queue("proxy"),
        Framer.create_app_id(app_basis),
        env,
        DEFAULT_MTU,
    )

    manager = UdpClientManager(writer)
    client = manager.add_client(("localhost", proxy.socket.getsockname()[1]))
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

    frame_count = 2
    with testenv["writer"].booted():
        # write some frames
        for _ in range(frame_count):
            testenv["frame_queue"].put(
                build_dummy_frame(testenv["client"][1], testenv["app_basis"])
            )

        # read expected number of frames
        for _ in range(frame_count):
            frame = testenv["proxy"].frames.get()
            assert not frame["valid"]

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
        frame = testenv["proxy"].frames.get()
        assert not frame["valid"]

    assert testenv["proxy"].stop()
