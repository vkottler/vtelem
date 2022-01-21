"""
vtelem - Utilities for calculating maximum transmission-unit sizes.
"""

# built-in
from enum import IntEnum
import logging
import socket
import sys
from typing import NamedTuple

# internal
from vtelem.channel.framer import build_dummy_frame
from vtelem.frame import FRAME_OVERHEAD

LOG = logging.getLogger(__name__)


def mtu_to_usable(mtu: int, medium_overhead: int = 60 + 8) -> int:
    """
    Given a desired overall size for transmission, get the usable size for
    a data payload.
    """

    return mtu - (medium_overhead + FRAME_OVERHEAD)


DEFAULT_MTU = mtu_to_usable(1500)


class Host(NamedTuple):
    """A generic representation of a network host."""

    address: str = "0.0.0.0"
    port: int = 0


class SocketConstants(IntEnum):
    """Some platform definitions necessary for mtu discovery."""

    IP_MTU = 14
    IP_MTU_DISCOVER = 10
    IP_PMTUDISC_DO = 2


def create_udp_socket(
    host: Host, is_client: bool = True, reuse: bool = True
) -> socket.SocketType:
    """Create a UDP socket, set to a requested peer address."""

    assert sys.platform == "linux"

    # create a udp socket and set it to the host
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if is_client:
        try:
            sock.connect(host)
        except socket.gaierror as exc:  # pragma: no cover
            LOG.error("%s, falling back to 'localhost:%d'", exc, host[1])
            sock.connect(("localhost", host[1]))
    else:
        sock.bind(host)

    if reuse:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    return sock


def discover_mtu(
    sock: socket.SocketType,
    probe_size: int = DEFAULT_MTU,
    app_id_basis: float = None,
) -> int:
    """
    Send a large frame and indicate that we want to perform mtu discovery, and
    not fragment any frames.
    """

    # see ip(7), force the don't-fragment flag and perform mtu discovery
    # such that the socket object can be queried for actual mtu upon error
    orig_val = sock.getsockopt(
        socket.IPPROTO_IP, SocketConstants.IP_MTU_DISCOVER
    )
    sock.setsockopt(
        socket.IPPROTO_IP,
        SocketConstants.IP_MTU_DISCOVER,
        SocketConstants.IP_PMTUDISC_DO,
    )

    try:
        count = sock.send(
            build_dummy_frame(probe_size, app_id_basis).with_size_header()[0]
        )
        LOG.info("mtu probe successfully sent %d bytes", count)
    except OSError:
        pass

    # restore the original value
    sock.setsockopt(
        socket.IPPROTO_IP, SocketConstants.IP_MTU_DISCOVER, orig_val
    )

    return sock.getsockopt(socket.IPPROTO_IP, SocketConstants.IP_MTU)


def get_free_port(
    kind: IntEnum,
    interface_ip: str = "0.0.0.0",
    test_port: int = 0,
    reuse: bool = True,
) -> int:
    """
    Create a socket to determine an arbitrary port number that's available.
    There is an inherent race condition using this strategy.
    """

    host = Host(interface_ip, test_port)

    sock = socket.socket(socket.AF_INET, kind)
    sock.bind((host.address, host.port))
    if reuse:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _, port = sock.getsockname()
    sock.close()
    return port


def host_resolve_zero(kind: IntEnum, host: Host) -> Host:
    """
    Convert a host with a zero port of a given kind to a host that resolves
    that port to one that should be open.
    """

    if host.port == 0:
        host = Host(host.address, get_free_port(kind, host.address))
    return host


def get_free_tcp_port(
    interface_ip: str = "0.0.0.0", test_port: int = 0
) -> int:
    """
    Determine if a given port is available for binding a tcp socket.
    """

    return get_free_port(socket.SOCK_STREAM, interface_ip, test_port)


def discover_ipv4_mtu(host: Host, probe_size: int = DEFAULT_MTU) -> int:
    """
    Determine the maximum transmission unit for an IPv4 payload to a provided
    host.
    """

    sock = create_udp_socket(host)
    result = discover_mtu(sock, probe_size)
    name = sock.getsockname()
    LOG.info(
        "discovered mtu to (%s:%d -> %s:%d) is %d (probe size: %d)",
        host[0],
        host[1],
        name[0],
        name[1],
        result,
        probe_size,
    )
    sock.close()
    return result
