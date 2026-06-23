# The Hypothesis — *The Megaphone and the Exit*

A career-spanning, falsifiable thesis about how Elon Musk converts narrative into
personal cash through public equity markets. This document defines **what we claim,
what would prove us wrong, and exactly which data grades each claim** — before any
chart is drawn.

> **Discipline carried from the SPCX dossier:** every load-bearing claim is labeled by
> basis — `b` filing/primary record · `a` analyst model/estimate · `c` third-party
> consensus · `m` market data — and **every finding is stated *after* its strongest
> counter-argument.** Filings show actions and dates. They cannot show intent, and we
> never claim they do. We are testing a **pattern**, not a motive.

---

## 0. The thesis in one sentence

> **Across a chain of companies, Musk has built a repeatable system for turning
> attention into cash: acquire a real-economy frontier, own the channel that broadcasts
> its story, list it (or absorb it) into a public vehicle he controls but does not
> economically own, let the resulting belief premium fund the business *and* inflate his
> stake, then realize his actual payday by selling that stake into the retail demand he
> manufactured — and roll the proceeds into the next vehicle.**

The sharp version of the claim is **not** "founders sell stock" (they all do). It is that
four features appear *together and at an extreme* in his case, and recur across vehicles:

1. **He owns the megaphone** — the narrative channel is internal to the operator
   (reflexivity; now literally so, with X/xAI/Grok folded into SpaceX).
2. **The control wedge is extreme** — voting control vastly exceeds economic ownership,
   engineered to be effectively permanent.
3. **Monetization is recurring and *rolled*** — the same move repeats across a chain of
   vehicles, with leverage that travels from deal to deal.
4. **The exit has timing and access asymmetry** — he distributes on a lagged calendar
   with hedging tools (collars/forwards) the inheriting public does not have.

### 0.1 Four co-equal pillars — *we test all of them*

This is not one master claim with supporting detail. It is **four independent pillars,
each graded on its own**, because the loop is only persuasive if all four hold at once.
The thesis survives or fails pillar by pillar:

| Pillar | The claim in one line | Graded by |
|---|---|---|
| **P1 · Reflexivity / megaphone** | He produces, broadcasts, **and prices** the belief he later sells into. | H4, H14, + qualitative (channel ownership) |
| **P2 · Control wedge** | Vote ≫ economics, engineered to be permanent; public funds, can't steer. | H1, H10, H11 |
| **P3 · Wealth / risk transfer** | The premium and the cash exit *to* insiders; the junior no-vote risk migrates *to* retail/index. | H2, H6, H9 |
| **P4 · Financial engineering / leverage** | Deal debt travels vehicle-to-vehicle, **buys time**, routes through a related-party web, and is ultimately refinanced by the public. | H7, H12, H13 |

Sub-hypotheses H1–H14 below are the measurable units; each pillar is the verdict we
report once its sub-hypotheses are graded.

---

## 1. The mechanism (the loop)

```
        ┌─────────────────────────────────────────────────────────────┐
        │                                                               │
        ▼                                                               │
 (1) FRONTIER          (2) MEGAPHONE        (3) PUBLIC VEHICLE          │
 acquire/found a   →   own the channel   →  IPO or absorb into a   →    │
 mission-grade        that broadcasts        listed entity he                │
 narrative            the story              controls                       │
        │                                       │                            │
        ▼                                       ▼                            │
 (4) CONTROL WEDGE                       (5) BELIEF PREMIUM                   │
 dual-class / super-vote:          →     high multiple lowers cost of        │
 economics ≠ control;                    capital, funds the cash gap via     │
 public funds, can't steer               issuance, AND inflates his stake    │
        │                                       │                            │
        └───────────────────┬───────────────────┘                           │
                            ▼                                                │
                  (6) THE EXIT                                               │
        sell the existing stake into the demand he created                  │
        (Form 4s; into strength; often via pre-set 10b5-1 plans)            │
                            │                                                │
                            ▼                                                │
                  (7) DIVERSIFY & ROLL ──────────────────────────────────────┘
        rotate proceeds into cash/Treasuries/other assets;
        risk + the junior no-vote claim migrate to retail/index
```

**The keystone insight (from the SPCX read):** the high price is not just a vanity
number — it is *the funding instrument*. The richer the multiple, the more cash a given
share sale raises. So belief is not incidental to the payday; **belief is the payday's
fuel.** An operator who can manufacture and broadcast belief, and who controls when his
shares unlock, is selling something he helped produce.

---

## 2. Sub-hypotheses (each independently falsifiable)

Each row: the claim, the observable prediction, the data that grades it, and **the
specific result that would prove it wrong.**

### H1 — The control/economics wedge is engineered and extreme
- **Claim.** In his public vehicles, voting control ≫ economic ownership, by design
  (dual-class, super-voting, board capture), and is built to be near-permanent.
- **Prediction.** vote-% − economics-% is large and positive; the structure has no
  meaningful sunset.
- **Data.** `b` 424(b)(4), Forms 3/4, DEF 14A (TSLA, SPCX). SPCX: ~82.4% vote / ~36% econ.
- **Falsifier.** If economic ownership ≈ voting control (no wedge), or the super-vote
  reliably sunsets, H1 fails.

### H2 — The payday is the share sale, not operating cash returned to owners
- **Claim.** His realized personal cash comes overwhelmingly from **selling existing
  stock**, not from salary, dividends, or buybacks reaching the common holder.
- **Prediction.** Σ(Form 4 sale proceeds) ≫ Σ(salary + dividends received). His public
  companies pay ~no dividend; salary is nominal ($0–$1 at Tesla historically; $54,080 at
  SpaceX).
- **Data.** `b` `data/transactions.csv` (already ~**$40B** of code-S sales 2010–2026);
  `b` proxy statements for salary; `b` dividend policy.
- **Falsifier.** If salary/dividends/operating distributions dominate realized cash, or if
  he has *not* materially sold, H2 fails. **Status: strongly supported so far.**

### H3 — Selling clusters into strength and is pre-arranged
- **Claim.** Sales occur disproportionately near local/all-time price highs and under
  **10b5-1 plans adopted before** the narrative catalysts that lift the price.
- **Prediction.** Sale-date prices sit in the upper percentile of trailing price; a large
  share of sales carry the 10b5-1 flag; plan-adoption dates precede catalysts (e.g. the
  Nov-2021 "should I sell 10%?" poll).
- **Data.** `b` transaction dates + the **613** 10b5-1-flagged rows we parsed; `m` daily
  TSLA closes (Phase 3); `b` 10b5-1 plan-adoption dates disclosed in Form 4 footnotes.
- **Falsifier.** If sales are randomly timed w.r.t. price, cluster at *lows*, or are
  demonstrably *forced* (margin calls, not opportunistic), H3 fails.

### H4 — Narrative precedes monetization
- **Claim.** Hype events (product reveals, mission framing, polls) precede price strength,
  which precedes sales — in that order.
- **Prediction.** event → run-up → sale, repeatedly, with short lags.
- **Data.** `c`/`b` event timeline (Stream E) overlaid on `m` price and `b` sale dates.
- **Falsifier.** If sales lead or are uncorrelated with narrative events, H4 fails.

### H5 — He monetizes into a large belief premium
- **Claim.** The price he sells into embeds a large belief layer over a defensible
  real-claim (DCF/asset) floor.
- **Prediction.** At sale windows, price ÷ floor is high (SPCX: ~1/3 claim, ~2/3 belief;
  ~129× sales). Tesla sale windows coincide with extreme multiples.
- **Data.** `a` DCF/floor models; `m` multiples at sale dates. **Denominator is contested**
  (fair-value spans ~5×) — weight accordingly.
- **Falsifier.** If he consistently sells at or below conservative fair value, H5 fails.

### H6 — Risk and value transfer is directional (insiders → public)
- **Claim.** Over time, insiders' ownership share falls and the public's rises; insiders
  rotate proceeds into safer/diversified assets; the junior, no-vote, high-vol claim
  migrates to retail and index funds.
- **Prediction.** Float rises on the unlock calendar; insider % declines; the inheriting
  buyer is price-insensitive (index/retail).
- **Data.** `b` lock-up calendars, share counts; `b`/`a` ownership-over-time;
  `c` retail/index flow data.
- **Falsifier.** If insiders predominantly *hold* through unlocks, or the claim does not
  migrate to retail/index, H6 fails.

### H7 — Leverage is carried forward and ultimately refinanced by the public
- **Claim.** Debt incurred in one deal travels into the next vehicle and is eventually
  made whole with public capital.
- **Prediction.** A traceable debt chain ends at a public-markets refinancing.
- **Data.** `b` Twitter LBO ~$13B → X → recast onto SpaceX (xAI/X fold-in) → +~$20B
  Goldman bridge → ~$30.3B → **IPO repays the bridge** (424(b)(4) subsequent events; terms
  externally supported, connective labels = our reading).
- **Falsifier.** If the inherited debt was retired from operating cash rather than public
  proceeds, or the chain breaks, H7 fails.

### H8 — The pattern recurs across vehicles (and *sharpens* over time)
- **Claim.** The same shape appears repeatedly, evolving from ordinary trade-sale exits to
  the distinctive "control-and-distribute-into-retail" modern form.
- **Prediction.** Each vehicle replays steps 1–7, with the megaphone/control/roll features
  intensifying.
- **Data (the chain):**
  | Vehicle | Year | Exit form | Note |
  |---|---|---|---|
  | Zip2 | 1999 | trade sale (Compaq, cash) | `c` precursor; private; no retail |
  | X.com→PayPal | 2002 | IPO then sold to eBay (stock) | `c` first public-market-adjacent cash |
  | Tesla | 2010→ | IPO; later sold tens of $B into market | `b` the template instance |
  | SolarCity | 2012→16 | IPO → **absorbed by Tesla** (related-party) | `b` "roll into another vehicle" / rescue |
  | Twitter | 2022 | take-private w/ $13B debt | `b` becomes the traveling leverage |
  | SpaceX | 2026 | IPO of the combined vehicle | `b` the latest, most extreme iteration |
- **Falsifier.** If the early exits look nothing like the later ones and there is no
  intensifying through-line, H8 (as stated) fails. **Honest caveat:** Zip2/PayPal were
  trade sales to acquirers — *standard founder exits, not selling into retail.* The
  distinctive retail-distribution mechanism is genuinely visible only from Tesla onward.

### H9 — Pledging is a *second* monetization channel that sidesteps the sale test
- **Claim.** He extracts cash **without selling** — and without a Form 4 sale or a taxable
  event — by **pledging stock as collateral for personal loans/margin lines**. This means
  the ~$40B of disclosed sales is a *floor* on liquidity extracted, not the whole picture,
  and "he didn't sell" does not mean "he didn't monetize."
- **Prediction.** A material fraction of his shares is pledged; pledged amounts are large
  relative to disclosed sales; borrowing rises with the share price (more collateral
  value → more borrowable).
- **Data.** `b` Tesla proxy statements (DEF 14A — pledged-shares disclosure & policy);
  `c` reporting on the personal credit lines; `b` 424(b)(4) (SpaceX margin/lease structure).
- **Falsifier.** If pledged shares are negligible, or borrowing is immaterial relative to
  sales, H9 fails — and the sale ledger really is the whole monetization story.
- **Counter (stated first).** Pledging is standard for concentrated founders, is
  disclosed, and is *not* a realization — the shares (and the bet) stay on his books. It
  can also be a sign of *conviction* (he'd rather borrow than sell). True. The point is
  only that it is a real cash channel the sale-ledger test cannot see.

### H10 — The pay packages are a parallel monetization + control mechanism, near-free on paper
- **Claim.** The mega-grants (the reinstated ~$56B→~$130B Tesla 2018 award, the up-to-$1T
  2025 Tesla package, the ~$120B SpaceX award) do two jobs at once: they **enlarge his
  sellable/votable stake** while the "improbable-milestone" accounting books **almost no
  expense today** — so they cost the company little, reinforce control, and supply an
  "alignment" story (he only gets paid if he delivers the mission) that obscures the fact
  that his *existing* stake already pays him via the public bid, gated on nothing.
- **Prediction.** Awards are equity (options/restricted shares), milestone-gated, booked at
  minimal expense; they increase votable shares before they vest; the headline "$X pay"
  vastly exceeds cash salary.
- **Data.** `b` DEF 14A (2018, 2025 Tesla), `b` 424(b)(4) (SpaceX award terms: $7.5T cap /
  Mars / 100 TW compute milestones), `b` Form 4 grants (code `A`), `b` nominal salary
  ($54,080 SpaceX; ~$0 Tesla).
- **Falsifier.** If comp is predominantly cash, market-rate, and small relative to his
  stake — or if the awards carry full expense and meaningful near-term dilution — H10 fails.
- **Counter (stated first).** This is the genuine **alignment case**, the same one
  shareholders voted for: he earns almost nothing unless extreme value is created, and
  near-zero expense means near-zero dilution today. The structure may simply reflect a
  founder who wants the upside of his own moonshots. The thesis only adds that the
  *alignment narrative* and the *actual payday* (selling the existing, ungated stake) are
  not the same thing.

---

## 2b. Structural mechanisms imported from the SPCX dossier

The SpaceX listing is one fully-documented instance of the loop, and it surfaces
*structural* mechanisms the Tesla sell-data alone does not. We promote the strongest to
testable sub-hypotheses (H11–H14) and catalog the rest. **Provenance:** every item below
is `b` (in the SPCX 424(b)(4)/8-Ks) *for SpaceX*; the **claim that they recur across
vehicles is the hypothesis** and stays `c` until graded company-by-company.

### H11 — Assemble-by-absorption, then restate the track record
- **Claim.** The public vehicle is *built* by absorbing his other ventures via common-control
  mergers, which lets the history be **recast** so a clean cash engine is blended with
  cash-burning bets — and no absorbed unit is shown standalone.
- **SPCX evidence (`b`).** X→xAI (3/28/25) then xAI→SpaceX (2/2/26); financials recast for
  all periods to embed Twitter + an early-stage AI lab; a 5-for-1 split (5/4/26) resets
  per-share optics weeks before pricing; a $60B Cursor deal struck the day after close.
- **Across-vehicle test.** SolarCity→Tesla (2016) is the prior instance — related-party
  absorption of a struggling venture into a public one. **Falsifier:** if his public
  vehicles are *not* assembled by absorbing his own other ventures, H11 fails.
- **Status: SUPPORTED (`b`).** Graded against SolarCity FY2015 10-K + 2016 merger proxy:
  $768.8M loss, $789.9M burn, ~6mo runway, $2.75B debt; all-stock absorption into Tesla,
  Musk+Gracias recused, cousins (Rives) ran target, insiders held $65M Solar Bonds + $10M
  notes. → `research/H11_solarcity_absorption.md`.

### H12 — Debt is used to *buy time*, not just leverage
- **Claim.** Bridge loans, credit facilities, and "failed sale-leasebacks" fund the cash gap
  *before* equity arrives, so monetization happens on **his schedule**, not the market's.
  The IPO is "a down payment on a perpetual capex program," not a finish line.
- **SPCX evidence (`b`).** $20B Goldman **bridge** (3/2/26, matures 9/2/27) funds AI capex
  pre-IPO; **$9.1B "failed sale-leaseback"** = secured borrowing dressed as an asset sale;
  $5B credit facility; a disclosed ~$13.9B/yr funding gap → another raise likely 2027–28.
- **Test.** Trace whether each vehicle leans on short-dated debt to bridge to an equity
  event (links to H7). **Falsifier:** if capex was funded from operating cash / long-dated
  equity rather than time-buying debt, H12 fails.
- **Status: SUPPORTED (`b`/`c`).** Dated debt chain assembled: Twitter ~$13B LBO → carried as
  X → recast into xAI → recast into SpaceX → +$20B bridge (~$30.3B) → IPO repays $18.9B +
  $1.16B penalty; cliff 2027-09. → `research/H12_H7_debt_chain.md`, `charts/H12_debt_chain.png`.

### H13 — A closed-loop related-party web routes value toward insiders
- **Claim.** The "empire" behaves as **one capital pool Musk rotates between vehicles**:
  related-party flows close back on Musk-controlled entities, and a *director's* firm
  provides off-balance-sheet financing — concentrating economics toward insiders, disclosed.
- **SPCX evidence (`b`).** Tesla both **sells to and invests in** xAI ($506M goods incl.
  $269M Megapacks; $2.0B Series E) and gets SpaceX shares back; Musk Industries leases
  property to xAI; a Musk security co. and Craft Aviation bill the issuer; **Valor (director
  Gracias) is at once #2 shareholder (7.3%), lessor on ~$20.2B of SpaceX-guaranteed compute
  leases, and on the comp committee.**
- **Test.** Build the related-party ledger per vehicle (Item 404 notes). **Falsifier:** if
  related-party flows are immaterial or genuinely arm's-length, H13 fails.
- **Status: SUPPORTED (`b`).** Tesla's own 2025 DEF 14A documents ~$235M/yr of inter-entity
  flows (SpaceX agreements + aircraft, X ads, TBC, Musk security co, Redwood/Straubel $30.3M,
  **xAI→Tesla Megapacks ~$191M**), with the same multi-hat names (Musk, Gracias, Straubel,
  Rives) recurring across Tesla/SolarCity/SpaceX. → `research/H13_related_party_web.md`.

### H14 — He sets *and* broadcasts the price he sells into (sharpest reflexivity claim)
- **Claim.** Beyond owning the narrative, he influences **price formation** itself: setting
  the private mark, controlling the disclosure channel, tiering retail demand.
- **SPCX evidence (`b`).** Musk **personally bought ~$1.42B of employee stock in 2025**,
  setting the private mark that feeds the $135 IPO; Reg FD material news flows via the
  **@SpaceX X account**, not the wires; **tiered pricing** monetizes retail at a premium
  abroad (US $135 / EU retail max $162).
- **Test.** Look for private-mark-setting and owned-channel disclosure at other vehicles
  (Tesla guidance via @elonmusk; the 2018 "funding secured" episode). **Falsifier:** if
  price/information formation is genuinely independent of him, H14 fails.
- **Counter (first).** Founders buy their own stock (conviction); CEOs use social media;
  global tranches are normal. The claim is only that *concentrating* price-setting + channel
  + audience in one person is unusual and self-reinforcing.
- **Status: SUPPORTED (`b`/`c`).** Graded: (1) Tesla designated Musk's personal Twitter as its
  Reg FD channel in 2013; in 2018 his "$420 funding secured" tweet moved TSLA **>6%** and drew an
  **SEC securities-fraud charge**, settled **$40M** + chairman removal + a committee to oversee his
  communications (SEC PR 2018-226); (2) the Nov-2021 poll→~$16B sale (10b5-1 adopted *before* the
  poll); (3) SPCX private-mark-setting + owned-channel disclosure + tiered retail pricing.
  → `research/H14_sets_broadcasts_price.md`.

### Mechanism catalog (monitored, not yet promoted)
| Mechanism (SPCX `b`) | Why it matters | Recurs? (to test) |
|---|---|---|
| 5-for-1 split right before pricing | resets per-share optics | Tesla splits 2020/2022 around runs |
| Comp granted weeks before pricing ("restate→reward→raise") | control now, dilution later, ~0 expense | Tesla 2018/2025 awards |
| Staircase (not cliff) lock-up | premium **harvested in slices**, invisible to options | every IPO he runs |
| "Controlled company" + Texas anti-takeover armor | forecloses shareholder remedies | charter/bylaws per vehicle |
| Tiered geographic retail pricing | monetizes retail at a premium | future listings |
| Borrow-against-stock vs. sell (margin/pledges) | liquidity w/o a Form 4 or tax event | **H9** — Tesla pledges |

---

## 3. The null / alternative hypothesis (what we must rule out)

The serious objection is not "he never sells." It is:

> **H₀ (the ordinary founder):** Musk's behavior is statistically indistinguishable from
> any successful, concentrated founder rationally diversifying a windfall. Selling stock,
> retaining founder control, carrying deal debt, and rotating into safer assets are all
> normal, legal, and disclosed. There is no special "playbook" — just survivorship and
> hindsight pattern-matching on a founder who happened to win.

**Our thesis only earns its keep if the data separates the loop from H₀.** Discriminating
tests (these are the ones that matter most for Phase 3):

| Discriminator | Loop predicts | H₀ predicts |
|---|---|---|
| **Megaphone ownership** | operator controls the narrative channel (X/xAI internalized) | narrative is exogenous (press, analysts) |
| **Sale timing vs. catalyst** | plan set *before* a self-created catalyst; sells into manufactured strength | sells on exogenous triggers (tax dates, real liquidity needs) |
| **Control wedge magnitude** | extreme & permanent (≫ peer founders) | in line with peer dual-class founders |
| **Recurrence & rolling** | same move across a *chain* with traveling debt | one-off liquidity events, unconnected |
| **Reason given vs. action** | stated reason (taxes, mission) is cover for an opportunistic exit | stated reason fully explains the sale |

If the discriminators land on the H₀ column, we **report that** — that is the honest
outcome and it is a real possibility.

**Scope of the H₀ test (moderate).** We acknowledge H₀ openly and grade the
discriminators **from Musk's own filing record**, using the *light* peer reference points
already in the SPCX record (Nvidia: Huang ~3.5% econ ≈ 3.5% vote; Meta: Zuckerberg ~13%
econ / ~61% vote) as calibration. We are **not** building full longitudinal peer datasets
(Bezos/Zuckerberg/Huang insider-sale histories) in v1 — that is a later upgrade if the
within-Musk evidence warrants a formal benchmark.

---

## 4. The strongest counter-arguments (steelman, stated first by rule)

1. **The base rate is brutal.** Betting against expensive, dominant, founder-led
   companies has a poor long-run record. Tesla and Amazon looked exactly like this and
   compounded enormously. Value is future cash flow, not this quarter's loss.
2. **It's all disclosed and legal.** Every structure here is in the filings and accepted
   by every buyer. 10b5-1 is a *safe harbor* designed to be used; using it is not evidence
   of bad intent.
3. **Diversification is rational.** Any advisor would tell a person with ~one concentrated
   volatile asset to diversify. Doing so is prudent, not predatory.
4. **The 2021–22 Tesla sales had concrete triggers** — a large option expiry/tax event and
   the Twitter financing. Those are real, exogenous reasons.
5. **He takes enormous real risk.** Many of these bets could have failed (Tesla nearly
   did, 2008). Survivorship makes the pattern look designed in hindsight.
6. **Filings cannot show intent.** We can show *what* and *when*, never *why*. The clean,
   symmetric version of this story is the version most likely to be wrong.

These are not throat-clearing. Each is a live way the thesis is wrong, and each must be
displayed *before* the corresponding finding in any output.

---

## 5. Scope conditions & limits

- **Time:** the *retail-distribution* mechanism is testable from **2010 (Tesla IPO)**
  onward, where his individual SEC record begins (CIK 1494730). Pre-2010 is context only.
- **Private cos** (SpaceX pre-2026, Boring, Neuralink, xAI): value only from funding
  rounds/tenders (`a`/`c`), not market prices.
- **Intent:** out of scope to prove. We grade *behavior and structure*.
- **Contested denominator:** H5's belief/claim split rests on DCF floors that span ~5×.
  We carry that uncertainty explicitly rather than pretending to a clean number.

---

## 6. Measurement dictionary → bridge to the test (Phase 3)

What each sub-hypothesis needs, and the chart that will grade it:

| H | Variable(s) | Source / stream | Chart that tests it |
|---|---|---|---|
| H1 | vote% vs econ% per vehicle | Forms 3/4, DEF 14A, 424(b)(4) | wedge bars per company |
| H2 | Σ sale proceeds vs salary+dividends | `transactions.csv`, proxies | "where the cash comes from" stack |
| H3 | sale price percentile; 10b5-1 share; plan dates | ledger + daily prices | sales-vs-price overlay; plan-vs-catalyst timeline |
| H4 | event dates vs run-ups vs sales | Stream E + prices + ledger | annotated price timeline |
| H5 | price ÷ DCF floor at sale windows | models + market multiples | belief-vs-claim at each sale wave |
| H6 | float%, insider% over time | filings, lock-ups | risk-handoff bands |
| H7 | debt balances by vehicle/date | 8-Ks, 424(b)(4), wires | traveling-debt flow |
| H8 | replication scorecard across vehicles | all of the above | cross-company pattern matrix |
| H9 | pledged shares %, loan size vs price | DEF 14A pledging disclosure | pledged-vs-sold liquidity channels |
| H10 | award value, expense booked, vote added vs salary | DEF 14A, 424(b)(4), Form 4 (code A) | comp-vs-salary + "free alignment" bar |
| H11 | common-control mergers, history recasts, splits pre-event | 8-K, S-1/424(b)(4), proxies | absorption timeline per vehicle |
| H12 | short-dated debt vs cash gap; bridge maturities | 8-K, 10-K debt notes, 424(b)(4) | debt-buys-time chain (with H7) |
| H13 | related-party $ flows; director conflicts | Item 404 / related-person notes | closed-loop value-routing map |
| H14 | private marks, disclosure channel, price tiers | 424(b)(4), 8-K, FWP, public record | reflexivity / price-formation panel |

**Definition of "done" for the hypothesis:** every sub-hypothesis (H1–H14) has (a) a
one-line claim, (b) a prediction, (c) a named data source, and (d) an explicit falsifier —
all satisfied above. Phase 3 now becomes *grading*, not *guessing*.

> **Note on H11–H14:** these began as documented `b`-grade facts *for SpaceX* (from the SPCX
> dossier in `../Spacexsec`). The across-vehicle recurrence is now **graded** for three of
> them: **H11** (SolarCity→Tesla, 2016), **H12+H7** (Twitter→…→SpaceX debt chain), and
> **H13** (Tesla 2025 proxy related-party web) are all SUPPORTED against primary filings —
> see `research/H11_solarcity_absorption.md`, `research/H12_H7_debt_chain.md`,
> `research/H13_related_party_web.md`. **H14** is now graded too (SEC's 2018 fraud finding +
> the 2013 Reg-FD-channel designation + 2021 poll→sale) → `research/H14_sets_broadcasts_price.md`.
> All four of H11–H14 are SUPPORTED across vehicles.

---

*Educational and informational commentary only — not a research report, not investment
advice, not an offer or solicitation. Money in Motion · Eigenstate Research ·
Kirandeep Kaur, Watts Advisor.*
