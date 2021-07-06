<!--
    =====================================
    generator=datazen
    version=1.7.4
    hash=c3674391701890d9b5ca28c91f0afb6d
    =====================================
-->

# vtelem ([0.2.5](https://pypi.org/project/vtelem/))

![Python package](https://github.com/vkottler/vtelem/workflows/Python%20package/badge.svg)

*A real-time telemetry library.*

# Command-line Options

```
$ ./venv3.8/bin/vtelem -h

usage: vtelem [-h] [--version] [-v] [-C DIR] [-i {lo,bond0,dummy0,eth0,sit0}]
              [-p PORT] [--ws-cmd-port WS_CMD_PORT]
              [--ws-tlm-port WS_TLM_PORT] [-t TICK] [--telem-rate TELEM_RATE]
              [--metrics-rate METRICS_RATE] [--time-scale TIME_SCALE]
              [-a APP_ID] [-u UPTIME]

A real-time telemetry library.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -v, --verbose         set to increase logging verbosity
  -C DIR, --dir DIR     execute from a specific directory
  -i {lo,bond0,dummy0,eth0,sit0}, --interface {lo,bond0,dummy0,eth0,sit0}
                        interface to bind to
  -p PORT, --port PORT  http api port
  --ws-cmd-port WS_CMD_PORT
                        websocket command-interface port
  --ws-tlm-port WS_TLM_PORT
                        websocket telemetry-interface port
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
