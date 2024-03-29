<!--
    =====================================
    generator=datazen
    version=3.1.0
    hash=e2b634299f7e920a2e765b42b4a29dcb
    =====================================
-->

# vtelem ([0.3.5](https://pypi.org/project/vtelem/))

[![python](https://img.shields.io/pypi/pyversions/vtelem.svg)](https://pypi.org/project/vtelem/)
![Build Status](https://github.com/vkottler/vtelem/workflows/Python%20Package/badge.svg)
[![codecov](https://codecov.io/gh/vkottler/vtelem/branch/master/graphs/badge.svg?branch=master)](https://codecov.io/github/vkottler/vtelem)
![PyPI - Status](https://img.shields.io/pypi/status/vtelem)
![Dependents (via libraries.io)](https://img.shields.io/librariesio/dependents/pypi/vtelem)

*A real-time telemetry library.*

See also: [generated documentation](https://vkottler.github.io/python/pydoc/vtelem.html)
(created with [`pydoc`](https://docs.python.org/3/library/pydoc.html)).

## Python Version Support

This package is tested with the following Python minor versions:

* [`python3.7`](https://docs.python.org/3.7/)
* [`python3.8`](https://docs.python.org/3.8/)
* [`python3.9`](https://docs.python.org/3.9/)
* [`python3.10`](https://docs.python.org/3.10/)

## Platform Support

This package is tested on the following platforms:

* `ubuntu-latest`

# Introduction

# Command-line Options

```
$ ./venv3.8/bin/vtelem -h

usage: vtelem [-h] [--version] [-v] [-C DIR] [-i {lo,bond0,dummy0,sit0,eth0}]
              [-p PORT] [--ws-cmd-port WS_CMD_PORT]
              [--ws-tlm-port WS_TLM_PORT] [--tcp-tlm-port TCP_TLM_PORT]
              [-t TICK] [--telem-rate TELEM_RATE]
              [--metrics-rate METRICS_RATE] [--time-scale TIME_SCALE]
              [-a APP_ID] [-u UPTIME]

A real-time telemetry library.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -v, --verbose         set to increase logging verbosity
  -C DIR, --dir DIR     execute from a specific directory
  -i {lo,bond0,dummy0,sit0,eth0}, --interface {lo,bond0,dummy0,sit0,eth0}
                        interface to bind to
  -p PORT, --port PORT  http api port
  --ws-cmd-port WS_CMD_PORT
                        websocket command-interface port
  --ws-tlm-port WS_TLM_PORT
                        websocket telemetry-interface port
  --tcp-tlm-port TCP_TLM_PORT
                        tcp telemetry-interface port
  -t TICK, --tick TICK  lenth of a time tick
  --telem-rate TELEM_RATE
                        rate of the telemetry-servicing loop
  --metrics-rate METRICS_RATE
                        default rate of internal metrics data
  --time-scale TIME_SCALE
                        scalar to apply to the progression of time
  -a APP_ID, --app-id APP_ID
                        a value that forms the basis for the application
                        identifier
  -u UPTIME, --uptime UPTIME
                        specify a finite duration to run the server

```

# Documentation

Project documentation can be found in
[Markdown](https://www.markdownguide.org/) files in the [`docs/`](docs)
directory.

* [Primitive Types](docs/primitive.md)
* [Frame Types](docs/message.md)
* [Message Types](docs/message_type.md)
* [Channel Identifiers](docs/channel_identifier.md)
* [Serializable Data Structures](docs/serializable.md)

# Internal Dependency Graph

A coarse view of the internal structure and scale of
`vtelem`'s source.
Generated using [pydeps](https://github.com/thebjorn/pydeps) (via
`mk python-deps`).

![vtelem's Dependency Graph](im/pydeps.svg)
