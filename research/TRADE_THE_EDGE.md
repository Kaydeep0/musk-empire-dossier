# RAIL 2 — Trade the edge (your own account)
### A disciplined, defined-risk framework for turning structural analysis into trades

> **Scope & disclaimer.** This is an **educational process framework**, not investment advice, not a
> recommendation to buy/sell any security, and not a promise of profit. It is *your* capital and *your*
> risk. Trading options and single names can lose 100% (or more, if undefined-risk). Read §5
> (compliance) before placing a trade under any registered-advisory identity.

---

## 0. The honest premise
Your edge is **reading public filings faster and more structurally than the market bothers to.** That
is a real, legal edge. But it has a hard limit, and your own work proved it:

- **Analysis edge ≠ timing edge.** `H3` showed even *Musk's* sales were partly **forced by price**, not
  freely timed. Being right about structure tells you *what* and roughly *which direction over what
  horizon* — almost never *when*.
- **Reflexive names punish shorts.** TSLA/SPCX are sentiment- and retail-driven; the coalition's own
  market critics (Chanos et al.) were *directionally right and still lost* fighting the momentum.
- **Conclusion:** express the edge as **defined-risk, catalyst-dated, position-sized** bets — never as
  open-ended shorts or leverage. The risk rules below are the actual product; the thesis is the input.

---

## 1. What your edge actually predicts (and what it doesn't)

| Your finding | What it implies for price | Tradeable horizon | Confidence |
|---|---|---|---|
| Lock-up unlocks / float doubling (`H14`/SPCX) | supply ↑ → downward pressure *around* dated unlocks | weeks, **dated** | medium |
| Continued dilution / issuance (`H6`) | per-share drag over time | months–years | medium |
| Insider Form 4 selling into strength (`H3`) | distribution signal near highs | days after filing | medium |
| Belief≫claim premium (`H4`) | rich valuation, *but can persist for years* | unbounded | **low for timing** |
| Debt cliffs (`H12`, bridge 2027-09) | refinancing-risk catalyst dates | event-dated | medium |

**Rule of thumb:** only trade the rows with a **date** attached. "Overvalued" without a catalyst is how
analysts go broke being right. Your **SEC filing watcher** (`watch_musk_filings.py`) is your genuine
edge here — it surfaces Form 4 / 8-K catalysts in near-real-time on public data.

## 2. Express the thesis as defined-risk (max loss known in advance)
Prefer instruments where the worst case is capped and pre-known:
- **Long puts / long calls** — max loss = premium paid. Directional, dated, defined.
- **Vertical spreads** (debit/credit) — cheaper, capped both ways, good for a *bounded* thesis ("breaks
  below X by date Y").
- **Avoid:** naked short stock (unlimited loss + squeeze risk on reflexive names), naked short options
  (undefined risk), margin/leverage, anything you can't fully fund in cash.
- **Date the option to the catalyst** (e.g., expiry just *after* an unlock/earnings/cliff), with buffer —
  options decay, so being early is the same as being wrong.

## 3. Position sizing & risk (this is where money is actually made or lost)
- **Risk capital only:** fund the account with money you can lose entirely without changing your life.
- **1R = max loss per trade ≤ 1–2% of risk capital.** With defined-risk options, 1R = premium.
- **Portfolio heat:** total open risk ≤ ~6–8% of the account; correlated Musk-name bets count as *one*
  exposure, not many.
- **No averaging down** a losing thesis trade; the invalidation level is the invalidation level.
- **Pre-commit the exit** (target + invalidation) *before* entry. Decisions made in the trade are
  emotional, not analytical.

## 4. Run it like your hypotheses — pre-register and grade
You already have the perfect discipline; point it at trades:

For each trade, log **before entry**:
```
Thesis (which H) · Catalyst + date · Instrument · Entry · Invalidation · Target · Size (R) · Disclosed?
```
Then **grade every closed trade** like H2/H3 — win/loss, R-multiple, was the *thesis* right vs the
*timing*. After ~20–30 logged trades you'll know if the edge is real **in P&L**, not just on paper.

- **Start on paper / tiny size.** Validate the calls produce money before scaling. The cost of learning
  this with real size is the most common way the account goes to zero.
- This trade log *is* a track record — which, kept honestly, also feeds Rail 1 (selling the research).

## 5. Compliance firewall (mandatory under Watts Advisor / IAR)
- **Personal-trading code:** registered advisers have a Code of Ethics — likely **pre-clearance and
  reporting** of personal securities trades, blackout windows, and **no trading ahead of clients**.
  Clear your personal-trading program with **Gary/WSP before the first trade.**
- **MNPI:** you're clean — inputs are 100% public EDGAR filings. Keep it that way; never trade on
  anything non-public.
- **Publish-vs-trade (§17(b)):** if you ever publish on a name you hold, **disclose the position**, and
  **never publish to move a price you're positioned in.** Simplest firewall: a delay/separation between
  what you trade and what you publish, plus a standing positions-disclosure line.
- **Don't trade client-affecting securities** in a way that conflicts with advisory duties.
- **Records:** keep the trade log + rationale; it's both your edge-validation and your compliance trail.

## 6. Honest expected value
Most retail options traders lose money; an information/analysis edge is *necessary but not sufficient*.
What separates the few who profit is **risk sizing and discipline**, not better theses — which is why
this file is 70% risk rules and 30% ideas. Treat the first 6–12 months as **tuition**: small size,
full logging, grade ruthlessly, scale only what the data proves.

---

## 7. Suggested first loop (lowest-risk start)
1. Fund a small, ring-fenced risk-capital account; get **WSP sign-off** on the personal-trading program.
2. Pick **one dated catalyst** from §1 (e.g., an SPCX unlock date or a Form-4 cluster your watcher flags).
3. Express it as a **single long put/call or vertical spread**, expiry past the catalyst, **risk = 1R ≤ 1%**.
4. Pre-register the trade in the log (§4). Hold to target or invalidation — no improvising.
5. Grade it. Repeat to ~20 trades on small size **before** increasing size.

## Cross-references
- Theses & dated calls: `HYPOTHESIS.md`, `PHASE3_FINDINGS.md`, `MECHANISM_attention_to_capital.md`.
- Catalyst feed: `build/watch_musk_filings.py` (real-time SEC alerts).
- Other rails: `STRUCTURE_BRIEF.md` (Rail 1 product), `COALITION_MAP.md` (advocacy). Rail 3 (event
  markets) to be written if wanted.

*Educational and informational only — not investment advice, not an offer or solicitation. Run the
personal-trading program through firm compliance (WSP) before trading.*
