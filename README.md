# FinVentory Intelligence

A PostgreSQL and Streamlit inventory and financial reporting application developed for the Database Systems course at FAST NUCES Karachi.

The existing interface provides a dashboard, inventory and alerts, weighted demand forecasts, and Admin-only profit and transaction pages. Manager and Staff accounts can access the first three pages. Forecasts are a deterministic weighted moving average, not a trained AI model.

## Local setup

Use Python 3.12+ and PostgreSQL 15+ with the `psql` client.

```sh
git clone https://github.com/Talha2555/FinVentory-Intelligence.git
cd FinVentory-Intelligence
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Create a database using your PostgreSQL administrator account, then install the schema **inside that database**:

```sh
createdb finventory_db
psql -X -v ON_ERROR_STOP=1 -d finventory_db -f finventory.sql
# Optional, once on an empty installation:
psql -X -v ON_ERROR_STOP=1 -d finventory_db -f demo_data.sql
```

`finventory.sql` uses psql's relative include command to load `views.sql`. Run with `psql`, not by pasting the file into pgAdmin's query editor. Schema creation is transactional and intended for a fresh database; do not rerun it over an existing installation.

Configure the connection using environment variables; no source edits are required. `.env.example` documents the settings; the app does not automatically load `.env` files.

```sh
export PGHOST=localhost PGPORT=5432 PGDATABASE=finventory_db PGUSER=finventory_app
read -r -s -p 'Database password: ' PGPASSWORD; echo
export PGPASSWORD
```

Provision `finventory_app` as a dedicated login through your database administrator, with CONNECT on the database, USAGE on the application schema, SELECT on reporting tables/views and UPDATE on inventory for the alert check. Ensure the trigger can INSERT into alerts and use its sequence. Avoid using a PostgreSQL superuser for the app. Alternatively set `DATABASE_URL` (takes precedence). Standard libpq settings, such as `PGSSLROOTCERT`, are supported; use `PGSSLMODE=verify-full` for remote servers. Keep connection strings and passwords private.

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

## Reporting definitions and limits

- Revenue is `SUM(sales_items.quantity * price)`. All financial reporting uses line items, avoiding stale header totals.
- Cost of goods sold is `SUM(quantity * unit_cost)`. New sale inserts capture the product's cost at sale time unless an explicit historical unit cost is supplied. Unsold purchase inventory is not an expense in this calculation.
- Gross profit is revenue minus cost of goods sold; net profit also subtracts recorded operating expenses. Empty totals are zero. This is an all-time operational summary, not a full accounting ledger or tax report.
- Forecasts target the current month using the latest three **completed calendar months**: 50%, 30%, 20%, newest first. Missing months contribute zero, current-month sales are excluded, and products with no history forecast zero. Weights are not renormalized for new products.
- Supplier and retailer rankings use explicit party IDs in the transaction ledger. Product rankings use sale lines and group by product ID, so equal names stay separate.
- Inventory changes automatically after sale/purchase line inserts. The transaction ledger is populated through `record_sale_transaction` and `record_purchase_transaction` procedures; it is **not automatically populated by triggers**. Call the relevant procedure once within the same transaction as your business write. Historical ledger completeness and header/line consistency remain the responsibility of the importing system.
- Existing inventory triggers implement insert workflows. Editing or deleting posted line items does not reverse stock movements; use a separate audited correction workflow. This repair does not add full accounting, returns, or perpetual inventory valuation.
- Database connections are short-lived and always closed. Failed transactions roll back; the UI displays a generic error instead of displaying empty data as a successful request. Server logs contain SQLSTATE codes, not driver error messages or credentials.

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

Tests create random schemas and drop them afterward. They execute the fresh schema, demo data and upgrade script, query reporting views, and check cost snapshots, forecast gaps, stock rejection and alert deduplication. Unit tests cover hashed accounts, configuration, and connection failure/cleanup. Streamlit smoke tests exercise login and the existing pages. See [VALIDATION.md](VALIDATION.md) for the checks actually run for this repair and remaining limits.

Contributors: Talha Khan, Muhammad Siraj, Muhammad Furqan, Maaz Umer.
