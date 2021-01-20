import time
import numpy as np
from pysolar import solar
import matplotlib.pyplot as plt
from matplotlib.dates import datestr2num, num2date
from matplotlib.ticker import MultipleLocator
import matplotlib
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true")
args = parser.parse_args()

matplotlib.use("Agg")  # backend not using IPython
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


try:  # pre-existing data in output file
    t, T, h = [], [], []
    with open("temp.out", "r") as f:
        for line in f:
            tt, TT, key = json2data(line)
            if not key == 1: continue
            t.append(tt)
            T.append(TT)
            h.append(solar_height(num2date(tt)))
        sr, ss = get_sunrise_sunset(tt)
except:  # output file is empty
    t, T, h = [], [], []
    sr, ss = None, None


fig, ax, axh = make_fig()
has_sr, has_ss = plot_sunrise_sunset(ax, t, sr, ss)
p, = axh.plot(t, h, "grey", ls="-", lw=5, alpha=0.5)
l, = ax.plot_date(t, T, fmt="b.")
m, = ax.plot([], [], "r-", lw=2.5)
plt.draw()


while True:
    with open("temp.out", "r") as f:
        for line in f:
            pass

    try:  # re-direct from opening; file may now have data
        data = line
    except NameError:  # file still empty
        time.sleep(151)  # wait for next signal in 02m31s

    tt, TT, key = json2data(data)
    if not key == 1: continue
    t.append(tt)
    T.append(TT)
    h.append(solar_height(num2date(tt)))

    l.set_data(t, T)
    m.set_data(*movavg(t, T))
    p.set_data(t, h)

    # sunrise/sunset
    if sr is None:  # (similar to `ss is None`)
        sr, ss = get_sunrise_sunset(tt)
    if not (has_sr and has_ss):
        has_sr, has_ss = plot_sunrise_sunset(ax, t, sr, ss, has_sr, has_ss)

    ax.relim()
    ax.autoscale_view(True, True, True)
    axh.relim()
    axh.autoscale_view(True, True, True)
    plt.draw()

    t_now = num2date(tt)
    if args.verbose:
        print(t_now.year, t_now.month, t_now.day,
              t_now.hour, t_now.minute, t_now.second, TT)

    fig.savefig("temp.pdf", bbox_inches="tight")

    # save plot and data
    # and open new figure every day
    if (len(t) > 2) and (int(t[-1]) != int(t[-2])):
        # 1. flush file output contents
        open("temp.out", "w").close()
        # 2. add figure title
        t1 = num2date(t[-2])
        ax.set_title("%d/%d/%d" % (t1.day, t1.month, t1.year), fontsize=14)
        # 3. save figure and make new one
        t0 = num2date(t[0])
        mm = "0" + str(t0.month) if t0.month < 10 else str(t0.month)
        dd = "0" + str(t0.day) if t0.day < 10 else str(t0.day)
        yymmdd = str(t0.year) + mm + dd
        fig.savefig("history/temp_data_%s.pdf" % yymmdd, bbox_inches="tight")
        # 4. save temperature data
        np.savez("history/temp_data_%s" % yymmdd, time=t, temperature=T)
        # 5. delete data from memory
        t, T, h = [], [], []
        sr, ss = None, None
        has_sr, has_ss = False, False
        # 6. make new figure
        fig, ax, axh = make_fig()
        has_sr, has_ss = plot_sunrise_sunset(ax, t, sr, ss)
        p, = axh.plot(t, h, "grey", ls="-", lw=5, alpha=0.5)
        l, = ax.plot_date(t, T, fmt="b.")
        m, = ax.plot([], [], "r-", lw=2.5)
        plt.draw()

    time.sleep(151)  # next signal in 02m31s
