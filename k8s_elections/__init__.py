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

from k8s_elections.models import sql

APP = F.Flask(__name__)
APP.config.from_object('config')
SESSION = sql.create_session(APP.config.get('DATABASE_URL'))  # database

from k8s_elections.models import meta  # noqa
from k8s_elections import utils  # noqa
META, log = meta.Election(APP.config.get('META')).update_store()


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
    utils.set_session(APP)


@APP.teardown_appcontext
def destroy_session(exception=None):
    # Remove the database session
    SESSION.remove()


####
# Controllers

import k8s_elections.controllers  # noqa - this circular import is fine
