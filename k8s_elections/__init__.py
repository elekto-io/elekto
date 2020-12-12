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

import os
import flask as F

from k8s_elections import models, constants
from authlib.integrations.requests_client import OAuth2Session

APP = F.Flask(__name__, static_folder=os.path.abspath('static'))
APP.config.from_object('config')
SESSION = models.create_session(APP.config.get('DATABASE_URL'))


@APP.before_request
def before_request():
    # Add APP name and other organization based configration in the global
    # request object
    F.g.NAME = APP.config.get('NAME')

    # When you import jinja2 macros, they get cached which is annoying for
    # local development, so wipe the cache every request.
    if APP.config.get('DEBUG') or 'localhost' in F.request.host_url:
        APP.jinja_env.cache = {}

    # Set Session
    #
    # Add the loggedin user in the global request object g
    F.session.permanent = True
    if constants.AUTH_STATE in F.session.keys() and \
            F.session[constants.AUTH_STATE] is not None:
        # Authenticate with every request if the user's token correct or not
        github = APP.config.get('GITHUB')
        oauthsession = OAuth2Session(client_id=github['client_id'],
                                     client_secret=github['client_secret'],
                                     token=F.session[constants.AUTH_STATE])
        resp = oauthsession.get(constants.GITHUB_PROFILE)

        # if unable to fetch the user's info, set auth to False
        if resp.status_code != 200:
            F.g.user = None
            F.g.auth = False
            F.session.pop(constants.AUTH_STATE)
        else:
            F.g.user = resp.json()
            F.g.auth = True
    else:
        F.g.user = None
        F.g.auth = False


@APP.teardown_appcontext
def destroy_session(exception=None):
    # Remove the database session
    SESSION.remove()


# Authentication
#
# This section is where the authentication routes are defined, the application
# is developed for only authentication user via an external vendor, currently
# github OAuth is supported.

import k8s_elections.controllers.errors  # noqa
import k8s_elections.controllers.authentication  # noqa
import k8s_elections.controllers.elections  # noqa
import k8s_elections.controllers.public  # noqa
