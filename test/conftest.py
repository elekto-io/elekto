import os
import shutil

import pytest

# Inject required environment variables
# TODO: make this nicer; this injection must happen before the APP and SESSION imports (or any other imports that
#  trigger APP and SESSION).
os.environ['DB_CONNECTION'] = 'sqlite'

from elekto import APP, SESSION
from elekto.models import meta
from elekto.models.sql import drop_all, migrate
from elekto.models.utils import sync

from test.factories import ElectionFactory, BallotFactory, VoterFactory, UserFactory


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


@pytest.fixture()
def db_session():
    return SESSION


@pytest.fixture(autouse=True)
def db_factories(db_session):
    ElectionFactory._meta.sqlalchemy_session = db_session
    BallotFactory._meta.sqlalchemy_session = db_session
    VoterFactory._meta.sqlalchemy_session = db_session
    UserFactory._meta.sqlalchemy_session = db_session


@pytest.fixture()
def metadir(tmpdir):
    """
    Set up a temporary meta directory per test. This requires the developer to have a correct meta directory in the
    local repository.

    This also updates the META.PATH value to point to the temporary directory.

    The generated tmpdir is returned for further use.
    """
    meta_src = os.path.join(os.path.dirname(__file__), '..', 'meta')
    assert os.path.isdir(meta_src), f'{meta_src} is not a directory'
    shutil.copytree(meta_src, str(tmpdir), dirs_exist_ok=True)
    APP.config['META']['PATH'] = str(tmpdir)
    return tmpdir


@pytest.fixture()
def load_metadir(metadir):
    with APP.app_context():
        sync(SESSION, meta.Election.all())

    return metadir
