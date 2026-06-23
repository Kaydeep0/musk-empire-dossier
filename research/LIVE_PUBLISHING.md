# LIVE PUBLISHING — maximum attention + automatic updates

**Goal.** One public surface that (1) gets found and shared, and (2) **updates itself** whenever
Musk moves in the **regulated** lane (SEC EDGAR). Social posts are the amplifier; EDGAR is the
engine. You already have half the engine — this doc completes the loop.

> Educational only — not investment advice. Anything published under Watts Advisor needs WSP review
> and the IAR/firm disclosure line before it goes live.

---

## Part A — What I would do *today* for maximum lawful attention

Attention compounds when three things align: **a hook with a date**, **proof nobody else has**, and
**a URL that stays fresh.**

### 1. Ship one canonical “live” URL (do this first)
Publish the `public/` folder (GitHub Pages, Cloudflare Pages, or Substack embed):

| Artifact | Path | Why it spreads |
|---|---|---|
| **Landing page** | `public/index.html` | Shareable link; “LIVE” badge + last EDGAR update |
| **RSS feed** | `public/feed.xml` | Journalists, bots, Google News, Feedly subscribe |
| **Machine JSON** | `public/status.json` | Other sites / your newsletter can pull it |
| **Changelog** | `public/CHANGELOG.md` | Proof you update when filings land |

Set your real URL once: `export MUSK_DOSSIER_URL=https://yoursite.com/musk-dossier`

**Why this beats another LinkedIn post alone:** a post dies in 48 hours; a **live dossier with an
RSS feed** keeps ranking, gets bookmarked, and gives every future post a home base.

### 2. Lead with the dated hook (your unfair advantage)
You already have what most commentary lacks — **pre-registered, calendar-dated tests**:

- **SPCX August unlock** — does price hold when float ~doubles?
- **Form 4 watch** — does he sell into unlock windows? (graded on filing date, not opinion)
- **Bridge cliff 2027-09-02** — refinancing test

One thread: *“Here’s the filing. Here’s the date. I’ll grade it on the day.”* That is shareable
because it can be **wrong in public** — which is exactly why people trust it.

### 3. Cascade each update (human-in-the-loop for compliance)
When the pipeline runs, **don’t auto-tweet trades** — auto-**draft**:

1. **ntfy** (already live) → you see the filing on your phone  
2. **Pipeline** rebuilds charts + `public/`  
3. **You** post a 3-tweet / LinkedIn thread: chart + EDGAR link + falsifier  
4. Optional: webhook to Slack with draft text (set `MUSK_WATCH_WEBHOOK`)

**Maximum attention channels (in order of ROI today):**
- **LinkedIn** (Money in Motion — you already have 223 subs + network): long-form + chart
- **X**: thread with one chart + EDGAR link + “grading on [date]”
- **One journalist** from `COALITION_MAP.md` (Lopez / FT Alphaville / Reuters tips) — offer the
  *RSS feed*, not your conclusion
- **HN / Reddit r/stocks** — only when a **new Form 4** or major filing lands (factual, sourced)

### 4. SEO + discovery (free, passive)
Title pattern: *“Elon Musk SEC filings — live sales ledger & empire mechanics”*  
Meta: *“Updated from EDGAR CIK 1494730. Form 4 sales, net worth decomposition, debt chain.”*  
That captures people searching **“Musk Form 4”**, **“Musk sold stock”**, **“SpaceX lock-up”** — high-intent queries.

---

## Part B — Automatic updates (what runs on your Mac)

```
┌─────────────────────────────────────────────────────────────┐
│  launchd (every 15 min)                                      │
│    watch_musk_filings.py                                     │
│      → diff EDGAR CIK 1494730                                │
│      → ntfy + desktop alert + filing_alerts.log              │
│      → on_new_filing.py  (if MUSK_WATCH_PIPELINE=1)          │
│           → pull_musk_filings.py  (re-parse Form 4 XML)      │
│           → phase3_analyze / networth / charts  (material)   │
│           → publish_live_feed.py  → public/*                   │
└─────────────────────────────────────────────────────────────┘
```

### What triggers a **full** rebuild
Material forms (insider trades, ownership, proxies, IPO docs):  
`4`, `4/A`, `3`, `5`, `13D/G`, `8-K`, `DEF 14A`, `S-1`, `424B*`

Everything else still alerts + updates the public feed changelog.

### Commands
```bash
# One-time: build public site artifacts now
python3 build/publish_live_feed.py

# Manual full pipeline (same as watcher runs on new Form 4)
python3 build/on_new_filing.py

# Disable auto-rebuild from watcher (alerts only)
export MUSK_WATCH_PIPELINE=0
```

### Deploy `public/` to the web (pick one)
- **GitHub Pages:** repo → Settings → Pages → `/public` or `gh-pages` branch; auto-deploy on push
- **Cloudflare Pages:** connect repo, build command `python3 build/publish_live_feed.py`, output `public/`
- **Substack:** embed `status.json` numbers in newsletter footer; link to hosted `index.html`

---

## Part C — “Anytime he moves a muscle” — scope honestly

| Signal | Auto today? | How |
|---|---|---|
| **Musk SEC filings** (Form 4, 13D, etc.) | **Yes** | `watch_musk_filings.py` + pipeline |
| **Tesla / SpaceX issuer filings** (8-K, proxy) | **Next** | Extend watcher to CIKs in `registry/entities.csv` |
| **X / social posts** | **Partial** | Not SEC-regulated; separate monitor (API cost / ToS). Use for *context*, not primary proof |
| **Price / options** | **Yes** | Cron refresh `prices_tsla.csv` daily (already have Yahoo pull) |

**Regulated space = EDGAR first.** That’s what your dossier is built on; automating social is optional
and legally noisier. The watcher you have covers the highest-signal lane (Form 4 = money moving).

### Phase 2 expansion (when ready)
- `watch_entities.py` — poll Tesla `0001318605` + SpaceX `0001181412` for 8-K / DEF 14A
- Daily `pull_prices.py` — refresh TSLA for H3 chart
- `draft_social_post.py` — reads latest alert, outputs compliant draft text (you approve before post)

---

## Part D — Compliance guardrails for “live” publishing
- **Auto-update numbers from EDGAR:** fine — that’s aggregation of public data  
- **Auto-post to social:** risky under IA marketing rules — keep **human approval** on every post  
- **Disclose** if you hold positions in names you publish on (`TRADE_THE_EDGE.md`)  
- **WSP review** before the public URL goes under Watts Advisor branding  

---

## Quick start checklist
- [ ] Run `python3 build/publish_live_feed.py` → open `public/index.html` locally  
- [ ] Set `MUSK_DOSSIER_URL` and deploy `public/` to GitHub/Cloudflare Pages  
- [ ] Confirm watcher pipeline: `MUSK_WATCH_PIPELINE=1` (default) in launchd plist  
- [ ] Post **one** LinkedIn piece linking to the live URL + August unlock test  
- [ ] Submit RSS to Feedly / give `feed.xml` to one journalist from `COALITION_MAP.md`  

*Cross-ref: `GAME_PLAN.md` (live watch), `COALITION_MAP.md` (amplification), `STRUCTURE_BRIEF.md` (institutional)*
