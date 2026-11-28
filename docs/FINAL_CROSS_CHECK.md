# Track A final cross-check

Rechecked on **29 November 2026, India time**. The application passed the technical acceptance checks below. The tested revision is [6073067](https://github.com/adityakudi/worker-wage-tracker/commit/60730677bf2ae7b172608f5051d82289eb8cb427), which was live on Render at the time of the check.

| MVP goal | Evidence |
|---|---|
| Signup, login and access control | Seven signup and identity assertions passed through the Postman collection. The API rejects missing credentials and access to another participant's records. |
| Contractor-owned worksites | A real browser created, searched, opened, edited and deleted a synthetic worksite. PostgreSQL tests cover ownership. |
| Worker invitations | The invited worker accepted from their own session before the contractor assigned work. |
| Assignments and wage agreements | Both roles saw the terms. Attendance posting was blocked while the applicable rate awaited acknowledgement. |
| Attendance | The browser posted full days and a half-day correction. Database tests cover concurrency, same-day uniqueness, input bounds and future dates. |
| Wage calculations | Three full days and one half day at ₹600 produced ₹2,100 net earnings. A ₹500 advance and ₹1,000 payment left ₹600 outstanding in both browser roles. Database tests cover rounding and rate snapshots. |
| Advances, payments and reversals | Each posting was retained. The correction used a linked reversal and replacement. Review and payment receipt were verified as distinct worker actions. |
| Dashboards and access | Browser views displayed the same balance for the contractor and the worker. API checks cover text search, dates, pagination and cross-participant isolation. Hindi sign-in rendered on mobile. |
| Disputes and activity history | The original balance stayed unchanged while the dispute was open. A worker-accepted correction applied the reversal and replacement and recorded the resolution. |
| Monthly CSV | The statement matched the ₹600 final screen balance, ₹500 advances and ₹1,000 payments. The earlier correction example also reconciled at ₹200. |

Fresh execution passed **50 automated tests without skips**, the frontend build, the signup collection and both Chromium roles. A public HTTPS smoke check confirmed database health, built assets, protected routes and private-file boundaries. Verified the committed MP4 duration of **120 seconds**. [GitHub checks](https://github.com/adityakudi/worker-wage-tracker/actions/runs/46181861256) · [Live app](https://worker-wage-tracker-wg8y.onrender.com/#live) · [Screenshots and video](release-evidence/2026-11-29)

## Milestone and challenge records

- The software release date remains **29 November 2026**. The originally planned **26 November 2026** deadline was missed.
- The Git history contains commits on the ten planned build dates from 17 through 26 November, with later release work recorded under its actual date.
- Milestones 10 and 15 have their tested software and submission materials ready. The [milestone table](BUILD_PLAN.md) records publication evidence and determines the Track A milestone count.
- The separate calendar posting cadence and DSA participation have no complete evidence here. An organiser determines challenge eligibility.

## Before using real wage records

The browser checks used synthetic accounts. Participant validation is still open. Invite one consenting contractor and two or three consenting workers to a short test with fictional wages. Ask how they currently agree rates and record half days, advances and corrections. Have each person try their role, check the balance and find the dispute or receipt controls. Record the date, role, device, tasks tried and any points of confusion. Keep names, contact details and real wages out of the public project record.

The app records bookkeeping entries. It does not transfer wages. The [hosting notes](DEPLOYMENT.md) give the free database expiry.
