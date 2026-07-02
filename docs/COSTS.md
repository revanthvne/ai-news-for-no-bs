# Cost Breakdown

The whole system is designed to **launch at $0/month** and stay cheap as you grow. Prices as of mid-2026; check each provider for current terms.

## Launch stack — $0/month

| Component | Service | Free tier | Enough for |
|---|---|---|---|
| Daily automation | GitHub Actions | 2,000 free minutes/mo | One ~2-min run/day = ~60 min/mo |
| AI synthesis | Groq API | Free rate-limited tier | 5 deep-dives/day easily |
| Email (approval + subscribers) | Resend | 3,000 emails/mo (100/day) | Approvals + a few hundred subs |
| Database | Supabase | 500 MB DB, 50k monthly active users | Years of editions |
| Web app hosting | Vercel Hobby | Free (personal/non-commercial) | The whole site |
| Mobile testing | Expo Go / EAS | Free builds tier | Dev + beta testing |
| **Total** | | | **$0/month** |

## One-time / annual (only when you're ready)

| Item | Cost | Needed for |
|---|---|---|
| Domain (e.g. `shouldyoubuythis.tech`) | ~$10–15/yr | Branded site + email `from` address |
| Apple Developer Program | $99/yr | Publishing the iOS app to the App Store |
| Google Play Developer | $25 one-time | Publishing the Android app |

## When you scale (rough guide)

| Trigger | What changes | Est. cost |
|---|---|---|
| Web app used commercially | Vercel Pro (Hobby is non-commercial) | ~$20/mo |
| >3,000 emails/mo | Resend paid tier | ~$20/mo for 50k emails |
| Heavier/better LLM | OpenAI `gpt-4o-mini` or Claude Haiku, ~5 calls/day | **cents/day** (~$1–3/mo) |
| Bigger DB / more users | Supabase Pro | ~$25/mo |
| Managed daily cron off GitHub | (optional) a $5 VPS or Vercel Cron | ~$5/mo |

**Realistic "growing but lean" bill: ~$0 for months, then ~$20–40/month** once you want a custom domain, commercial hosting, and higher email volume.

## Cost-control tips

- Keep synthesis on a **small, cheap model** — `gpt-4o-mini` / `llama-3.3-70b` (Groq) / `claude-3-5-haiku` are plenty for 5 stories.
- The pipeline caches nothing you pay for twice: one LLM call per hero per day (~5 calls).
- Static-JSON fallback means the web app can serve for free from Vercel/GitHub Pages even without a live database.
- Batch email with Resend/one provider rather than per-message services.
