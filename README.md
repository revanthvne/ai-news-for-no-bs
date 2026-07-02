# NO BS — Should You Buy This? 🎬

An automated daily tech-news pipeline + web app + mobile app for the **"NO BS — Should You Buy This?"** channel.

Every day it: pulls the latest news across **8 sectors** — AI, Semiconductors, Robotics, eVTOL, Drones, Hardware, Stocks, and top-rated GitHub/Open-Source releases → picks **5 hero stories per sector (~40/day)** plus each sector's other news → writes a NO-BS deep-dive for every hero (the story, the founding story, who should use it, who should buy it, and free/better alternatives) → attaches a real **article image** to each → runs a **source-legitimacy gate (no fake news)** → emails you an **`APPROVAL REQUIRED: Daily AI Short`** edition with a **Deep Dive** on every story and a **"Deep Dive — All News"** firehose → and once you approve, publishes to the **web app**, **mobile app**, and **email subscribers**.

Built to run at **~$0/month** to start.

**What's new in v2:** per-sector sections (5 heroes each), story images (Open Graph + fallback), a credibility rating on every source, per-story Deep Dive expand **and** a global All-News page.

---

## What's in the box

```
ai-news-for-no-bs/
├── pipeline/          # Python engine: fetch → filter → rank → synthesize → render → send
│   ├── run.py         #   the daily entry point (seed or live, sector edition)
│   ├── assemble.py    #   merge 8 sector research files → one edition + images + audit
│   ├── credibility.py #   reputable-source allowlist — the "no fake news" gate
│   ├── images.py      #   og:image fetch + per-sector gradient fallback
│   ├── broadcast.py   #   send an APPROVED edition to subscribers + push
│   ├── sources.py     #   free news: RSS + Hacker News + GitHub
│   ├── ranker.py      #   scores stories (freshness + buy-relevance + signal)
│   ├── synthesize.py  #   LLM deep-dive (or template fallback, zero-key)
│   ├── email_render.py#   sector email + Deep Dive + All-News firehose (HTML + text)
│   └── data/          #   sectors/<date>/*.json research + assembled edition
├── web/               # Next.js web app (browse editions, approve, subscribe)
├── mobile/            # Expo (iOS + Android) app: feed, detail, push
├── supabase/          # Postgres schema (editions, stories, subscribers, tokens)
├── .github/workflows/ # daily cron that runs the whole thing for free
├── samples/           # a REAL generated email for 2026-07-01 — open it!
└── docs/              # BUILD_GUIDE.md · COSTS.md · STRATEGY.md
```

## The email format (exactly as specified)

```
Subject: APPROVAL REQUIRED: Daily AI Short - [Headline]

🎬 THE NEWS :
SOURCE LINKS: [URLs]
Story
Their founding story
Who should use this
Who should purchase this
Are there any free tools that are similar or better than these
```

`pipeline/email_render.py` renders these sections for **every hero story** (5 per sector × 8 sectors), each with a story **image**, a **source-credibility tag**, a collapsible **🔎 Deep Dive**, and the sector's other news below. The email header has **Approve / Reject** buttons plus a **🔍 Deep Dive — All News** button that opens the full firehose of everything gathered that day.

---

## 60-second local demo (no accounts, no keys)

```bash
cd pipeline
pip install -r requirements.txt
python run.py --seed 2026-07-01 --no-email
# → open pipeline/output/email-2026-07-01.html in your browser
```

That produces the full edition + the approval email from today's verified stories — **with zero API keys**. Add keys later to go live (fetch fresh news, call an LLM, actually send email).

Run the **web app** against it:

```bash
cd web && npm install && npm run dev   # → http://localhost:3000
```

Run the **mobile app**:

```bash
cd mobile && npm install && npx expo start   # scan the QR with Expo Go
```

---

## How it works (data flow)

```
        ┌─────────────── GitHub Actions (daily cron, free) ───────────────┐
        │                                                                  │
  free sources ──▶ rank top 5 ──▶ LLM deep-dive ──▶ render email ──▶  📧 APPROVAL REQUIRED → you
 (RSS/HN/GitHub)                                          │                        │
                                                          ▼                    approve ✓
                                                  Supabase (Postgres)  ◀────────────┘
                                                          │
                                         ┌────────────────┼────────────────┐
                                         ▼                ▼                 ▼
                                     Web app          Mobile app       Email subscribers
                                    (Next.js)          (Expo)          (broadcast.py)
```

Everything degrades gracefully: **no LLM key** → template synthesis; **no email provider** → writes the email to disk; **no Supabase** → web/mobile read static JSON the pipeline commits.

## Next steps

- **Deploy it for real:** follow `docs/BUILD_GUIDE.md` (step-by-step, ~30–45 min).
- **See the money:** `docs/COSTS.md` — it's $0 to launch.
- **Read the strategy notes:** `docs/STRATEGY.md` — what you're missing + the "NO BS" pivot.

> Facts in every edition link to primary sources. This is decision-support, **not financial advice.**
