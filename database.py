"""Short-lived database connections: no shared sessions or poisoned transactions."""
import logging
import os

import pandas as pd
import psycopg2

logger = logging.getLogger(__name__)


class DatabaseError(RuntimeError):
    pass


def connection_options():
    if os.getenv('DATABASE_URL'):
        return {'dsn': os.environ['DATABASE_URL'], 'connect_timeout': 10}
    return {key: os.environ[env] for key, env in {
        'host': 'PGHOST', 'port': 'PGPORT', 'dbname': 'PGDATABASE',
        'user': 'PGUSER', 'password': 'PGPASSWORD', 'sslmode': 'PGSSLMODE',
    }.items() if env in os.environ} | {'connect_timeout': 10}


def _run(query, params=None, *, read=False):
    conn = None
    try:
        conn = psycopg2.connect(**connection_options())
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if read:
                    return pd.DataFrame(cursor.fetchall(), columns=[c[0] for c in cursor.description])
    except psycopg2.Error as exc:
        # Do not log exception text: drivers may include credentials or row contents.
        logger.error('Database operation failed (SQLSTATE %s)', exc.pgcode or 'connection')
        raise DatabaseError('Database operation failed') from None
    finally:
        if conn is not None:
            conn.close()


def fetch_frame(query, params=None):
    return _run(query, params, read=True)


def execute(query, params=None):
    _run(query, params)
