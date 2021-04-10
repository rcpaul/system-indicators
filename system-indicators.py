from datetime import datetime
import shutil

import tkinter as tk
from random import randint, seed, choice
from string import ascii_letters
import psutil

class MeasurementIndicator(tk.Label):
    keepVisibleNumUpdates = 0

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.config(bg="black", fg="white")

    def update(self, visible: bool, text: str, urgency=0):
        if visible: self.keepVisibleNumUpdates = 10
        else: self.keepVisibleNumUpdates -= 1

        if self.keepVisibleNumUpdates <= 0: text = ""
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

class CpuUsageIndicator(MeasurementIndicator):
    def measure(self):
        usage = psutil.cpu_percent()
        self.update(usage > 10, "C%.0f%%" % usage, self.clamp01(90, 100, usage))

class CpuMaxTemperatureIndicator(MeasurementIndicator):
    def measure(self):
        maxTemp = 0
        for core in psutil.sensors_temperatures()['coretemp']:
            if core.current > maxTemp: maxTemp = core.current

        human = "%.0f°C" % maxTemp
        self.update(True, human, self.clamp01(50, 80, maxTemp))

class MemoryUsageIndicator(MeasurementIndicator):
    def measure(self):
        usage = psutil.virtual_memory().percent
        human = "M%.0f%%" % usage
        self.update(True, human, self.clamp01(90, 95, usage))

class NetworkThroughputIndicator(MeasurementIndicator):
    r1 = 0
    t1 = 0

    def __init__(self, interface, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interface = interface
        
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
    r1 = 0
    w1 = 0

    def __init__(self, device, label, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = device
        self.label = label
        
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
    def __init__(self):
        tk.Tk.__init__(self)
        self.overrideredirect(True)
        self.geometry("+1090+1204")

        self.indicators = []
        self.indicators.append(CpuUsageIndicator())
        self.indicators.append(CpuMaxTemperatureIndicator())
        self.indicators.append(MemoryUsageIndicator())
        self.indicators.append(NetworkThroughputIndicator('enp7s0f1'))
        self.indicators.append(DiskTroughputIndicator('nvme0n1', 'SSD'))
        self.indicators.append(DiskTroughputIndicator('sda', 'HDD'))

        x = 0
        for indicator in self.indicators:
            indicator.grid(row=0, column=x)
            x += 1

        self.grid()

    def update(self):
        for indicator in self.indicators:
            indicator.measure()

        delay = round((1000000 - datetime.now().microsecond) / 1000)
        self.after(delay, self.update)

window=Window()
window.update()
window.mainloop()

# def do_stuff():
#     s = "C%.0f%% foo bar baz very\nlong string" % psutil.cpu_percent()
#     s += str(datetime.now().microsecond)
#     l.config(text=s, bg="black", fg="white")
#     n.config(text=s, bg="black", fg="white")

#     delay = round((1000000 - datetime.now().microsecond) / 1000)
#     # root.update_idletasks() 
#     # width = l.winfo_width() + 10
#     # print(width)
#     # root.geometry("{}x{}".format(width, 26))
#     # root.update_idletasks()

#     root.after(delay, do_stuff)

# root = tk.Tk()
# root.wm_overrideredirect(True)
# root.geometry("500x24+1200+1200")

# root.config(bg='silver')

# l = tk.Label(text='', font=("Helvetica", 8))
# l.pack(expand=True, side=tk.LEFT)

# n = tk.Label(text='Tweede', font=("Helvetica", 8))
# n.pack(expand=True)

# do_stuff()
# root.mainloop()
