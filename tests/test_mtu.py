"""
vtelem - Test the maximum-transmission-unit size calculation module.
"""

# built-in
import socket

# module under test
from vtelem.mtu import discover_ipv4_mtu, create_udp_socket


def test_mtu_discovery_basic():
    """Test that mtu discovery works for given clients."""

    assert discover_ipv4_mtu((socket.getfqdn(), 0)) > 0
    assert discover_ipv4_mtu((socket.getfqdn(), 0), 2 ** 15 - 1) > 0
    assert discover_ipv4_mtu(("google.com", 0)) > 0
    assert discover_ipv4_mtu(("google.com", 0), 2 ** 15 - 1) > 0


def test_unreachable_host():
    """Test that we fall back to localhost when applicable."""

    create_udp_socket(("google.com", 0)).close()
    create_udp_socket(("unreachable.asdf", 0)).close()
