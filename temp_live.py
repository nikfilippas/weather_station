import time
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from matplotlib.dates import num2date
import matplotlib
from argparse import ArgumentParser
from funcs import make_fig, json2data, movavg, solar_height, \
                  get_sunrise_sunset, plot_sunrise_sunset
parser = ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true")
args = parser.parse_args()

matplotlib.use("Agg")  # backend not using IPython

try:  # pre-existing data in output file
    t, T, h = [], [], []
    with open("temp.out", "r") as f:
        for line in f:
            tt, TT, key = json2data(line)
            if not key == 1: continue
            t.append(tt)
            T.append(TT)
            h.append(solar_height(num2date(tt)))

            # propagate current data to next block of code
            t_b4 = tt
            T_b4 = TT
            data_b4 = line

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

signal_every = 151  # signal every 02m31s

while True:
    with open("temp.out", "r") as f:
        for line in f:
            pass

    try:  # re-direct from opening; file may now have data
        data = line
        if data == data_b4:  # repeated line (perhaps not recording?)
            if args.verbose:
                print("No new data. Perhaps recording has stopped?")
            time.sleep(signal_every)
            continue
    except NameError:  # file still empty
        time.sleep(signal_every)
        continue

    # add new data
    tt, TT, key = json2data(data)
    if not key == 1: continue
    t.append(tt)
    T.append(TT)
    h.append(solar_height(num2date(tt)))

    # interpolate discontinuities (e.g. stopped recording)
    try:
        missed_signals = int(86400*(tt - t_b4) / signal_every)
        if missed_signals > 10:
            # interpolate/re-calculate
            t_interp = np.linspace(t_b4, tt, missed_signals+1)[1:-1]
            T_interp = interp1d(t, T, kind="slinear")(t_interp)
            h_recalc = [solar_height(num2date(tt_int)) for tt_int in t_interp]
            # inject to existing data
            t = t[:-1] + t_interp.tolist() + [t[-1]]
            T = T[:-1] + T_interp.tolist() + [T[-1]]
            h = h[:-1] + h_recalc + [h[-1]]
            # indicate interpolated region in plot
            ax.axvspan(xmin=t_interp[0], xmax=t_interp[-1],
                       ymin=0, ymax=(1/15),
                       facecolor="indianred", hatch="xx")
    except NameError:  # file is empty (just started recording)
        pass
    except ValueError:  # not enough data points to interpolate
        pass

    # plot new data
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

    # make data from current state available in the next loop (b4 = before)
    t_b4 = tt
    T_b4 = TT
    data_b4 = data
    time.sleep(signal_every)
