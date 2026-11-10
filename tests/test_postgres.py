"""Real PostgreSQL checks; each test uses and drops an isolated schema."""
import os
from pathlib import Path
import shutil
import subprocess
import uuid

import psycopg2
import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.postgres


@pytest.fixture
def db():
    url = os.getenv('TEST_DATABASE_URL')
    if not url or not shutil.which('psql'):
        pytest.skip('Set TEST_DATABASE_URL to a disposable PostgreSQL database and install psql')
    schema = 'test_' + uuid.uuid4().hex
    conn = psycopg2.connect(url)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA {schema}')
        cur.execute(f'SET search_path TO {schema}')
    parameters = psycopg2.extensions.parse_dsn(url)
    pg_names = {'dbname': 'PGDATABASE', 'user': 'PGUSER', 'password': 'PGPASSWORD',
                'host': 'PGHOST', 'port': 'PGPORT', 'sslmode': 'PGSSLMODE'}
    env = os.environ | {pg_names[k]: v for k, v in parameters.items() if k in pg_names}
    env['PGOPTIONS'] = f'-c search_path={schema}'
    try:
        subprocess.run(['psql', '-X', '-v', 'ON_ERROR_STOP=1', '-f', str(ROOT / 'finventory.sql')], env=env, check=True, stdout=subprocess.DEVNULL)
        yield conn, env
    finally:
        with conn.cursor() as cur:
            cur.execute(f'DROP SCHEMA {schema} CASCADE')
        conn.close()


def query(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall() if cur.description else None


def product(conn, name='Widget', stock=100):
    pid = query(conn, 'INSERT INTO products(name,cost_price,selling_price) VALUES (%s,10,20) RETURNING product_id', (name,))[0][0]
    query(conn, 'INSERT INTO inventory(product_id,quantity) VALUES (%s,%s)', (pid, stock))
    return pid


def sale(conn, pid, quantity, months_ago):
    sid = query(conn, "INSERT INTO sales(sale_date,total_amount) VALUES ((date_trunc('month',CURRENT_DATE) - %s * interval '1 month')::date,99999) RETURNING sale_id", (months_ago,))[0][0]
    query(conn, 'INSERT INTO sales_items(sale_id,product_id,quantity,price) VALUES (%s,%s,%s,20)', (sid,pid,quantity))


def test_all_views_and_empty_finances(db):
    conn, _ = db
    for view in ['top_products', 'top_suppliers', 'top_retailers', 'monthly_sales_view', 'inventory_status_view', 'demand_prediction_view', 'profit_loss_summary']:
        assert query(conn, f'SELECT * FROM {view}') is not None
    assert query(conn, 'SELECT * FROM profit_loss_summary')[0] == (0,0,0,0,0)


def test_cogs_snapshot_and_unsold_purchases(db):
    conn, _ = db
    pid = product(conn)
    query(conn, "INSERT INTO purchases(purchase_date,total_cost) VALUES (CURRENT_DATE,5000)")
    sale(conn, pid, 2, 1)
    query(conn, 'UPDATE products SET cost_price=15 WHERE product_id=%s', (pid,))
    query(conn, "INSERT INTO expenses(amount,expense_date) VALUES (7,CURRENT_DATE)")
    assert query(conn, 'SELECT * FROM profit_loss_summary')[0] == (40,20,20,7,13)
    assert query(conn, 'SELECT revenue FROM monthly_sales_view')[0][0] == 40
    query(conn, "INSERT INTO expenses(amount,expense_date) VALUES (100,CURRENT_DATE)")
    assert query(conn, 'SELECT net_profit FROM profit_loss_summary')[0][0] == -87


def test_calendar_forecast_gaps_current_and_product_identity(db):
    conn, _ = db
    pid = product(conn)
    other = product(conn)  # same name, separate product
    no_history = product(conn, 'New product')
    sale(conn, pid, 10, 1)
    sale(conn, pid, 20, 3)
    sale(conn, pid, 40, 0)  # excluded incomplete month
    sale(conn, other, 4, 2)
    rows = dict(query(conn, 'SELECT product_id,predicted_sales FROM demand_prediction_view'))
    assert rows[no_history] == 0
    assert rows[pid] == 9  # 10*.5 + 0*.3 + 20*.2
    assert float(rows[other]) == 1.2
    assert len(query(conn, 'SELECT * FROM top_products')) == 2


def test_stock_failure_recovers_and_alert_scan_is_repeatable(db):
    conn, _ = db
    pid = product(conn, stock=2)
    with pytest.raises(psycopg2.Error):
        sale(conn, pid, 3, 1)
    assert query(conn, 'SELECT quantity FROM inventory')[0][0] == 2
    query(conn, 'UPDATE inventory SET quantity=quantity')
    query(conn, 'UPDATE inventory SET quantity=quantity')
    assert query(conn, "SELECT COUNT(*) FROM alerts WHERE alert_type='LOW_STOCK'")[0][0] == 1
    sale(conn, pid, 1, 1)
    assert query(conn, 'SELECT quantity FROM inventory')[0][0] == 1


def test_demo_and_upgrade_script(db):
    conn, env = db
    for script in ['demo_data.sql', 'migrations/2026_11_critical_fixes.sql']:
        subprocess.run(['psql', '-X', '-v', 'ON_ERROR_STOP=1', '-f', str(ROOT / script)], env=env, check=True, stdout=subprocess.DEVNULL)
    assert query(conn, 'SELECT net_profit FROM profit_loss_summary')[0][0] == 4000
    assert query(conn, 'SELECT COUNT(*) FROM transactions')[0][0] == 5
    assert query(conn, 'SELECT total_purchases FROM top_suppliers')[0][0] == 2100000
    assert query(conn, 'SELECT total_sales FROM top_retailers')[0][0] == 1185000


def test_migration_backfills_legacy_cost_column(db):
    conn, env = db
    pid = product(conn)
    sale(conn, pid, 2, 1)
    # Reproduce the old schema's missing cost column; dependent reports are
    # intentionally dropped, as on the original installation.
    query(conn, 'ALTER TABLE sales_items DROP COLUMN unit_cost CASCADE')
    subprocess.run(['psql', '-X', '-v', 'ON_ERROR_STOP=1', '-f', str(ROOT / 'migrations/2026_11_critical_fixes.sql')], env=env, check=True, stdout=subprocess.DEVNULL)
    assert query(conn, 'SELECT unit_cost FROM sales_items')[0][0] == 10
    assert query(conn, 'SELECT net_profit FROM profit_loss_summary')[0][0] == 20
    sale(conn, pid, 1, 1)
    assert query(conn, 'SELECT total_cost FROM profit_loss_summary')[0][0] == 30


def test_real_database_helper_rollback_and_recovery(db, monkeypatch):
    import database
    conn, env = db
    monkeypatch.setenv('DATABASE_URL', os.environ['TEST_DATABASE_URL'])
    monkeypatch.setenv('PGOPTIONS', env['PGOPTIONS'])
    with pytest.raises(database.DatabaseError):
        database.execute("INSERT INTO expenses(amount,expense_date) VALUES (5,CURRENT_DATE); SELECT 1/0")
    assert database.fetch_frame('SELECT COUNT(*) AS count FROM expenses').iloc[0, 0] == 0
    database.execute('INSERT INTO expenses(amount,expense_date) VALUES (%s,CURRENT_DATE)', (7,))
    assert query(conn, 'SELECT SUM(amount) FROM expenses')[0][0] == 7


def test_streamlit_pages_with_postgresql(db, monkeypatch):
    from streamlit.testing.v1 import AppTest
    conn, env = db
    subprocess.run(['psql', '-X', '-v', 'ON_ERROR_STOP=1', '-f', str(ROOT / 'demo_data.sql')], env=env, check=True, stdout=subprocess.DEVNULL)
    monkeypatch.setenv('DATABASE_URL', os.environ['TEST_DATABASE_URL'])
    monkeypatch.setenv('PGOPTIONS', env['PGOPTIONS'])
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=15)
    app.session_state['logged_in'] = True
    app.session_state['role'] = 'Admin'
    app.run()
    for page in app.sidebar.radio[0].options:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
        assert not any('Database request failed' in error.value for error in app.error), page
    assert query(conn, 'SELECT net_profit FROM profit_loss_summary')[0][0] == 4000
