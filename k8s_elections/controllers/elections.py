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
The module is responsible for handling all the election's related request.
"""

import flask as F

from k8s_elections.models import meta
from k8s_elections import constants, APP
from k8s_elections.controllers.authentication import auth_guard

# Yaml based Election backend
ele = meta.Election(APP.config.get('META')).query()


@APP.route('/app')
@auth_guard
def app():
    upcoming = ele.where('status', constants.ELEC_STAT_RUNNING)
    return F.render_template('views/dashboard.html', upcoming=upcoming)


@APP.route('/app/elections')
@auth_guard
def elections():
    status = F.request.args.get('status')
    elections = ele.all() if status is None else ele.where('status', status)
    elections.sort(key=lambda e: e['start_datetime'], reverse=True)
    return F.render_template('views/elections/index.html',
                             elections=elections,
                             status=status)


@APP.route('/app/elections/<eid>')
@auth_guard
def elections_single(eid):
    election = ele.get(eid)
    candidates = ele.candidates(eid)
    voters = ele.voters(eid)
    return F.render_template('views/elections/single.html',
                             election=election,
                             candidates=candidates,
                             voters=voters)


@APP.route('/app/elections/<eid>/candidates/<cid>')
@auth_guard
def elections_candidate(eid, cid):
    election = ele.get(eid)
    candidate = ele.candidate(eid, cid)

    print(candidate)
    return F.render_template('views/elections/candidate.html',
                             election=election,
                             candidate=candidate)


@APP.route('/app/elections/<eid>/vote')
def elections_voting_page(eid):
    election = ele.get(eid)
    candidates = ele.candidates(eid)
    voters = ele.voters(eid)
    if F.g.user['login'] not in voters['eligible_voters']:
        return 'not eligible to vote'
    return F.render_template('views/elections/vote.html',
                             election=election,
                             candidates=candidates,
                             voters=voters)

# webhook route from kubernetes prow


@APP.route('/v1/webhooks/meta/updated', methods=['POST'])
def update_meta():
    """
    update the meta
    """
    ele.query()
    return "ok"
