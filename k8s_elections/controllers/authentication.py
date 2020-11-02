# Copyright 2020 Manish Sahani
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author(s):         Manish Sahani <rec.manish.sahani@gmail.com>

"""
The module is responsible for handling all the user authentication related
queries, and user's session management
"""

import flask as F

from authlib.integrations.requests_client import OAuth2Session
from k8s_elections import constants, APP


def check():
    """
    Check the state of user's authentication

    Returns:
        (bool)
    """
    return hasattr(F.g, 'user') and F.g.user is not None


def csrf_protection(ses, req):
    """
    Validate the CSRF_STATE token

    Args:
        ses (dict): application's session dict
        req (dict): request's args dict

    Returns:
        F.redirect: if not same redirect to login or error url
    """
    if constants.CSRF_STATE not in req.args.keys() \
            or constants.CSRF_STATE not in ses.keys() \
            or req.args[constants.CSRF_STATE] != ses[constants.CSRF_STATE]:
        return F.redirect(F.url_for('render_login_page'))


def oauth_session(vendor):
    """
    Create and return an OAuth2Session for the given vendor

    Args:
        vendor (dict): OAuth Vendor config with id, secret and scope

    Returns:
        OAuth2Session: OAuth2Session's object
    """
    return OAuth2Session(vendor['client_id'],
                         vendor['client_secret'],
                         scope=github['scope'])


# Common Login Routes


@APP.route('/login', methods=['GET'])
def render_login_page():
    """
    Render login page, see prototype document - http://bit.ly/k8s-markup

    Returns:
        F.redirect: redirect to the login page.
    """
    if check():
        return F.redirect('/app')

    return F.render_template('login.html')


@APP.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Logout the authenticated user and destory his session

    Returns:
        F.redirect: redirect to the login page.
    """
    F.session.pop(constants.AUTH_STATE)
    return F.redirect('/login')


# OAuth Routes
#
# It's very common for other organizations to use SSO or other vendor of their
# choice therefore please use the following route pattern for specifying other
# OAuth - /oauth/<vendor>/login and /oauth/<vendor>/callback

# Github
github = APP.config.get('GITHUB')


@APP.route('/oauth/github/login', methods=['POST'])
def oauth_github_login():
    """
    Redirect the user to the github vendor login page

    Returns:
        F.redirect
    """
    client = oauth_session(github)
    uri, state = client.create_authorization_url(constants.GITHUB_AUTHORIZE)

    # CSRF protection
    F.session[constants.CSRF_STATE] = state

    return F.redirect(uri)


@APP.route(github['redirect'])
def oauth_github_redirect():
    """
    Callback for the OAuth vendor and start the user's session.

    Returns:
        F.redirect: redirect to application's dashboard
    """
    # CSRF protection with the previously store state
    csrf_protection(F.session, F.request)

    client = oauth_session(github)
    token = client.fetch_token(constants.GITHUB_ACCESS,
                               authorization_response=F.request.url)

    # Add user's authentication token to the flask session
    F.session[constants.AUTH_STATE] = token

    return F.redirect('/app')
