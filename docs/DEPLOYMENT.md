# Combined frontend and API deployment

Status, 25 November 2026 (Asia/Kolkata): configuration prepared; **public deployment is blocked**. No verified public application URL exists yet. The private frontend showcase is separate.

## Infrastructure

`render.yaml` defines one Docker web service and one PostgreSQL 16 database in Singapore. Both explicitly use `plan: free`; the database permits internal connections only. Render generates `JWT_SECRET` and supplies the internal `DATABASE_URL` through the database reference. Neither secret belongs in source control or frontend build variables.

The Docker build uses Node 22 to compile React with `VITE_API_BASE_URL=/api`. Its Python 3.12 runtime runs as an unprivileged user. FastAPI serves only built frontend assets at `/` and handles API routes under `/api`; `/health` returns 200 only after a real database query succeeds. Missing files and unknown API routes return 404 instead of the landing page.

`python -m backend.serve` validates configuration and built assets, applies tracked migrations, then replaces its process with Uvicorn on `0.0.0.0:$PORT` (default 8000). Migration failure stops startup. This avoids a paid pre-deploy hook. The migration runner locks and checksums migrations; do not edit an already applied migration or point this at an unreviewed manually initialized database.

## Access blocker

The connected Render account returned one workspace named **My Workspace**, but `list_services` rejected the request because no workspace is selected. The connector explicitly requires user confirmation before choosing a workspace. No confirmation is recorded, so no workspace selection, resource creation or deployment was performed in this run.

After that confirmation, inspect existing services/databases before provisioning to avoid duplicate resources. Free-tier eligibility and limits still need account-level verification. Apply the repository Blueprint, review a plan containing only free resources, then inspect build/deploy events and database-connected health. `autoDeployTrigger: checksPass` limits later automatic deploys to passing CI revisions.

## Verification

From repository root, run checks on the actual service origin after deployment:

```sh
python scripts/smoke_deployment.py --url https://<actual-service-hostname>
```

This default mode is read-only: it verifies database-connected health, the frontend and its built assets, unauthenticated API rejection, unknown-route 404s and private source-file boundaries. It does not prove browser interactions or all requirements.

CI uses a disposable PostgreSQL service and builds this exact Dockerfile. It starts the image, waits for `/health`, runs the same script with `--exercise-api`, restarts the image, then repeats read-only checks. The write mode creates three synthetic accounts, an accepted invitation, an assignment and an acknowledged wage agreement. It deletes an unassigned temporary worksite, but retains the assigned worksite and its history. **Use write mode only against a disposable test database.** It verifies signup/login/identity, worksite CRUD/search/ownership, invitation acceptance and assignment/rate acknowledgement over the production HTTP paths.

Before marking milestone 14 done, record the deployed commit, real public URL, successful live checks and a browser signup/login/worksite flow from another user/session. Capture meaningful failures and fixes. A passing CI container is deployment preparation, not public-hosting evidence.

## Local container run

Provide a fresh, reachable PostgreSQL connection and a random JWT secret of at least 32 characters in environment variables, then:

```sh
docker build -t worker-wage-tracker .
docker run --rm -p 8000:8000 --env DATABASE_URL --env JWT_SECRET worker-wage-tracker
```

`localhost` inside the container identifies the container, not the host database. Use a database address reachable from Docker. Open `http://localhost:8000`, choose **Open workspace**, and inspect `http://localhost:8000/health`.

## Free-hosting limits and remaining work

Render's current free-hosting documentation says free web services spin down after 15 idle minutes and free PostgreSQL databases expire after 30 days. Plan exports before expiration; this free setup is for a prototype, with sample data. Do not silently upgrade plans or add payment details to overcome limits.

Assignments and acknowledged wage agreements have passing PostgreSQL and container HTTP checks. Their UI, persistent attendance and ledger entries, reversals, disputes, full browser verification and pilot validation are still missing. Hosting the existing subset cannot satisfy those acceptance checks. See [25 November verification](VERIFICATION_2026-11-25.md).

References checked 25 November 2026: [Blueprint specification](https://render.com/docs/blueprint-spec), [JSON schema](https://render.com/schema/render.yaml.json), [free hosting](https://render.com/docs/free), [health checks](https://render.com/docs/health-checks), [deploys](https://render.com/docs/deploys). The Blueprint passed local JSON-schema validation; Render account-level planning/application remains blocked.
