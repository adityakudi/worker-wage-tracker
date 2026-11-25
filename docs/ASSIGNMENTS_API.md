# Assignments and wage agreements

Implemented 25 November 2026 as carry-forward work for milestone 7. PostgreSQL acceptance evidence must be recorded after the new CI run passes. These APIs do not record attendance or payments.

All calls require a Bearer JWT. Routes below are available both directly for development and under `/api` in the combined production service.

| Route | Permission and behavior |
|---|---|
| `POST /assignments` | Contractor creates an assignment using an accepted `membership_id`, an owned active `worksite_id`, `start_date` and optional `end_date`. |
| `GET /assignments` | Participants only. Supports worksite-name `q`, `membership_id`, `worksite_id`, `limit` 1–100 and non-negative `offset`. Returns items, total, limit and offset. |
| `GET /assignments/{id}` | Owning contractor or assigned worker only; other callers receive 404. |
| `POST /assignments/{id}/wage-agreements` | Owning contractor proposes positive integer `daily_rate_paise` and `effective_from`. New proposals remain unacknowledged. |
| `GET /assignments/{id}/wage-agreements` | Participant-only chronological history with pagination. |
| `POST /wage-agreements/{id}/acknowledge` | Assigned worker only. Records server time and the authenticated worker ID; repeated acknowledgement returns 409. |

Dates must be ISO calendar dates `YYYY-MM-DD`. Monetary input must be an actual integer, not a boolean, float or numeric string. The API accepts positive signed-64-bit paise amounts. A frontend must handle large JSON integers without precision loss before financial UI is connected.

## Integrity and retention

Migration 004 uses composite foreign keys to prevent an assignment joining different contractors' membership/worksite records. Accepted membership is checked in both the API and database. Assignment end dates cannot precede their start.

Agreement effective dates must fall inside the assignment and strictly increase. An agreement's effective period is implicitly `[effective_from, next effective_from)`; the final period extends to the assignment end, if any. There are no overlapping explicit end-date intervals. Assignment row locks serialize proposals. A new proposal cannot rewrite an earlier period.

Terms cannot be edited or deleted. The database permits a single acknowledgement by the assigned worker and retains its timestamp and actor. A new future rate is a separate proposal and leaves old terms unchanged. There is no withdrawal/correction UI for a mistaken proposal yet; do not enter real financial records.

Worksites with assignments cannot be deleted: the API returns 409 and instructs the contractor to archive the worksite. Archiving retains its assignments and agreement history.

## Remaining integration

Pending proposals must never be treated as worker-approved wages. Future attendance posting must inspect the latest applicable proposal, require its acknowledgement, and snapshot that rate. This posting gate, attendance uniqueness, ledger/reversals, disputes and financial audit events are not implemented by this change. Rate acknowledgement confirms the wage terms, not receipt of a payment.

The current live frontend has authentication/worksite forms; invitation, assignment and rate management remain API-only. Sample-data showcase screens remain labelled prototypes. Public hosting and a browser end-to-end demonstration are still pending.
