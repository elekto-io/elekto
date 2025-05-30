from unittest import mock

from elekto import APP
from elekto.middlewares.auth import authenticated, auth_guard, csrf_guard, len_guard


######################################################################
####                        authenticate()                        ####
######################################################################
@mock.patch('elekto.middlewares.auth.F.g')
def test_authenticated_not_false(flask_mock, client):
    """
    Test any value for F.g.auth that's not explicitly `False` counts as being authenticated.

    FIXME: auth should be `True` if authenticated, but anything that is not `False` passes the check. Ideally this is
     made more strict.
    """
    assert authenticated()


def test_authenticated_true(client):
    """Test authenticated context."""
    with APP.app_context() as ctx:
        ctx.g.auth = True
        assert authenticated()


def test_authenticated_false(client):
    """Test unauthenticated context."""
    with APP.app_context() as ctx:
        ctx.g.auth = False
        assert not authenticated()


@mock.patch('elekto.middlewares.auth.hasattr', return_value=False)
def test_authenticated_attr_missing_from_flask_global_context(hasattr_mock, client):
    """Test the session is considered unauthenticated if `auth` can't be extracted from the global context."""
    assert not authenticated()


######################################################################
####                         auth_guard()                         ####
######################################################################
@mock.patch('elekto.middlewares.auth.F.redirect')
def test_auth_guard_authenticated(redirect, client):
    with APP.app_context() as ctx:
        ctx.g.auth = True

        func = mock.Mock()
        auth_guard(func)()
        assert not redirect.called


@mock.patch('elekto.middlewares.auth.F.redirect')
def test_auth_guard_unauthenticated(redirect, client):
    with APP.test_request_context():
        func = mock.Mock()
        auth_guard(func)()
        redirect.assert_called_once_with('/login?r=aHR0cDovL2xvY2FsaG9zdC8%3D')


######################################################################
####                         csrf_guard()                         ####
######################################################################
@mock.patch('elekto.middlewares.auth.F.redirect')
def test_csrf_guard_missing_url_state(redirect, client):
    with APP.test_request_context(path='/') as ctx:
        ctx.session.update({'state': 'foobar42'})
        func = mock.Mock()
        csrf_guard(func)()
        assert redirect.called


@mock.patch('elekto.middlewares.auth.F.redirect')
def test_csrf_guard_missing_session_state(redirect, client):
    with APP.test_request_context(path='/?state=foobar42'):
        func = mock.Mock()
        csrf_guard(func)()
        assert redirect.called


@mock.patch('elekto.middlewares.auth.F.redirect')
def test_csrf_guard_conflicting_states(redirect, client):
    """The state in the URL query param and the state in the session are different."""
    with APP.test_request_context(path='/?state=AAA') as ctx:
        ctx.session.update({'state': 'ZZZ'})
        func = mock.Mock()
        csrf_guard(func)()
        assert redirect.called


@mock.patch('elekto.middlewares.auth.F.redirect')
def test_csrf_guard_ok(redirect, client):
    csrf = 'foobar42'

    with APP.test_request_context(path=f'/?state={csrf}') as ctx:
        ctx.session.update({'state': csrf})
        func = mock.Mock()
        csrf_guard(func)()
        assert not redirect.called



######################################################################
####                         len_guard()                          ####
######################################################################
@mock.patch('elekto.middlewares.auth.F.redirect')
def test_len_guard_ok(redirect, client):
    with APP.test_request_context(path='/somewhere', method='POST', data={'password': 'something_very_long'}):
        func = mock.Mock()
        len_guard(func)()
        assert not redirect.called


@mock.patch('elekto.middlewares.auth.F.redirect')
def test_len_guard_empty_password(redirect, client):
    """Test the password being zero characters long."""
    with APP.test_request_context(path='/somewhere', method='POST', data={'password': ''}):
        func = mock.Mock()
        len_guard(func)()

        # The redirect is only triggered if the passcode is longer than zero characters (and smaller than the minimum
        # length).
        assert not redirect.called


@mock.patch('elekto.middlewares.auth.F.redirect')
def test_len_guard_short_password(redirect, client):
    """Test the password being longer than zero characters, but shorter than the minimum password length."""
    with APP.test_request_context(path='/somewhere', method='POST', data={'password': '1'}):
        func = mock.Mock()
        len_guard(func)()
        redirect.assert_called_once_with('http://localhost/somewhere')
