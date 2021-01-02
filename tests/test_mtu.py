
"""
vtelem - Test the maximum-transmission-unit size calculation module.
"""

# built-in
import socket

# module under test
from vtelem.mtu import discover_ipv4_mtu


def test_mtu_discovery_basic():
    """ Test that mtu discovery works for given clients. """

    assert discover_ipv4_mtu((socket.getfqdn(), 0)) > 0
    assert discover_ipv4_mtu((socket.getfqdn(), 0), 2 ** 15 - 1) > 0
    assert discover_ipv4_mtu(("google.com", 0)) > 0
    assert discover_ipv4_mtu(("google.com", 0), 2 ** 15 - 1) > 0
