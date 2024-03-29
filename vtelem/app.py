"""
vtelem - This package's command-line entry-point application.
"""

# built-in
import argparse
import socket

# third-party
import netifaces  # type: ignore

# internal
from vtelem.mtu import Host
from vtelem.telemetry.server import TelemetryServer
from vtelem.types.telemetry_server import (
    Service,
    TelemetryServices,
    default_services,
)


def entry(args: argparse.Namespace) -> int:
    """Execute the requested task."""

    # determine appropriate ip address
    ip_address = Host().address
    if args.interface is not None:
        iface = netifaces.ifaddresses(args.interface)[socket.AF_INET]
        ip_address = iface[0]["addr"]

    defaults = default_services()
    services = TelemetryServices(
        Service(defaults.http.name, Host(ip_address, args.port)),
        Service(
            defaults.websocket_cmd.name, Host(ip_address, args.ws_cmd_port)
        ),
        Service(
            defaults.websocket_tlm.name, Host(ip_address, args.ws_tlm_port)
        ),
        Service(defaults.tcp_tlm.name, Host(ip_address, args.tcp_tlm_port)),
    )

    # instantiate the server
    server = TelemetryServer(
        args.tick,
        args.telem_rate,
        args.metrics_rate,
        args.app_id,
        services,
    )

    # run until the server shuts down because of timeout, external command, or
    # interruption
    server.start_all()
    server.scale_speed(args.time_scale)
    server.await_shutdown(args.uptime)
    return 0


def add_app_args(parser: argparse.ArgumentParser) -> None:
    """Add application-specific arguments to the command-line parser."""

    base_rate = 0.05
    telem_rate = base_rate * 5
    metrics_rate = telem_rate * 2

    parser.add_argument(
        "-i",
        "--interface",
        required=False,
        help="interface to bind to",
        type=str,
        choices=netifaces.interfaces(),
    )
    parser.add_argument(
        "-p", "--port", default=0, type=int, help="http api port"
    )
    parser.add_argument(
        "--ws-cmd-port",
        default=0,
        type=int,
        help="websocket command-interface port",
    )
    parser.add_argument(
        "--ws-tlm-port",
        default=0,
        type=int,
        help="websocket telemetry-interface port",
    )
    parser.add_argument(
        "--tcp-tlm-port",
        default=0,
        type=int,
        help="tcp telemetry-interface port",
    )
    parser.add_argument(
        "-t",
        "--tick",
        default=base_rate,
        type=float,
        help="lenth of a time tick",
    )
    parser.add_argument(
        "--telem-rate",
        default=telem_rate,
        type=float,
        help="rate of the telemetry-servicing loop",
    )
    parser.add_argument(
        "--metrics-rate",
        default=metrics_rate,
        type=float,
        help="default rate of internal metrics data",
    )
    parser.add_argument(
        "--time-scale",
        type=float,
        help="scalar to apply to the progression of time",
        default=1.0,
    )
    parser.add_argument(
        "-a",
        "--app-id",
        type=float,
        help=(
            "a value that forms the basis for the " + "application identifier"
        ),
        required=False,
    )
    parser.add_argument(
        "-u",
        "--uptime",
        type=float,
        help="specify a finite duration to run the server",
        required=False,
    )
