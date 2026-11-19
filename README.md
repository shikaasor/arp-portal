# ARP Portal — Arewa Revival Project Empowerment Portal

[![CI](https://github.com/shikaasor/arp-portal/actions/workflows/ci.yml/badge.svg)](https://github.com/shikaasor/arp-portal/actions/workflows/ci.yml)
[![CodeQL](https://github.com/shikaasor/arp-portal/actions/workflows/codeql.yml/badge.svg)](https://github.com/shikaasor/arp-portal/actions/workflows/codeql.yml)

The application and review portal for the proposed **5,000 Youth Global Entrepreneurship
Initiative** across the 19 Northern States.

A monorepo deployed as **two Vercel projects** from this one repo:

| Layer    | Stack                                                 | Vercel project (root dir)   |
| -------- | ----------------------------------------------------- | --------------------------- |
| Frontend | Next.js 16 (App Router), React 19, TypeScript         | `arp-portal` (`frontend`)   |
| API      | FastAPI (Python 3.12) as one serverless function      | `arp-portal-api` (`backend`) |
| Data     | Supabase Postgres, Auth, and a private Storage bucket | (Supabase)                  |

**Routing:** the website forwards `/api/*` to the API, so everything is served from one
domain. `/api` belongs to FastAPI only, and CI fails if either side breaks that rule (see
[Routing contract](docs/DEPLOYMENT.md#the-routing-contract-how-api-paths-cant-clash)).

## Features

- **Overview and programme brief** pages, matching the approved design.
- **Applicant accounts** with email and password through Supabase Auth, including email
  verification and password reset.
- **Application form** covering personal, location, education, enterprise and identity
  sections. Validation runs in the browser and again on the API: NIN must be 11 digits, a
  passport number is one letter plus 8 digits, the business idea needs at least 30 words,
  and applicants must be 18 or older.
- **Uploads go straight to storage:** documents are sent directly to a private Supabase
  bucket through one-time signed URLs, which avoids Vercel's 4.5 MB request limit. The API
  then checks each file's real type and size before saving the application.
- **Status tracking**: a progress tracker (State → LGA → Ward → Approved) plus the review
  history and reviewer feedback.
- **Review workspace** limited by role:
  - `state`, `lga` and `ward` reviewers see only their assigned area, and can act only on
    applications at their own stage.
  - `national` reviewers see everything, can act at any active stage, and are the **only**
    role that can open identity documents. Those open through 5-minute signed URLs, and
    every view is logged.
- **Preview mode**: if the environment variables are missing, the site still builds and runs
  with clear banners. You can demo the design before the backend is set up.

## Repository layout

```
frontend/              Next.js app            → Vercel project #1 (root: frontend)
  next.config.ts       /api/* proxy to API_ORIGIN
  scripts/check-routes.mjs   blocks frontend routes under /api
backend/               FastAPI app            → Vercel project #2 (root: backend)
  api/index.py         Vercel entrypoint; vercel.json routes everything to it
  tests/               pytest suite (incl. routing-contract tests)
  Dockerfile           portable fallback (tested in CI)
supabase/migrations/   SQL migrations (source of truth for the database)
supabase/snippets/     Handy SQL (e.g. assigning reviewer roles)
supabase/tests/        Migration assertions run in CI
docs/DEPLOYMENT.md     Step-by-step: Supabase → API project → web project → domain
.github/workflows/     CI, CodeQL, Supabase migration deploy
```

## Local development

Prerequisites: Node 22+, Python 3.12+, and a Supabase project (free tier is fine).

```bash
# 1. Database: paste supabase/migrations/*.sql into the Supabase SQL editor
#    (or: supabase link --project-ref <ref> && supabase db push)

# 2. API
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                 # fill in SUPABASE_URL + service-role key
uvicorn app.main:app --reload --port 8000            # docs at http://localhost:8000/api/docs

# 3. Frontend
cd ../frontend
npm install
cp .env.local.example .env.local                     # API_ORIGIN=http://localhost:8000 + Supabase
npm run dev                                          # http://localhost:3000 (proxies /api → :8000)
```

### Quality checks (the same ones CI runs)

```bash
cd frontend && npm run check && npm run build     # check = routes + lint + typecheck + tests
cd backend  && ruff check . && ruff format --check . && pytest
```

## CI/CD

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `ci.yml` | PRs, pushes to `main` | Frontend: `/api` route check, lint, typecheck, unit tests, production build (with the proxy enabled), `npm audit`. Backend: ruff, pytest (coverage ≥ 80%, including the routing-contract tests and a Vercel entry-point import check), Docker build plus a `/health` smoke test. Migrations: applied twice to Postgres 17 to prove they can safely re-run, then checked by the behavioural assertions. Jobs for parts of the repo a PR doesn't touch are skipped. |
| `codeql.yml` | PRs, `main`, weekly | Static security analysis for TypeScript, Python and the workflow files. |
| `supabase-deploy.yml` | `supabase/migrations/**` changes on `main` | Runs `supabase db push` to production. Skips itself until the secrets are added. |
| Dependabot | Weekly/monthly | Grouped update PRs for npm, pip, Docker and Actions. |

**Deployments** come from Vercel's Git integration, so no deploy tokens are stored in
GitHub. Both projects get a preview URL on every PR and deploy `main` to production. Each one
rebuilds only when its own folder changes.

Recommended: in **Settings → Branches**, protect `main` and require the `CI` checks to pass.

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for the full walkthrough, including the
custom domain (`arewarevivalproject.org`) and Cloudflare DNS.

## Assigning reviewers

Reviewers sign up like anyone else. A Supabase admin then promotes them (see
`supabase/snippets/assign_reviewer.sql`):

```sql
update public.profiles set role = 'state', state = 'Kano' where email = 'reviewer@example.org';
```

## Before accepting real applications

- [ ] Publish a privacy notice and retention schedule (NDPA 2023). Confirm the legal basis for
      collecting NIN and passport data.
- [ ] Turn on Supabase **CAPTCHA** (Auth → Bot protection) and set up custom SMTP so
      verification emails are delivered reliably.
- [ ] Add rate limiting at the edge (Cloudflare rules) for `POST /api/applications`.
- [ ] Turn on Supabase backups/PITR, and set up error monitoring (e.g. Sentry) for both apps.
- [ ] Test access with separate applicant, ward, LGA, state and national accounts.

## License

MIT. See [LICENSE](LICENSE).
