# Worker Attendance & Wage Tracker

A mobile-friendly platform for daily-wage workers and contractors to maintain shared attendance, wage, advance, payment, and dispute records.

## Status

Day 1 planning is complete. Application implementation, pilot validation, tests, and deployment are pending. This repository starts from scratch.

## Problem and users

Contractors and workers need a shared, reviewable record of work and money owed. This is a problem hypothesis to validate with one contractor and two or three workers. Contractors manage worksites and records; workers review their own records, acknowledge entries, and raise disputes.

## Planned features

- Secure contractor and worker accounts.
- Worksites, worker invitations, assignments, and agreed wage rates.
- Full-day, half-day, and absent attendance.
- Wage balances with advances and payments recorded once.
- Searchable dashboards and downloadable monthly CSV statements.
- Acknowledgement, disputes, corrections, and audit history.
- English and Hindi interface.

See [FEATURES.md](FEATURES.md) for the ten-feature MVP, calculation rules, access boundaries, and acceptance checks.

## Planned stack

React with Vite, FastAPI, and PostgreSQL. Money is stored as integer paise; work dates use Asia/Kolkata. Implementation dependencies will be selected during setup.

## 15-day plan

The [detailed milestone plan](docs/BUILD_PLAN.md) maps each of the fifteen Track A days to its work and evidence. Milestone numbering is retained when work is completed early. Actual completion dates and GitHub timestamps remain the source of evidence.

## Run locally

Application setup is planned for milestone 3. Runnable commands will be documented after the backend and frontend exist and have been verified.

## Tests

No application tests exist yet. Milestone 13 requires at least five API tests, including meaningful money and access-control coverage.

## Screenshots, deployment, and demo

Pending working software. Real screenshots, the verified public URL, and a two-minute demo will be added during delivery.

## What I built and what I understood

Day 1: defined the problem hypothesis, contractor and worker roles, MVP boundaries, and acceptance checks. The design separates review acknowledgement from payment receipt, snapshots historical wage rates, and uses reversals so corrections preserve an audit trail. Implementation and first-hand learning will be recorded as milestones are completed.
