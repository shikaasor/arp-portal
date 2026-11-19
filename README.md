# ARP Portal — Arewa Revival Project Empowerment Portal

[![CI](https://github.com/shikaasor/arp-portal/actions/workflows/ci.yml/badge.svg)](https://github.com/shikaasor/arp-portal/actions/workflows/ci.yml)
[![CodeQL](https://github.com/shikaasor/arp-portal/actions/workflows/codeql.yml/badge.svg)](https://github.com/shikaasor/arp-portal/actions/workflows/codeql.yml)

The application and review portal for the proposed **5,000 Youth Global Entrepreneurship
Initiative** across the 19 Northern States.

| Layer    | Stack                                             | Hosted on (suggested)      |
| -------- | ------------------------------------------------- | -------------------------- |
| Frontend | Next.js 16 (App Router), React 19, TypeScript     | Vercel **or** Netlify      |
| API      | FastAPI (Python 3.12), Docker                      | Render (blueprint included) |
| Data     | Supabase Postgres, Auth, and a private Storage bucket | Supabase                |

## Features

- **Overview and programme brief** pages, matching the approved design.
- **Applicant accounts** with email and password through Supabase Auth, including email
  verification and password reset.
- **Application form** covering personal, location, education, enterprise and identity
  sections. Validation runs in the browser and again on the API: NIN must be 11 digits, a
  passport number is one letter plus 8 digits, the business idea needs at least 30 words,
  applicants must be 18 or older, and uploaded files are checked by their real file type
  (up to 5 MB each).
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
frontend/              Next.js app (deploy this to Vercel/Netlify)
backend/               FastAPI app + Dockerfile + pytest suite
supabase/migrations/   SQL migrations (source of truth for the database)
supabase/snippets/     Handy SQL (e.g. assigning reviewer roles)
supabase/tests/        Migration assertions run in CI
docs/DEPLOYMENT.md     Step-by-step: Supabase → API → Vercel/Netlify → custom domain
netlify.toml           Netlify build config (base = frontend)
render.yaml            Render blueprint for the API
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
uvicorn app.main:app --reload --port 8000            # docs at http://localhost:8000/docs

# 3. Frontend
cd ../frontend
npm install
cp .env.local.example .env.local                     # API URL + Supabase URL + anon key
npm run dev                                          # http://localhost:3000
```

### Quality checks (the same ones CI runs)

```bash
cd frontend && npm run lint && npm run typecheck && npm test && npm run build
cd backend  && ruff check . && ruff format --check . && pytest
```

## CI/CD

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `ci.yml` | PRs, pushes to `main` | Frontend: lint, typecheck, unit tests, production build, `npm audit`. Backend: ruff, pytest (coverage ≥ 80%), Docker build plus a `/health` smoke test. Migrations: applied twice to Postgres 17 to prove they can safely re-run, then checked by the behavioural assertions. Jobs for parts of the repo a PR doesn't touch are skipped. |
| `codeql.yml` | PRs, `main`, weekly | Static security analysis for TypeScript, Python and the workflow files. |
| `supabase-deploy.yml` | `supabase/migrations/**` changes on `main` | Runs `supabase db push` to production. Skips itself until the secrets are added. |
| Dependabot | Weekly/monthly | Grouped update PRs for npm, pip, Docker and Actions. |

**Deployments** come from the hosts' own Git integrations, so no deploy tokens are stored
in GitHub:

- **Vercel / Netlify** build `frontend/`. Every PR gets a preview URL and `main` goes to
  production. Builds are skipped when nothing under `frontend/` changed.
- **Render** builds `backend/Dockerfile` from `render.yaml` and redeploys on every push
  to `main`. The `/health` check must pass before traffic switches over.

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
