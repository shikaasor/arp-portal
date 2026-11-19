# Deployment guide: Vercel monorepo

One GitHub repo is deployed as **two Vercel projects**, plus Supabase:

| Vercel project | Root directory | What it serves |
| --- | --- | --- |
| `arp-portal` | `frontend` | The website, and the public domain |
| `arp-portal-api` | `backend` | FastAPI as one Python serverless function |

```
                         arewarevivalproject.org  (frontend project)
Browser ──► /, /apply, /status, …  ─────────────► Next.js pages
        ──► /api/*  ── rewrite (same origin) ───► arp-portal-api.vercel.app ──► Supabase Postgres
        ──► Supabase Auth (sign-in, anon key)                                 (service-role key)
        ──► Supabase Storage (one-time signed upload URLs issued by the API)
```

## The routing contract: how API paths can't clash

| Path | Owner | Enforced by |
| --- | --- | --- |
| `/api/*` | **FastAPI only** | `frontend/scripts/check-routes.mjs` fails `npm run build` and CI if the frontend defines anything under `/api`. That covers `app/api`, route groups like `(x)/api`, `pages/api` and `public/api*`. |
| every other path | **Next.js only** | `backend/tests/test_routes.py` fails CI if FastAPI adds a public route outside `/api/`. |

- The frontend forwards `/api/:path*` to `API_ORIGIN/api/:path*` (`frontend/next.config.ts`).
  The forwarding runs *before* any of Next's own files are checked, so the API always wins
  for `/api`.
- The API docs are served at `/api/docs` and `/api/openapi.json`, so they work through the
  public domain too.
- The browser calls the API on its own domain, so production needs no CORS setup and no
  API URL in the browser.

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
2. Apply the schema: paste `supabase/migrations/20261119000000_init.sql` into the **SQL
   Editor** and run it. Or run `supabase link --project-ref <ref>` then `supabase db push`.
3. **Authentication → URL configuration**
   - Site URL: `https://arp-portal.vercel.app` (switch it to the custom domain later).
   - Redirect URLs: `https://arp-portal.vercel.app/**`. For PR previews, also add
     `https://arp-portal-*-<your-vercel-team>.vercel.app/**`.
4. **Authentication → Providers → Email**: keep "Confirm email" **on**.
5. **Project settings → API**: copy the Project URL, the `anon`/publishable key and the
   `service_role` key.

### Optional: automatic migrations from GitHub

Create a GitHub environment called `production`, then add these repository secrets:
`SUPABASE_ACCESS_TOKEN`, `SUPABASE_PROJECT_REF`, `SUPABASE_DB_PASSWORD`. After that, any new
file in `supabase/migrations/` merged to `main` is applied by `supabase-deploy.yml`.
**Never edit a migration that has already been applied. Add a new one.**

## 2. Vercel project: API (`backend`)

1. **Add New → Project**, then import `shikaasor/arp-portal`.
2. **Project name:** `arp-portal-api`. **Root Directory:** `backend`. **Framework Preset:** Other.
   `backend/vercel.json` sends every request to `api/index.py`. Dependencies come from
   `requirements.txt` and the Python version from `.python-version` (3.12).
3. Environment variables (Production *and* Preview):

   | Name | Value |
   | --- | --- |
   | `SUPABASE_URL` | `https://<ref>.supabase.co` |
   | `SUPABASE_SERVICE_ROLE_KEY` | service-role key (**secret**: mark it Sensitive) |
   | `FRONTEND_ORIGINS` | `https://arp-portal.vercel.app`. This only matters when calling the API host directly; normal traffic is same-origin. |

4. Deploy, then open `https://arp-portal-api.vercel.app/api/health`. It should show
   `"supabase_configured": true`.

## 3. Vercel project: website (`frontend`)

1. **Add New → Project**, then import the same repo again.
2. **Project name:** `arp-portal`. **Root Directory:** `frontend`. Next.js is detected
   automatically.
3. Environment variables:

   | Name | Production | Preview |
   | --- | --- | --- |
   | `API_ORIGIN` | `https://arp-portal-api.vercel.app` | same (or a staging API) |
   | `NEXT_PUBLIC_SUPABASE_URL` | `https://<ref>.supabase.co` | same |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | anon/publishable key | same |
   | `NEXT_PUBLIC_SITE_URL` *(optional)* | `https://arewarevivalproject.org` | — |

   `API_ORIGIN` must be an origin only, with no path and no trailing `/api`. The build fails
   if it's malformed. If it's missing, the site deploys in **preview mode**: pages render, and
   sign-in and submission are turned off with a banner.
4. Deploy.

### Monorepo build behaviour

- Each project rebuilds only when its own folder changes (the `ignoreCommand` in each
  `vercel.json`). Vercel's **Settings → Git → "Skip deployments when there are no changes to
  the root directory"** does the same job if you prefer to set it there.
- Every PR gets preview URLs for whichever project changed. `main` deploys to production.
- By default, frontend previews call the **production** API. To test a backend change from a
  frontend preview, set `API_ORIGIN` for that branch to the backend's branch URL
  (`https://arp-portal-api-git-<branch>-<team>.vercel.app`) under **Settings → Environment
  Variables → Preview → (branch)**.

### Protect `main`

**GitHub → Settings → Branches → Add rule** for `main`: require a pull request, and require
these checks: `Frontend · routes, lint, typecheck, test, build`, `Backend · lint, test`, and
`Supabase · validate migrations`.

## 4. Custom domain: `arewarevivalproject.org` on Cloudflare

1. In the **frontend** project: **Settings → Domains**, add `arewarevivalproject.org` and
   `www.arewarevivalproject.org`.
2. In Cloudflare DNS, add the records Vercel shows, with the proxy **off (DNS only, grey
   cloud)**. They're typically an apex `A` record to Vercel's IP and `www CNAME cname.vercel-dns.com`.
   Always use the values your dashboard shows. Don't touch MX, SPF, DKIM or DMARC records.
3. The API needs **no** domain of its own: `https://arewarevivalproject.org/api/*` already
   reaches it through the forwarding. (Optionally give the backend `api.arewarevivalproject.org`
   and point `API_ORIGIN` at it.)
4. Update the Supabase Site URL and redirect URLs, and `NEXT_PUBLIC_SITE_URL`.

## 5. Go-live checks

- [ ] `https://<site>/api/health` returns `supabase_configured: true` (this proves the forwarding works)
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
Point `API_ORIGIN` at it.
