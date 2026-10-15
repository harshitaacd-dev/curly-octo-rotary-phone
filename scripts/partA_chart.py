"""Event-study chart for Part A. Usage: python scripts/partA_chart.py analysis/partA"""
import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURF, INK, INK2, GRID, BLUE = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6"
out = sys.argv[1]
e = pd.read_csv(os.path.join(out, "event_study.csv"))
e["irr"], e["lo"], e["hi"] = np.exp(e.Estimate), np.exp(e.Estimate - 1.96 * e["Std. Error"]), np.exp(e.Estimate + 1.96 * e["Std. Error"])
x = np.arange(len(e))
fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=SURF)
ax.set_facecolor(SURF)
for i, el in enumerate(e.elec):
    if el:
        ax.axvspan(i - 0.5, i + 0.5, color="#efeee9", zorder=0, lw=0)
ax.axhline(1, color=INK2, lw=1, zorder=1)
ax.vlines(x, e.lo, e.hi, color=BLUE, lw=2, zorder=2)
ax.scatter(x, e.irr, s=42, color=BLUE, edgecolor=SURF, linewidth=2, zorder=3)
ax.set_yscale("log")
ax.minorticks_off()
ax.set_yticks([0.03, 0.1, 0.3, 1, 3, 10, 30, 100])
ax.set_yticklabels(["0.03×", "0.1×", "0.3×", "1×", "3×", "10×", "30×", "100×"])
ax.set_xticks(x)
ax.set_xticklabels([m[2:].replace("-", "/") for m in e.month], rotation=0, fontsize=8, color=INK2)
for lab, m in (("Grok-1\n(text, paid)", "2023-11"), ("Grok-2 image\ngeneration", "2024-08"), ("Grok + Aurora\nfree for all", "2024-12")):
    i = list(e.month).index(m)
    ax.axvline(i - 0.5, color=INK, lw=1, ls=(0, (3, 3)), zorder=1)
    ax.text(i - 0.4, 140, lab, fontsize=8.5, color=INK, va="top")
ax.set_ylim(0.015, 160)
ax.grid(axis="y", color=GRID, lw=0.8)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.tick_params(colors=INK2, length=0)
ax.set_ylabel("Synthetic-media grievances vs X's other categories\n(rate ratio vs Jun 2021–Jul 2023, log scale)", color=INK2, fontsize=9)
ax.set_title("X India: synthetic & manipulated media grievances around Grok releases", loc="left", color=INK, fontsize=12, fontweight="bold")
fig.text(0.01, 0.01, "Poisson event study, category + month fixed effects; bars = 95% CI (robust SE); shaded columns = election months.\n"
         "Months are X reporting periods (26th–25th). Source: IT Rules monthly compliance reports (India).", fontsize=7.5, color=INK2)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(os.path.join(out, "event_study.png"), dpi=160, facecolor=SURF)
