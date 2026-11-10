# Setup and operations

The validated environment is Python 3.12 and PostgreSQL 17.11. PostgreSQL 15+ is the intended baseline, but other versions have not been tested. Commands below use Bash on Linux/macOS; Windows users can use WSL. Install PostgreSQL server/client tools and ensure `psql` and `createdb` are on PATH.

```sh
git clone https://github.com/Talha2555/FinVentory-Intelligence.git
cd FinVentory-Intelligence
# Until PR #1 is merged, the documented implementation is on this branch:
git switch repair/finventory-critical-fixes-2026-11
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run the following as a PostgreSQL account allowed to create databases and schema objects. Local PostgreSQL authentication must already be configured; on some installations you will need to specify `-U` and `-h`. Then install the schema **inside the new database**:

```sh
createdb finventory_db
psql -X -v ON_ERROR_STOP=1 -d finventory_db -f finventory.sql
# Optional, once on an empty installation:
psql -X -v ON_ERROR_STOP=1 -d finventory_db -f demo_data.sql
```

`finventory.sql` uses psql's relative include command to load `views.sql`. Run with `psql`, not by pasting the file into pgAdmin's query editor. Schema creation is transactional and intended for a fresh database; do not rerun it over an existing installation.

Configure the connection using environment variables; no source edits are required. [`.env.example`](../.env.example) documents the settings; the app does not automatically load `.env` files.

Provision `finventory_app` as a dedicated login through your database administrator, with CONNECT on the database, USAGE on the application schema, SELECT on reporting tables/views and UPDATE on inventory for the alert check. Ensure the trigger can INSERT into alerts and use its sequence. Avoid using a PostgreSQL superuser for the app. Alternatively set `DATABASE_URL` (takes precedence). Standard libpq settings, such as `PGSSLROOTCERT`, are supported; use `PGSSLMODE=verify-full` for remote servers. Keep connection strings and passwords private.

For a fresh local installation using the default `public` schema, run these statements as the database owner/administrator to provision the application role. `\password` prompts privately; do not commit a role password to SQL files:

```sql
-- In psql connected to finventory_db as an administrator:
CREATE ROLE finventory_app LOGIN;
\password finventory_app
GRANT CONNECT ON DATABASE finventory_db TO finventory_app;
GRANT USAGE ON SCHEMA public TO finventory_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO finventory_app;
GRANT UPDATE ON inventory TO finventory_app;
GRANT INSERT ON alerts TO finventory_app;
GRANT USAGE, SELECT ON SEQUENCE alerts_alert_id_seq TO finventory_app;
```

These grants support the current read/reporting interface and alert scan. A separate data-import account should own sales/purchase writes. Adapt object/schema names and grants if you install into another schema. Configure the PostgreSQL server's host authentication to accept the app role, then export its credentials:

```sh
export PGHOST=localhost PGPORT=5432 PGDATABASE=finventory_db PGUSER=finventory_app
read -r -s -p 'Database password: ' PGPASSWORD; echo
export PGPASSWORD
```

Create local accounts with privately prompted passwords:

```sh
python auth.py owner --role Admin
python auth.py colleague --role Staff
streamlit run app.py
```

There are **no default login credentials**. Passwords must have at least 12 characters and are stored as salted scrypt hashes. `users.csv` is private, ignored by Git, and created with owner-only permissions. `FINVENTORY_USERS_FILE` can select an absolute path outside the repository; by default the file is next to `auth.py`, independent of the working directory. Valid roles are Admin, Manager, and Staff. Back up the account file securely. Account creation is a single-administrator CLI operation; do not run concurrent writers.

## Upgrade an existing database

Back up the database first. Do **not** run the fresh schema or demo data over existing tables.

```sh
psql -X -v ON_ERROR_STOP=1 -d finventory_db -f migrations/2026_11_critical_fixes.sql
```

The migration adds and backfills sale-item unit costs, replaces reporting views, locks stock rows during sale validation, and prevents repeated scans from inserting duplicate unread low-stock alerts. Existing historical cost snapshots cannot be reconstructed from the old schema: the backfill uses each product's **current cost price**. Audit and correct `sales_items.unit_cost` against historical records before treating migrated profits as authoritative. The migration preserves existing snapshots on reruns. The legacy SQL `users` table is unused by the app; existing plaintext values in that table should be removed or migrated according to your data retention policy.

Remove the old plaintext CSV and recreate accounts with `python auth.py`. Legacy `username,password,role` files are rejected, never accepted as a fallback. The previously published demo passwords must be considered compromised. The unused users table in fresh installs has a `password_hash` column instead.

## Automated tests

```sh
pip install -r requirements-dev.txt
python -m pytest -q
```

Without PostgreSQL configuration, integration tests are explicitly skipped. To run them, create a **disposable test database**, grant its test user CREATE SCHEMA, and set a private connection string:

```sh
export TEST_DATABASE_URL='postgresql://localhost/finventory_test'
python -m pytest -q
```

Tests create random schemas and drop them afterward. They execute the fresh schema, demo data and upgrade script, query reporting views, and check cost snapshots, forecast gaps, stock rejection and alert deduplication. Unit tests cover hashed accounts, configuration, and connection failure/cleanup. Streamlit smoke tests exercise login and the existing pages. See [VALIDATION.md](../VALIDATION.md) for the checks actually run for this repair and remaining limits.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Database request fails | Confirm PostgreSQL is running, connection variables select the intended database, and schema/view installation completed. Inspect the server log SQLSTATE; credentials are deliberately omitted from UI errors. |
| A relation/view is missing | Use the fresh schema only for a new database, or the migration for the original installation. Run scripts with `psql -v ON_ERROR_STOP=1`, keeping `views.sql` in its repository location. |
| Authentication is unavailable | Create an account with `python auth.py`; check `FINVENTORY_USERS_FILE` and file readability. Old plaintext CSV files are rejected. |
| Forecasts are zero with demo data | Demo sales are dated April 2026. Only the last three completed calendar months contribute to a forecast. This is expected outside that window. |
| Integration tests skip | Set `TEST_DATABASE_URL`, install `psql`, and allow the disposable test user to create schemas. |
| Permission denied during alert scan | Verify UPDATE on inventory, INSERT on alerts, and sequence permissions for the app role. |

Never point the test suite at a production database. Private `.env`, account files and Streamlit secrets are excluded from Git. Do not share real customer records in screenshots or demos.
