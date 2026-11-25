# Worker Attendance & Wage Tracker

A mobile-friendly platform for daily-wage workers and contractors to maintain shared attendance, wage, advance, payment, and dispute records.

## Status

Authentication, worksite CRUD, accepted worker invitations, assignments and immutable wage agreements have passing PostgreSQL-backed checks. Integer-paise calculations have unit coverage. CI also boots and restarts the combined frontend/API container and exercises it over HTTP. A free Render Blueprint is prepared, but public deployment is blocked on Render workspace confirmation. Persistent attendance/payments, disputes, relationship-management UI and pilot validation remain pending. This repository starts from scratch.

## Problem and users

Contractors and workers need a shared, reviewable record of work and money owed. This is a problem hypothesis to validate with one contractor and two or three workers. Contractors manage worksites and records; workers review their own records, acknowledge entries, and raise disputes.

## Planned features

- Secure contractor and worker accounts.
- Worksites, worker invitations, assignments, and agreed wage rates.
- Full-day, half-day, and absent attendance.
- Wage balances with advances and payments recorded once.
- Searchable dashboards and downloadable monthly CSV statements.
- Acknowledgement, disputes, corrections, and audit history.
- English and Hindi interface.

See [FEATURES.md](FEATURES.md) for the ten-feature MVP, calculation rules, access boundaries, and acceptance checks.

## Planned stack

React with Vite, FastAPI, and PostgreSQL. Money calculations use integer paise; work dates follow Asia/Kolkata. Persistent financial records are still planned.

## 15-day plan

The [detailed milestone plan](docs/BUILD_PLAN.md) maps each of the fifteen Track A days to its work and evidence. Milestone numbering is retained when work is completed early. Actual completion dates and GitHub timestamps remain the source of evidence.

## Run locally

From repository root, create a Python virtual environment and install `backend/requirements-dev.txt`. Set `DATABASE_URL` to a PostgreSQL database and `JWT_SECRET` to a long random secret. Run `python -m backend.migrate`, then `uvicorn backend.main:app`. Use a fresh empty database for the migration runner; databases previously created manually need an explicit reviewed baseline before adopting tracked migrations.

Check `/health` for `status: ok` and `database: connected`. Database outages return 503 without exposing connection details.

## Tests

Run `python -m unittest discover -s backend/tests -v`. Set `TEST_DATABASE_URL` to enable the real PostgreSQL suite; it creates and removes a uniquely named test schema and does not modify other schemas. Without that variable, integration checks are explicitly skipped. The GitHub Actions workflow provisions PostgreSQL 16, runs the full suite, then builds the frontend.

Auth, worksite, membership and database error checks are in backend/tests. Milestone 13 requires at least five API tests, including meaningful money and access-control coverage.

Latest recorded result: [45 passing checks, no skips, plus production-container smoke and restart](docs/VERIFICATION_2026-11-25.md). See the [assignment/rate API](docs/ASSIGNMENTS_API.md) and [four planned screen wireframes](docs/WIREFRAMES.md). These design assets are not screenshots of implemented financial flows.

## Screenshots, deployment, and demo

See [deployment setup and blocker](docs/DEPLOYMENT.md) for the combined service, migration startup, environment configuration and verification commands. No public backend/database URL has been verified. The existing frontend captures and one-minute showcase do not count as a complete two-minute product demonstration.

## What I built and what I understood

Day 1: defined the problem hypothesis, contractor and worker roles, MVP boundaries, and acceptance checks. The design separates review acknowledgement from payment receipt, snapshots historical wage rates, and uses reversals so corrections preserve an audit trail. Implementation and first-hand learning will be recorded as milestones are completed.

25 November: implemented the assignment/rate prerequisite and tested how membership acceptance, composite ownership constraints and worker-only acknowledgement protect shared wage terms. Packaging the frontend and API together also made routing, migrations and restart behavior part of the CI checks. Attendance snapshots and ledger reversals remain planned rather than claimed as working features.

## Frontend development

Run `npm ci --prefix frontend` then `npm run dev --prefix frontend`. Start backend from repository root with `uvicorn backend.main:app`. Vite proxies auth, worksite, membership and `/api` requests to port 8000. For the combined production service, build with `VITE_API_BASE_URL=/api npm run build --prefix frontend`; FastAPI serves `frontend/dist` and the authenticated API under `/api`. The Docker build sets this variable automatically. It is a public build setting; never put database credentials or JWT secrets in a `VITE_` variable.

## Redesigned frontend and showcase

The frontend now opens with a cinematic landing page. Choose **Explore the demo** to try a sample-data workspace, or **Open workspace** to use the existing backend-connected forms. Sample attendance and payment screens are prototypes; no real financial data is recorded. See [showcase details](docs/SHOWCASE.md).
