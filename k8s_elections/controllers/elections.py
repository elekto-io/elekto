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

from k8s_elections.models import meta, Election, Ballot, Voter
from k8s_elections import constants, APP, SESSION
from k8s_elections.controllers.authentication import auth_guard
from werkzeug.security import generate_password_hash

# Yaml based Election backend
ele = meta.Election(APP.config.get('META')).query()


@APP.route('/app')
@auth_guard
def app():
    # Find all the user's past elections
    query = SESSION.query(Election).filter(Election.id.in_(
        SESSION.query(Voter.election_id).filter(
            Voter.handle == F.g.user['login']).subquery()
    )).all()

    upcoming = ele.where('status', constants.ELEC_STAT_RUNNING)
    past = [ele.get(e.key) for e in query]

    return F.render_template('views/dashboard.html',
                             upcoming=upcoming,
                             past=past)


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


@APP.route('/app/elections/<eid>/vote', methods=['GET', 'POST'])
@auth_guard
def elections_voting_page(eid):
    election = ele.get(eid)
    candidates = ele.candidates(eid)
    voters = ele.voters(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()

    if F.g.user['login'] not in voters['eligible_voters']:
        return F.render_template('errors/not_eligible.html',
                                 election=election)

    # Redirect to thankyou page if already voted
    if F.g.user['login'] in [v.handle for v in e.voters]:
        return F.redirect(F.url_for('elections_confirmation_page', eid=eid))

    if F.request.method == 'POST':
        # encrypt the voter identity
        voter = generate_password_hash(
            F.g.user['login'] + '+' + F.request.form['password'])
        print(voter)
        for k in F.request.form.keys():
            if k.split('@')[0] == 'candidate':
                candidate = k.split('@')[-1]
                rank = F.request.form[k]
                ballot = Ballot(rank=rank, candidate=candidate, voter=voter)
                e.ballots.append(ballot)

        # Add user to the voted list
        e.voters.append(Voter(handle=F.g.user['login']))
        SESSION.commit()
        return 'saved'

    return F.render_template('views/elections/vote.html',
                             election=election,
                             candidates=candidates,
                             voters=voters)


@APP.route('/app/elections/<eid>/confirmation', methods=['GET'])
@auth_guard
def elections_confirmation_page(eid):
    election = ele.get(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()

    if F.g.user['login'] in [v.handle for v in e.voters]:
        return F.render_template('views/elections/confirmation.html',
                                 election=election)

# webhook route from kubernetes prow


@APP.route('/v1/webhooks/meta/updated', methods=['POST'])
def update_meta():
    """
    update the meta
    """
    ele.query()  # update the meta store
    elections = ele.all()
    for e in elections:
        query = SESSION.query(Election).filter_by(key=e['key']).first()
        if query:
            query.name = e['name']
        else:
            SESSION.add(Election(key=e['key'], name=e['name']))
        SESSION.commit()
    return "ok"
