
"""
vtelem - Test the UDP-client manager module's correctness.
"""

# built-in
from queue import Queue

# module under test
from vtelem.classes.channel_framer import build_dummy_frame
from vtelem.classes.udp_client_manager import UdpClientManager
from vtelem.classes.stream_writer import StreamWriter


def test_udp_client_manager_basic():
    """ TODO """

    frame_queue = Queue()
    writer = StreamWriter("test_writer", frame_queue)
    manager = UdpClientManager(writer)

    with writer.booted():
        clients = []

        # add clients
        mtu = 1500 - 8
        for _ in range(5):
            client = manager.add_client(("localhost", 0))
            mtu = min(mtu, client[1])
            clients.append(client[0])

        # add some frames
        for _ in range(100):
            frame_queue.put(build_dummy_frame(mtu))

    # remove clients
    for client in clients:
        manager.remove_client(client)

    assert frame_queue.empty()
    frame_queue.join()
