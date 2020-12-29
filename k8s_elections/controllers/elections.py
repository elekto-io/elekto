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

from werkzeug.security import generate_password_hash, check_password_hash

from k8s_elections import constants, APP, SESSION
from k8s_elections.models import meta
from k8s_elections.core.election import Election as CoreElection
from k8s_elections.models.sql import Election, Ballot, Voter
from k8s_elections.middlewares.auth import auth_guard
from k8s_elections.middlewares.election import (
    voter_guard, admin_guard,
    has_completed_condition,
    has_voted_condition
)


@APP.route('/app')
@auth_guard
def app():
    # Find all the user's past and all upcoming (meta only) elections
    query = SESSION.query(Election).filter(Election.id.in_(
        SESSION.query(Voter.election_id).filter(
            Voter.handle == F.g.user['login']).subquery()
    )).all()

    past = [meta.Election(e.key).get() for e in query]
    upcoming = meta.Election.where('status', constants.ELEC_STAT_RUNNING)
    return F.render_template('views/dashboard.html',
                             upcoming=upcoming,
                             past=past)


@APP.route('/app/elections')  # Election listing
@auth_guard
def elections():
    status = F.request.args.get('status')
    res = meta.Election.all() if status is None else meta.Election.where('status', status)
    res.sort(key=lambda e: e['start_datetime'], reverse=True)

    return F.render_template('views/elections/index.html',
                             elections=res,
                             status=status)


@APP.route('/app/elections/<eid>')  # Particular Election
@auth_guard
def elections_single(eid):
    election = meta.Election(eid)
    candidates = election.candidates()
    voters = election.voters()
    e = SESSION.query(Election).filter_by(key=eid).first()

    return F.render_template('views/elections/single.html',
                             election=election.get(),
                             candidates=candidates,
                             voters=voters,
                             voted=[v.handle for v in e.voters])


@APP.route('/app/elections/<eid>/candidates/<cid>')  # Particular Candidate
@auth_guard
def elections_candidate(eid, cid):
    election = meta.Election(eid)
    candidate = election.candidate(cid)

    return F.render_template('views/elections/candidate.html',
                             election=election.get(),
                             candidate=candidate)


@APP.route('/app/elections/<eid>/vote', methods=['GET', 'POST'])
@auth_guard
@voter_guard
def elections_voting_page(eid):
    election = meta.Election(eid)  # eid is also validated here
    candidates = election.candidates()
    voters = election.voters()
    e = SESSION.query(Election).filter_by(key=eid).first()

    # Redirect to thankyou page if already voted
    if F.g.user['login'] in [v.handle for v in e.voters]:
        F.flash('You have already Voted, to change your vote visit edit page.')
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
                             election=election.get(),
                             candidates=candidates,
                             voters=voters)


@APP.route('/app/elections/<eid>/vote/edit', methods=['GET', 'POST'])
@auth_guard
@voter_guard
@has_voted_condition
def elections_edit_ballot(eid):
    election = meta.Election(eid)  # eid is also validated here
    candidates = election.candidates()
    voters = election.voters()
    e = SESSION.query(Election).filter_by(key=eid).first()

    if F.request.method == 'POST':
        # encrypt the voter identity
        vstr = F.g.user['login'] + '+' + F.request.form['password']

        ballots = {
            b.candidate: b for b in e.ballots if check_password_hash(b.voter, vstr)}

        if len(ballots.keys()) == 0:
            F.flash('Incorrect password, the password must match with the one \
                used before')
            return F.redirect(F.url_for('elections_edit_ballot', eid=eid))

        for k in F.request.form.keys():
            if k.split('@')[0] == 'candidate':
                candidate = k.split('@')[-1]
                rank = F.request.form[k]
                if candidate in ballots.keys():
                    ballots[candidate].rank = rank

        SESSION.commit()
        F.flash('Upated Ballot sucessfully')
        return F.redirect(F.url_for('elections_confirmation_page', eid=eid))

    return F.render_template('views/elections/edit_vote.html',
                             election=election.get(),
                             candidates=candidates,
                             voters=voters)


@APP.route('/app/elections/<eid>/confirmation', methods=['GET'])
@auth_guard
def elections_confirmation_page(eid):
    election = meta.Election(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()

    if F.g.user['login'] in [v.handle for v in e.voters]:
        return F.render_template('views/elections/confirmation.html',
                                 election=election.get())

    return F.redirect(F.url_for('elections_single', eid=eid))


@APP.route('/app/elections/<eid>/results/')  # Election's Result
@auth_guard
@has_completed_condition
def elections_results(eid):
    election = meta.Election(eid)

    return F.render_template('views/elections/results.html',
                             election=election.get())


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
#                                                                            #
#                      /!/ Election officer section \!\                      #
#                                                                            #
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #

@APP.route('/app/elections/<eid>/admin/')  # Admin page for the election
@auth_guard
@admin_guard
def elections_admin(eid):
    election = meta.Election(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()

    return F.render_template('views/elections/admin.html',
                             election=election.get(),
                             e=e)


@APP.route('/app/elections/<eid>/admin/results')  # Admin page for the election
@auth_guard
@admin_guard
@has_completed_condition
def elections_admin_results(eid):
    election = meta.Election(eid)
    candidates = election.candidates()
    e = SESSION.query(Election).filter_by(key=eid).first()

    result = CoreElection.build(candidates,
                                e.ballots,
                                election.get()['no_winners']).schulze()

    return F.render_template('views/elections/admin_result.html',
                             election=election.get(),
                             result=result)
