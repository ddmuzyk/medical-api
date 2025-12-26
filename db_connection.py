import os
from contextlib import contextmanager
from typing import Optional
from psycopg2 import pool as pg_pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

class DbPool:
    _pool: Optional[pg_pool.SimpleConnectionPool] = None

    @classmethod
    def init(cls) -> None:
        if cls._pool is None:
            cls._pool = pg_pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=os.environ["DB_HOST"],
                database=os.environ["DB_NAME"],
                user=os.environ["DB_USERNAME"],
                password=os.environ["DB_PASSWORD"],
            )

    @classmethod
    def getconn(cls):
        cls.init()
        assert cls._pool is not None
        return cls._pool.getconn()

    @classmethod
    def putconn(cls, conn):
        if cls._pool and conn:
            cls._pool.putconn(conn)

    @classmethod
    @contextmanager
    def cursor(cls, commit: bool = True):
        conn = None
        cur = None
        try:
            conn = cls.getconn()
            cur = conn.cursor(cursor_factory=RealDictCursor)  # Add this
            yield cur
            if commit:
                conn.commit() 
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if cur:
                cur.close()
            if conn:
                cls.putconn(conn)

    @classmethod
    def closeall(cls):
        if cls._pool:
            cls._pool.closeall()