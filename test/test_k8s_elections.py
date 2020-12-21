import os
import sys
import pytest

# Workaround to safely import the k8s_elections module
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from k8s_elections import APP  # noqa
from k8s_elections.models.sql import migrate  # noqa


@pytest.fixture
def client():
    # Generate Database
    db = os.path.abspath('./test.db')
    os.system('touch {}'.format(db))

    with APP.test_client() as client:
        with APP.app_context():
            migrate(APP.config['DATABASE_URL'])
        yield client

    os.system('rm {}'.format(db))


def test_clone(client):
    """
    Tests the cloing of the meta repo
    """
    assert os.path.isdir(APP.config['META']['PATH'])


def test_welcome(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert str.encode(APP.config['NAME']) in rv.data
