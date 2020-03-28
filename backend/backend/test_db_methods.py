from sqlalchemy import create_engine
from backend import db_models as fk

engine = create_engine('sqlite:///db.sqlite', echo=True)


def do_create():
    fk.Base.metadata.create_all(engine)


def make_test_usr():
    test_usr = fk.FabUser('test', 'test', 'test@test.test', 'Bob', 'Bobson', 'USA', 'CA', 'LA', 'ender3', 'fantastic')
    return test_usr
