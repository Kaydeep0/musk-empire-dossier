#!/usr/bin/env python3
"""
Phase 3 — grade H2 (the payday is the sale) and H3 (he sells into strength).

Inputs:  data/transactions.csv (parsed Form 4s), data/prices_tsla.csv (Yahoo, split-adjusted)
Outputs: charts/H3_sells_into_strength.png, charts/H2_cumulative_cash.png
         + a printed numeric summary used in the write-up.

All prices are normalized to TODAY'S split-adjusted basis so the Form 4 markers sit
on the Yahoo price line. Proceeds (shares*price) are split-invariant.
TSLA splits: 5:1 eff. 2020-08-31, 3:1 eff. 2022-08-25.
"""
import csv, os, statistics
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
CHARTS = os.path.join(HERE, "..", "charts")
os.makedirs(CHARTS, exist_ok=True)


def split_factor(d):
    """Divide a nominal price by this to reach today's basis; multiply shares by it."""
    if d < "2020-08-31":
        return 15.0
    if d < "2022-08-25":
        return 3.0
    return 1.0


def load_prices():
    rows = list(csv.DictReader(open(os.path.join(DATA, "prices_tsla.csv"))))
    dates = [r["date"] for r in rows]
    close = [float(r["close"]) for r in rows]  # already split-adjusted
    pmap = dict(zip(dates, close))
    return dates, close, pmap


def main():
    dates, close, pmap = load_prices()
    # index for trailing windows
    idx = {d: i for i, d in enumerate(dates)}

    tx = list(csv.DictReader(open(os.path.join(DATA, "transactions.csv"))))
    sales = []
    for r in tx:
        if r["ticker"] != "TSLA" or r["code"] != "S":
            continue
        if not (r["price_per_share"] and r["shares"] and r["transaction_date"]):
            continue
        d = r["transaction_date"]
        f = split_factor(d)
        adj_price = float(r["price_per_share"]) / f
        adj_shares = float(r["shares"]) * f
        proceeds = float(r["value_usd"]) if r["value_usd"] else adj_price * adj_shares
        sales.append({
            "date": d, "adj_price": adj_price, "adj_shares": adj_shares,
            "proceeds": proceeds, "plan": r["rule_10b5_1"] == "Y",
        })
    sales.sort(key=lambda s: s["date"])

    # ---- H3: percentile of each sale price within trailing 1y, weighted by proceeds
    def trailing_pct(d, price, win=252):
        if d not in idx:
            # nearest prior trading day
            prior = [x for x in dates if x <= d]
            if not prior:
                return None
            i = idx[prior[-1]]
        else:
            i = idx[d]
        lo = max(0, i - win)
        window = close[lo:i + 1]
        if len(window) < 20:
            return None
        return sum(1 for p in window if p <= price) / len(window)

    pcts, weights = [], []
    ath_fracs = []
    for s in sales:
        p = trailing_pct(s["date"], s["adj_price"])
        if p is not None:
            pcts.append(p); weights.append(s["proceeds"])
        # fraction of all-time-high up to that date
        prior = [close[i] for i, dd in enumerate(dates) if dd <= s["date"]]
        if prior:
            ath_fracs.append((s["adj_price"] / max(prior), s["proceeds"]))

    def wmedian(vals, wts):
        pairs = sorted(zip(vals, wts))
        tot = sum(wts); acc = 0
        for v, w in pairs:
            acc += w
            if acc >= tot / 2:
                return v
        return pairs[-1][0]

    print("=== H3: does he sell into strength? (TSLA, split-adjusted) ===")
    print(f"sale transactions w/ price: {len(sales)}")
    print(f"simple-mean trailing-1y percentile of sale price: {statistics.mean(pcts)*100:5.1f}%")
    print(f"proceeds-weighted median trailing-1y percentile : {wmedian(pcts, weights)*100:5.1f}%")
    wath = wmedian([a for a, _ in ath_fracs], [w for _, w in ath_fracs])
    print(f"proceeds-weighted median (sale price / prior all-time-high): {wath*100:5.1f}%")
    above80 = sum(w for p, w in zip(pcts, weights) if p >= 0.80) / sum(weights)
    print(f"share of proceeds sold at >=80th percentile of trailing year: {above80*100:5.1f}%")

    # ---- H2: cumulative realized cash + plan share
    total = sum(s["proceeds"] for s in sales)
    plan_total = sum(s["proceeds"] for s in sales if s["plan"])
    print("\n=== H2: the payday is the sale ===")
    print(f"total gross TSLA sale proceeds (2010-2026): ${total/1e9:.2f}B")
    print(f"   of which under 10b5-1 plans:            ${plan_total/1e9:.2f}B ({plan_total/total*100:.0f}%)")
    print("   dividends to common holder:              $0 (Tesla pays none)")
    print("   cash salary (Tesla):                     ~$0 (declined; minimum-wage accrued, untaken)")

    # ===================== CHART 1: sells into strength =====================
    px_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.plot(px_dates, close, color="#444", lw=1.0, zorder=1, label="TSLA price (split-adjusted)")
    ax.set_yscale("log")

    sd = [datetime.strptime(s["date"], "%Y-%m-%d") for s in sales]
    sp = [s["adj_price"] for s in sales]
    sizes = [max(12, (s["proceeds"] / 1e9) * 220) for s in sales]
    colors = ["#c81e3a" if s["plan"] else "#1f6fb2" for s in sales]
    ax.scatter(sd, sp, s=sizes, c=colors, alpha=0.6, edgecolors="white",
               linewidths=0.4, zorder=3)

    # legend proxies
    from matplotlib.lines import Line2D
    leg = [
        Line2D([0], [0], color="#444", lw=1.2, label="TSLA price (split-adj.)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#c81e3a",
               markersize=10, label="Sale under 10b5-1 plan"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#1f6fb2",
               markersize=10, label="Discretionary sale"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#999",
               markersize=14, label="marker size \u221d $ proceeds"),
    ]
    ax.legend(handles=leg, loc="upper left", frameon=True, fontsize=9)

    ax.annotate("Nov-2021: Twitter poll,\nthen ~$16B sold near ATH",
                xy=(datetime(2021, 11, 10), 405), xytext=(datetime(2014, 9, 1), 250),
                fontsize=9, color="#c81e3a",
                arrowprops=dict(arrowstyle="->", color="#c81e3a"))
    ax.annotate("2022: ~$23B sold\n(Twitter financing)",
                xy=(datetime(2022, 8, 20), 290), xytext=(datetime(2023, 2, 1), 95),
                fontsize=9, color="#c81e3a",
                arrowprops=dict(arrowstyle="->", color="#c81e3a"))

    ax.set_title("H3 \u00b7 Does Musk sell into strength?  TSLA insider sales vs. price (2010\u20132026)",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("Share price, USD (split-adjusted, log scale)")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(True, which="both", alpha=0.15)
    fig.text(0.5, 0.01,
             "Source: SEC Form 4 (CIK 1494730), prices Yahoo Finance. Educational only \u2014 not investment advice.",
             ha="center", fontsize=8, color="#666")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    out1 = os.path.join(CHARTS, "H3_sells_into_strength.png")
    fig.savefig(out1, dpi=150); plt.close(fig)
    print(f"\nwrote {out1}")

    # ===================== CHART 2: cumulative cash realized =====================
    cum_dates, cum_vals = [], []
    run = 0.0
    for s in sales:
        run += s["proceeds"]
        cum_dates.append(datetime.strptime(s["date"], "%Y-%m-%d"))
        cum_vals.append(run / 1e9)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [3, 1]})
    ax1.step(cum_dates, cum_vals, where="post", color="#c81e3a", lw=2)
    ax1.fill_between(cum_dates, cum_vals, step="post", alpha=0.12, color="#c81e3a")
    ax1.set_title("H2 \u00b7 Cumulative cash Musk has realized by SELLING Tesla stock",
                  fontsize=12, fontweight="bold")
    ax1.set_ylabel("Cumulative gross proceeds ($B)")
    ax1.xaxis.set_major_locator(mdates.YearLocator(2))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.grid(True, alpha=0.15)
    ax1.annotate(f"${cum_vals[-1]:.0f}B total",
                 xy=(cum_dates[-1], cum_vals[-1]), xytext=(-90, -20),
                 textcoords="offset points", fontsize=11, fontweight="bold", color="#c81e3a")

    # cash-source comparison
    bars = ["Stock\nsales", "Dividends", "Cash\nsalary"]
    vals = [total / 1e9, 0.0, 0.0]
    ax2.bar(bars, vals, color=["#c81e3a", "#1f6fb2", "#1f6fb2"])
    ax2.set_title("Where the personal cash\ncomes from ($B)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("$B")
    for i, v in enumerate(vals):
        ax2.text(i, v + total/1e9*0.02, f"${v:.0f}B" if v >= 1 else "~$0", ha="center", fontsize=10)
    ax2.grid(True, axis="y", alpha=0.15)

    fig.text(0.5, 0.01,
             "Source: SEC Form 4 (CIK 1494730). Tesla pays no dividend; salary declined. Educational only \u2014 not investment advice.",
             ha="center", fontsize=8, color="#666")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    out2 = os.path.join(CHARTS, "H2_cumulative_cash.png")
    fig.savefig(out2, dpi=150); plt.close(fig)
    print(f"wrote {out2}")


if __name__ == "__main__":
    main()
