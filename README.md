<!--
    =====================================
    generator=datazen
    version=1.3.1
    hash=ada2a55008448e17422b51a9f8e07d2d
    =====================================
-->

# vtelem ([0.2.1](https://pypi.org/project/vtelem/))

![Python package](https://github.com/vkottler/vtelem/workflows/Python%20package/badge.svg)

*A real-time telemetry library.*

# Command-line Options

```
$ ./venv3.7/bin/vtelem -h

usage: vtelem [-h] [--version] [-v] [-C DIR]
              [-i {lo,eth0,eth1,br-3c06a5f5e1a4,docker0,dummy0}] [-p PORT]
              [-t TICK] [--telem-rate TELEM_RATE]
              [--metrics-rate METRICS_RATE] [--time-scale TIME_SCALE]
              [-a APP_ID] [-u UPTIME]

A real-time telemetry library.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -v, --verbose         set to increase logging verbosity
  -C DIR, --dir DIR     execute from a specific directory
  -i {lo,eth0,eth1,br-3c06a5f5e1a4,docker0,dummy0}, --interface {lo,eth0,eth1,br-3c06a5f5e1a4,docker0,dummy0}
                        interface to bind to
  -p PORT, --port PORT  http api port
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
