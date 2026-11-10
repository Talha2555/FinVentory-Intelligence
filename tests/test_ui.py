from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

import database

ROOT = Path(__file__).resolve().parents[1]


def test_login_rejects_bad_credentials(tmp_path, monkeypatch):
    import auth
    path = tmp_path / 'users.csv'
    path.write_text('username,password_hash,role\nowner,' + auth.hash_password('a secure password') + ',Admin\n')
    monkeypatch.setenv('FINVENTORY_USERS_FILE', str(path))
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=15).run()
    app.text_input[0].input('owner')
    app.text_input[1].input('wrong')
    app.button[0].click().run()
    assert not app.exception
    assert app.error[0].value == 'Invalid credentials. Please try again.'
    app.text_input[1].input('a secure password')
    monkeypatch.setattr(database, 'fetch_frame', lambda *args: pd.DataFrame())
    app.button[0].click().run()
    assert app.session_state['role'] == 'Admin'
    assert not app.exception


def test_admin_pages_and_staff_navigation(monkeypatch):
    def frame(sql):
        if 'profit_loss_summary' in sql:
            return pd.DataFrame([dict(total_revenue=40,total_cost=20,gross_profit=20,total_expenses=7,net_profit=13)])
        if 'demand_prediction_view' in sql:
            return pd.DataFrame([dict(product_id=1,name='Widget',predicted_sales=9)])
        if 'monthly_sales_view' in sql:
            return pd.DataFrame([dict(month=pd.Timestamp('2026-09-01'),revenue=40)])
        return pd.DataFrame()
    monkeypatch.setattr(database, 'fetch_frame', frame)
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=15)
    app.session_state['logged_in'] = True
    app.session_state['role'] = 'Admin'
    app.run()
    for page in app.sidebar.radio[0].options:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
    app.session_state['role'] = 'Staff'
    app.run()
    assert app.sidebar.radio[0].options == ['Dashboard', 'Inventory & Alerts', 'AI Demand Predictions']


def test_database_failure_stops_false_success(monkeypatch):
    def fail(*args):
        raise database.DatabaseError()
    monkeypatch.setattr(database, 'fetch_frame', fail)
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=15)
    app.session_state['logged_in'] = True
    app.session_state['role'] = 'Staff'
    app.run()
    app.sidebar.radio[0].set_value('Inventory & Alerts').run()
    assert not app.exception
    assert app.error
    assert not app.success
