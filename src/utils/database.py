import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from src.utils import logger

import sqlite3

def get_db_config(profile: str = "default"):
    """
    Returns DB configuration. 
    'default' uses existing env vars.
    'inquiry' (example) uses a different set of env vars.
    """
    if profile == "backend":
        return {
            "host": os.getenv("INQUIRY_DB_HOST", "192.168.1.62"),
            "port": os.getenv("INQUIRY_DB_PORT", "5432"),
            "user": os.getenv("INQUIRY_DB_USER", "postgres"),
            "password": os.getenv("INQUIRY_DB_PASS", "POSTGRES_PASS"),
            "dbname": os.getenv("INQUIRY_DB_NAME", "erp"),
            "db_type": "postgres"
        }
    
    # Default behavior remains UNCHANGED
    return {
        "host": os.getenv("TARGET_DB_HOST", os.getenv("DB_HOST", "localhost")),
        "port": os.getenv("TARGET_DB_PORT", os.getenv("DB_PORT", "5432")),
        "user": os.getenv("TARGET_DB_USER", os.getenv("DB_USER", "postgres")),
        "password": os.getenv("TARGET_DB_PASS", os.getenv("DB_PASS", "postgres")),
        "dbname": os.getenv("TARGET_DB_NAME", os.getenv("DB_NAME", "postgres")),
        "db_type": "postgres"
    }


@contextmanager
def get_db_connection(db_config: dict = None, profile: str = "default"):
    """Context manager for database connections (Postgres or SQLite)"""
    conn = None
    config = db_config or get_db_config(profile)
    db_type = config.get("db_type", "postgres")
    
    try:
        if db_type == "postgres":
            logger.debug(f"Connecting to Postgres database: {config.get('host')}:{config.get('port')}/{config.get('dbname')}")
            conn = psycopg2.connect(
                host=config.get("host"),
                port=int(config.get("port", 5432)),
                dbname=config.get("dbname"),
                user=config.get("user"),
                password=config.get("password")
            )
            logger.info(f"Postgres database connection established")
        elif db_type == "sqlite":
            db_path = config.get("db_path", "database.sqlite")
            logger.debug(f"Connecting to SQLite database: {db_path}")
            conn = sqlite3.connect(db_path)
            logger.info(f"SQLite database connection established")
        else:
            raise ValueError(f"Unsupported db_type: {db_type}")
            
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")



class LoggingCursor:
    """Wrapper around RealDictCursor that logs queries and results"""

    def __init__(self, cursor):
        self._cursor = cursor
        self._last_query = None
        self._last_params = None

    def execute(self, query, params=None):
        self._last_query = query
        self._last_params = params
        
        # Clean up query for logging (remove extra whitespace)
        clean_query = " ".join(query.split())
        logger.info(f"Executing query: {clean_query}")
        if params:
            logger.debug(f"Query params: {params}")
        
        result = self._cursor.execute(query, params)
        
        rowcount = self._cursor.rowcount
        if rowcount >= 0:
            logger.info(f"Rows affected: {rowcount}")
        
        return result

    def fetchone(self):
        result = self._cursor.fetchone()
        if result:
            logger.debug(f"Fetched 1 row")
        else:
            logger.debug(f"No rows returned")
        return result

    def fetchall(self):
        results = self._cursor.fetchall()
        logger.info(f"Fetched {len(results)} rows")
        return results

    def fetchmany(self, size=None):
        results = self._cursor.fetchmany(size)
        logger.info(f"Fetched {len(results)} rows")
        return results

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        self._cursor.close()

    def __getattr__(self, name):
        return getattr(self._cursor, name)



@contextmanager
def get_db_cursor(commit=True, db_config: dict = None, profile: str = "default"):
    """Context manager for database cursor with auto-commit and logging"""
    config = db_config or get_db_config(profile)
    db_type = config.get("db_type", "postgres")
    
    with get_db_connection(config) as conn:
        if db_type == "postgres":
            raw_cursor = conn.cursor(cursor_factory=RealDictCursor)
        elif db_type == "sqlite":
            conn.row_factory = sqlite3.Row
            raw_cursor = conn.cursor()
        
        cursor = LoggingCursor(raw_cursor)
        try:
            yield cursor
            if commit:
                conn.commit()
                logger.debug("Transaction committed")
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error, transaction rolled back: {e}")
            raise
        finally:
            cursor.close()
