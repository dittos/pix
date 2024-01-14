from sqlalchemy import create_engine, literal, select

from pixdb.db import Database

engine = create_engine("sqlite://", echo=True)
db = Database(engine)


def test_execute_without_transaction():
    db.execute(select(literal(1)))


def test_execute_with_transaction():
    with db.transactional():
        db.execute(select(literal(1)))


def test_execute_with_nested_transaction():
    with db.transactional():
        with db.transactional():
            db.execute(select(literal(1)))
