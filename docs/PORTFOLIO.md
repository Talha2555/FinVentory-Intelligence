# Resume and interview notes

## Project entry

**FinVentory Intelligence — Inventory Analytics & Financial Reporting**  
Python · PostgreSQL · Streamlit · Pandas · pytest · GitHub Actions  
[Repository](https://github.com/Talha2555/FinVentory-Intelligence) · [Repair PR](https://github.com/Talha2555/FinVentory-Intelligence/pull/1)

**Short description:** A team-built inventory analytics application with SQL reporting views, stock/alert triggers, role-aware dashboards, weighted demand forecasting and sale-time profit calculations.

## Resume bullets

Choose two or three bullets that reflect work you personally performed. For team-owned work, use “Contributed to” and identify your specific component; the project-level facts below do not establish individual ownership.

- Contributed to a Python/PostgreSQL inventory analytics application with Streamlit dashboards for product performance, inventory alerts, financial reporting and transaction review.
- Implemented PostgreSQL reporting views and a three-month weighted moving average forecast with calendar-gap handling and separate product identities.
- Corrected profit reporting with sale-time unit-cost snapshots, line-item revenue and separate operating-expense aggregation.
- Hardened local authentication with salted scrypt hashes and environment-based database configuration, plus rollback and connection cleanup on failed requests.
- Added 18 automated tests spanning authentication, database handling, Streamlit pages and PostgreSQL integration, with PostgreSQL-backed GitHub Actions.

The 18-test count describes suite size, not test coverage percentage. No measured business savings, user scale or forecast-accuracy figure is available.

## Compact resume version

> **FinVentory Intelligence | Python, PostgreSQL, Streamlit**  
> Contributed to a team inventory analytics project featuring SQL-driven reporting, stock alerts, role-aware dashboards and weighted demand forecasts. Validated reporting and database behavior through an 18-test suite and PostgreSQL-backed CI.

Adapt “Contributed to” to a precise description of your role before publishing. Use your actual dates and link to the branch/PR while review is pending.

## Interview talking points

| Question | Evidence-based answer |
| --- | --- |
| Why snapshot unit cost? | Product costs change; storing the sale-time value preserves past COGS. Legacy snapshots must be reconciled because original historical costs were not stored. |
| How does forecasting work? | Three completed calendar months weighted 50/30/20. Missing months are zero; current-month activity is excluded. It is a statistical baseline, with no claimed accuracy metric. |
| How do you avoid inflated financial totals? | Aggregate sales and expenses separately rather than joining one-to-many collections into a multiplied result set. |
| What happens on database failure? | The operation rolls back, cursor/connection resources close, and the UI shows a sanitized error instead of a successful empty state. |
| What is actually automated? | Line-item insert triggers update stock and create relevant alerts. Transaction-ledger procedures are invoked explicitly by the importing workflow. |
| How was it tested? | Unit checks, Streamlit AppTest and isolated PostgreSQL schema tests; the full suite and PostgreSQL-backed CI passed. |
| What would you improve next? | Audited corrections/returns, ledger reconciliation, hosted identity and login throttling, forecast backtesting, and concurrency/load tests. |

## Claims to keep accurate

Describe this as a course/team portfolio project. Avoid claims of production deployment, trained AI, proven forecast accuracy, a complete accounting system, database-enforced per-user RBAC, or sole authorship unless you have separate evidence. Credit the team listed in the README.
