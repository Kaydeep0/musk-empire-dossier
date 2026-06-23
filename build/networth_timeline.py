#!/usr/bin/env python3
"""
Build the career + net-worth visualization:
  charts/JOURNEY_companies.png   - Gantt of the companies Musk moved through
  charts/CLIMB_networth.png      - net worth over time, decomposed into traceable parts,
                                   with net-worth labeled at specific dates.

Net worth proxy = Tesla stake (beneficial shares from Form 4 ledger x split-adjusted
price, b/m) + SpaceX stake (his econ % x funding-round valuation, c) + cumulative
realized cash from Tesla sales (b). Validated against published net worth (see
research/PHASE3_FINDINGS.md / printed cross-check).
"""
import csv, os
from datetime import datetime, date
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
REG = os.path.join(HERE, "..", "registry")
CHARTS = os.path.join(HERE, "..", "charts")
os.makedirs(CHARTS, exist_ok=True)

TESLA_RED = "#c81e3a"
SPACEX_BLUE = "#1f3b6f"
CASH_GOLD = "#caa028"


def split_factor(d):
    if d < "2020-08-31": return 15.0
    if d < "2022-08-25": return 3.0
    return 1.0


def load_prices():
    px = {r["date"]: float(r["close"]) for r in csv.DictReader(open(os.path.join(DATA, "prices_tsla.csv")))}
    return px, sorted(px)


def month_grid(start, end):
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(date(y, m, 1))
        m += 1
        if m > 12: m, y = 1, y + 1
    return out


def step_lookup(events, d):
    """events: sorted list of (date_str, value); return latest value at-or-before d."""
    v = 0.0
    ds = d.isoformat()
    for ed, val in events:
        if ed <= ds: v = val
        else: break
    return v


def main():
    px, pdates = load_prices()
    def price_on(d):
        ds = d.isoformat()
        prior = [x for x in pdates if x <= ds]
        return px[prior[-1]] if prior else 0.0

    # --- Tesla beneficial holdings from validated anchors (split-adjusted), forward-filled.
    # We use clean anchors rather than per-transaction shares_owned_after because some
    # filings around the 2022 split report holdings in post-split terms, which corrupts a
    # naive date-based split adjustment.
    tx = [r for r in csv.DictReader(open(os.path.join(DATA, "transactions.csv")))
          if r["ticker"] == "TSLA"]
    hold_events = [(r["date"], float(r["shares_mm_adjusted"]) * 1e6)
                   for r in csv.DictReader(open(os.path.join(DATA, "tesla_holdings_anchors.csv")))]
    hold_events.sort()

    # --- cumulative realized cash from Tesla sales
    sales = [(r["transaction_date"] or r["filing_date"], float(r["value_usd"]))
             for r in tx if r["code"] == "S" and r["value_usd"]]
    sales.sort()
    cash_events, run = [], 0.0
    for d, v in sales:
        run += v
        cash_events.append((d, run))

    # --- SpaceX stake value (valuation x econ pct)
    sx = list(csv.DictReader(open(os.path.join(DATA, "spacex_valuations.csv"))))
    sx_events = [(r["date"], float(r["valuation_usd_b"]) * 1e9 * float(r["musk_econ_pct"])) for r in sx]
    sx_events.sort()

    # --- monthly series
    grid = month_grid(date(2010, 6, 1), date(2026, 6, 1))
    tesla, spacex, cash, total = [], [], [], []
    for d in grid:
        t = step_lookup(hold_events, d) * price_on(d)
        s = step_lookup(sx_events, d)
        c = step_lookup(cash_events, d)
        tesla.append(t / 1e9); spacex.append(s / 1e9); cash.append(c / 1e9)
        total.append((t + s + c) / 1e9)

    # ===================== CHART: THE CLIMB =====================
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.stackplot(grid, tesla, spacex, cash,
                 labels=["Tesla stake (shares \u00d7 price)  \u00b7 filings",
                         "SpaceX stake (% \u00d7 round value)  \u00b7 est.",
                         "Cash realized from selling Tesla  \u00b7 filings"],
                 colors=[TESLA_RED, SPACEX_BLUE, CASH_GOLD], alpha=0.9)
    ax.plot(grid, total, color="#111", lw=1.3, zorder=5)

    # event markers
    events = list(csv.DictReader(open(os.path.join(REG, "career_events.csv"))))
    label_events = {
        "2010-06-29": "Tesla IPO",
        "2012-12-13": "SolarCity IPO",
        "2016-11-21": "SolarCity\nrolled into Tesla",
        "2020-03-01": "COVID surge",
        "2021-11-06": "Twitter poll \u2192\n~$16B sold",
        "2022-10-27": "Buys Twitter\n(~$44B)",
        "2025-11-06": "~$1T Tesla\npay package",
        "2026-06-16": "SpaceX IPO\n(SPCX)",
    }
    li = 0
    for ev in events:
        if ev["date"] in label_events:
            dt = datetime.strptime(ev["date"], "%Y-%m-%d")
            ax.axvline(dt, color="#555", ls=":", lw=0.8, zorder=4)
            yoff = max(total) * (1.02 if li % 2 == 0 else 1.10)
            ax.text(dt, yoff, label_events[ev["date"]], rotation=0,
                    fontsize=8, ha="center", va="bottom", color="#333")
            li += 1

    # net-worth callouts at anchor dates
    anchors = ["2012-12-01", "2016-12-01", "2020-12-01", "2021-11-01",
               "2022-12-01", "2024-12-01", "2026-06-01"]
    gridstr = [d.isoformat() for d in grid]
    for a in anchors:
        if a in gridstr:
            i = gridstr.index(a)
            dt = grid[i]
            ax.scatter([dt], [total[i]], color="#111", s=22, zorder=6)
            ax.annotate(f"${total[i]:,.0f}B",
                        xy=(dt, total[i]), xytext=(0, 10), textcoords="offset points",
                        ha="center", fontsize=9, fontweight="bold", color="#111")

    # annotate the SpaceX IPO repricing (shown conservatively at the last private round)
    ax.annotate("At the June-2026 SPCX IPO, his ~36% SpaceX stake\n"
                "reprices to ~$870B (36% \u00d7 $2.4T) \u2192 paper net worth ~$1.0T.\n"
                "Shown here at the last private round ($350B) to stay conservative.",
                xy=(date(2026, 6, 1), total[-1]), xytext=(date(2018, 6, 1), max(total) * 0.78),
                fontsize=8.5, color="#1f3b6f",
                bbox=dict(boxstyle="round,pad=0.4", fc="#eef2f8", ec="#1f3b6f", lw=0.8),
                arrowprops=dict(arrowstyle="->", color="#1f3b6f"))

    ax.set_title("The Climb \u00b7 Elon Musk's net worth and where it comes from (2010\u20132026)",
                 fontsize=15, fontweight="bold", pad=42)
    ax.set_ylabel("Estimated net worth ($ billions)")
    ax.set_ylim(0, max(total) * 1.18)
    ax.set_xlim(grid[0], date(2026, 12, 1))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", fontsize=10, framealpha=0.95)
    ax.grid(True, axis="y", alpha=0.15)
    fig.text(0.5, 0.012,
             "Tesla stake & realized cash: SEC Form 4 (CIK 1494730) \u00d7 Yahoo prices (b/m). "
             "SpaceX stake: his econ % \u00d7 reported round valuations (c). Educational only \u2014 not investment advice.",
             ha="center", fontsize=8, color="#666")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    out = os.path.join(CHARTS, "CLIMB_networth.png")
    fig.savefig(out, dpi=150); plt.close(fig)
    print("wrote", out)

    # print anchor table
    print("\nNet worth at specific dates (computed proxy):")
    for a in anchors:
        i = gridstr.index(a)
        print(f"  {a[:7]}   total ${total[i]:>6,.0f}B   (Tesla ${tesla[i]:,.0f}B + SpaceX ${spacex[i]:,.0f}B + cash ${cash[i]:,.0f}B)")

    # ===================== CHART: THE JOURNEY (Gantt) =====================
    spans = [
        ("Zip2", "1995-11-01", "1999-02-01", "#888"),
        ("X.com / PayPal", "1999-03-01", "2002-10-03", "#888"),
        ("SpaceX", "2002-05-01", "2026-12-01", SPACEX_BLUE),
        ("Tesla", "2004-02-01", "2026-12-01", TESLA_RED),
        ("SolarCity", "2006-07-01", "2016-11-21", "#2a9d8f"),
        ("OpenAI (cofounder)", "2015-12-01", "2018-02-01", "#888"),
        ("Neuralink", "2016-07-01", "2026-12-01", "#7b4fa3"),
        ("The Boring Co.", "2016-12-01", "2026-12-01", "#7b4fa3"),
        ("Twitter / X", "2022-10-27", "2026-12-01", "#444"),
        ("xAI", "2023-07-12", "2025-09-01", "#444"),
    ]
    fig, ax = plt.subplots(figsize=(15, 7))
    for i, (name, s, e, col) in enumerate(spans):
        sd = datetime.strptime(s, "%Y-%m-%d"); ed = datetime.strptime(e, "%Y-%m-%d")
        ax.barh(i, (ed - sd).days, left=sd, height=0.55, color=col, alpha=0.85)
        ax.text(sd, i + 0.42, name, fontsize=9, va="bottom", color="#222")

    typ_marker = {"ipo": ("^", "#c81e3a", "IPO"), "exit": ("s", "#444", "exit/sale"),
                  "acq": ("D", "#444", "acquisition"), "found": ("o", "#999", "founded"),
                  "event": ("*", "#caa028", "event")}
    name_to_y = {n: i for i, (n, *_ ) in enumerate(spans)}
    alias = {"PayPal": "X.com / PayPal", "Twitter": "Twitter / X"}
    for ev in events:
        ent = alias.get(ev["entity"], ev["entity"])
        if ent not in name_to_y: continue
        y = name_to_y[ent]
        mk = typ_marker.get(ev["type"], ("o", "#999", ""))
        dt = datetime.strptime(ev["date"], "%Y-%m-%d")
        ax.scatter([dt], [y], marker=mk[0], color=mk[1], s=90, zorder=5, edgecolors="white", linewidths=0.5)

    from matplotlib.lines import Line2D
    leg = [Line2D([0],[0], marker=m, color="w", markerfacecolor=c, markersize=10, label=l)
           for m, c, l in [("^","#c81e3a","IPO"),("D","#444","acquisition"),
                            ("s","#444","exit/sale"),("*","#caa028","key event"),("o","#999","founded")]]
    ax.legend(handles=leg, loc="lower right", fontsize=9, ncol=5, framealpha=0.95)

    ax.set_yticks([]); ax.set_ylim(-0.6, len(spans))
    ax.set_xlim(datetime(1995, 1, 1), datetime(2027, 6, 1))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_title("The Journey \u00b7 the companies Elon Musk moved through (1995\u20132026)",
                 fontsize=15, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.15)
    fig.text(0.5, 0.012, "Source: company filings & public record. Educational only \u2014 not investment advice.",
             ha="center", fontsize=8, color="#666")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    out2 = os.path.join(CHARTS, "JOURNEY_companies.png")
    fig.savefig(out2, dpi=150); plt.close(fig)
    print("wrote", out2)


if __name__ == "__main__":
    main()
