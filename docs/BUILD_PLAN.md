# 15-Day Milestone Plan

ALTA BUILDER 30 — Track A: Worker Attendance & Wage Tracker

The day numbers below identify the sheet's fifteen milestones. Work may be completed ahead of schedule, with several milestones on one actual date. Commit timestamps and completion dates remain accurate.

| Day milestone | Phase | Work | Evidence required | Status |
|---|---|---|---|---|
| 1 | Plan | Define the problem, contractor and worker roles, ten MVP features, later features, and acceptance rules. | FEATURES.md and new GitHub repository | Done |
| 2 | Design | Design PostgreSQL tables, relationships, constraints, and login, list, detail, dashboard wireframes. | Schema diagram and four wireframes in docs/ | In progress |
| 3 | Setup | Initialise backend, connect PostgreSQL, configure environment variables, and add health endpoint. | Running backend and database-connected /health | In progress |
| 4 | Signup | Implement user model, validation, password hashing, and signup. | Signup verified in Postman | In progress |
| 5 | Login | Implement JWT login and role-protected routes. | 401 without valid token, authorised data with token; progress post | In progress |
| 6 | CRUD | Implement authenticated worksite create, read, update, and delete APIs. | Four CRUD operations with ownership checks | Not started |
| 7 | Relationships | Add memberships, assignments, wage agreements, and search/filter/pagination. | Related entity APIs and paginated lists | Not started |
| 8 | Frontend auth | Set up React routing/layout and connect signup/login forms. | Signup and login usable from browser | Not started |
| 9 | Lists and details | Connect worksite, worker, and record list/detail pages to live APIs. | Live data with loading, empty, and error states | Not started |
| 10 | Management flows | Build create/edit/delete flows, attendance, advances, and payments; use reversals for posted ledger corrections. | CRUD usable from UI; progress post | Not started |
| 11 | Heavy feature backend | Implement acknowledgement, disputes, responses, correction proposals, and immutable audit records. | Heavy feature backend verified | Not started |
| 12 | Heavy feature UI | Connect worker dispute and contractor response screens; worker confirms resolution. | Complete end-to-end dispute demonstration | Not started |
| 13 | Testing | Test main flows and bad input; cover wage maths, access isolation, duplicate attendance, reversals, and disputes. | At least five passing API tests and resolved main-flow bugs | Not started |
| 14 | Deployment | Deploy frontend, backend, and PostgreSQL on free hosting; configure secrets through environment. | Public URL verified for another user | Not started |
| 15 | Ship | Write README run steps and learning section, add screenshots, record two-minute demo, and prepare launch post. | README, screenshots, real demo video, and published LinkedIn link | Not started |

## Progress and evidence

Day 1 specification: [requirements commit](https://github.com/adityakudi/worker-wage-tracker/commit/c375aacc9331473f2c6f259732cd45d75b3467a3), completed 17 November 2026 (Asia/Kolkata). No application code has been implemented yet.

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
