from datetime import datetime

from flask.testing import FlaskClient
from nacl.utils import EncryptedMessage

from elekto import APP, SESSION, constants
from elekto.models.sql import User, Election, Voter


def create_user(token, username='carson') -> None:
    with APP.app_context():
        SESSION.add(User(username=username,
                         name='Carson Weeks',
                         token=token,
                         token_expires_at=datetime.max))
        SESSION.commit()


def provision_session(client: FlaskClient, token: str, username: str = 'carson') -> None:
    create_user(token, username)

    with client.session_transaction() as session:
        session[constants.AUTH_STATE] = token


def is_authenticated(client: FlaskClient) -> bool:
    """
    Test if the client has an authenticated session by calling /login and see what happens.

    If /login responds with HTTP302, the user IS authenticated.
    If /login responds with HTTP200, the user IS NOT authenticated.
    """
    return client.get('/login').status_code == 302


def user_exists(username: str) -> bool:
    with APP.app_context():
        return SESSION.query(User).filter_by(username=username).count() == 1


def get_csrf_token(client: FlaskClient, path='/login') -> str:
    response = client.get(path)
    csrf_token = response.data.decode('utf8').split('csrf_token" value="')[1].split('"')[0]
    return csrf_token


def vote(username: str, election_key: str) -> None:
    with APP.app_context():
        user_id = SESSION.query(User).filter_by(username=username).one().id
        election_id = SESSION.query(Election).filter_by(key=election_key).one().id
        SESSION.add(Voter(
            user_id=user_id,
            election_id=election_id,
        ))
        SESSION.commit()


ENCRYPTED_MESSAGE = EncryptedMessage(b'\xa1\xbaH\xfb\xb3\t9X\xb4\x8f\xeb\x0f\x80\xd9\x11{\xc1!\xe8\x8f\x96\x0f\x94\x18\xf9\xbfi\\,oe:\xd8\xcey\xe8\xbeJB\xa5\xa1\x17?\x81qJ\xde\x9e\x03\x1b\x9d\x1dG`;\x82\xce\xb8\x17Q,\xec\x02\x95\x92\xaa\xd1\x1e\xa1\xa9\xef\xd3q\xd3~3')
