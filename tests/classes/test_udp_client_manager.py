"""
vtelem - Test the UDP-client manager module's correctness.
"""

# module under test
from vtelem.channel.framer import build_dummy_frame
from vtelem.classes.udp_client_manager import UdpClientManager
from vtelem.classes.stream_writer import default_writer
from vtelem.mtu import DEFAULT_MTU


def test_udp_client_manager_basic():
    """Test that adding clients and sending data is functional."""

    writer, frame_queue = default_writer("test_writer")
    manager = UdpClientManager(writer)

    with writer.booted():
        clients = []

        # add clients
        mtu = DEFAULT_MTU
        for _ in range(5):
            client = manager.add_client(("google.com", 0))
            mtu = min(mtu, client[1])
            clients.append(client[0])
            assert manager.client_name(client[0])[1] != 0
            client = manager.add_client(("localhost", 0))
            mtu = min(mtu, client[1])
            clients.append(client[0])
            assert manager.client_name(client[0])[1] != 0

        # add some frames
        for i in range(100):
            crc_type = i % 2 == 0
            frame_queue.put(build_dummy_frame(mtu, None, crc_type))

    # remove clients
    for client in clients:
        manager.remove_client(client)

    assert frame_queue.empty()
    frame_queue.join()
