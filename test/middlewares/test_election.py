from unittest import mock

import flask as F
from freezegun import freeze_time

from elekto import APP
from elekto.middlewares.election import (
    admin_guard,
    voter_guard,
    exception_guard,
    has_completed_condition,
    has_voted_condition,
)
from elekto.models.sql import User
from test.factories import ElectionFactory, VoterFactory, UserFactory


######################################################################
####                        admin_guard()                         ####
######################################################################
@mock.patch('elekto.middlewares.election.F.abort')
def test_admin_guard_ok(abort, client, metadir):
    with APP.test_request_context():
        F.g.user = User(username='kalkayan')
        func = mock.Mock()
        admin_guard(func)(eid='name_the_app')
        assert not abort.called


@mock.patch('elekto.middlewares.election.F.abort')
def test_admin_guard_unauthorized(abort, client, metadir):
    """Make guard call with a non-admin user."""
    with APP.test_request_context():
        F.g.user = User(username='oduludo')
        func = mock.Mock()
        admin_guard(func)(eid='name_the_app')
        abort.assert_called_once_with(401)


@mock.patch('elekto.middlewares.election.F.abort')
def test_admin_guard_missing_eid(abort, client, metadir):
    """Make guard call without an election ID (eid)."""
    with APP.test_request_context():
        F.g.user = User(username='kalkayan')
        func = mock.Mock()
        admin_guard(func)()
        abort.assert_called_once_with(401)


######################################################################
####                        voter_guard()                         ####
######################################################################
@mock.patch('elekto.middlewares.election.F.render_template')
@mock.patch('elekto.middlewares.election.F.abort')
def test_voter_guard_ok(abort, render_template, client, metadir):
    with APP.test_request_context():
        F.g.user = User(username='kalkayan')
        func = mock.Mock()
        voter_guard(func)(eid='name_the_app')
        assert not abort.called
        assert not render_template.called


@mock.patch('elekto.middlewares.election.F.render_template')
@mock.patch('elekto.middlewares.election.F.abort')
def test_voter_guard_missing_eid(abort, render_template, client, metadir):
    """Make guard call without an election ID (eid)."""
    with APP.test_request_context():
        F.g.user = User(username='kalkayan')
        func = mock.Mock()
        voter_guard(func)()
        abort.assert_called_once_with(404)
        assert not render_template.called


@mock.patch('elekto.middlewares.election.F.render_template')
@mock.patch('elekto.middlewares.election.F.abort')
def test_voter_guard_not_eliginle(abort, render_template, client, metadir):
    with APP.test_request_context():
        F.g.user = User(username='oduludo')
        func = mock.Mock()
        voter_guard(func)(eid='name_the_app')
        assert not abort.called
        render_template.assert_called_once_with('errors/not_eligible.html', election=mock.ANY)


######################################################################
####                      exception_guard()                       ####
######################################################################
@mock.patch('elekto.middlewares.election.F.redirect')
@mock.patch('elekto.middlewares.election.F.abort')
def test_exception_guard_missing_eid(abort, redirect, client, metadir):
    with APP.test_request_context():
        F.g.user = User(username='kalkayan')
        func = mock.Mock()
        exception_guard(func)()
        abort.assert_called_once_with(404)
        assert not redirect.called


@freeze_time('2025-05-05')
@mock.patch('elekto.middlewares.election.F.flash')
@mock.patch('elekto.middlewares.election.F.redirect')
@mock.patch('elekto.middlewares.election.F.abort')
def test_exception_guard_exception_overdue(abort, redirect, flash, client, metadir):
    with APP.test_request_context():
        F.g.user = User(username='kalkayan')
        func = mock.Mock()
        exception_guard(func)(eid='name_the_app')
        assert not abort.called
        redirect.assert_called_once_with('/app/elections/name_the_app')
        flash.assert_called_once_with('Not accepting any exception request.')


@freeze_time('2023-08-1')
@mock.patch('elekto.middlewares.election.F.flash')
@mock.patch('elekto.middlewares.election.F.redirect')
@mock.patch('elekto.middlewares.election.F.abort')
def test_exception_guard_already_eligible(abort, redirect, flash, client, metadir):
    with APP.test_request_context():
        F.g.user = User(username='kalkayan')
        func = mock.Mock()
        exception_guard(func)(eid='name_the_app')
        assert not abort.called
        redirect.assert_called_once_with('/app/elections/name_the_app')
        flash.assert_called_once_with('You are already eligible to vote in the election.')


@freeze_time('2023-08-1')
@mock.patch('elekto.middlewares.election.F.flash')
@mock.patch('elekto.middlewares.election.F.redirect')
@mock.patch('elekto.middlewares.election.F.abort')
def test_exception_guard_ok(abort, redirect, flash, client, metadir):
    with APP.test_request_context():
        F.g.user = User(username='oduludo')
        func = mock.Mock()
        exception_guard(func)(eid='name_the_app')
        assert not abort.called
        assert not redirect.called
        assert not flash.called


######################################################################
####                  has_completed_condition()                   ####
######################################################################
@mock.patch('elekto.middlewares.election.F.abort')
def test_has_completed_condition_missing_eid(abort, client, metadir):
    with APP.test_request_context():
        func = mock.Mock()
        has_completed_condition(func)()
        abort.assert_called_once_with(404)


@freeze_time('2023-08-25')
@mock.patch('elekto.middlewares.election.F.render_template')
def test_has_completed_condition_false(render_template, client, metadir):
    with APP.test_request_context():
        func = mock.Mock()
        has_completed_condition(func)(eid='name_the_app')
        render_template.assert_called_once_with(
            'errors/message.html',
            title='The election is not completed yet',
            message='The application needs election to be \
                                     over first.'  # Yes, that funky formatting is required for the test to pass...
        )


@freeze_time('2025-05-05')
@mock.patch('elekto.middlewares.election.F.abort')
@mock.patch('elekto.middlewares.election.F.render_template')
def test_has_completed_condition_ok(render_template, abort, client, metadir):
    with APP.test_request_context():
        func = mock.Mock()
        has_completed_condition(func)(eid='name_the_app')
        assert not abort.called
        assert not render_template.called


######################################################################
####                    has_voted_condition()                     ####
######################################################################
@mock.patch('elekto.middlewares.election.F.abort')
def test_has_voted_condition_missing_eid(abort, client, metadir):
    with APP.test_request_context():
        func = mock.Mock()
        has_voted_condition(func)()
        abort.assert_called_once_with(404)


@mock.patch('elekto.middlewares.election.F.redirect')
def test_has_voted_condition_not_yet_voted(redirect, client, metadir):
    _ = ElectionFactory.create(key='name_the_app')
    user = UserFactory.create(username='kalkayan')

    with APP.test_request_context():
        F.g.user = user
        func = mock.Mock()
        has_voted_condition(func)(eid='name_the_app')
        redirect.assert_called_once_with('/app/elections/name_the_app')


@mock.patch('elekto.middlewares.election.F.redirect')
def test_has_voted_condition_ok(redirect, client, metadir):
    election = ElectionFactory.create(key='name_the_app')
    user = UserFactory.create(username='kalkayan')
    _ = VoterFactory.create(election=election, user=user)

    with APP.test_request_context():
        F.g.user = user
        func = mock.Mock()
        has_voted_condition(func)(eid='name_the_app')
        assert not redirect.called
