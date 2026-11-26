# Track A handover — 26 November 2026

The original 26 November completion target has not been met. Keep the fifteen milestone numbers and actual completion dates in BUILD_PLAN.md. Do not mark attendance/payment/dispute requirements satisfied by sample screens or arithmetic unit tests.

## Implementation order

1. Connect invitation, assignment and wage-agreement management to the live contractor/worker UI. Preserve participant-only visibility and handle exact paise values safely in JavaScript.
2. Add persistent attendance: use Asia/Kolkata dates; reject future dates; require the latest applicable proposal to be acknowledged; snapshot its rate; enforce duplicate prevention for contractor/worker/date across worksites, including concurrent requests.
3. Add immutable ledger postings, advances, payments, opening adjustments and linked one-time reversals. Use integer paise and atomic transactions; preserve original records and author/time/reason for corrections.
4. Build acknowledgements, separate payment receipt confirmation, disputes, contractor responses, correction proposals and worker-confirmed resolution. Add durable audit events. Disputes flag records without removing their amounts.
5. Connect the financial UI and monthly CSV export. Verify dashboard and export totals at identical cutoffs, inclusive opening balances and the INR 600 specification example.
6. Extend PostgreSQL and browser checks for the above, including ownership leaks, races, stale rate proposals, repeat reversals and failed transaction rollback. API-only coverage cannot close the complete-flow testing milestone.
7. Obtain the missing Render workspace selection, inspect free-tier eligibility and existing resources, apply the prepared Blueprint, and verify a real public URL and independent-user browser session. Do not purchase services or claim a private preview is public deployment.
8. Obtain real pilot feedback with consent, capture the completed flows, update README/screenshots and record the complete end-to-end product demo. Publish only with explicit instruction; preserve the actual post URL/date.

## Evidence and challenge gaps

The existing LinkedIn publication is one 24 November progress post. Drafts exist for milestones 5, 10, 15 and calendar day 5; the calendar-day-5 draft is retrospective and cannot establish a 21 November publication. A 26 November progress draft is separate from a verified launch.

Postman desktop execution remains unrecorded. DSA participation and any challenge grace/eligibility decisions need separate genuine evidence; they cannot be inferred from project commits. Track B remains separate.
