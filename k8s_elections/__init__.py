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

import flask as F

from k8s_elections import models, constants

APP = F.Flask(__name__)
APP.config.from_object('config')

SESSION = models.create_session(APP.config.get('DATABASE_URL'))


@APP.before_request
def before_request():
    # When you import jinja2 macros, they get cached which is annoying for
    # local development, so wipe the cache every request.
    if APP.config.get('DEBUG') or 'localhost' in F.request.host_url:
        APP.jinja_env.cache = {}

    # Set Session
    #
    # Add the loggedin user in the global request object g
    F.session.permanent = True
    if 'token' in F.session.keys() and F.session['token'] is not None:
        # F.request.headers['token'] = F.session['token']
        # user = F.request.get('https://api.github.com/user').content
        print('')
    else:
        F.g.token = None


@APP.teardown_appcontext
def destroy_session(exception=None):
    # Remove the database session
    SESSION.remove()


# Authentication
#
# This section is where the authentication routes are defined, the application
# is developed for only authentication user via an external vendor, currently
# github OAuth is supported.

import k8s_elections.controllers.authentication  # noqa


@APP.route('/app')
def app():
    return 'Dashboard'
