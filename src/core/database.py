import atexit

from typing import Any, Optional, Sequence, Generator

from psycopg_pool import ConnectionPool
from psycopg import rows, sql
from psycopg.errors import UniqueViolation

from src.settings import settings
from core.logger import Logger


class Database:
    logger = Logger("Database")

    def __init__(self, dsn: str = settings["DATABASE"], min_size: int = 1, max_size: int = 2096) -> None:
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[ConnectionPool] = None

        atexit.register(self.close)

    def close(self):
        """ close pool cleanly """
        if self.pool:
            try: self.pool.close()
            except Exception as e:
                self.logger.error(f"an error happened while closing the db pool  error {e}")

    def _ensure_pool(self) -> None:
        """ ensure pool exists (reconnect) """
        if not self.pool:
            self.pool: Optional[ConnectionPool] = ConnectionPool(
                settings["DATABASE"],
                min_size=self.min_size,
                max_size=self.max_size,
                num_workers=settings["CPU_CORES"],
            )

    def fetch(self, sql_query: str, params: Optional[Sequence[Any]] = None) -> Generator[Any, None, None]:
        """ fetch all/one row/s for a query """
        self._ensure_pool()
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=rows.dict_row) as cur:
                cur.execute(sql_query, params)
                yield from cur

    def insert(self, sql_query: sql.Composed, values: Sequence[Any]) -> bool:
        """ insert a record and return false on unique violation """
        self._ensure_pool()
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(sql_query, values)
                    conn.commit()
                except UniqueViolation:
                    conn.rollback()
                    return False
                except Exception as e:
                    conn.rollback()
                    self.logger.error(f'Error inserting record: {e}')
                    return False
        return True

    def execute(self, sql_query: str, params: Optional[Sequence[Any]] = None) -> bool:
        """ execute an arbitrary sql statement """
        self._ensure_pool()
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                try:
                    if params is None: cur.execute(sql_query)
                    else: cur.execute(sql_query, params)
                    conn.commit()
                except (UniqueViolation, Exception) as e:
                    conn.rollback()
                    self.logger.error(f'Error executing SQL: {e}')
                    return False
        return True

    def delete_record(self, record_id: int) -> bool:
        """ delete a record by id """
        self._ensure_pool()
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("DELETE FROM articles WHERE id = %s;", (record_id,))
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    self.logger.error(f'Error deleting record: {e}')
                    return False
        return True
