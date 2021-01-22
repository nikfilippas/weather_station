import numpy as np
from pysolar import solar
import matplotlib.pyplot as plt
from matplotlib.dates import datestr2num, num2date
from matplotlib.ticker import MultipleLocator


def make_fig():
    plt.close("all")
    fig, ax = plt.subplots(1, 1, figsize=(15, 7))
    ax.set_xlabel("date (MM-DD hh)", fontsize=16)
    ax.set_ylabel("temperature ($^{\\circ} \\mathrm{C}$)", fontsize=16)
    ax.yaxis.set_major_locator(MultipleLocator(0.5))
    ax.yaxis.set_minor_locator(MultipleLocator(0.1))

    ax2 = ax.twinx()
    ax2.spines["right"]
    ax2.set_ylabel("solar height ($^{\\circ}$)", fontsize=16)

    ax.grid(which="major", ls="--")
    ax.grid(which="minor", ls=":")
    fig.tight_layout()

    ax.set_autoscale_on(True) # enable autoscale
    ax.autoscale_view(True, True, True)
    return fig, ax, ax2

def json2data(data):
    """Convert json data format to datetime and temperature."""
    if not "AlectoV1-Temperature" in data:
        return None, None, 0
    else:
        # time
        timestamp = data[11:30]
        timestamp = datestr2num(timestamp)
        # temperature
        temp = data.split("temperature_C")[-1].split(",")[0][4:]
        temp = float(temp)
        return timestamp, temp, 1

def movavg(t, T, size=11):
    """Calculates and outputs the moving average of the y-axis."""
    if len(t) - size + 1 <= 0:  # convolution for set window will fail
        return [], []
    T = np.convolve(T, np.ones(size), mode="valid")/size
    t = t[size//2 : -size//2 + 1]
    return t, T

def solar_height(t, lat=37.9, lon=23.9, gmt_offset=+2):
    """Calculate height of the Sun given a time, and geographical coords."""
    lon_mod = lon-15*gmt_offset  # longitude relative to center of timezone
    return solar.get_altitude(lat, lon_mod, t)

def get_sunrise_sunset(date, lat=37.9, lon=23.9, gmt_offset=+2):
    """Calculate sunrise and sunset times for a set of given coordinates."""
    lon_mod = lon-15*gmt_offset  # longitude relative to center of timezone
    t = np.linspace(int(date), int(date)+1, 1440)
    h = [solar.get_altitude_fast(lat, lon_mod, num2date(tt)) for tt in t]
    return t.take( np.where( np.array(h)>0 )[0].take((0, -1)) )

def plot_sunrise_sunset(ax, t, sr, ss, has_sr=False, has_ss=False):
    """Plots the sunrise and sunset times if they have occured."""
    if len(t) < 2:
        return False, False
    if not has_sr and (t[0] < sr < t[-1]):  # plot sunrise
        ax.axvline(sr, c="orange", lw=5, alpha=0.5)
        has_sr = True
    if not has_ss and (t[0] < ss < t[-1]):  # plot sunset
        ax.axvline(ss, c="orange", lw=5, alpha=0.5)
        has_ss = True
    return has_sr, has_ss
