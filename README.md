# Worker Attendance & Wage Tracker

A fresh React/FastAPI/PostgreSQL project for shared work and wage records between daily-wage workers and small contractors.

**Software release — 29 November 2026.** The live app covers signup, worksite management, worker invitations, agreed wage rates, attendance, advances and payments, corrections, disputes and monthly statements. The public demo runs on free Render hosting. The challenge publication and participant feedback remain separate open items.

[Open the live workspace](https://worker-wage-tracker-wg8y.onrender.com/#live) · [Two-minute walkthrough](docs/release-evidence/2026-11-29/Worker_Wage_Tracker.mp4) · [Verification](docs/VERIFICATION_2026-11-29.md)

## Problem and users

Contractors and workers need a shared way to reconcile attendance, wage rates and money owed. Contractors manage their own worksites, invite workers and post records. Workers receive invitations, approve wage rates, and can review or dispute their own entries.

## What you can do

| Area | Available |
|---|---|
| Accounts | Worker or contractor signup, Argon2 password hashes, JWT login and role-protected access |
| Worksites and workers | Worksite create, edit, search, archive and eligible deletion. Worker invitations, assignments and agreed wage rates |
| Attendance and pay | Full day, half day and absence. Effective wage snapshots, advance and payment records, adjustments and one-time reversals |
| Review and disputes | Separate review and receipt confirmation, worker disputes, contractor responses, worker decisions and audit history |
| Records and statements | Participant-only ledgers, date and text filters, pagination, balance totals and monthly CSV |
| Workspace language | English and Hindi interface labels |

The [feature specification](FEATURES.md) describes the acceptance rules. All amounts are bookkeeping records. The application does not move money.

## Stack

React 19 and Vite frontend; Python/FastAPI with psycopg, Argon2 and PyJWT; PostgreSQL 16 in CI; multi-stage Docker image with Node 22 and Python 3.12. INR calculations use integer paise, not floating-point money. Work dates follow Asia/Kolkata; timestamps use UTC.

## Run locally

Use a fresh, reachable PostgreSQL database. From repository root:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
export DATABASE_URL='postgresql://USER:PASSWORD@HOST:5432/DATABASE'
export JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
python -m backend.migrate
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Replace the example database connection locally; never commit credentials. In another terminal:

```sh
npm ci --prefix frontend
npm run dev --prefix frontend
```

Open the Vite URL printed in the terminal. Choose **Open workspace** and create a contractor account and a worker account to try both roles. Each password needs 10–128 characters. Copy the worker ID from their account. The contractor uses it to invite the worker, and the worker accepts the invitation before the contractor assigns work. The worker acknowledges the proposed rate before attendance can be posted. **Explore the demo** opens a separate sample workspace.

Vite proxies API calls to port 8000. Check `http://127.0.0.1:8000/health` for `status: ok` and `database: connected`. Interactive API documentation is at `/docs`. See the [assignment and wage rate API](docs/ASSIGNMENTS_API.md) and [ledger and dispute API](docs/LEDGER_API.md).

For a combined local build:

```sh
VITE_API_BASE_URL=/api npm run build --prefix frontend
python -m backend.serve
```

This validates configuration, runs migrations and serves the built frontend and `/api` from the same process. `PORT` defaults to 8000. `VITE_API_BASE_URL` is a public build setting; never put database or JWT secrets in any `VITE_` variable.

The migration runner records checksums, locks migration execution and fails if an applied file changes. Add new migrations rather than editing applied SQL. Databases initialized manually need a reviewed baseline before adopting this runner.

## Checks

```sh
python -m unittest discover -s backend/tests -v
npm run build --prefix frontend
```

Set `TEST_DATABASE_URL` to a disposable PostgreSQL database for the real integration suite. It creates/removes an isolated schema and requires schema-creation rights. Without it, database tests are explicitly skipped. Never use production data for tests.

The [release verification](docs/VERIFICATION_2026-11-29.md) records **50 automated tests** with no skips, seven successful signup assertions from the [Postman collection](docs/postman/signup.postman_collection.json), browser checks for both roles and public deployment smoke checks.

## Screenshots and walkthrough

![Contractor wage ledger with attendance and advance records](docs/release-evidence/2026-11-29/04-wage-ledger.png)

![Worker view of an open attendance dispute](docs/release-evidence/2026-11-29/05-worker-dispute.png)

[All screenshots](docs/release-evidence/2026-11-29) · [Two-minute MP4](docs/release-evidence/2026-11-29/Worker_Wage_Tracker.mp4) · [Free hosting and expiry](docs/DEPLOYMENT.md)

The recording runs through an invitation, an agreed wage rate, attendance posting, a wage dispute and reconciliation after the worker accepts a correction. It uses synthetic data against PostgreSQL.

## What I built and what I understood

I built the contractor and worker workflows with React, FastAPI and PostgreSQL. I learned why locking the worker-day record prevents duplicate attendance across worksites, and why calculating money in integer paise matters for half days and exports.

A rate snapshot keeps past attendance stable. Corrections retain the original entry and post a linked reversal. A worker can review a record without confirming that money was received, so each action has its own history.

## Fifteen-milestone record and launch materials

[BUILD_PLAN.md](docs/BUILD_PLAN.md) preserves all fifteen Track A milestones, planned dates and actual evidence. Commits use real timestamps. Track B remains separate. The [handover](docs/REMAINING_WORK.md) lists the remaining challenge and pilot work.

Unpublished LinkedIn drafts are available for [milestone 5](docs/LINKEDIN_MILESTONE_5_DRAFT.md), [milestone 10](docs/LINKEDIN_MILESTONE_10_DRAFT.md), [milestone 15](docs/LINKEDIN_MILESTONE_15_DRAFT.md), [calendar day 5](docs/LINKEDIN_CALENDAR_DAY_5_DRAFT.md), and [26 November](docs/LINKEDIN_2026-11-26_DRAFT.md). Publication requires explicit instruction. The single [24 November progress post](https://www.linkedin.com/feed/update/urn:li:activity:7530932552811925504/) does not count as separate milestone publications.
