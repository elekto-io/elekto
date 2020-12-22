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
from werkzeug.security import generate_password_hash

from k8s_elections import constants, APP, SESSION
# from k8s_elections.core import generate_result
from k8s_elections.core.election import Election as CoreElection
from k8s_elections.models import meta
from k8s_elections.models.sql import Election, Ballot, Voter
from k8s_elections.controllers.authentication import auth_guard

# Yaml based Election backend
e_meta = meta.Election(APP.config.get('META')).update_store()


@APP.route('/app')
@auth_guard
def app():
    # Find all the user's past and all upcoming (meta only) elections
    query = SESSION.query(Election).filter(Election.id.in_(
        SESSION.query(Voter.election_id).filter(
            Voter.handle == F.g.user['login']).subquery()
    )).all()

    past = [e_meta.get(e.key) for e in query]
    upcoming = e_meta.where('status', constants.ELEC_STAT_RUNNING)

    return F.render_template('views/dashboard.html',
                             upcoming=upcoming,
                             past=past)


@APP.route('/app/elections')  # Election listing
@auth_guard
def elections():
    status = F.request.args.get('status')
    elections = e_meta.all() if status is None else e_meta.where('status',
                                                                 status)
    elections.sort(key=lambda e: e['start_datetime'], reverse=True)

    return F.render_template('views/elections/index.html',
                             elections=elections,
                             status=status)


@APP.route('/app/elections/<eid>')  # Particular Election
@auth_guard
def elections_single(eid):
    election = e_meta.get(eid)
    candidates = e_meta.candidates(eid)
    voters = e_meta.voters(eid)

    return F.render_template('views/elections/single.html',
                             election=election,
                             candidates=candidates,
                             voters=voters)


@APP.route('/app/elections/<eid>/candidates/<cid>')  # Particular Candidate
@auth_guard
def elections_candidate(eid, cid):
    election = e_meta.get(eid)
    candidate = e_meta.candidate(eid, cid)

    return F.render_template('views/elections/candidate.html',
                             election=election,
                             candidate=candidate)


@APP.route('/app/elections/<eid>/admin/')  # Admin page for the election
@auth_guard
def elections_admin(eid):
    election = e_meta.get(eid)

    if F.g.user['login'] not in election['election_officers']:
        return F.abort(404)

    e = SESSION.query(Election).filter_by(key=eid).first()
    voters = e.voters

    return F.render_template('views/elections/admin.html',
                             election=election,
                             voters=voters)


@APP.route('/app/elections/<eid>/admin/results')  # Admin page for the election
@auth_guard
def elections_admin_results(eid):
    election = e_meta.get(eid)
    candidates = e_meta.candidates(eid)

    if F.g.user['login'] not in election['election_officers']:
        return F.abort(404)
    e = SESSION.query(Election).filter_by(key=eid).first()
    print(CoreElection.build(candidates, e.ballots).result())
    return F.render_template('views/elections/admin_result.html',
                             election=election)


@APP.route('/app/elections/<eid>/results/')  # Election's Result
@auth_guard
def elections_results(eid):
    election = e_meta.get(eid)

    return F.render_template('views/elections/results.html', election=election)


@APP.route('/app/elections/<eid>/vote', methods=['GET', 'POST'])
@auth_guard
def elections_voting_page(eid):
    election = e_meta.get(eid)  # eid is also validated here
    candidates = e_meta.candidates(eid)
    voters = e_meta.voters(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()

    if F.g.user['login'] not in voters['eligible_voters']:
        return F.render_template('errors/not_eligible.html',
                                 election=election)

    # Redirect to thankyou page if already voted
    if F.g.user['login'] in [v.handle for v in e.voters]:
        return F.redirect(F.url_for('elections_confirmation_page', eid=eid))

    if F.request.method == 'POST':
        # encrypt the voter identity
        voter_str = F.g.user['login'] + '+' + F.request.form['password']
        voter = generate_password_hash(voter_str)

        for k in F.request.form.keys():
            if k.split('@')[0] == 'candidate':
                candidate = k.split('@')[-1]
                rank = F.request.form[k]
                ballot = Ballot(rank=rank, candidate=candidate, voter=voter)
                e.ballots.append(ballot)

        # Add user to the voted list
        e.voters.append(Voter(handle=F.g.user['login']))
        SESSION.commit()
        return F.redirect(F.url_for('elections_confirmation_page', eid=eid))

    return F.render_template('views/elections/vote.html',
                             election=election,
                             candidates=candidates,
                             voters=voters)


@APP.route('/app/elections/<eid>/confirmation', methods=['GET'])
@auth_guard
def elections_confirmation_page(eid):
    election = e_meta.get(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()

    if F.g.user['login'] in [v.handle for v in e.voters]:
        return F.render_template('views/elections/confirmation.html',
                                 election=election)

    return F.redirect(F.url_for('elections_single', eid=eid))

# webhook route from kubernetes prow


@APP.route('/v1/webhooks/meta/updated', methods=['POST'])
def update_meta():
    e_meta.update_store()
    return "ok"
