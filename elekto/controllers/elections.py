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
The module is responsible for handling all the election's related request.
"""

import secrets
import string
import flask as F

from werkzeug.security import generate_password_hash, check_password_hash

from elekto import constants, APP, SESSION
from elekto.models import meta
from elekto.core.election import Election as CoreElection
from elekto.models.sql import Election, Ballot, Voter, Request
from elekto.middlewares.auth import auth_guard
from elekto.middlewares.election import *  # noqa


@APP.route('/app')
@auth_guard
def app():
    running = meta.Election.where('status', constants.ELEC_STAT_RUNNING)

    return F.render_template('views/dashboard.html', running=running)


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
                             voted=[v.user_id for v in e.voters])


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
    election = meta.Election(eid)
    candidates = election.candidates()
    voters = election.voters()
    e = SESSION.query(Election).filter_by(key=eid).first()

    # Redirect to thankyou page if already voted
    if F.g.user.id in [v.user_id for v in e.voters]:
        return F.render_template('errors/message.html',
                                 title='You have already voted',
                                 message='To re-cast your vote, please visit\
                                 the election page.')

    if F.request.method == 'POST':
        # encrypt the voter identity
        passcode = ''.join(secrets.choice(string.digits) for i in range(6))
        if len(F.request.form['password']):
            passcode = F.request.form['password']
        voter = generate_password_hash(F.g.user.username + '+' + passcode)

        for k in F.request.form.keys():
            if k.split('@')[0] == 'candidate':
                candidate = k.split('@')[-1]
                rank = F.request.form[k]
                ballot = Ballot(rank=rank, candidate=candidate, voter=voter)
                e.ballots.append(ballot)

        # Add user to the voted list
        e.voters.append(Voter(user_id=F.g.user.id))
        SESSION.commit()
        return F.redirect(F.url_for('elections_confirmation_page', eid=eid))

    return F.render_template('views/elections/vote.html',
                             election=election.get(),
                             candidates=candidates,
                             voters=voters)


@APP.route('/app/elections/<eid>/vote/edit', methods=['POST'])
@auth_guard
@voter_guard
@has_voted_condition
def elections_edit(eid):
    election = meta.Election(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()

    # encrypt the voter identity
    voter = F.g.user.username + '+' + F.request.form['password']
    ballots = [b for b in e.ballots if check_password_hash(b.voter, voter)]

    if not len(ballots):
        F.flash('Incorrect password, the password must match with the one used\
                before')
        return F.redirect(F.url_for('elections_single', eid=eid))

    # Delete all the ballots for the user
    for b in ballots:
        SESSION.delete(b)
    # Remove the voter from the voted list
    for voter in e.voters:
        if voter.user_id == F.g.user.id:
            SESSION.delete(voter)

    SESSION.commit()
    F.flash('The old ballot is sucessfully deleted, please re-cast the ballot.')
    return F.redirect(F.url_for('elections_voting_page', eid=eid))


@APP.route('/app/elections/<eid>/confirmation', methods=['GET'])
@auth_guard
def elections_confirmation_page(eid):
    election = meta.Election(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()

    if F.g.user.id in [v.user_id for v in e.voters]:
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


# Exception Request form
@APP.route('/app/elections/<eid>/exception', methods=['POST', 'GET'])
@auth_guard
@exception_guard
def elections_exception(eid):
    election = meta.Election(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()
    req = SESSION.query(Request).join(Request, Election.requests).filter(
        Request.user_id == F.g.user.id).first()

    if req:
        return F.render_template('errors/message.html',
                                 title="You have already filled the form.",
                                 message="please wait for the election's\
                                 supervisor to view your request.")

    if F.request.method == 'POST':
        erequest = Request(user_id=F.g.user.id,
                           name=F.request.form['name'],
                           email=F.request.form['email'],
                           chat=F.request.form['chat'],
                           description=F.request.form['description'],
                           comments=F.request.form['comments'])
        e.requests.append(erequest)
        SESSION.commit()

        F.flash('Request sucessfully submitted.')
        return F.redirect(F.url_for('elections_single', eid=eid))

    return F.render_template('views/elections/exception.html',
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


@APP.route('/app/elections/<eid>/admin/exception/<rid>', methods=['GET', 'POST'])
@auth_guard                             # Admin page for the reviewing exception
@admin_guard
def elections_admin_review(eid, rid):
    election = meta.Election(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()
    req = SESSION.query(Request).join(
        Request, Election.requests).filter(Request.id == rid).first()

    if F.request.method == 'POST':
        req.reviewed = False if req.reviewed else True
        SESSION.commit()

    return F.render_template('views/elections/admin_exception.html',
                             election=election.get(),
                             req=req,
                             e=e)


@APP.route('/app/elections/<eid>/admin/results')  # Admin page for the election
@auth_guard
@admin_guard
@has_completed_condition
def elections_admin_results(eid):
    election = meta.Election(eid)
    candidates = election.candidates()
    e = SESSION.query(Election).filter_by(key=eid).first()

    result = CoreElection.build(candidates, e.ballots).schulze()

    return F.render_template('views/elections/admin_result.html',
                             election=election.get(),
                             result=result)


@APP.route('/app/elections/<eid>/admin/download')  # download ballots as csv
@auth_guard
@admin_guard
@has_completed_condition
def elections_admin_download(eid):
    election = meta.Election(eid)
    candidates = election.candidates()
    e = SESSION.query(Election).filter_by(key=eid).first()

    # Generate a csv
    ballots = CoreElection.build(candidates, e.ballots).ballots
    candidates = {c['key']: '' for c in candidates}
    csv = ','.join(list(candidates.keys())) + '\n'
    for b in ballots.keys():
        for c in candidates.keys():
            candidates[c] = 'No opinion'
        for c, rank in ballots[b]:
            candidates[c] = rank
        csv += ','.join([str(candidates[c]) for c in candidates.keys()]) + '\n'

    return F.Response(csv,
                      mimetype="text/csv",
                      headers={"Content-disposition": "attachment; filename=ballots.csv"})
