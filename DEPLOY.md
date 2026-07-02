# Deploy to Vercel — 2 minutes

The web app is **build-verified** (`next build` compiles and pre-renders all pages). It's in the `web/` folder and needs your Vercel login to go live. Pick either path.

---

## Path A — one command (fastest, no GitHub needed)

From your computer, in the project folder:

```bash
cd web
npx vercel --prod
```

- First run asks you to log in (browser opens) and a few setup questions — accept the defaults.
- Because you run it **inside `web/`**, Vercel auto-detects Next.js and deploys the right folder. No "root directory" setting needed.
- You get a live URL like `https://no-bs-xxxx.vercel.app`. Done.

That's the whole thing. Re-run `npx vercel --prod` anytime to redeploy.

---

## Path B — GitHub + Vercel (best for the daily auto-updates)

1. Push this project to a GitHub repo:
   ```bash
   cd ..            # project root (ai-news-for-no-bs)
   git init && git add . && git commit -m "NO BS daily"
   git branch -M main
   git remote add origin https://github.com/<you>/ai-news-for-no-bs.git
   git push -u origin main
   ```
2. Go to https://vercel.com/new → **Import** the repo.
3. **Set Root Directory to `web`** (important — the app lives in the `web/` subfolder).
4. Click **Deploy**. You get your URL.

Now the daily GitHub Action (`.github/workflows/daily.yml`) commits each new edition, and Vercel auto-redeploys — so the site updates itself every day.

---

## After it's live (optional, enables the dynamic bits)

The site works immediately as a **read-only** browser of editions (sectors, images, Deep Dives, All-News) using the static JSON the pipeline commits. To turn on approvals persistence + subscribers + push, add these Environment Variables in Vercel (Project → Settings → Environment Variables) — all free tier:

```
NEXT_PUBLIC_SUPABASE_URL       = https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY  = eyJ...
SUPABASE_SERVICE_KEY           = eyJ...      # used by /approve
APPROVE_SECRET                 = any-random-string
```

Then point `APPROVE_BASE_URL` in `pipeline/.env` at your new Vercel URL so the email's Approve/Reject buttons hit the live site. Full details in `docs/BUILD_GUIDE.md`.

---

## What you get at your URL

- `/` — the latest edition: 8 sectors × 5 deep-dives, images, Deep Dive expanders
- `/all-news/2026-07-01` — the full firehose (all 89 stories, grouped by sector)
- `/edition/2026-07-01` — any specific day
- `/approve?edition=…&action=approve` — the endpoint the email buttons call
- `/api/subscribe`, `/api/push-token` — used by the site + mobile app

> Vercel's Hobby tier is free for personal use. If you monetize the channel/site commercially, Vercel asks you to move to Pro (~$20/mo).
