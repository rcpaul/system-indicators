# system-indicators
Show vital information with Python Tk. Support for
- 1 minute average system load
- CPU usage (percentage)
- Maximum temperature amongst all CPU cores
- Memory usage (percentage)
- Network throughput
- Disk throughput

It also can warn the user for values that become high.

Sample configuration to be placed in `config.yml`:

    indicators:
    - load:
        red: 2-4
    - cpu-usage:
        red: 80-100
    - cpu-max-temperature:
        red: 50-80
    - memory-usage:
        red: 85-95
    - network-throughput:
        interface: enp7s0f1
    - disk-throughput:
        device: nvme0n1
        label: SSD
    - disk-throughput:
        device: sda
        label: HHD

    window:
    geometry: +1090+1204