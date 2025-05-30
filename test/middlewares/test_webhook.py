from unittest import mock

from elekto import APP
from elekto.middlewares.webhook import webhook_guard


@mock.patch('elekto.middlewares.webhook.F.abort')
@mock.patch('elekto.middlewares.webhook.hmac.compare_digest', return_value=True)
def test_webhook_guard_ok(compare_digest, abort, client):
    """Test happy path, mocking a successful comparison for the HMAC digests."""
    headers = {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': 'sha256=...'
    }

    with APP.test_request_context(headers=headers, method='POST'):
        func = mock.Mock()
        webhook_guard(func)()
        assert not abort.called


@mock.patch('elekto.middlewares.webhook.F.abort')
def test_webhook_guard_missing_sign(abort, client):
    headers = {
        'Content-Type': 'application/json',
    }

    with APP.test_request_context(headers=headers, method='POST'):
        func = mock.Mock()
        webhook_guard(func)()
        abort.assert_called_once_with(400, 'X-Hub-Signature-256 is not provided or invalid')


@mock.patch('elekto.middlewares.webhook.F.abort')
def test_webhook_guard_hmac_invalid(abort, client):
    headers = {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': '...'
    }

    with APP.test_request_context(headers=headers, method='POST'):
        func = mock.Mock()
        webhook_guard(func)()
        abort.assert_called_once_with(400, 'X-Hub-Signature-256 is not provided or invalid')


@mock.patch('elekto.middlewares.webhook.F.abort')
@mock.patch('elekto.middlewares.webhook.hmac.new', return_value=None)
def test_webhook_guard_error_on_digest_creation(hmac_new, abort, client):
    headers = {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': 'sha256=...'
    }

    with APP.test_request_context(headers=headers, method='POST'):
        func = mock.Mock()
        webhook_guard(func)()
        abort.assert_called_once_with(500, 'Error while creating a digest')


@mock.patch('elekto.middlewares.webhook.F.abort')
@mock.patch('elekto.middlewares.webhook.hmac.compare_digest', return_value=False)
def test_webhook_guard_bad_compare(compare_digest, abort, client):
    headers = {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': 'sha256=...'
    }

    with APP.test_request_context(headers=headers, method='POST'):
        func = mock.Mock()
        webhook_guard(func)()
        abort.assert_called_once_with(400, 'Invalid X-Hub-Signature-256 ')


@mock.patch('elekto.middlewares.webhook.F.abort')
@mock.patch('elekto.middlewares.webhook.hmac.compare_digest')
@mock.patch('elekto.middlewares.webhook.hmac.new')
def test_webhook_guard_debug_mode(hmac_new, compare_digest, abort, client):
    APP.config['DEBUG'] = True

    headers = {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': 'sha256=...'
    }

    with APP.test_request_context(headers=headers, method='POST'):
        func = mock.Mock()
        webhook_guard(func)()
        assert not abort.called
        assert not hmac_new.called
        assert not compare_digest.called
