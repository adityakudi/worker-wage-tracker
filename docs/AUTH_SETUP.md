# Authentication setup

Install backend/requirements.txt and install httpx to run tests. Export DATABASE_URL and a random JWT_SECRET of at least 32 characters. Apply backend/migrations/001_users.sql once using psql. From repository root run `uvicorn backend.main:app`.

POST /auth/signup: email, password (10–128 characters), role (worker or contractor). POST /auth/login: email and password. GET /auth/me: Bearer token. Password hashes never appear in returned user data. Tokens expire after 30 minutes.

Verified 19 November: five unittest checks passed. Run `python -m unittest discover -s backend/tests -v`. Database-backed success paths remain unverified. PostgreSQL provisioning is still needed; do not substitute an in-memory user store.
