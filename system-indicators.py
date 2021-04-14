from datetime import datetime

import tkinter as tk
import psutil
import yaml

class MeasurementIndicator(tk.Label):
    """Superclass for all indicators"""

    keepVisibleNumUpdates = 0
    redStart = None
    redEnd = None

    def __init__(self, *args, **kwargs):
        config = kwargs['config']
        del kwargs['config']
        super().__init__(args, kwargs)

        if 'red' in config:
            redStartString, redEndString = config['red'].split('-')
            self.redStart = int(redStartString)
            self.redEnd = int(redEndString)

        self.config(bg="black", fg="white")

    def update(self, visible: bool, text: str, value=0):
        if visible: self.keepVisibleNumUpdates = 10
        else: self.keepVisibleNumUpdates -= 1

        if self.keepVisibleNumUpdates <= 0: text = ""
        
        urgency = 0
        if self.redStart != None and self.redEnd != None:
            urgency = self.clamp01(self.redStart, self.redEnd, value)
        
        self.config(text=text, background=self.rgbtohex(urgency * 255, 0, 0))

    def rgbtohex(self, r, g, b):
        r = int(r)
        g = int(g)
        b = int(b)
        return f'#{r:02x}{g:02x}{b:02x}'

    def clamp01(self, min, max, value):
        if value < min: return 0
        if value > max: return 1
        return (value - min) / (max - min)

    def readString(self, path):
        with open(path, 'r') as f:
            return f.read()

    def readInteger(self, path):
        with open(path, 'r') as f:
            raw = f.read()
            integer = int(raw)
            return integer

    def sizeof_fmt(self, num):
        if abs(num) < 1024.0: return "%.0f" % num
        num /= 1024.0
        if abs(num) < 1024.0: return "%.0fk" % num

        for unit in ['k','M','G']:
            if abs(num) < 1024.0:
                return "%3.1f%s" % (num, unit)
            num /= 1024.0
        
        return "%.1fT" % (num)

class LoadIndicator(MeasurementIndicator):
    """Indicator for showing load"""

    def measure(self):
        load = psutil.getloadavg()[0];
        self.update(load > 1, "L{0:.2f}".format(load), load)

class CpuUsageIndicator(MeasurementIndicator):
    """Indicator for showing CPU usage"""

    def measure(self):
        usage = psutil.cpu_percent()
        self.update(usage > 10, "C%.0f%%" % usage, usage)

class CpuMaxTemperatureIndicator(MeasurementIndicator):
    """Indicator for showing the maximum temperature all cores"""

    def measure(self):
        maxTemp = 0
        for core in psutil.sensors_temperatures()['coretemp']:
            if core.current > maxTemp: maxTemp = core.current

        human = "%.0f°C" % maxTemp
        self.update(True, human, maxTemp)

class MemoryUsageIndicator(MeasurementIndicator):
    """Indicator for showing percentage of system memory in use"""
    def measure(self):
        usage = psutil.virtual_memory().percent
        human = "M%.0f%%" % usage
        self.update(True, human, usage)

class NetworkThroughputIndicator(MeasurementIndicator):
    """Indicator for showing network throughput"""

    r1 = 0
    t1 = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs['config']
        self.interface = config['interface']
        
    def measure(self):
        r2 = self.readInteger('/sys/class/net/' + self.interface + '/statistics/rx_bytes')
        t2 = self.readInteger('/sys/class/net/' + self.interface + '/statistics/tx_bytes')

        r = r2 - self.r1
        t = t2 - self.t1
        visible = r > 100 * 1024 or t > 100 * 1024
        text = "N %s/%s" % (self.sizeof_fmt(r), self.sizeof_fmt(t))
        self.update(visible, text)
        self.r1 = r2
        self.t1 = t2

class DiskTroughputIndicator(MeasurementIndicator):
    """Indicator for showing disk throughput"""

    r1 = 0
    w1 = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs['config']
        self.device = config['device']
        self.label = config['label']
        
    def measure(self):
        stat = self.readString('/sys/block/' + self.device + '/stat').split()
        r2 = int(stat[2])
        w2 = int(stat[6])

        r = (r2 - self.r1) * 512
        w = (w2 - self.w1) * 512
        visible = r > 1 * 1024 * 1024 or w > 1 * 1024 * 1024
        text = self.label + " %s/%s" % (self.sizeof_fmt(r), self.sizeof_fmt(w))
        self.update(visible, text)
        self.r1 = r2
        self.w1 = w2

class Window(tk.Tk):
    """Main window and instantiation of all indicators"""

    def __init__(self, config):
        tk.Tk.__init__(self)
        self.overrideredirect(True)
        self.geometry(config['window']['geometry'])

        indicatorClasses = {
            'load': LoadIndicator,
            'cpu-usage': CpuUsageIndicator,
            'cpu-max-temperature': CpuMaxTemperatureIndicator,
            'memory-usage': MemoryUsageIndicator,
            'network-throughput': NetworkThroughputIndicator,
            'disk-throughput': DiskTroughputIndicator
        }

        self.indicators = []
        for indicatorItem in config['indicators']:
            indicatorName = next(iter(indicatorItem))
            indicatorConfig = indicatorItem[indicatorName]
            indicator = indicatorClasses[indicatorName](config=indicatorConfig)
            self.indicators.append(indicator)

        x = 0
        for indicator in self.indicators:
            indicator.grid(row=0, column=x)
            x += 1

        self.grid()

    def update(self):
        for indicator in self.indicators:
            indicator.measure()

        # Schedule update at next wall clock second
        delay = round((1000000 - datetime.now().microsecond) / 1000)
        self.after(delay, self.update)

config = None
with open('config.yml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

window=Window(config)
window.update()
window.mainloop()
