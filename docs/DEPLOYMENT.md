# Deployment guide

The order matters: **Supabase → API → frontend → domain**. Each step produces a value the
next one needs.

```
Browser ──(anon key: sign-in only)──► Supabase Auth
   │
   └──(Bearer JWT)──► FastAPI on Render ──(service-role key)──► Supabase Postgres + Storage
```

The browser never gets database access. Every table has RLS turned on and grants nothing
to `anon` or `authenticated`. All reads and writes go through the API.

---

## 1. Supabase

1. Create a project at <https://supabase.com/dashboard>. Choose a region close to Nigeria,
   e.g. `eu-west` (London) or `eu-central` (Frankfurt).
2. Apply the schema. Either:
   - open **SQL Editor**, paste `supabase/migrations/20261119000000_init.sql`, and run it, or
   - run `supabase link --project-ref <ref>` then `supabase db push`.
3. **Authentication → URL configuration**
   - Site URL: your production frontend URL (e.g. `https://arp-portal.vercel.app`, and later
     `https://arewarevivalproject.org`).
   - Redirect URLs: add `<site>/status` and `<site>/reset-password`. For deploy previews,
     also add a wildcard such as `https://*-<team>.vercel.app/**` or
     `https://deploy-preview-*--<site>.netlify.app/**`.
4. **Authentication → Providers → Email**: keep "Confirm email" **on**.
5. **Project settings → API**: copy these values:
   - Project URL → `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL`
   - `anon` / publishable key → `NEXT_PUBLIC_SUPABASE_ANON_KEY` (frontend)
   - `service_role` / secret key → `SUPABASE_SERVICE_ROLE_KEY` (**backend only**)

### Optional: automatic migrations from GitHub

Add these under **Repo → Settings → Secrets and variables → Actions**. Create an environment
called `production` first. You can add required reviewers to it if you want a manual approval
gate.

| Secret | Where to get it |
| --- | --- |
| `SUPABASE_ACCESS_TOKEN` | supabase.com → Account → Access tokens |
| `SUPABASE_PROJECT_REF` | The `xxxx` in `https://xxxx.supabase.co` |
| `SUPABASE_DB_PASSWORD` | The database password you set when creating the project |

After that, any new file in `supabase/migrations/` merged to `main` is pushed automatically.
**Never edit a migration that has already been applied. Add a new one.**

---

## 2. API (Render)

1. On Render: **New → Blueprint**, then pick `shikaasor/arp-portal`. It reads `render.yaml`.
2. Fill in the prompted secrets:
   - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
   - `FRONTEND_ORIGINS`: a comma-separated list, e.g.
     `https://arp-portal.vercel.app,https://arewarevivalproject.org,https://www.arewarevivalproject.org`
   - `FRONTEND_ORIGIN_REGEX` (optional): allows deploy previews, e.g.
     `^https://arp-portal-[a-z0-9-]+\.vercel\.app$` or
     `^https://deploy-preview-\d+--arp-portal\.netlify\.app$`
3. Deploy, then open `https://<service>.onrender.com/health`. It should show
   `"supabase_configured": true`.

> Render's free plan sleeps when idle, so the first request after a pause takes about 30
> seconds. That's fine for demos. Use a paid instance for the real launch.
>
> The same Docker image also runs on Railway, Fly.io or Google Cloud Run. It reads `$PORT`.

---

## 3. Frontend: Vercel *or* Netlify

Both need the same three environment variables:

| Variable | Value |
| --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | `https://<service>.onrender.com` (no trailing slash) |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://<ref>.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | the anon / publishable key |
| `NEXT_PUBLIC_SITE_URL` *(optional)* | the canonical URL, used for social previews |

Without these, the site deploys in **preview mode**: every page renders, and sign-in and
submission are turned off with a banner explaining why.

### Vercel

1. **Add New → Project**, then import `shikaasor/arp-portal`.
2. **Root Directory: `frontend`**. The framework (Next.js) is detected automatically.
3. Add the environment variables for Production **and** Preview, then click Deploy.

### Netlify

1. **Add new site → Import an existing project**, then pick the repo.
2. `netlify.toml` already sets the base directory (`frontend`) and the build command. Leave
   the UI fields as they are.
3. **Site configuration → Environment variables**: add the variables above, then deploy.

Both hosts build a preview for every pull request and deploy `main` to production.

---

## 4. Custom domain: `arewarevivalproject.org` on Cloudflare

1. In Vercel or Netlify, add `arewarevivalproject.org` and `www.arewarevivalproject.org` as
   domains. The host will show the exact DNS records it needs.
2. In Cloudflare DNS, add those records with the proxy **off (DNS only, grey cloud)** so the
   host can issue its TLS certificate. Typical records:
   - Vercel: apex `A 76.76.21.21`, `www CNAME cname.vercel-dns.com`
   - Netlify: apex `A 75.2.60.5` (or ALIAS), `www CNAME <site>.netlify.app`

   Always use the values your dashboard shows, not these examples.
3. Optional API subdomain: in Render, add the custom domain `api.arewarevivalproject.org`,
   create the `CNAME` it shows in Cloudflare, then update `NEXT_PUBLIC_API_BASE_URL` and
   redeploy the frontend.
4. **Don't touch** existing MX, SPF, DKIM or DMARC records.
5. Update everything that refers to the URL:
   - Supabase Site URL and redirect URLs
   - the API's `FRONTEND_ORIGINS`
   - `NEXT_PUBLIC_SITE_URL`

---

## 5. Go-live checks

- [ ] `GET /health` on the API returns `supabase_configured: true`
- [ ] Sign up, receive the verification email, and sign in
- [ ] Submit an application with real-sized files. The reference shows on **Application status**.
- [ ] A `state` reviewer for another state sees **0** applications
- [ ] A `lga` reviewer can't act on a `state_review` application
- [ ] Only a `national` reviewer gets the **View KYC documents** button, and the links expire
- [ ] In Supabase, the `application_events` table shows a `kyc_viewed` row for that access
- [ ] The `applicant-documents` bucket is **private**
