import os
import shutil
import zipfile

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

KDF_KEY_MOCK = b'\x8f\x85"!17=t\xee7P\x07"\xb4\xe0\x07\x9a\xce\xa4\xef\x96\xcb\x96\x06\x13\xc5\xa0\x8d\xb30\x1al'


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
    zip_path = os.path.join(os.path.dirname(__file__), 'meta.zip')
    meta_src = os.path.join(os.path.dirname(__file__), 'meta')
    main_branch_src = os.path.join(meta_src, 'elekto.meta.test-main', 'elections')

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(meta_src)

    shutil.move(main_branch_src, meta_src)

    assert os.path.isdir(meta_src), f'{meta_src} is not a directory'
    shutil.copytree(meta_src, str(tmpdir), dirs_exist_ok=True)
    APP.config['META']['PATH'] = str(tmpdir)
    yield tmpdir
    shutil.rmtree(meta_src)


@pytest.fixture()
def load_metadir(metadir):
    with APP.app_context():
        sync(SESSION, meta.Election.all())

    return metadir
