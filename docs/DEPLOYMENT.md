# Deployment guide: one Vercel project

One GitHub repo is deployed as **one Vercel project** using
[Vercel Services](https://vercel.com/docs/services), plus Supabase. The root `vercel.json`
declares two services that build separately and deploy together:

| Service | Root | What it serves |
| --- | --- | --- |
| `web` | `frontend/` | Next.js: every path except `/api/*` |
| `api` | `backend/` | FastAPI (`app.main:app`): `/api/*` |

```
                         arewarevivalproject.org  (one Vercel project, one deployment)
Browser ──► /, /apply, /status, …  ─► web service (Next.js)
        ──► /api/*  ────────────────► api service (FastAPI) ──► Supabase Postgres
        ──► Supabase Auth (sign-in, anon key)                    (service-role key)
        ──► Supabase Storage (one-time signed upload URLs issued by the API)
```

Every deployment, including each PR preview, contains the frontend **and** the API from the
same commit. A preview URL tests both halves of a change together.

## The routing contract: how API paths can't clash

| Path | Owner | Enforced by |
| --- | --- | --- |
| `/api/*` | **FastAPI only** | `frontend/scripts/check-routes.mjs` fails `npm run build` and CI if the frontend defines anything under `/api`. That covers `app/api`, route groups like `(x)/api`, `pages/api` and `public/api*`. |
| every other path | **Next.js only** | `backend/tests/test_routes.py` fails CI if FastAPI adds a public route outside `/api/`, or if `vercel.json` stops routing `/api/*` to the API service ahead of the frontend catch-all. |

- The root `vercel.json` rewrites `/api/:path*` to the `api` service and everything else to
  `web`. Vercel checks these rules in order, so `/api` always reaches FastAPI. The API
  receives the **original path** (`/api/health`, not `/health`), which is why its routes
  are declared with the `/api` prefix.
- Once a request is routed to a service, it stays there: an unknown `/api/...` path is a
  FastAPI 404, never a Next.js page.
- The API docs are served at `/api/docs` and `/api/openapi.json`.
- The browser calls the API on its own domain, so production needs no CORS setup and no
  API URL in the browser.
- **Outside Vercel** (local `npm run dev`, or self-hosting), set `API_ORIGIN` and Next.js
  proxies `/api/*` to it instead (`frontend/next.config.ts`). On Vercel, leave it unset.

## Why files upload straight to Supabase

Vercel functions reject request bodies over **4.5 MB**, and an application carries two files
of up to 5 MB each. So the files never pass through the API:

1. `POST /api/applications/uploads`: the API checks the user can apply and checks the
   declared file types and sizes. It then returns one-time signed upload URLs for paths it
   chooses (`{user_id}/{reference}/…`).
2. The browser uploads directly to the **private** `applicant-documents` bucket.
3. `POST /api/applications`: the API confirms the paths belong to this user and this
   reference, downloads each file, and checks its real type and size. Only then does it save
   the application. Files that fail the check are deleted.

---

## 1. Supabase

1. Create a project at <https://supabase.com/dashboard>. Choose a region close to Nigeria,
   e.g. London (`eu-west-2`) or Frankfurt.
2. Apply the schema: paste each file in `supabase/migrations/` into the **SQL Editor**, oldest
   first, and run it. Or run `supabase link --project-ref <ref>` then `supabase db push`.
   **Apply new migrations before deploying the code that needs them**: the API selects the
   columns they add, so an older database makes every application request fail.
3. **Authentication → URL configuration**
   - Site URL: `https://arewarevivalproject.org`.
   - Redirect URLs: `https://arewarevivalproject.org/**`, `https://www.arewarevivalproject.org/**`
     and `https://arp-portal.vercel.app/**`. For PR previews, also add
     `https://arp-portal-*-<your-vercel-team>.vercel.app/**`.
4. **Authentication → Sign In / Providers** (under *Configuration*) → **Email**: keep
   "Confirm email" **on**.
5. Copy the project URL and keys. Supabase moves these pages around, so search the
   dashboard for "API keys" or "Data API" if the paths below don't match.
   - **Project Settings → Data API** (some dashboards: **Integrations → Data API**): the
     Project URL (`https://<ref>.supabase.co`).
   - **Project Settings → API Keys**: the **publishable** key (`sb_publishable_…`) for the
     website, and a **secret** key (`sb_secret_…`) for the API. If you only see
     **Create new API keys**, create them first. The legacy `anon` / `service_role` keys
     (under **Legacy API keys**) also work, but Supabase is retiring them.
   - The variable names stay the same: the publishable key goes in
     `NEXT_PUBLIC_SUPABASE_ANON_KEY`, and the secret key in `SUPABASE_SERVICE_ROLE_KEY`.

### Optional: automatic migrations from GitHub

Create a GitHub environment called `production`, then add these repository secrets:
`SUPABASE_ACCESS_TOKEN`, `SUPABASE_PROJECT_REF`, `SUPABASE_DB_PASSWORD`. After that, any new
file in `supabase/migrations/` merged to `main` is applied by `supabase-deploy.yml`.
**Never edit a migration that has already been applied. Add a new one.**

## 2. Vercel project

1. **Add New → Project**, then import `shikaasor/arp-portal`.
2. **Project name:** `arp-portal`. **Root Directory:** the repository root (leave it empty).
   **Framework Preset:** **Services**. (CLI: `vercel project update --framework services`.)
   Vercel reads both services from the root `vercel.json`. The frontend installs with
   `npm ci` and builds with `npm run build`. The API's dependencies come from
   `backend/requirements.txt` and its Python version from `backend/.python-version` (3.12).
3. Environment variables (Production *and* Preview). They are shared by both services:

   | Name | Value | Used by |
   | --- | --- | --- |
   | `NEXT_PUBLIC_SUPABASE_URL` | `https://<ref>.supabase.co` | website and API |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | publishable (or legacy anon) key | website |
   | `SUPABASE_SERVICE_ROLE_KEY` | secret (or legacy service_role) key (**secret**: mark it Sensitive) | API |
   | `NEXT_PUBLIC_SITE_URL` *(optional)* | `https://arewarevivalproject.org` | website |

   Never give the service-role key a `NEXT_PUBLIC_` name. Only `NEXT_PUBLIC_*` values are
   built into browser code, so the key stays server-side even though the web service can
   see it. Don't set `API_ORIGIN` or `FRONTEND_ORIGINS` on Vercel: the site and API share
   one domain. If the Supabase variables are missing, the site deploys in **preview mode**:
   pages render, and sign-in and submission are turned off with a banner.
4. Deploy, then open `https://arp-portal.vercel.app/api/health`. It should show
   `"supabase_configured": true`.

If you deployed the earlier two-project setup, delete the `arp-portal-api` project after
this one works, and remove the old `API_ORIGIN` variable.

### Build behaviour

- Each push builds both services and deploys them as one deployment, so the frontend and
  API can never be out of step. To skip builds for documentation-only commits, set
  **Settings → Git → Ignored Build Step**, for example
  `git diff --quiet HEAD^ HEAD -- frontend backend vercel.json`.
- Every PR gets one preview URL, with its own frontend and API. `main` deploys to production.
- `.vercelignore` keeps tests, local caches and the Docker fallback out of the upload.
- The API runs as a Vercel Function on Fluid compute with Vercel's default time limit.
  Every endpoint answers in well under a second, so there is no custom `maxDuration`.

### Local development

- **One env file:** both apps read `.env.local` in the repo root. Copy `.env.example`, or run
  `vercel env pull .env.local` to fetch the project's Development values. This is the same
  set of variables the Vercel project uses.
- **Two terminals** (shown in the README): `uvicorn` on port 8000, and `npm run dev` with
  `API_ORIGIN=http://localhost:8000` in the root `.env.local`.
- **Or everything at once:** `vercel dev -L` from the repo root. This runs both services with
  the same routing as production (`API_ORIGIN` isn't needed).

### Protect `main`

**GitHub → Settings → Branches → Add rule** for `main`: require a pull request, and require
these checks: `Frontend · routes, lint, typecheck, test, build`, `Backend · lint, test`, and
`Supabase · validate migrations`.

## 4. Custom domain and email: `arewarevivalproject.org`

The domain's DNS is managed at its registrar. The site is served by Vercel; mail for
`info@arewarevivalproject.org` is handled by the mailbox provider. Add only the records
below and leave the provider's existing mail records (MX, SPF, DKIM, DMARC) in place.

### Website

1. In the Vercel project: **Settings → Domains**, add `arewarevivalproject.org` and
   `www.arewarevivalproject.org`. Make the apex the primary domain and let `www` redirect to it.
2. At the registrar's DNS settings, add the records Vercel shows. They're typically an apex
   `A` record (`@`) to Vercel's IP and `www` `CNAME` to Vercel's target. Always use the values
   your dashboard shows. If a parking-page `A` or `CNAME` record already exists for `@` or
   `www`, replace that one only. Don't change the nameservers, which would drop the mail records.
3. The API needs **no** domain of its own: `https://arewarevivalproject.org/api/*` is the API.
4. In Vercel, set `NEXT_PUBLIC_SITE_URL=https://arewarevivalproject.org` for Production, then
   redeploy.
5. In Supabase, **Authentication → URL configuration**: set the Site URL and redirect URLs as in
   section 1, step 3.

### Email (`info@arewarevivalproject.org`)

Supabase's built-in mailer is for testing only: it sends a few messages an hour and only to
team members. Real applicants need custom SMTP.

1. **Authentication → Emails → SMTP Settings**: turn on custom SMTP and enter the mail
   provider's SMTP host, port and username (`info@arewarevivalproject.org`) and the mailbox
   password. Sender email `info@arewarevivalproject.org`, sender name `Arewa Revival Project`.
   Alternatively, use a sending service such as Resend with the same sender address; it gives
   you its own DNS records to add.
2. **Authentication → Rate Limits**: raise the email limit to suit the expected sign-ups; it
   starts low once custom SMTP is on.
3. DNS records for delivery (check what the mail provider already created first; there must
   be exactly **one** SPF record):
   - **SPF:** a `TXT` record on `@` starting `v=spf1` that includes the mail provider (and the
     sending service, if you use one), e.g. `v=spf1 include:<provider> ~all`.
   - **DKIM:** the `TXT` or `CNAME` record(s) the provider shows for `<selector>._domainkey`.
   - **DMARC:** a `TXT` record on `_dmarc`, starting with monitoring only:
     `v=DMARC1; p=none; rua=mailto:info@arewarevivalproject.org`. Move to `p=quarantine` once
     reports show mail passing SPF and DKIM.
4. Send yourself a sign-up and a password reset, and check they arrive in the inbox, not spam.

## 5. Go-live checks

- [ ] `https://<site>/api/health` returns `supabase_configured: true` (this proves `/api` reaches FastAPI)
- [ ] `https://<site>/api/docs` loads the API docs
- [ ] Sign up, verify the email and sign in
- [ ] Submit an application with a **4–5 MB** photo. This proves uploads bypass the 4.5 MB limit.
- [ ] A `state` reviewer for another state sees 0 applications; an `lga` reviewer can't act on
      a `state_review` application
- [ ] Only a `national` reviewer sees **View KYC documents**, the links expire, and the
      access appears as `kyc_viewed` in `application_events`
- [ ] The `applicant-documents` bucket is **private**

## Housekeeping

Files uploaded in step 2 by an applicant who never submits are left in the bucket under their
own user folder. Once real traffic starts, add a scheduled clean-up: a Supabase cron job that
deletes objects with no matching `application_kyc` row after 24 hours.

## Portability

`backend/Dockerfile` is kept and tested in CI. If you ever need a long-running server
(e.g. background jobs), the same API runs unchanged on Render, Railway, Fly.io or Cloud Run.
Remove the `/api` rewrite from the root `vercel.json` and set `API_ORIGIN` on the Vercel
project. Next.js then proxies `/api/*` to the external API.
