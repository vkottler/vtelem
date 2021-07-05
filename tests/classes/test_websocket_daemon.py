"""
vtelem - Test the websocket daemon's correctness.
"""

# built-in
import asyncio
import time

# third-party
import websockets

# module under test
from vtelem.classes.websocket_daemon import WebsocketDaemon
from vtelem.mtu import get_free_tcp_port


async def consumer(websocket, message, _) -> None:
    """Simple echo consumer."""
    await websocket.send(message)


def test_websocket_daemon_boot():
    """Test that the daemon can be started and stopped."""

    daemon = WebsocketDaemon("test", consumer)

    # make sure the loop can be started again
    for _ in range(5):
        with daemon.booted():
            time.sleep(0.01)


def test_websocket_daemon_basic():
    """Test basic client-server echoes with a few starts and stops."""

    port = get_free_tcp_port()
    daemon = WebsocketDaemon("test", consumer, ("0.0.0.0", port))

    for _ in range(5):
        with daemon.booted():
            time.sleep(0.1)

            # connect a client
            async def ping_test():
                """Send an arbitrary message and expect the same back."""

                uri = "ws://localhost:{}".format(port)
                async with websockets.connect(uri) as websocket:
                    msg = "hello!"
                    await websocket.send(msg)
                    response = await websocket.recv()
                    assert response == msg

            asyncio.get_event_loop().run_until_complete(ping_test())
