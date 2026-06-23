# The attention → capital mechanism — a measurable model (detector, not playbook)

**What this is.** A formal, falsifiable model of how *attention* (bits) is converted into *capital*
(atoms) inside a founder-controlled, narrative-driven structure — built so the mechanism can be
**measured and exposed**, not operated. It turns the reflexivity pillar (P1: H4 + H14) and the
transfer pillar (P3: H6) from a story into a set of instrumented, gradable signals.

**Stance.** This is a *detector*. Every lever below is paired with an observable signal and a
falsifier. If the signals don't show up in the data, the mechanism isn't operating — that's the point.

> Provenance: `b` primary filing · `m` market data · `s` social/platform data · `a` our model.

---

## 1. The loop, stage by stage (bit → atom)

```
   (1) ATTENTION        (2) NARRATIVE        (3) AUDIENCE         (4) BELIEF
   capture eyeballs  →  frame the story  →  aggregate a       →  convert attention
   (posts, events,      (mission, Mars,      following that       into a valuation
    controversy)         "story stock")       trusts the source     premium
        ▲                                                              │
        │                                                              ▼
   (7) RECYCLE  ◀──  (6) EXTRACTION  ◀──────────────────────  (5) PRICE/SUPPLY
   roll proceeds      sell/issue into the bid                  thin float + the
   into next vehicle   (Form 4 sales, IPO, dilution)            premium clears high
```

The mechanism is **extractive** when value flows *backward* along the dashed path — from the audience
(4→5) to the operator (6) — and **productive** when stages 1–4 deliver something the audience keeps
(information, a working product) and the operator is paid for the service, not by the asymmetry.

---

## 2. The instrument table — each lever has an observable signal + falsifier

| # | Stage | Lever | **Observable signal** | Data source | Detection metric | Falsifier (mechanism *off*) |
|---|---|---|---|---|---|---|
| 1 | Attention | own/borrow the megaphone | post volume, reach, engagement spikes | X/social API `s` | attention index z-score | attention is exogenous to the operator |
| 2 | Narrative | frame mission > fundamentals | recurring frames ("Mars", "story stock", polls) | posts, transcripts `s` | frame frequency around events | frames don't cluster pre-event |
| 3 | Audience | aggregate a captive following | follower count vs **public float** | platform + 424(b)(4) `s`/`b` | following-to-float ratio | following ≪ float (no leverage) |
| 4 | Belief | manufacture a premium | valuation vs cash-flow floor | filings + analyst DCF `b`/`a` | **belief share** = 1 − (claim ÷ price) | price ≈ claim (no premium) |
| 5 | Price/Supply | thin float, set the mark | float %, lock-up calendar, private mark | 424(b)(4) `b` | float %; scarcity index | normal float (15–20%), no mark-setting |
| 6 | Extraction | sell/issue into the bid | Form 4 sales, IPO proceeds, dilution | Form 4 / 424(b)(4) `b` | $ realized; sale-percentile vs price | no net selling into strength |
| 7 | Recycle | roll into the next vehicle | proceeds → new entity/round | filings, rounds `b`/`c` | reinvestment trace | proceeds diversify out, not recycled |

**The single sharpest test (H4 + H14).** Stages 1→6 should fire *in order, with short lags*:
**attention spike → price/volume run-up → insider monetization.** If that ordering is real and
repeatable, the megaphone isn't decorative — it's the pricing tool.

---

## 3. The core quantitative design (an event study you can actually run)

**Question:** does the operator's *attention* lead *price/volume*, which leads *monetization*?

**Three aligned time series (daily):**
1. **Attention** `A(t)` — Musk post count + engagement on X (and major reveal/poll/earnings events). `s`
2. **Market** `P(t), V(t)` — TSLA split-adjusted price + volume (already have `prices_tsla.csv`). `m`
3. **Monetization** `M(t)** — Form 4 sale $ and dilution/issuance events (already have `transactions.csv`). `b`

**Estimators:**
- **Lead–lag / cross-correlation** between `A`, then `P/V`, then `M` (expect peak corr at positive lags: A leads P leads M).
- **Event study** around top-decile attention days: cumulative abnormal volume/return in the window, then probability a Form 4 sale lands within N days after.
- **Pre-registration discipline:** fix the windows and lags *before* looking (same method as the SPCX August-unlock call).

**Already-graded fragments** (from Phase 3): the **Nov-2021 Twitter poll → ~$16B sold near ATH**, with the **10b5-1 plan adopted 2021-09-14, weeks before the poll**, is one realized instance of 1→6 firing in order (`PHASE3_FINDINGS.md`). This model generalizes that single instance into a repeatable, dated test.

---

## 4. Extractive vs. productive — the falsifiable signature

Both look like "audience-building." The data distinguishes them:

| Signature | Extractive (transfer) | Productive (service) |
|---|---|---|
| Direction of value | audience → operator (6 before they benefit) | operator → audience (they keep the info/product) |
| Disclosure | position/timing hidden; "signals" pushed | positions disclosed; method shown; calls graded |
| Premium | belief share high & detached from claim | premium tracks delivered fundamentals |
| Following vs float | following ≫ float (max leverage on price) | following serves understanding, not the bid |
| Ordering | attention → price → **insider sale** | attention → price, **no insider sale into it** |

This is also the bright line for your *own* work: the detector flags Path-1 behavior in **others**;
running it on yourself keeps you provably on Path 2 (no undisclosed positions, no selling into the
attention you create, every call graded).

---

## 5. Data to pull next (to fully arm the detector)

- [ ] **Attention series:** Musk X post timestamps + engagement (or a public proxy / event log of reveals, polls, earnings). `s`
- [ ] **Issuance/dilution events** to complement Form 4 sales (S-3/424 shelf takedowns, pay-award grants). `b`
- [ ] **Belief-share series:** rolling price ÷ analyst DCF floor (the "claim") to chart the premium over time. `a`/`m`
- [ ] Join all three with `prices_tsla.csv` + `transactions.csv` → run the lead–lag/event study → chart `ATTENTION_to_capital.png`.

## 6. Mapping to the thesis
- **H4** (narrative precedes monetization) ← stage ordering 1→6, the lead–lag estimator.
- **H14** (sets *and* broadcasts the price) ← stages 1–2 + 5 (channel ownership + mark/float control).
- **H6** (directional transfer) ← stage 6→7 + following-to-float leverage.
- **P1 verdict** is reported once H4 + H14 are graded on this instrument.

---

## 7. Ethics / scope
This document models the mechanism to **detect and disclose** it. It is **not** a guide to operating
it. Using attention to push undisclosed trading signals, coordinate amplification, or sell into a bid
you manufactured is market manipulation / touting and (under a registered advisory identity)
Investment-Advisers-Act fraud. The lawful use of this model is measurement, education, and the
viewpoint-neutral disclosure ask in `COALITION_MAP.md`.

*Educational and informational only — not investment advice, not an offer or solicitation.
Money in Motion · Eigenstate Research.*
