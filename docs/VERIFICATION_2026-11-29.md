# Release verification — 29 November 2026

[Source commit](https://github.com/adityakudi/worker-wage-tracker/commit/61efb8408bf6c85e414fe16a66e7dc38d23f08c2) · [GitHub API and container checks](https://github.com/adityakudi/worker-wage-tracker/actions/runs/46181286352) · [Browser and media checks](https://github.com/adityakudi/worker-wage-tracker/actions/runs/46181286351) · [Saved capture commit](https://github.com/adityakudi/worker-wage-tracker/commit/935ff6abf3a77899a5744cfc897ebb69a67dfce5)

- All 50 automated tests passed with no skips. Real PostgreSQL checks included concurrent duplicate attendance, rate snapshots, pending rates, disbursement retries, separate receipt confirmation, concurrent reversals, immutable audit history, participant isolation, and statement reconciliation.
- Seven Postman collection assertions passed with Newman. Signup rejected invalid and repeated credentials. Login returned the expected synthetic identity.
- Real browser sessions exercised both roles, including worksite create/search/detail/edit/delete, an accepted invitation, assignment and worker-approved rate, attendance, an advance and a disputed attendance correction. The outstanding amount stayed ₹500 until the worker accepted the correction. The resulting closing balance was ₹200 in both the UI and the CSV. Mobile Hindi login also passed.
- The saved evidence includes seven browser screenshots and a captioned, two-minute MP4 recorded against the production image and disposable PostgreSQL. [Media folder](https://github.com/adityakudi/worker-wage-tracker/tree/935ff6abf3a77899a5744cfc897ebb69a67dfce5/docs/release-evidence/2026-11-29)
- Render deployed the verified code on the approved free web service. Public HTTPS checks confirmed the built frontend, PostgreSQL-connected health, protected routes, and a fresh browser signup/login/worksite session. [Public app](https://worker-wage-tracker-wg8y.onrender.com/#live)

Browser checks exposed a missing React import in the first workspace rewrite. The corrected commit passed the full flow. Local startup also exposed a virtual-environment interpreter mismatch, fixed by launching Uvicorn through the active Python interpreter.

The application software was verified on 29 November 2026. Challenge posts and real participant validation remain open. The superseded 26 November progress recording is kept as historical evidence.
