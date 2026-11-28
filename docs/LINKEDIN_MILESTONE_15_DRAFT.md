# Milestone 15 launch draft

Prepared on 29 November 2026. Publication status: draft.

I built Worker Attendance & Wage Tracker for small contractors and daily-wage workers who need a shared record of work and money owed.

A contractor can invite a worker, agree a daily rate, record attendance and enter advances or payments. Workers can review their own records, dispute an entry and download a monthly statement. When a worker accepts a correction, the original entry and reversal stay in the history.

The project uses React, FastAPI and PostgreSQL. My biggest lesson was making the ledger reconcile when two people view the same record or a correction changes a past amount. I tested that workflow in a browser from both roles and checked that the CSV matched the displayed balance.

- [Try the live workspace with sample data](https://worker-wage-tracker-wg8y.onrender.com/#live)
- [Watch the two-minute demo](https://github.com/adityakudi/worker-wage-tracker/blob/main/docs/release-evidence/2026-11-29/Worker_Wage_Tracker.mp4)
- [GitHub repository](https://github.com/adityakudi/worker-wage-tracker)

I’d like to hear how workers and contractors already handle half days, advances and corrections. The live service is a free prototype for synthetic records.

#ALTABuilder30 @ALTA School of Technology
