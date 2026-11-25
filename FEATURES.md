# Worker Attendance & Wage Tracker

Day 1 — ALTA BUILDER 30, Track A

## Problem statement
This project will help small contractors and daily-wage workers maintain a shared record of attendance, agreed wage rates, advances, and payments. The problem hypothesis is that scattered paper records and messages make it difficult to reconcile amounts and resolve disagreements. We will validate this with one contractor and two or three workers before treating demand as established. The first release will support one small pilot, with a simple mobile-friendly interface in English and Hindi.

## Roles
- Contractor: creates worksites, invites workers, agrees wage rates, records attendance and payments, and responds to disputes.
- Worker: sees only their own assignments and records, acknowledges entries, raises disputes, and downloads statements.

## MVP: 10 must-have features
1. Signup and login with hashed passwords and protected, role-based access.
2. Contractor-managed worksites with name, location text, and active status.
3. Worker invitations and membership acceptance. A contractor cannot link an arbitrary existing account without acceptance.
4. Worksite assignments with an explicit daily wage, effective date, and worker acknowledgement.
5. Daily attendance with absent, half-day, and full-day options, plus date and notes.
6. Wage calculation from attendance and the rate effective on the work date.
7. Separate records for advances, wage payments, and reversal entries.
8. Worker and contractor dashboards with search, date filters, pagination, and balances.
9. Worker acknowledgement and dispute workflow with contractor response and an activity history.
10. Downloadable monthly CSV statements showing earnings, payments, advances, and closing balance.

## Heavy feature: Days 11–12
Build acknowledgement and dispute resolution end to end. A worker can acknowledge an entry or dispute it with a reason. A contractor can respond and propose a correction; the worker confirms resolution. Corrections retain the original record, reason, author, and timestamp. Pending disputes remain visible and do not silently remove amounts from the recorded ledger.

## Calculation and integrity rules
- Store INR amounts as integer paise. No floating-point money arithmetic.
- Day units are 0, 0.5, or 1. Round half-day earnings to the nearest paise, with halves rounded up.
- Prevent duplicate attendance for the same worker and date within a contractor account, including across worksites. Splitting a day across sites is outside the MVP.
- Snapshot the applicable wage rate on each attendance entry. Later rate changes do not rewrite prior earnings.
- Closing balance = opening balance + earnings − advances paid − wage payments + signed adjustment amounts. A negative balance means recorded payments exceed earned wages.
- An advance is an actual disbursement and reduces the balance once. Do not deduct it again as a separate recovery.
- Opening balance is an explicit dated adjustment. Historical statements include all prior posted entries when calculating opening balance.
- Only posted records affect balances. Draft rate changes awaiting agreement cannot generate posted attendance.
- Acknowledgement confirms review, not payment receipt. Payment receipt confirmation is a separate worker action.
- Posted attendance and financial entries cannot be hard-deleted. Correct them through linked reversals and replacement entries.
- No future attendance. Use Asia/Kolkata work dates and retain timestamps in UTC.
- Enforce ownership on the server for every record and export. Never expose another worker's wages through a team endpoint.

## Suggested implementation
- Frontend: React with Vite, responsive forms, English/Hindi text.
- Backend: FastAPI with input validation and JWT authentication.
- Database: PostgreSQL with migrations and relational constraints.
- Main entities: users, contractor memberships, worksites, assignments, wage agreements, attendance, ledger entries, disputes, and audit events.
- Core financial workflow is the priority. No bank integration is required.

## Later features
SMS/WhatsApp notifications, offline synchronisation, voice entry, additional languages, overtime, hourly wages, split-site attendance, online payments, and native mobile apps. Statutory payroll, tax calculations, and legal wage compliance automation are outside this MVP.

## Acceptance checks
- A worker cannot read another worker's attendance, payments, or statement.
- A contractor cannot access another contractor's worksites or ledger.
- Three full days and one half-day at ₹600/day earn ₹2,100. After a ₹500 advance and ₹1,000 payment, the outstanding balance is ₹600.
- Changing the rate for tomorrow leaves yesterday's earnings unchanged.
- A duplicate attendance submission is rejected, including concurrent requests.
- A reversal preserves the original entry and restores its effect exactly once.
- A disputed entry is clearly flagged, with its recorded amount and dispute status shown separately.
- CSV statement totals reconcile with dashboard balances for the same cutoff date.

## Validation before pilot
Ask one contractor and two or three workers how they record attendance, agree rates, track advances, resolve disagreements, and access smartphones. Use sample data until pilot participants agree to participate. Record findings without inventing interviews or outcomes.

## Challenge delivery plan
- Day 1: feature specification and new repository.
- Day 2: database schema and four wireframes: login, attendance list, worker detail, dashboard.
- Day 3: backend, database connection, environment configuration, and /health.
- Days 4–5: signup, login, JWT, and protected routes.
- Days 6–7: authenticated CRUD, related entities, search, filtering, and pagination.
- Days 8–10: frontend authentication, list/detail screens, and create/edit/correction flows.
- Days 11–12: acknowledgement and dispute workflow, backend then UI.
- Day 13: main-flow verification, validation, and at least five API tests, including money and access-control checks.
- Day 14: deploy frontend, backend, and database; verify public access.
- Day 15: README, screenshots, run steps, two-minute demo, and launch post.
- Every challenge day: a genuine GitHub commit. Days 5, 10, 15: LinkedIn posts with #ALTABuilder30 and @ALTA School of Technology.
- README includes “What I built and what I understood”.

## Current status
As of 25 November 2026: authentication, worksite CRUD, invitations and integer-paise calculation rules have automated verification. Deployment configuration is prepared, but public deployment is blocked on Render workspace confirmation. Assignments, acknowledged wage agreements, persistent attendance/ledger/disputes and user validation remain pending. See README.md and docs/BUILD_PLAN.md for current evidence. Repository: https://github.com/adityakudi/worker-wage-tracker. No previous project's code or progress is being reused.
