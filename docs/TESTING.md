# Test coverage and verification

## Running the checks

Install `backend/requirements-dev.txt`. From repository root:

```sh
python -m unittest discover -s backend/tests -v
```

For real database checks, export `TEST_DATABASE_URL` pointing to a reachable PostgreSQL database and rerun the same command. The suite creates a unique schema, routes its connections through that search path, and removes it on completion. It requires schema-creation rights. Do not use a production connection for test work.

The CI workflow `.github/workflows/verify.yml` provisions a disposable PostgreSQL 16 service. Its credentials are test-only and do not configure production.

## Coverage

- Validated signup, Argon2 storage, successful JWT identity lookup, normalized duplicate email, wrong passwords and unknown emails.
- Missing, malformed and expired tokens; deleted account token rejection.
- Worksite CRUD success, cross-contractor denial, search, active filter and pagination.
- Invitation duplicate checks, participant-only listing, invitee-only acceptance and repeat-accept rejection.
- Live DB health, unavailable database 503, safe error messages and repeatable migrations.

## Outstanding coverage

Integer-paise wage and statement calculations have eight passing unit tests, including the required earnings/advance/payment example, rounding, cutoffs and reversal arithmetic. Wage agreement APIs now have PostgreSQL coverage. Persistent attendance/rate snapshots, advances/payments, attendance uniqueness and disputes remain unimplemented; those end-to-end acceptance checks cannot pass. Browser end-to-end checks against the database-backed API and a full live deployment are also pending. The sample frontend showcase is not proof of those features.

## Migration handling

`python -m backend.migrate` applies each SQL file and checksum ledger entry in one transaction. Repeated runs skip unchanged migrations. Edited applied files cause an explicit error; add a new numbered migration for later changes. Databases created from earlier raw SQL need a reviewed baseline rather than automatic adoption. Migration checksums are computed on exact file bytes.

## Production routing and image checks — 25 November 2026

Four additional tests cover frontend/static asset serving, authentication on original and `/api` routes, unknown/private path 404s, and database health failure through the static mount. The workflow also builds the non-root production image, starts it against disposable PostgreSQL, runs `scripts/smoke_deployment.py --exercise-api`, restarts it and repeats read-only smoke checks. Those HTTP checks cover real packaged signup/login, identity, worksite CRUD/search/ownership and invitation acceptance. They do not execute a browser or unimplemented financial workflows. See [DEPLOYMENT.md](DEPLOYMENT.md) for usage and write-mode restrictions.

Eight more PostgreSQL checks verify accepted-membership and active-site prerequisites, assignment visibility/search/filter/pagination, strict money/date validation, proposal chronology, worker-only acknowledgement, retained immutable history, database-level cross-owner rejection, worksite retention/archiving and concurrent same-date proposals. The container smoke flow also exercises assignment and wage acknowledgement.

[CI run 45636316651](https://github.com/adityakudi/worker-wage-tracker/actions/runs/45636316651) passed **45 tests with no skips**, including nineteen PostgreSQL integration checks, then passed frontend build, production-image boot, HTTP smoke flow and restart. See [the evidence record](VERIFICATION_2026-11-25.md). Local execution passed 26 checks and skipped the nineteen database checks; Docker is unavailable locally, so container acceptance was verified in CI.

## Recorded evidence — 24 November 2026

[PostgreSQL CI run 45411066973](https://github.com/adityakudi/worker-wage-tracker/actions/runs/45411066973) passed 25 tests with no skips and built the frontend at commit 7d770721bc04ecfd4e9a7b72caa333d91e10f6a9. The expanded wage suite adds eight checks; local execution passed 22 with 11 database checks skipped because this execution environment denies server socket creation. Refer to the current commit's Actions run for the combined result.
