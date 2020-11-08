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
import k8s_elections.models.meta as meta

from k8s_elections import models, constants
from authlib.integrations.requests_client import OAuth2Session

APP = F.Flask(__name__)
APP.config.from_object('config')
META = APP.config.get('META')
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
        user = OAuth2Session(client_id=github['client_id'],
                             client_secret=github['client_secret'],
                             token=F.session[constants.AUTH_STATE])
        # print(user.get(constants.GITHUB_PROFILE).json())
        F.g.user = user.get(constants.GITHUB_PROFILE).json()
    else:
        F.g.user = None


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


@APP.route('/')
def welcome():
    return APP.name


@APP.route('/app')
def app():
    upcoming = ele.where('status', constants.ELEC_STAT_UPCOMING)
    return F.render_template('views/dashboard.html', upcoming=upcoming)


ele = meta.Election(META).query()


@APP.route('/app/elections')
def elections():
    status = F.request.args.get('status')
    elections = ele.all() if status is None else ele.where('status', status)
    elections.sort(key=lambda e: e['start_datetime'], reverse=True)
    return F.render_template('views/elections/index.html',
                             elections=elections,
                             status=status)


@APP.route('/app/elections/<eid>')
def elections_single(eid):
    election = ele.get(eid)
    candidates = ele.candidates(eid)
    return F.render_template('views/elections/single.html',
                             election=election,
                             candidates=candidates)


@APP.route('/app/elections/<eid>/<cid>')
def elections_candidate(eid, cid):
    election = ele.get(eid)
    candidate = ele.candidate(eid, cid)

    print(candidate)
    return F.render_template('views/elections/candidate.html',
                             election=election,
                             candidate=candidate)


# webhook route from kubernetes prow


@APP.route('/v1/webhooks/meta/updated', methods=['POST'])
def update_meta():
    """
    update the meta
    """
    ele.query()
    return "ok"
