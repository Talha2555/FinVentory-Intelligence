from unittest.mock import MagicMock

import psycopg2
import pytest

import database


def test_configuration(monkeypatch):
    for name in ['DATABASE_URL', 'PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD', 'PGSSLMODE']:
        monkeypatch.delenv(name, raising=False)
    assert database.connection_options() == {'connect_timeout': 10}
    monkeypatch.setenv('PGHOST', 'db.example')
    monkeypatch.setenv('PGPASSWORD', 'secret')
    assert database.connection_options()['host'] == 'db.example'
    monkeypatch.setenv('DATABASE_URL', 'postgresql://example/db')
    assert database.connection_options() == {'dsn': 'postgresql://example/db', 'connect_timeout': 10}


def connection(monkeypatch):
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    monkeypatch.setattr(database.psycopg2, 'connect', MagicMock(return_value=conn))
    return conn, cursor


def test_success_closes_connection_and_binds_params(monkeypatch):
    conn, cursor = connection(monkeypatch)
    cursor.description = [('value',)]
    cursor.fetchall.return_value = [(42,)]
    assert database.fetch_frame('SELECT %s AS value', (42,)).iloc[0, 0] == 42
    cursor.execute.assert_called_once_with('SELECT %s AS value', (42,))
    assert conn.__exit__.call_args.args[0] is None  # psycopg context commits
    conn.close.assert_called_once()


def test_query_failure_rolls_back_and_closes(monkeypatch, caplog):
    conn, cursor = connection(monkeypatch)
    cursor.execute.side_effect = psycopg2.ProgrammingError('sensitive contents')
    with pytest.raises(database.DatabaseError, match='Database operation failed'):
        database.execute('broken SQL')
    assert conn.__exit__.call_args.args[0] is psycopg2.ProgrammingError
    conn.close.assert_called_once()
    assert 'sensitive' not in caplog.text


def test_connection_failure_is_sanitized(monkeypatch, caplog):
    monkeypatch.setattr(database.psycopg2, 'connect', MagicMock(side_effect=psycopg2.OperationalError('password=secret')))
    with pytest.raises(database.DatabaseError):
        database.fetch_frame('SELECT 1')
    assert 'secret' not in caplog.text
