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

Integer-paise wage and statement calculations now have eight passing unit tests, including the required earnings/advance/payment example, rounding, cutoffs and reversal arithmetic. Persistent attendance, wage agreements, advances/payments, uniqueness guarantees and disputes remain unimplemented; those end-to-end acceptance checks cannot pass. Browser end-to-end checks against the database-backed API and a full live deployment are also pending. The sample frontend showcase is not proof of those features.

## Migration handling

`python -m backend.migrate` applies each SQL file and checksum ledger entry in one transaction. Repeated runs skip unchanged migrations. Edited applied files cause an explicit error; add a new numbered migration for later changes. Databases created from earlier raw SQL need a reviewed baseline rather than automatic adoption. Migration checksums are computed on exact file bytes.

## Recorded evidence — 24 November 2026

[PostgreSQL CI run 45411066973](https://github.com/adityakudi/worker-wage-tracker/actions/runs/45411066973) passed 25 tests with no skips and built the frontend at commit 7d770721bc04ecfd4e9a7b72caa333d91e10f6a9. The expanded wage suite adds eight checks; local execution passed 22 with 11 database checks skipped because this execution environment denies server socket creation. Refer to the current commit's Actions run for the combined result.
