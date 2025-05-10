import os

import pytest

# Inject required environment variables
# TODO: make this nicer; this injection must happen before the APP and SESSION imports
os.environ['DB_CONNECTION'] = 'sqlite'

from elekto import APP, SESSION
from elekto.models.sql import drop_all, migrate


@pytest.fixture(scope="module", autouse=True)
def reset_db():
    with APP.app_context():
        drop_all(APP.config.get('DATABASE_URL'))


@pytest.fixture()
def client():
    with APP.app_context():
        migrate(APP.config.get('DATABASE_URL'))
        yield APP.test_client()
        SESSION.close()
        drop_all(APP.config.get('DATABASE_URL'))


@pytest.fixture()
def salt() -> bytes:
    return os.urandom(16)
