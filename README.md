# ARP Portal — Arewa Revival Project Empowerment Portal

[![CI](https://github.com/shikaasor/arp-portal/actions/workflows/ci.yml/badge.svg)](https://github.com/shikaasor/arp-portal/actions/workflows/ci.yml)
[![CodeQL](https://github.com/shikaasor/arp-portal/actions/workflows/codeql.yml/badge.svg)](https://github.com/shikaasor/arp-portal/actions/workflows/codeql.yml)

The application and review portal for the proposed **5,000 Youth Global Entrepreneurship
Initiative** across the 19 Northern States.

A monorepo deployed as **one Vercel project** with [Vercel Services](https://vercel.com/docs/services):

| Layer    | Stack                                                 | Vercel service (root)   |
| -------- | ----------------------------------------------------- | ----------------------- |
| Frontend | Next.js 16 (App Router), React 19, TypeScript         | `web` (`frontend/`)     |
| API      | FastAPI (Python 3.12) as a Vercel Function            | `api` (`backend/`)      |
| Data     | Supabase Postgres, Auth, and a private Storage bucket | (Supabase)              |

**Routing:** the root `vercel.json` sends `/api/*` to FastAPI and everything else to Next.js,
on one domain. Every deployment, PR previews included, has the frontend and API from the
same commit. `/api` belongs to FastAPI only, and CI fails if either side breaks that rule (see
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
  history and reviewer feedback. When a reviewer requests more information, the applicant
  replies from the status page (optionally with replacement documents) and the application
  goes back to the stage that asked.
- **Location matching**: applicants pick their LGA from the official list for their state, and
  reviewers are matched by LGA and ward ignoring case, spacing and punctuation.
- **One application per person**: an identification number (NIN or passport) can only be used
  once, enforced by the API and a unique index.
- **Review workspace** limited by role:
  - `state`, `lga` and `ward` reviewers see only their assigned area, and can act only on
    applications at their own stage.
  - `national` reviewers see everything, can act at any active stage, and are the **only**
    role that can open identity documents. Those open through 5-minute signed URLs, and
    every view is logged.
- **Preview mode**: if the Supabase environment variables are missing, the site still builds and runs
  with clear banners. You can demo the design before the backend is set up.

## Repository layout

```
vercel.json            Vercel Services: web + api, and /api/* → api routing
frontend/              Next.js app            → service `web`
  next.config.ts       /api/* proxy to API_ORIGIN (local dev / outside Vercel only)
  scripts/check-routes.mjs   blocks frontend routes under /api
backend/               FastAPI app            → service `api` (entrypoint app.main:app)
  tests/               pytest suite (incl. routing-contract tests)
  Dockerfile           portable fallback (tested in CI)
supabase/migrations/   SQL migrations (source of truth for the database)
supabase/snippets/     Handy SQL (e.g. assigning reviewer roles)
supabase/tests/        Migration assertions run in CI
docs/DEPLOYMENT.md     Step-by-step: Supabase → Vercel project → domain
.github/workflows/     CI, CodeQL, Supabase migration deploy
```

## Local development

Prerequisites: Node 22+, Python 3.12+, and a Supabase project (free tier is fine).

```bash
# 1. Database: paste supabase/migrations/*.sql into the Supabase SQL editor
#    (or: supabase link --project-ref <ref> && supabase db push)

# 2. One env file for both apps, in the repo root
cp .env.example .env.local                           # fill in the Supabase URL and keys
#    (or, once the Vercel project exists: vercel env pull .env.local, then add API_ORIGIN)

# 3. API
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000            # docs at http://localhost:8000/api/docs

# 4. Frontend (second terminal)
cd frontend
npm install
npm run dev                                          # http://localhost:3000 (proxies /api → :8000)
```

Both apps read the root `.env.local`. Real environment variables take priority over it, and
an optional `backend/.env` or `frontend/.env.local` overrides it for one app only. Restart
`npm run dev` after editing the root file: Next.js only watches its own env files.

Or run both with production routing from the repo root: `vercel dev -L`.

### Quality checks (the same ones CI runs)

```bash
cd frontend && npm run check && npm run build     # check = routes + lint + typecheck + tests
cd backend  && ruff check . && ruff format --check . && pytest
```

## CI/CD

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `ci.yml` | PRs, pushes to `main` | Frontend: `/api` route check, lint, typecheck, unit tests, production build, `npm audit`. Backend: ruff, pytest (coverage ≥ 80%, including the routing-contract tests and checks that the `vercel.json` entrypoint imports and `/api/*` is routed to FastAPI first), Docker build plus a `/health` smoke test. Migrations: applied twice to Postgres 17 to prove they can safely re-run, then checked by the behavioural assertions. Jobs for parts of the repo a PR doesn't touch are skipped. |
| `codeql.yml` | PRs, `main`, weekly | Static security analysis for TypeScript, Python and the workflow files. |
| `supabase-deploy.yml` | `supabase/migrations/**` changes on `main` | Runs `supabase db push` to production. Skips itself until the secrets are added. |
| Dependabot | Weekly/monthly | Grouped update PRs for npm, pip, Docker and Actions. |

**Deployments** come from Vercel's Git integration, so no deploy tokens are stored in
GitHub. Every PR gets one preview URL containing both the frontend and the API, and `main`
deploys to production.

Recommended: in **Settings → Branches**, protect `main` and require the `CI` checks to pass.

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for the full walkthrough, including the
custom domain (`arewarevivalproject.org`) and Cloudflare DNS.

## Design & images

The look draws on Northern Nigeria: flag green, Durbar gold, Kano dye-pit indigo and mud-wall
terracotta, with original SVG patterns in `frontend/public/patterns/` (an Arewa-knot motif and a
zig-zag band inspired by Hausa wall relief and textile edging). Headlines use Bricolage Grotesque
and body text uses Plus Jakarta Sans, loaded through `next/font`.

Photos are Creative Commons images from Wikimedia Commons. They're credited on `/credits`, a
page generated from the same image list, so credits can't fall out of sync with the photos.

- **To add or replace a photo:** put the original in `frontend/scripts/image-src/` (not
  committed), add an entry to `frontend/scripts/images.json` with its alt text and credit,
  then run `python3 frontend/scripts/build-images.py`. Commit the generated
  `public/img/*.webp` files and `src/lib/images.generated.ts`.
- **Only use photos that allow commercial use** (CC0, CC BY or CC BY-SA), and always include
  the credit fields.
- **Render images with `<Img name="…" sizes="…" />`, not `next/image`.** Next's `/_next/image`
  optimiser isn't served under Vercel Services routing (it returns 404), so images are
  optimised ahead of time and served as plain static files.

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
- [ ] Turn on Supabase backups/PITR, and set up error monitoring (e.g. Sentry) for both services.
- [ ] Test access with separate applicant, ward, LGA, state and national accounts.

## License

MIT. See [LICENSE](LICENSE).
