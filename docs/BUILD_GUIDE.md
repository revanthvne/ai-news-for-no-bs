# Build & Deploy Guide — NO BS Daily AI Short

This takes you from the code in this repo to a **live, automated, production system** in about **30–45 minutes**. Every service below has a free tier; you can launch for **$0**.

The order matters. Do the steps top to bottom.

---

## Step 0 — Prerequisites (5 min)

Install if you don't have them:
- **Python 3.11+**, **Node 18+**, **Git**
- A **GitHub** account (hosts the code + runs the free daily cron)

Clone / open the repo and do the local smoke test from the README first. If `pipeline/output/email-2026-07-01.html` opens and looks right, you're ready.

---

## Step 1 — Get your free API keys (10 min)

You need two services to go from "demo" to "live." Both are free to start.

| Purpose | Service | Free tier | Where |
|---|---|---|---|
| AI synthesis | **Groq** | Generous free rate limits, very fast | https://console.groq.com → API Keys |
| Sending email | **Resend** | 3,000 emails/mo, 100/day | https://resend.com → API Keys |

> Alternatives: use **OpenAI** (`gpt-4o-mini`) or **Anthropic** (`claude-3-5-haiku`) instead of Groq — set `LLM_PROVIDER` accordingly. For email you can use **Gmail SMTP** with an app password instead of Resend.

Copy `pipeline/.env.example` to `pipeline/.env` and fill in:

```ini
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_...
EMAIL_FROM=NO BS Daily <onboarding@resend.dev>   # resend.dev works before you add a domain
APPROVER_EMAIL=k.revanth123@gmail.com
APPROVE_BASE_URL=http://localhost:3000            # change to your Vercel URL after Step 4
```

Test it live (fetches fresh news, calls the LLM, emails you):

```bash
cd pipeline
python run.py --live
```

Check your inbox for **`APPROVAL REQUIRED: Daily AI Short - …`**. 🎉

---

## Step 2 — Database on Supabase (5 min) — free

1. Create a project at https://supabase.com (free tier).
2. Open **SQL Editor**, paste all of `supabase/schema.sql`, click **Run**.
3. In **Project Settings → API**, copy:
   - `Project URL` → `SUPABASE_URL`
   - `service_role` key → `SUPABASE_SERVICE_KEY` (server-only, keep secret)
   - `anon` key → used by the web app (`NEXT_PUBLIC_SUPABASE_ANON_KEY`)

Add the two service values to `pipeline/.env`. Re-run `python run.py --live` — the edition now upserts into the `editions` table.

---

## Step 3 — Deploy the web app on Vercel (5 min) — free

1. Push this repo to GitHub.
2. At https://vercel.com → **New Project** → import the repo.
3. Set **Root Directory** to `web`.
4. Add environment variables (Project → Settings → Environment Variables):
   ```
   NEXT_PUBLIC_SUPABASE_URL       = https://xxxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY  = eyJ...
   SUPABASE_SERVICE_KEY           = eyJ...   (used by /approve)
   APPROVE_SECRET                 = any-random-string
   ```
5. Deploy. You'll get a URL like `https://no-bs.vercel.app`.
6. Put that URL into `pipeline/.env` as `APPROVE_BASE_URL` so the email's Approve/Reject buttons point at the live site.

> The web app also reads static JSON from `web/public/editions/` as a fallback, so it shows content even before Supabase is wired.

---

## Step 4 — Automate the daily run with GitHub Actions (5 min) — free

The workflow is already at `.github/workflows/daily.yml`. Add your keys as repo secrets:

**GitHub repo → Settings → Secrets and variables → Actions → New repository secret**, add:

```
LLM_PROVIDER, GROQ_API_KEY, LLM_MODEL,
EMAIL_PROVIDER, RESEND_API_KEY, EMAIL_FROM, APPROVER_EMAIL,
SUPABASE_URL, SUPABASE_SERVICE_KEY, APPROVE_BASE_URL,
GH_READ_TOKEN   (a GitHub PAT with public repo read — raises GitHub API limits; optional)
```

Then **Actions tab → Daily AI Short → Run workflow** to test immediately. It will email you an edition and commit the JSON. Adjust the schedule (the `cron:` line) to your preferred time — it's in UTC.

---

## Step 5 — Ship the mobile app with Expo (10 min)

1. `cd mobile && npm install`
2. Edit `mobile/app.json` → set `extra.apiBase` to your Vercel URL (so the app pulls the latest edition and can register push tokens).
3. Test instantly on your phone: `npx expo start`, then scan the QR with the **Expo Go** app.
4. To publish real apps later:
   - Install EAS: `npm i -g eas-cli && eas login`
   - `eas build -p android` / `eas build -p ios`
   - Submit: `eas submit` (needs Apple Developer $99/yr and/or Google Play $25 one-time).

Push notifications work out of the box in Expo Go for testing; for production push you'll add an EAS `projectId` to `app.json` under `extra.eas.projectId`.

---

## Step 6 — The approve → publish → broadcast loop

1. Pipeline emails you `APPROVAL REQUIRED`.
2. You click **✓ Approve** → hits `web /approve` → sets the edition `status = approved` in Supabase → it appears on the web app + mobile app.
3. To email subscribers + push mobile users, run:
   ```bash
   cd pipeline && python broadcast.py --date $(date -u +%Y-%m-%d)
   ```
   (Optional: add a second GitHub Action that runs `broadcast.py` when an edition flips to `approved`.)

---

## Troubleshooting

- **No email arrived:** check `EMAIL_PROVIDER`/keys; with none set, the pipeline just writes `output/email-DATE.html` — open it.
- **LLM errors:** the pipeline auto-falls back to template synthesis so it never fails the run. Check your provider key/rate limits.
- **Web app empty:** make sure `web/public/editions/latest.json` exists (the pipeline writes it) or Supabase env vars are set.
- **Live fetch returns few stories:** normal on quiet days; RSS feeds vary. HN + GitHub are the most reliable and always return.

You're live. From here it's a daily 2-minute habit: open the approval email, read, approve, film your Short.
