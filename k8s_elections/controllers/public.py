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
The controller is responsible for handling all application's request that does
not require authentication.
"""

import flask as F

from k8s_elections import APP, SESSION
from k8s_elections.models.sql import Election
from k8s_elections.controllers.elections import META


@APP.route('/')
def welcome():
    return F.render_template('/views/public/welcome.html')


@APP.route('/elections')
def public_elections():
    elections = META.all()
    elections.sort(key=lambda e: e['start_datetime'], reverse=True)

    return F.render_template('views/public/elections_index.html',
                             elections=elections)


@APP.route('/elections/<eid>')
def public_election(eid):
    election = META.get(eid)
    candidates = META.candidates(eid)

    return F.render_template('views/public/elections_single.html',
                             election=election,
                             candidates=candidates)


@APP.route('/core/methods/schulze')
def public_schulze():
    query = SESSION.query(Election).all()
    return "%s" % len(query)
    # return "Public Schulze"
