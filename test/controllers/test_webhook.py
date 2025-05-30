from unittest import mock

from flask.testing import FlaskClient

from elekto import APP


def perform_sync(client: FlaskClient):
    APP.config['DEBUG'] = True  # Skip X-Hub signature validation, which is tested in the webhook middleware tests.
    try:
        client.post('/v1/webhooks/meta/sync')
    except TypeError:
        # At the moment, this endpoint doesn't return a string rather than a valid response type. This will cause a
        # TypeError which is caught here. The below assertions are made to verify the endpoint's internals work OK.
        ...

    APP.config['DEBUG'] = False


@mock.patch('elekto.controllers.webhook.os.path.exists')
@mock.patch('elekto.controllers.webhook.meta.Meta.clone')
@mock.patch('elekto.controllers.webhook.sync')
def test_webhook_metadir_does_not_exist(sync_mock, clone_mock, path_exists_mock, client: FlaskClient):
    path_exists_mock.return_value = False

    perform_sync(client)
    clone_mock.assert_called_once()
    sync_mock.assert_called_once()


@mock.patch('elekto.controllers.webhook.os.path.exists')
@mock.patch('elekto.controllers.webhook.os.path.isdir')
@mock.patch('elekto.controllers.webhook.meta.Meta.clone')
@mock.patch('elekto.controllers.webhook.sync')
@mock.patch('elekto.controllers.webhook.meta.Election.all')
def test_webhook_metadir_is_not_a_dir(all_mock, sync_mock, clone_mock, path_isdir_mock, path_exists_mock, client: FlaskClient):
    all_mock.return_value = []
    path_exists_mock.return_value = True
    path_isdir_mock.return_value = False

    perform_sync(client)
    clone_mock.assert_called_once()
    sync_mock.assert_called_once()


@mock.patch('elekto.controllers.webhook.os.path.exists')
@mock.patch('elekto.controllers.webhook.os.path.isdir')
@mock.patch('elekto.controllers.webhook.meta.Meta.pull')
@mock.patch('elekto.controllers.webhook.sync')
@mock.patch('elekto.controllers.webhook.meta.Election.all')
def test_webhook_metadir_updates(all_mock, sync_mock, pull_mock, path_isdir_mock, path_exists_mock, client: FlaskClient):
    all_mock.return_value = []
    path_exists_mock.return_value = True
    path_isdir_mock.return_value = True

    perform_sync(client)
    pull_mock.assert_called_once()
    sync_mock.assert_called_once()
