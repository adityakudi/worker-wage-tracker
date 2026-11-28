# Attendance, ledger and dispute API

All routes can be accessed under `/api` on the same origin. Use a Bearer token from login. The server scopes each record to the contractor and worker in its accepted membership.

| Route | Action |
|---|---|
| `POST /attendance` | Contractor posts attendance for an assignment. Supply `assignment_id`, `work_date`, `half_day_units` (0, 1 or 2), `request_id` and optional `notes`. |
| `POST /memberships/{id}/ledger` | Contractor records an advance, wage payment or adjustment. Supply `kind`, `effective_date`, `amount_paise`, `request_id` and optional `notes`. An adjustment requires a note. |
| `GET /memberships/{id}/ledger` | Participant lists records with `start`, `end`, `q`, `limit` and `offset`. Totals cover the selected period, independent of text search and pagination. |
| `GET /ledger/{entry_id}` | Participant reads an entry and its audit history. |
| `POST /ledger/{entry_id}/reviews/{kind}` | Worker records either `acknowledged` or `receipt_confirmed`. A receipt applies to a current advance or payment. |
| `POST /ledger/{entry_id}/reverse` | Contractor supplies a `reason` and optionally `replace_units` or `replace_amount_paise`. Open disputes must go through resolution. |
| `POST /ledger/{entry_id}/dispute` | Worker opens a dispute with a `reason`. |
| `POST /ledger/{entry_id}/dispute/respond` | Contractor responds with a `reason`, optionally sets `correct: true` and proposes a replacement. |
| `POST /ledger/{entry_id}/dispute/decide` | Worker sends `accept` and an optional `notes` field. Accepting a proposed correction posts the reversal and any replacement atomically. Declining makes the dispute available for another response. |
| `GET /memberships/{id}/statement.csv?month=YYYY-MM` | Participant downloads the monthly totals and posted rows together. |

Money inputs are integer paise. Positive advances and payments become negative postings. Adjustments are signed and cannot be zero. Responses carry ledger amounts and totals as decimal strings so JavaScript preserves each paise. The forms parse rupees exactly and restrict a single input to JavaScript's safe integer range in paise.

Generate a UUID for each posting and reuse it if retrying the same payload. A successful retry returns the original entry. Reusing an identifier for a different entry returns 409. A unique worker-day slot prevents two current attendance records for one contractor and worker, even across worksites. The latest applicable wage proposal must be acknowledged. A recorded attendance snapshot retains its rate and calculated amount.

Pending disputes leave ledger amounts unchanged. Corrections retain the effective work date and record their actual audit timestamp. Attendance replacements use the original rate snapshot. Historical periods incorporate later corrections to their effective dates. Rows retain the original, reversal and replacement IDs so users can trace the changes.

The statement reports opening, earnings, advances, payments, adjustments and closing in paise. The same SQL summary provides dashboard totals. Recorded amounts and reviews describe bookkeeping. Actual wage payments happen outside the app.
