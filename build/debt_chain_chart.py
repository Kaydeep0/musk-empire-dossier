#!/usr/bin/env python3
"""H12+H7 — the traveling/time-buying debt chain. Renders charts/H12_debt_chain.png."""
import csv, os
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = os.path.dirname(__file__)
rows = list(csv.DictReader(open(os.path.join(HERE, "..", "data", "debt_chain.csv"))))
dates = [datetime.strptime(r["date"], "%Y-%m-%d") for r in rows]
debt = [float(r["debt_outstanding_b"]) for r in rows]

fig, ax = plt.subplots(figsize=(14, 7))
ax.step(dates, debt, where="post", color="#7a2230", lw=2.4, zorder=3)
ax.fill_between(dates, debt, step="post", alpha=0.12, color="#7a2230")
ax.scatter(dates, debt, color="#7a2230", s=40, zorder=4)

ann = {
    "2022-10-27": ("Twitter LBO\n~$13B debt", 20, 15),
    "2025-03-28": ("X \u2192 xAI\n(debt travels)", 0, 18),
    "2026-02-02": ("xAI(+X) \u2192 SpaceX\n(recast)", -10, 20),
    "2026-03-02": ("+$20B Goldman bridge\n\u2192 ~$30.3B total", -40, 14),
    "2026-06-15": ("IPO repays $18.9B\n(+$1.16B penalty)", 8, -38),
    "2027-09-02": ("Bridge matures\n(refi cliff)", -20, 18),
}
for r, d, v in zip(rows, dates, debt):
    if r["date"] in ann:
        t, dx, dy = ann[r["date"]]
        ax.annotate(t, xy=(d, v), xytext=(dx, dy), textcoords="offset points",
                    fontsize=8.5, color="#333", ha="center",
                    arrowprops=dict(arrowstyle="->", color="#7a2230", lw=0.8))

ax.set_title("H7 + H12 \u00b7 The traveling, time-buying debt: Twitter \u2192 X \u2192 xAI \u2192 SpaceX \u2192 the public",
             fontsize=13, fontweight="bold")
ax.set_ylabel("Acquisition / bridge debt carried by the Musk vehicle ($B)")
ax.set_ylim(0, 36)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.grid(True, alpha=0.15)
fig.text(0.5, 0.012,
         "Sources: SpaceX 424(b)(4) subsequent events & debt note (b); Twitter LBO terms from public/bank record (c). "
         "Educational only \u2014 not investment advice.",
         ha="center", fontsize=8, color="#666")
fig.tight_layout(rect=[0, 0.03, 1, 1])
out = os.path.join(HERE, "..", "charts", "H12_debt_chain.png")
fig.savefig(out, dpi=150)
print("wrote", out)
