
"""
vtelem - Utilities for calculating maximum transmission-unit sizes.
"""

# built-in
from enum import IntEnum
import logging
import socket
import sys
from typing import Tuple

# internal
from .classes.channel_framer import build_dummy_frame

LOG = logging.getLogger(__name__)


class SocketConstants(IntEnum):
    """ Some platform definitions necessary for mtu discovery. """

    IP_MTU = 14
    IP_MTU_DISCOVER = 10
    IP_PMTUDISC_DO = 2


def discover_ipv4_mtu(host: Tuple[str, int],
                      probe_size: int = 2 ** 15 - 1) -> int:
    """
    Determine the maximum transmission unit for an IPv4 payload to a provided
    host.
    """

    assert sys.platform == "linux"

    # create a udp socket and set it to the host
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(host)

    # see ip(7), force the don't-fragment flag and perform mtu discovery
    # such that the socket object can be queried for actual mtu upon error
    sock.setsockopt(socket.IPPROTO_IP, SocketConstants.IP_MTU_DISCOVER,
                    SocketConstants.IP_PMTUDISC_DO)

    try:
        count = sock.send(build_dummy_frame(probe_size).raw()[0])
        LOG.info("mtu probe successfully sent %d bytes", count)
    except socket.error:
        pass

    # determine mtu
    result = sock.getsockopt(socket.IPPROTO_IP, SocketConstants.IP_MTU)
    name = sock.getsockname()
    LOG.info("discovered mtu to (%s:%d -> %s:%d) is %d (probe size: %d)",
             host[0], host[1], name[0], name[1], result, probe_size)
    sock.close()
    return result
