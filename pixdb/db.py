from contextlib import contextmanager
from contextvars import ContextVar
from sqlalchemy import Connection, CursorResult, Engine

_transactional_conn = ContextVar[Connection]("transactional db connection", default=None)


class Database:
    def __init__(self, engine: Engine):
        self.engine = engine
    
    @contextmanager
    def transactional(self):
        if _transactional_conn.get():
            yield
        else:
            with self.engine.connect() as conn:
                token = _transactional_conn.set(conn)
                try:
                    with conn.begin():
                        yield
                finally:
                    _transactional_conn.reset(token)

    def execute(self, *args, **kwargs) -> CursorResult:
        conn = _transactional_conn.get()
        if conn:
            return conn.execute(*args, **kwargs)
        else:
            with self.engine.connect() as conn:
                return conn.execute(*args, **kwargs)
