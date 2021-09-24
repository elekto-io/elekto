# Copyright 2020 The Elekto Authors
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

from elekto import APP
from elekto.models import meta


@APP.route('/')
def welcome():
    return F.redirect(F.url_for('app'))


@APP.route('/elections')
def public_elections():
    status = F.request.args.get('status')
    res = meta.Election.all() if status is None else meta.Election.where('status', status)
    res.sort(key=lambda e: e['start_datetime'], reverse=True)

    return F.render_template('views/public/elections_index.html',
                             elections=res,
                             status=status)


@APP.route('/elections/<eid>')
def public_election(eid):
    election = meta.Election(eid)
    candidates = election.candidates()

    return F.render_template('views/public/elections_single.html',
                             election=election.get(),
                             candidates=candidates)
                             
@APP.route('/health')
def health_check():
    status_code = F.Response(status=200)
    return status_code
