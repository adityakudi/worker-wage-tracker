# Worker Attendance & Wage Tracker

A mobile-friendly platform for daily-wage workers and contractors to maintain shared attendance, wage, advance, payment, and dispute records.

## Status

Planning, authentication and initial worksite APIs are implemented. Database-backed integration, related entity APIs, frontend end-to-end checks, pilot validation and deployment remain pending. This repository starts from scratch.

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

React with Vite, FastAPI, and PostgreSQL. Money is stored as integer paise; work dates use Asia/Kolkata. Implementation dependencies will be selected during setup.

## 15-day plan

The [detailed milestone plan](docs/BUILD_PLAN.md) maps each of the fifteen Track A days to its work and evidence. Milestone numbering is retained when work is completed early. Actual completion dates and GitHub timestamps remain the source of evidence.

## Run locally

From repository root, create a Python virtual environment and install `backend/requirements-dev.txt`. Set `DATABASE_URL` to a PostgreSQL database and `JWT_SECRET` to a long random secret. Run `python -m backend.migrate`, then `uvicorn backend.main:app`. Use a fresh empty database for the migration runner; databases previously created manually need an explicit reviewed baseline before adopting tracked migrations.

Check `/health` for `status: ok` and `database: connected`. Database outages return 503 without exposing connection details.

## Tests

Run `python -m unittest discover -s backend/tests -v`. Set `TEST_DATABASE_URL` to enable the real PostgreSQL suite; it creates and removes a uniquely named test schema and does not modify other schemas. Without that variable, integration checks are explicitly skipped. The GitHub Actions workflow provisions PostgreSQL 16, runs the full suite, then builds the frontend.

Auth, worksite, membership and database error checks are in backend/tests. Milestone 13 requires at least five API tests, including meaningful money and access-control coverage.

## Screenshots, deployment, and demo

Pending working software. Real screenshots, the verified public URL, and a two-minute demo will be added during delivery.

## What I built and what I understood

Day 1: defined the problem hypothesis, contractor and worker roles, MVP boundaries, and acceptance checks. The design separates review acknowledgement from payment receipt, snapshots historical wage rates, and uses reversals so corrections preserve an audit trail. Implementation and first-hand learning will be recorded as milestones are completed.

## Frontend development

Run `npm ci --prefix frontend` then `npm run dev --prefix frontend`. Start backend from repository root with `uvicorn backend.main:app`. Vite proxies auth and worksite requests to port 8000. `npm run build --prefix frontend` builds static assets. Production hosting must proxy these API paths; no production routing has been configured yet.

## Redesigned frontend and showcase

The frontend now opens with a cinematic landing page. Choose **Explore the demo** to try a sample-data workspace, or **Open workspace** to use the existing backend-connected forms. Sample attendance and payment screens are prototypes; no real financial data is recorded. See [showcase details](docs/SHOWCASE.md).
