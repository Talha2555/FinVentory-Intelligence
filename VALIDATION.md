# Repair validation — 2026-11-10

Branch: `repair/finventory-critical-fixes-2026-11`, based on `main` at `2fd5d34`.

## Completed checks

- Full suite: **18 passed, 0 skipped** on Python 3.12.14 and a disposable local PostgreSQL **17.11** instance, using the versions in `requirements.txt`.
- Eight PostgreSQL integration tests exercise schema creation; all interface views; empty and loss-making financial summaries; sale-time cost snapshots; exclusion of unsold purchases from COGS; calendar-gap forecasts; zero-history products; duplicate product names; stock rejection; repeated alert scans; demo ledger rankings; migration backfill; real transaction rollback/recovery; and every Admin Streamlit page reading real PostgreSQL data.
- Ten unit/Streamlit tests cover salted scrypt authentication, rejection of plaintext CSVs and duplicate users, private account-file creation, environment configuration, query binding, sanitized failures, connection cleanup, login, role navigation, and suppression of false success after database errors.
- Separately recreated the exact original SQL and demo data from `main` (omitting only its `CREATE DATABASE` statement), then applied the upgrade with `psql -X -v ON_ERROR_STOP=1`. Result: revenue 1,591,000; COGS 1,407,000; gross profit 184,000; expenses 180,000; net profit **4,000**.
- `python -m compileall -q app.py auth.py database.py tests` passed.
- `pip check` reported no broken requirements.
- `git diff --check` passed.
- Added GitHub Actions coverage with PostgreSQL 17 and Python 3.12; remote CI results must be checked on the pull request.

The final local run enabled PostgreSQL tests with `TEST_DATABASE_URL`. Without that variable and the `psql` executable, those tests report explicit skips rather than claiming SQL verification.

## Not verified

- No connection was made to a user-hosted or production PostgreSQL instance. Production data, historical costs, deployment credentials, least-privilege grants, remote TLS, and other PostgreSQL versions were not verified.
- The original database had no sale-time cost history. Migration backfills from current product costs; accuracy of historical profit requires reconciliation with source records.
- Streamlit was tested through its automated AppTest harness, including real database reads. A manual browser visual review and concurrent multi-user/load testing were not performed.
- Existing ledger omissions or incorrect historical ledger entries are not reconstructed. The migration test preserves the original data; the optional fresh demo fixes its mismatched example transactions.
