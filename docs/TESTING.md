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

Attendance, wage snapshots/calculations, advances, payments, ledger reversals and disputes are not yet implemented, so their acceptance checks cannot pass. Browser end-to-end checks against the database-backed API and a full live deployment are also pending. The sample frontend showcase is not proof of those features.

## Migration handling

`python -m backend.migrate` applies each SQL file and checksum ledger entry in one transaction. Repeated runs skip unchanged migrations. Edited applied files cause an explicit error; add a new numbered migration for later changes. Databases created from earlier raw SQL need a reviewed baseline rather than automatic adoption. Migration checksums are computed on exact file bytes.
