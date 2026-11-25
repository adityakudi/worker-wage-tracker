# 15-Day Milestone Plan

ALTA BUILDER 30 — Track A: Worker Attendance & Wage Tracker

The day numbers below identify the sheet's fifteen milestones. Work may be completed ahead of schedule, with several milestones on one actual date. Commit timestamps and completion dates remain accurate.

| Day milestone | Phase | Work | Evidence required | Status |
|---|---|---|---|---|
| 1 | Plan | Define the problem, contractor and worker roles, ten MVP features, later features, and acceptance rules. | FEATURES.md and new GitHub repository | Done |
| 2 | Design | Design PostgreSQL tables, relationships, constraints, and login, list, detail, dashboard wireframes. | Schema diagram and four wireframes in docs/ | Done — 25 November 2026 |
| 3 | Setup | Initialise backend, connect PostgreSQL, configure environment variables, and add health endpoint. | Running backend and database-connected /health | Done |
| 4 | Signup | Implement user model, validation, password hashing, and signup. | Signup verified in Postman | In progress |
| 5 | Login | Implement JWT login and role-protected routes. | 401 without valid token, authorised data with token; progress post | Done |
| 6 | CRUD | Implement authenticated worksite create, read, update, and delete APIs. | Four CRUD operations with ownership checks | Done |
| 7 | Relationships | Add memberships, assignments, wage agreements, and search/filter/pagination. | Related entity APIs and paginated lists | Done — 25 November 2026 |
| 8 | Frontend auth | Set up React routing/layout and connect signup/login forms. | Signup and login usable from browser | In progress |
| 9 | Lists and details | Connect worksite, worker, and record list/detail pages to live APIs. | Live data with loading, empty, and error states | In progress |
| 10 | Management flows | Build create/edit/delete flows, attendance, advances, and payments; use reversals for posted ledger corrections. | CRUD usable from UI; progress post | In progress |
| 11 | Heavy feature backend | Implement acknowledgement, disputes, responses, correction proposals, and immutable audit records. | Heavy feature backend verified | Not started |
| 12 | Heavy feature UI | Connect worker dispute and contractor response screens; worker confirms resolution. | Complete end-to-end dispute demonstration | Not started |
| 13 | Testing | Test main flows and bad input; cover wage maths, access isolation, duplicate attendance, reversals, and disputes. | At least five passing API tests and resolved main-flow bugs | In progress |
| 14 | Deployment | Deploy frontend, backend, and PostgreSQL on free hosting; configure secrets through environment. | Public URL verified for another user | In progress — workspace confirmation blocked |
| 15 | Ship | Write README run steps and learning section, add screenshots, record two-minute demo, and prepare launch post. | README, screenshots, real demo video, and published LinkedIn link | Not started |

## Progress and evidence

Day 1 specification: [requirements commit](https://github.com/adityakudi/worker-wage-tracker/commit/c375aacc9331473f2c6f259732cd45d75b3467a3), completed 17 November 2026 (Asia/Kolkata). No application code had been implemented at that point.

Update each milestone only after checking its deliverables. Record its actual completion date and commit URL here. Future commits must contain real work, with no fabricated or backdated history.

## Challenge requirements

- Commit genuine work each actual build day; the challenge's daily commit requirement continues to apply to its calendar.
- Prepare progress posts at milestones 5 and 10 and a launch post with the demo at milestone 15. Include #ALTABuilder30 and tag @ALTA School of Technology.
- Also maintain the challenge's every-five-calendar-days post cadence. If starting 17 November, the first dates are 21 and 26 November.
- Store actual published LinkedIn URLs as evidence. A draft does not count as publication.
- README must include screenshots, features, stack, run steps, and “What I built and what I understood”.
- Continue the daily DSA requirement separately. Eligibility, grace-day rules, and final verification remain with the challenge organisers.
- Track B is a separate AI product on sheet milestones 16–30. This Track A plan does not complete Track B or establish thirty days of participation.

## Milestone adaptations

This original project follows the sheet's full-stack milestones. Its main CRUD entity is the worksite. Its heavy feature is worker acknowledgement and dispute resolution. Financial records retain corrections through reversals; delete demonstrations use eligible editable records. Posted attendance or ledger history must never be silently deleted.

## 19 November 2026
Authentication implemented with Argon2 hashes, JWT expiry/issuer/audience verification, and database-backed identity lookup. Five auth checks passed. Successful database signup/login, role-specific route tests, full migrations and visual wireframes remain pending; milestones 2–5 remain in progress.

## 20 November 2026
Added contractor-owned worksite CRUD, bounded pagination, search and active filtering, migration 002 and access/validation tests. PostgreSQL success-path integration remains pending. Milestone 6 is in progress; milestone 7 relationships remain pending.

## 21 November 2026
Added React/Vite authentication forms, role-aware layout, API-backed contractor worksite search/pagination and detail view. Tokens stay in memory and clear on sign out/401. Worker financial screens, dedicated routing, browser end-to-end checks and database integration remain pending. Milestones 8–9 remain in progress.

## 22 November 2026
Added API-backed worksite create/edit/delete forms with confirmation, loading/error states and list refresh. Fixed 204 response handling so successful deletion does not attempt JSON parsing. Attendance/payments and their membership/wage prerequisites remain unimplemented; milestone 10 remains in progress. Database success-path and browser end-to-end verification remain pending.

## 23 November 2026
Implemented authenticated worker invitation/list/accept APIs and membership migration with unique contractor/worker pairs. Acceptance requires the invited worker, and list queries restrict rows to participants. Added three access checks. Membership success paths still require PostgreSQL integration. Assignments, wage agreements, attendance, ledger and dispute workflow remain pending; milestones 11–12 were not completed.

## 24 November 2026 — showcase request
Redesigned the frontend and added an interactive sample-data showcase, preserving API-connected screens. Production build and browser interaction checks passed. Created a motion showcase from actual frontend captures. This does not mark backend financial workflows or milestone 13 complete. See SHOWCASE.md for verification and limitations.

Published LinkedIn progress post: https://www.linkedin.com/feed/update/urn:li:activity:7530932552811925504/ (ALTA tagged). This single post is evidence of a progress update, not three separate milestone publications.

## 24 November 2026 — verification
Added an atomic migration runner with a checksum ledger and advisory lock, eleven PostgreSQL integration tests, two database error tests and a PostgreSQL-backed GitHub Actions job. Existing migration transaction wrappers were moved into the runner to keep schema and ledger writes atomic. Database connection failures now return a sanitized 503. The temporary PostgreSQL package could not start because socket creation is denied in this local execution environment. Local integration checks are skipped; remote CI results must be inspected before claiming they passed. Milestone 13 remains in progress because financial/dispute flows are still absent.

### Verified database evidence
The PostgreSQL-backed CI run [45411066973](https://github.com/adityakudi/worker-wage-tracker/actions/runs/45411066973) passed all 25 API/unit checks without skips and built the frontend. It ran source commit [7d77072](https://github.com/adityakudi/worker-wage-tracker/commit/7d770721bc04ecfd4e9a7b72caa333d91e10f6a9). This supersedes earlier notes that database success paths were unverified. Milestones 3, 5 and 6 now have database-backed acceptance evidence; milestone 5 also has the published LinkedIn URL recorded above. Signup is API-tested, but milestone 4's explicit Postman execution remains pending.

Added integer-paise wage rules and eight tests covering the specification's INR 600 outstanding example, half-paise rounding, advances counted once, negative opening balances, inclusive cutoffs, invalid inputs and reversal arithmetic. These functions are not yet wired to persistent attendance/payment APIs. Local checks: 22 passed, 11 PostgreSQL checks skipped locally; the preceding remote PostgreSQL run passed those 11. The expanded CI suite must be checked on the new commit. Milestone 13 remains in progress, with unfinished financial/dispute features explicitly open.

## Actual execution schedule

These dates group work into ten calendar days while retaining all fifteen milestones above. They are targets, not claims of completion.

| Actual date in 2026 | Planned milestones |
|---|---|
| 17 November | 1 — requirements |
| 18 November | 2–3 — schema, four wireframes, setup and database health |
| 19 November | 4–5 — signup, hashing, JWT and protected routes |
| 20 November | 6–7 — authenticated CRUD, relationships and paginated search |
| 21 November | 8–9 — frontend authentication and live lists/details |
| 22 November | 10 — management, attendance and payment UI |
| 23 November | 11–12 — acknowledgement and dispute backend/UI |
| 24 November | 13 — tests and fixes |
| 25 November | 14 — deploy and verify |
| 26 November | 15 — README, screenshots, two-minute demo and launch materials |

## 25 November 2026 — deployment preparation

Prepared a multi-stage, non-root Docker image with the built React frontend, FastAPI API under `/api`, environment-driven startup and atomic migrations before serving traffic. Existing development API paths remain supported. Added four static/API boundary checks and a production-image HTTP smoke script. CI now builds and boots the image against disposable PostgreSQL, exercises authenticated worksite and invitation flows, then restarts it to check migration replay and readiness.

Local verification: 26 tests passed; eleven database integration checks were explicitly skipped because no local PostgreSQL service is available. Frontend production build passed. `render.yaml` passed validation against Render's published JSON schema. The new container/database CI checks are pending until their Actions run is inspected.

Render access is available, but service inventory was rejected because no workspace is selected. The connector requires the user to confirm a workspace; the sole returned option is **My Workspace**. No workspace was chosen automatically, no infrastructure was created and no paid plan was requested. See [DEPLOYMENT.md](DEPLOYMENT.md). Milestone 14 stays in progress until a public frontend/API/database deployment and independent-user access are verified.

Carry-forward gaps: milestone 2 visual design evidence, milestone 4 Postman execution, assignment/wage agreements, persistent attendance/advances/payments/reversals, disputes and full browser flows remain unfinished. The 26 November target is at risk; missing work must not be relabelled complete for the deadline. Track B remains separate.

### Carry-forward relationship implementation

Added migration 004 and participant-scoped assignment and wage agreement APIs. Assignments require accepted membership and an owned active worksite. Composite ownership keys reject cross-contractor relationships. Rate proposals use strict integer paise and increasing ISO effective dates; only the assigned worker can acknowledge, and database guards retain immutable rate/acknowledgement history. Assigned worksites return 409 on deletion and can be archived instead. See [ASSIGNMENTS_API.md](ASSIGNMENTS_API.md).

Added eight PostgreSQL acceptance checks, including concurrent same-date proposals, and expanded the production smoke flow for assignments and rate acknowledgement. Local run: 26 passed, 19 database checks skipped; remote CI must pass before milestone 7 is marked complete. The preceding deployment-only CI run [45635095940](https://github.com/adityakudi/worker-wage-tracker/actions/runs/45635095940) passed at commit [62f0777](https://github.com/adityakudi/worker-wage-tracker/commit/62f07771de2c71578fabfe160265f0aa4fc207d0), including container startup, HTTP flows and restart. The first run exposed an empty-204 parsing error in the smoke script, which was corrected before that passing run.

This carries assignments and wage agreements out of the earlier implementation gap once verified; attendance posting/rate snapshot integration, ledger, disputes and their UI remain open. All four requested LinkedIn drafts are now present, with accurate limitations and no new publication. The calendar-day-5 draft is labelled retrospective rather than backdated.

### Verified acceptance and design evidence

[CI run 45636316651](https://github.com/adityakudi/worker-wage-tracker/actions/runs/45636316651) passed source [e3476b3](https://github.com/adityakudi/worker-wage-tracker/commit/e3476b31c605d35475d1916b7ee98351c496a0c3): **45 tests, no skips**, including nineteen real PostgreSQL checks. The production container build, migration startup, frontend/API smoke flow, assignment/rate acknowledgement and restart checks also passed. This supersedes the pending-check notes above. Milestone 7 is complete at API level on 25 November; its UI remains separate work under milestones 9–10.

Created and rendered four SVG wireframes for login, attendance list, worker detail and dashboard, and visually checked all four for legible layout. They show proposed states and sample amounts, not implemented financial screens. Together with the schema diagram and constraint design in DATABASE_SCHEMA.md, these complete milestone 2's design evidence on 25 November. [WIREFRAMES.md](WIREFRAMES.md) links the assets. See [full verification record](VERIFICATION_2026-11-25.md).

Remaining: milestone 4 Postman execution; full frontend/browser relationship flows; persistent attendance and ledger with snapshots, uniqueness and reversals; disputes/audit workflow; public deployment and independent-user access; pilot validation; real two-minute end-to-end product demo. Milestones 13–15 remain incomplete. No paid resources or new LinkedIn publications were created.
