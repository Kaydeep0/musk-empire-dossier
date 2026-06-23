# Elon Musk — The Empire & The Exit

A longitudinal, SEC-grounded test of one hypothesis, built on the same provenance
discipline as `../Spacexsec` (SPCX: *The Anatomy of a Premium*).

> **Hypothesis.** Elon Musk runs a repeatable loop: build hype in the real economy,
> channel it into a public vehicle, retain control via super-voting structures, and
> realize his payday by **selling his existing stake into the retail demand he created** —
> then roll the proceeds into the next venture. The thesis is that his cash comes from
> *the public buying his shares*, not from operating businesses paying their owners.

**This is educational research only — not investment advice, not an allegation of
wrongdoing. Filings show actions and dates; they cannot show intent.** Every
load-bearing figure traces to a primary SEC document.

---

## The hypothesis as a testable mechanism

Each step of the loop leaves a public, dated footprint:

1. **Build hype** (product, mission, megaphone).
2. **Go public / absorb** into a public vehicle.
3. **Retain control** via dual-class / super-voting (public funds it, can't steer it).
4. **Sell the existing stake** into retail demand → realize *cash* (Form 4s).
5. **Roll proceeds** into the next venture, repeat.

**The test:** Does realized cash come from owners being paid, or from selling shares
into public enthusiasm — and does selling cluster *after* hype-driven price strength?

---

## The five data streams

| Stream | What | Source | Status |
|---|---|---|---|
| A. Entity registry | Companies, CIKs, roles, dates | `registry/entities.csv` | built |
| B. Personal filing trail | All Forms 3/4/5 + 13D/G | CIK 1494730 submissions | built (`data/filings_index.csv`) |
| C. Transaction ledger | Every buy/sell/exercise/gift | Form 4 XML (structured) | built (`data/transactions.csv`) |
| D. Net-worth timeseries | Holdings × price over time | filings + free price APIs | next |
| E. Structure & narrative | IPOs, M&A, comp pkgs, hype timeline | DEF 14A, S-1, 8-K, 13D | next |

## Scope (v1 = public-market core)

Tesla (TSLA), Twitter (TWTR), SolarCity (SCTY), SpaceX (SPCX). PayPal/Zip2 and the
private cos (Boring, Neuralink, xAI) are registered for a later pass.

---

## Phases

- [x] **Phase 0 — Scaffold.** Repo skeleton: `registry/ sources/ build/_text/ data/ charts/ research/`.
- [x] **Phase 1 — Registry + filing index.** Resolve CIKs; pull all 172 of Musk's filings.
- [x] **Phase 2 — Transaction ledger.** Parse all Form 3/4/5 XML → `data/transactions.csv` (1,486 tx).
- [x] **Phase 2.5 — Hypothesis lock.** Generalize the SPCX read into a falsifiable, career-spanning thesis: **4 co-equal pillars** (reflexivity, control wedge, wealth transfer, financial engineering) tested via **14 sub-hypotheses (H1–H14)**, an explicit null/alternative (H₀), and per-claim falsifiers → [`research/HYPOTHESIS.md`](research/HYPOTHESIS.md). **Phase 3 is now *grading*, not guessing.**
- [x] **Phase 2.6 — Import SPCX structural mechanisms.** Mined the SpaceX dossier (`../Spacexsec`) for patterns beyond sell-timing and promoted the strongest to sub-hypotheses: **H11** assemble-by-absorption + restate history; **H12** debt buys time (bridge / failed sale-leaseback / credit facility = the capital treadmill); **H13** closed-loop related-party web (Tesla↔xAI↔SpaceX; Valor director conflict); **H14** he sets & broadcasts the price (private marks, Reg-FD-via-X, tiered retail pricing). Plus a mechanism catalog (splits-before-pricing, restate→reward→raise, staircase lock-ups, controlled-company armor, borrow-vs-sell).
- [x] **Phase 3 (part 1) — Sale-timing grading.** Joined the ledger to split-adjusted TSLA prices (Yahoo) → graded **H2 (strongly supported: ~$40B all sale-sourced, $0 div, ~$0 salary)** and **H3 (supported w/ nuance: 2021 wave near ATH & pre-planned via a 10b5-1 plan adopted 2021-09-14, before the Nov-6 poll; 2022 wave forced on the way down)**. See [`research/PHASE3_FINDINGS.md`](research/PHASE3_FINDINGS.md), `charts/H2_*.png`, `charts/H3_*.png`.
- [x] **Phase 3 (part 2) — Career timeline + net worth at specific dates.** Built **The Journey** (company Gantt, `charts/JOURNEY_companies.png`) and **The Climb** (net worth decomposed into Tesla + SpaceX stakes + realized cash, with net worth labeled at anchor dates, `charts/CLIMB_networth.png`). Net-worth proxy validated against published figures. Key visual: only ~$40B of a ~$358B→~$1T net worth is *realized cash*. Inputs: `data/tesla_holdings_anchors.csv`, `data/spacex_valuations.csv`, `registry/career_events.csv`. Builder: `build/networth_timeline.py`.
- [x] **Phase 3 (part 3) — Graded H11, H12+H7, H13 against primary filings.** Pulled Tesla 2025 DEF 14A, SolarCity FY2015 10-K, and the 2016 Tesla/SolarCity merger proxy (saved under `sources/`).
  - **H13 (related-party web) — SUPPORTED `b`:** Tesla's own proxy shows ~$235M/yr of inter-entity flows (SpaceX agreements + aircraft, X ads, TBC, Musk security co, Redwood/Straubel $30.3M, **xAI→Tesla Megapacks ~$191M**), same multi-hat names as SpaceX/Valor. → [`research/H13_related_party_web.md`](research/H13_related_party_web.md).
  - **H12+H7 (debt buys time / travels) — SUPPORTED `b`/`c`:** traced Twitter ~$13B LBO → carried as X → recast into xAI → recast into SpaceX → +$20B Goldman bridge (~$30.3B) → IPO repays $18.9B + $1.16B penalty; bridge cliff 2027-09. → [`research/H12_H7_debt_chain.md`](research/H12_H7_debt_chain.md), `charts/H12_debt_chain.png`.
  - **H11 (assemble-by-absorption) — SUPPORTED `b`:** SolarCity prototype — $768.8M loss, $789.9M cash burn, ~6mo runway, $2.75B debt; all-stock related-party absorption into Tesla with Musk+Gracias recusing, cousins (Rives) running the target, insiders holding $65M Solar Bonds + $10M notes. → [`research/H11_solarcity_absorption.md`](research/H11_solarcity_absorption.md).
- [x] **Phase 3 (part 4) — Graded H14 + Empire Mechanics synthesis.** **H14 (sets & broadcasts price) — SUPPORTED `b`/`c`:** Tesla designated Musk's personal Twitter as its Reg-FD channel (2013); his 2018 "$420 funding secured" tweet moved TSLA >6% → **SEC securities-fraud charge, $40M settlement, chairman removal, comms-oversight committee** (SEC PR 2018-226); + 2021 poll→$16B sale + SPCX mark-setting. → [`research/H14_sets_broadcasts_price.md`](research/H14_sets_broadcasts_price.md). Then folded **H11+H12+H13+H14** into one **repeatable five-move play** (absorb→restate→lever→circulate→broadcast/exit) run by a tiny multi-hat cast at ~10× scale (SolarCity→Tesla vs Twitter→SpaceX). → [`research/EMPIRE_MECHANICS.md`](research/EMPIRE_MECHANICS.md), `charts/EMPIRE_actors.png`. **All of H11–H14 now SUPPORTED.**
- [x] **Monetization Rail 2 — Trade-the-edge framework.** Educational, defined-risk process for trading one's own account off the structural edge: what the edge predicts (and its timing limits), defined-risk option expressions, position sizing/risk rules, pre-register-and-grade discipline (reusing the hypothesis method), and the mandatory IA/WSP personal-trading + §17(b) publish-vs-trade firewall. Risk-management-first, honest EV. → [`research/TRADE_THE_EDGE.md`](research/TRADE_THE_EDGE.md).
- [x] **Track A deliverables — Structure brief + SEC comment-letter outline.** Verified the coalition map's open `?` rows against primary/press sources (NBIM, CalPERS, CalSTRS, NYC Comptroller/Lander, Amalgamated/Frishberg, SOC, Lipton→Colorado Law) and added the 2023 17-investor (~$1.5B) letter as a coalition precedent. Wrote the 2-page **source-labeled structure brief** ([`research/STRUCTURE_BRIEF.md`](research/STRUCTURE_BRIEF.md)) and the **SEC rule-comment-letter outline/draft** with submission checklist + WSP gate ([`research/SEC_COMMENT_LETTER.md`](research/SEC_COMMENT_LETTER.md)).
- [x] **Advocacy scaffolding — Coalition map + outreach plan.** Cataloged credible *public* voices (proxy advisors, asset owners/pensions, academics, market critics, journalists, watchdogs) with stated position, influence, public contact route, and fit-to-thesis; plus a sequenced, lawful outreach plan (**policy/regulatory first**, then coalition/media) and explicit compliance guardrails. → [`research/COALITION_MAP.md`](research/COALITION_MAP.md).
- [x] **Mechanism model — attention → capital (detector).** Formalized the bit→atom→capital loop (attention → narrative → audience → belief → price → extraction → recycle) as a measurable, falsifiable *detector* with an observable signal + falsifier per lever, plus the lead–lag/event-study design that grades P1 (H4 + H14) and H6. Built for **measurement/exposure, not operation** (explicit ethics scope). → [`research/MECHANISM_attention_to_capital.md`](research/MECHANISM_attention_to_capital.md).
- [ ] **Phase 4 — Hype/event overlay + structure pulls.** Sales vs. price strength; cumulative cash realized; paper-vs-realized net worth; pledged-shares (H9) & pay-package (H10) pulls from proxies; traveling-debt chain; cross-company pattern matrix. Grades H1, H4, H6–H10 + the H₀ discriminators.

---

## Phase 2 results (validation)

Pulled from EDGAR CIK `0001494730` ("Musk Elon"): **172 filings, 2010–2026**;
**1,486 transactions** parsed.

Open-market **sales (code S)** gross proceeds by year — independent reconstruction:

| Year | Proceeds | Cross-check |
|---|---|---|
| 2021 | **$16.43B** | matches reported ~$16B around the Nov-2021 Twitter poll ✓ |
| 2022 | **$22.93B** | matches reported ~$23B for the Twitter acquisition ✓ |
| other | ~$0.6B | 2016 SolarCity, 2010 IPO, 2026 |
| **Total** | **~$40B** | |

**613** transactions carry the **Rule 10b5-1** pre-arranged-plan flag — directly
relevant to the claim that the 2021 selling plan was adopted weeks *before* the poll.

### Transaction codes present
`S` sale · `P` purchase · `M` option exercise · `C` conversion · `G` gift · `J` other
· `A` award · `D` disposition to issuer · `X` exercise · `F` tax withholding.

---

## Data-quality notes

- **Endeavor Group Holdings (EDR), 3 RSU rows:** attached to Musk's CIK but almost
  certainly a filing-agent mis-association (Tesla's Musk is not an Endeavor director).
  Non-cash, immaterial. **Flagged — exclude from empire analysis pending verification.**
- Pre-2010 (PayPal/Zip2) is **not** under this CIK; Section 16 e-filing + his individual
  CIK begin with Tesla (2010). PayPal-era data must come from PayPal's issuer CIK and
  the eBay merger record.
- `value_usd` = shares × price-per-share as disclosed; option exercises/grants often
  have no market price and show blank value (intentional).

---

## How to rebuild

```bash
python3 build/pull_musk_filings.py   # re-pulls EDGAR, rewrites data/*.csv
```
Stdlib only. Respects SEC rate limits (<10 req/s) and sends a descriptive User-Agent.

---

## Live filing watch (alerts on anything new)

A background watcher polls Musk's CIK and alerts on every new SEC filing.

- **Engine:** `build/watch_musk_filings.py` — diffs EDGAR against `data/.watch_state.json`,
  fires a **macOS desktop notification**, and appends to **`data/filing_alerts.log`**.
- **Auto-rebuild:** on new filings, runs **`build/on_new_filing.py`** → re-pulls Form 4s,
  regenerates charts (material forms), publishes **`public/`** (index, RSS, JSON, changelog).
  Disable with `MUSK_WATCH_PIPELINE=0`.
- **Public feed:** `python3 build/publish_live_feed.py` → `public/index.html`, `feed.xml`,
  `status.json`, `CHANGELOG.md`. Deploy to GitHub/Cloudflare Pages for a shareable live URL.
  See [`research/LIVE_PUBLISHING.md`](research/LIVE_PUBLISHING.md).
- **Scheduler:** `build/com.wattsadvisor.muskwatch.plist` (a macOS LaunchAgent), installed
  at `~/Library/LaunchAgents/`. Runs **every 15 min + at login**. Status: **installed & live.**
- **Zero-code fallback (RSS):** drop this into any reader/browser —
  `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001494730&type=&owner=include&count=40&output=atom`

### Phone push — ENABLED
Free phone push is active via [ntfy.sh](https://ntfy.sh) on a private topic:
**`musk-sec-9053334806`**. To receive alerts on your phone: install the **ntfy** app
(iOS/Android), tap **Subscribe to topic**, and enter `musk-sec-9053334806` (server
`ntfy.sh`). No account needed. Anyone who knows the topic name can read it, so keep it
private; to rotate it, change `MUSK_WATCH_NTFY` in the plist and reload.

To add Slack/Discord too, add a `MUSK_WATCH_WEBHOOK` key (incoming-webhook URL) to the
plist's `EnvironmentVariables` block and reload.

### Manage it
```bash
launchctl list | grep muskwatch                                   # is it running?
python3 build/watch_musk_filings.py                               # check now (manual)
launchctl unload ~/Library/LaunchAgents/com.wattsadvisor.muskwatch.plist   # stop
launchctl load -w ~/Library/LaunchAgents/com.wattsadvisor.muskwatch.plist  # start
tail -f data/filing_alerts.log                                    # watch the alert log
```

## Provenance tags (carried forward from the SPCX methodology)
`b` = from filings (fact) · `a` = analyst model/estimate · `c` = third-party consensus
· `m` = market data.

*Maintained by Kirandeep Kaur · Watts Advisor — Money in Motion. Educational only.*
