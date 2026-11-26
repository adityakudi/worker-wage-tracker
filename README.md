# Worker Attendance & Wage Tracker

A fresh React/FastAPI/PostgreSQL project for shared work and wage records between daily-wage workers and small contractors.

**Status — 26 November 2026: partial build, not launched.** Authentication and worksite management work in the live UI. Accepted invitations, assignments and immutable wage agreements work through the API. Persistent attendance, payments, reversals, disputes and relationship-management UI remain unfinished. Public deployment is blocked on Render workspace confirmation. The original Track A completion target has not been met.

## Problem and users

The problem hypothesis is that scattered paper records and messages make it difficult to reconcile work, rates and money owed. Contractors manage their own worksites and invite workers; workers review only their own records. Demand still needs validation with one contractor and two or three consenting workers. No interviews or pilot outcomes are claimed.

## Features and implementation boundaries

| Feature | Current implementation |
|---|---|
| Signup/login | Argon2 hashes, JWT expiry/issuer/audience, role checks, in-memory frontend token |
| Worksites | Live UI and authenticated CRUD/search/pagination API with contractor ownership |
| Worker invitations | Participant-only API and worker-only acceptance |
| Assignments | API requires accepted membership and an owned active worksite |
| Wage agreements | API uses positive integer paise, ordered effective dates and immutable worker acknowledgement |
| Money arithmetic | Tested integer-paise helpers, half-day rounding and statement cutoffs; no persisted financial flow |
| Attendance/payments/reversals | Planned; showcase uses labelled sample data |
| Disputes/audit and monthly CSV | Planned; sample CSV is not a real worker statement |
| English/Hindi interface | Planned; current interface is English |

The [canonical feature specification](FEATURES.md) retains the full ten-feature MVP and acceptance rules. [Remaining work](docs/REMAINING_WORK.md) gives the implementation order.

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

Open the Vite URL printed in the terminal. Choose **Open workspace** for real signup/login/worksite forms, or **Explore the demo** for the separate sample-data design preview. Passwords require 10–128 characters. Create a contractor account to manage worksites; the worker UI currently displays an honest placeholder.

Vite proxies API calls to port 8000. Check `http://127.0.0.1:8000/health` for `status: ok` and `database: connected`. Interactive API documentation is at `/docs`. See [assignment/rate routes](docs/ASSIGNMENTS_API.md).

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

The [26 November verification](docs/VERIFICATION_2026-11-26.md) records **45 passing tests with no skips**, including nineteen PostgreSQL checks, plus production-image boot, HTTP smoke and restart verification. The [browser capture workflow](.github/workflows/capture-demo.yml) also passed real signup/login, persisted worksite CRUD and worker signup, with no browser page errors. It produced six screenshots and a verified 120-second partial-build recording.

Read-only deployment checks use `python scripts/smoke_deployment.py --url https://ACTUAL-HOST`. The optional `--exercise-api` mode creates synthetic fixtures and is strictly for disposable test databases. Full financial-flow testing remains open.

## Screenshots, recording and deployment

The [four wireframes](docs/WIREFRAMES.md) are planned designs, not implementation screenshots. The [showcase](docs/SHOWCASE.md) and its earlier one-minute video are sample-data design demonstrations. The [two-minute recording script](docs/DEMO_SCRIPT.md) covers only the implemented live authentication/worksite subset and clearly states missing features.

[Watch/download the two-minute progress recording](docs/demo/Worker_Wage_Progress_2026-11-26.mp4). It is silent, captioned, and uses synthetic accounts against the real container/database. [Capture metadata](docs/demo/capture.json) records the source commit. These are actual browser screenshots, not wireframes:

![Live sign-in screen](docs/screenshots/02-sign-in.png)

![Created worksite retrieved from the live API](docs/screenshots/04-created-worksite.png)

![Worker account showing financial views are unfinished](docs/screenshots/06-worker-account.png)

All six captures are in [docs/screenshots](docs/screenshots). Captions were overlaid for explanation; application/API responses were not mocked.

No verified public application URL exists. The [free Render Blueprint and blocker](docs/DEPLOYMENT.md) describe deployment preparation, generated secrets and database health checks. No paid hosting has been purchased. Container CI is not proof of public hosting or independent-user access.

## What I built and what I understood

I built a new requirements baseline, schema design and four wireframes; secure accounts; owned worksite APIs and forms; accepted invitations; assignments; and worker-acknowledged wage terms. I learned to enforce ownership in server queries and composite database keys, keep immutable historical terms, and verify packaged startup and migration replay rather than only isolated functions.

The financial design separates review acknowledgement from payment receipt. Rate snapshots and linked reversals must preserve history, but those persistent attendance/ledger workflows are not implemented yet. Arithmetic tests and attractive sample screens cannot establish that the money-recording product works end to end.

## Fifteen-milestone record and launch materials

[BUILD_PLAN.md](docs/BUILD_PLAN.md) preserves all fifteen Track A milestones, planned dates and actual evidence. Commits use real timestamps. Track B remains separate. The [handover](docs/REMAINING_WORK.md) lists the missed requirements and challenge-evidence gaps.

Unpublished LinkedIn drafts are available for [milestone 5](docs/LINKEDIN_MILESTONE_5_DRAFT.md), [milestone 10](docs/LINKEDIN_MILESTONE_10_DRAFT.md), [milestone 15](docs/LINKEDIN_MILESTONE_15_DRAFT.md), [calendar day 5](docs/LINKEDIN_CALENDAR_DAY_5_DRAFT.md), and [26 November](docs/LINKEDIN_2026-11-26_DRAFT.md). Publication requires explicit instruction. The single [24 November progress post](https://www.linkedin.com/feed/update/urn:li:activity:7530932552811925504/) does not count as separate milestone publications.
