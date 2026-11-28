# Combined frontend and API deployment

Status, 29 November 2026 (Asia/Kolkata): the free web service and PostgreSQL 16 are live. [Public workspace](https://worker-wage-tracker-wg8y.onrender.com/#live)

## Infrastructure

`render.yaml` defines one Docker web service and one PostgreSQL 16 database in Singapore. Both explicitly use `plan: free`; the database permits internal connections only. Render generates `JWT_SECRET` and supplies the internal `DATABASE_URL` through the database reference. Neither secret belongs in source control or frontend build variables.

The Docker build uses Node 22 to compile React with `VITE_API_BASE_URL=/api`. Its Python 3.12 runtime runs as an unprivileged user. FastAPI serves only built frontend assets at `/` and handles API routes under `/api`; `/health` returns 200 only after a real database query succeeds. Missing files and unknown API routes return 404 instead of the landing page.

`python -m backend.serve` validates configuration and built assets, applies tracked migrations, then replaces its process with Uvicorn on `0.0.0.0:$PORT` (default 8000). Migration failure stops startup. This avoids a paid pre-deploy hook. The migration runner locks and checksums migrations; do not edit an already applied migration or point this at an unreviewed manually initialized database.

## Approved deployment

My Workspace was confirmed and the reviewed Blueprint was approved. Render provisioned one free web service and one free PostgreSQL database in Singapore. The release deployment is `dep-dc5io6tbedkc73eq4sdg`. Render checks the GitHub status before automatically deploying later main-branch changes.

## Verification

From repository root, run checks on the actual service origin after deployment:

```sh
python scripts/smoke_deployment.py --url https://<actual-service-hostname>
```

This default mode is read-only: it verifies database-connected health, the frontend and its built assets, unauthenticated API rejection, unknown-route 404s and private source-file boundaries. It does not prove browser interactions or all requirements.

CI uses a disposable PostgreSQL service and builds this exact Dockerfile. It starts the image, waits for `/health`, runs the same script with `--exercise-api`, restarts the image, then repeats read-only checks. The write mode creates three synthetic accounts, an accepted invitation, an assignment and an acknowledged wage agreement. It deletes an unassigned temporary worksite, but retains the assigned worksite and its history. **Use write mode only against a disposable test database.** It verifies signup/login/identity, worksite CRUD/search/ownership, invitation acceptance and assignment/rate acknowledgement over the production HTTP paths.

The public release passed these read-only checks and a new browser session exercised the sign-in and worksite flow with a synthetic account. [Release verification](VERIFICATION_2026-11-29.md)

## Local container run

Provide a fresh, reachable PostgreSQL connection and a random JWT secret of at least 32 characters in environment variables, then:

```sh
docker build -t worker-wage-tracker .
docker run --rm -p 8000:8000 --env DATABASE_URL --env JWT_SECRET worker-wage-tracker
```

`localhost` inside the container identifies the container, not the host database. Use a database address reachable from Docker. Open `http://localhost:8000`, choose **Open workspace**, and inspect `http://localhost:8000/health`.

## Free hosting

Render lists the database expiration as **29 December 2026, 12:50 a.m. IST** (28 December 2026, 19:20 UTC). Free services may also go to sleep after inactivity. Use synthetic records for the public prototype and export statements before the database expires. No paid plan was selected. [Render free hosting details](https://render.com/docs/free)
