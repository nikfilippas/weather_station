import os
import numpy as np
from matplotlib.dates import num2date, DateFormatter
from matplotlib.ticker import MultipleLocator
from funcs import solar_height, get_sunrise_sunset, make_fig

# load historic data
outdir = "history/"
t, T = [], []
for fname in sorted(os.listdir(outdir)):
    if fname[-4:] == ".npz":
        f = np.load(outdir+fname)
        t.append(f["time"])
        T.append(f["temperature"])
t, T = map(np.hstack, [t, T])
t -= 719163  # include to correct for saving conversion of ``numpy.savez``

# calculate solar height
h = np.array([solar_height(num2date(time), mode="fast") for time in t])
sr_ss = [get_sunrise_sunset(d) for d in sorted(list(set(np.around(t))))]

# plot
fig, ax, axh = make_fig()
ax.set_xlabel("date (dd/mm)", fontsize=16)
ax.set_facecolor("navy")
ax.xaxis.set_major_locator(MultipleLocator(3))
ax.xaxis.set_minor_locator(MultipleLocator(1))
ax.yaxis.set_major_locator(MultipleLocator(5))
ax.yaxis.set_minor_locator(MultipleLocator(1))
axh.yaxis.set_major_locator(MultipleLocator(10))
ax.xaxis.set_major_formatter(DateFormatter("%d/%m"))
ax.tick_params(labelsize=12)
axh.tick_params(labelsize=12)
ax.set_xlim(t[0], t[-1])
ax.grid(which="major", color="k", ls=":", lw=1.5)
ax.grid(which="minor", color="k", ls=":", lw=1)
# plot day and night
for h0 in sr_ss:
    ax.axvspan(h0[0], h0[1], color="white")
    ax.axvspan(h0[0], h0[1], color="y", alpha=0.3)
# plot data
axh.plot(t, h, "grey", lw=3, alpha=0.7)
ax.plot_date(t, T, "r.")
fig.savefig("history/all_data.pdf", bbox_inches="tight")
