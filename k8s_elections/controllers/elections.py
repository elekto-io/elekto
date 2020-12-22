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

import hmac
import hashlib
import flask as F

from functools import wraps
from werkzeug.security import generate_password_hash

from k8s_elections import constants, APP, SESSION
# from k8s_elections.core import generate_result
from k8s_elections.core.election import Election as CoreElection
from k8s_elections.models import meta
from k8s_elections.models.sql import Election, Ballot, Voter
from k8s_elections.controllers.authentication import auth_guard

# Yaml based Election backend
e_meta, log = meta.Election(APP.config.get('META')).update_store()


def webhook_guard(f):
    """
    Middleware (guard): checks if the current webhook request is valid or not.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        sign = F.request.headers.get("X-Hub-Signature-256")

        if not sign or not sign.startswith('sha256='):
            F.abort(400, "X-Hub-Signature-256 is not provided or invalid")
        try:
            digest = hmac.new(e_meta.SECRET.encode(),
                              F.request.data, hashlib.sha256).hexdigest()
        except AttributeError:
            F.abort(500, 'Secret not set at server')

        if not hmac.compare_digest(sign, "sha256=" + digest):
            F.abort(400, "Invalid X-Hub-Signature-256 ")

        print('verified ' + sign + ' with ' + digest)
        return f(*args, **kwargs)
    return decorated_function


def admin_guard(f):
    """
    Middleware (guard): checks if the current authorized user is election
    officer or not.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'eid' not in kwargs.keys() or F.g.user['login'] \
                not in e_meta.get(kwargs['eid'])['election_officers']:
            F.abort(401)
        return f(*args, **kwargs)
    return decorated_function


def voter_guard(f):
    """
    Middleware (guard): checks if the current authorized user is in the voters
    list of the election or not.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'eid' not in kwargs.keys():
            return F.abort(404)

        election = e_meta.get(kwargs['eid'])
        voters = e_meta.voters(kwargs['eid'])

        if F.g.user['login'] not in voters['eligible_voters']:
            return F.render_template('errors/not_eligible.html',
                                     election=election)
        return f(*args, **kwargs)
    return decorated_function


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
    res = e_meta.all() if status is None else e_meta.where('status', status)
    res.sort(key=lambda e: e['start_datetime'], reverse=True)

    return F.render_template('views/elections/index.html',
                             elections=res,
                             status=status)


@APP.route('/app/elections/<eid>')  # Particular Election
@auth_guard
def elections_single(eid):
    election = e_meta.get(eid)
    candidates = e_meta.candidates(eid)
    voters = e_meta.voters(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()

    return F.render_template('views/elections/single.html',
                             election=election,
                             candidates=candidates,
                             voters=voters,
                             voted=[v.handle for v in e.voters])


@APP.route('/app/elections/<eid>/candidates/<cid>')  # Particular Candidate
@auth_guard
def elections_candidate(eid, cid):
    election = e_meta.get(eid)
    candidate = e_meta.candidate(eid, cid)

    return F.render_template('views/elections/candidate.html',
                             election=election,
                             candidate=candidate)


@APP.route('/app/elections/<eid>/vote', methods=['GET', 'POST'])
@auth_guard
@voter_guard
def elections_voting_page(eid):
    election = e_meta.get(eid)  # eid is also validated here
    candidates = e_meta.candidates(eid)
    voters = e_meta.voters(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()

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


@APP.route('/app/elections/<eid>/results/')  # Election's Result
@auth_guard
def elections_results(eid):
    election = e_meta.get(eid)

    return F.render_template('views/elections/results.html', election=election)


# ########################################################################## #
#                                                                            #
#                      /!/ Election officer section \!\                      #
#                                                                            #
# ########################################################################## #

@APP.route('/app/elections/<eid>/admin/')  # Admin page for the election
@auth_guard
@admin_guard
def elections_admin(eid):
    election = e_meta.get(eid)
    e = SESSION.query(Election).filter_by(key=eid).first()

    return F.render_template('views/elections/admin.html',
                             election=election,
                             e=e)


@APP.route('/app/elections/<eid>/admin/results')  # Admin page for the election
@auth_guard
@admin_guard
def elections_admin_results(eid):
    election = e_meta.get(eid)
    candidates = e_meta.candidates(eid)

    if election['status'] != constants.ELEC_STAT_COMPLETED:
        return F.render_template('errors/message.html',
                                 title='The election is not completed yet',
                                 message='The application needs election to be \
                                     over first.')

    e = SESSION.query(Election).filter_by(key=eid).first()
    result = CoreElection.build(
        candidates, e.ballots, election['no_winners']).schulze()

    return F.render_template('views/elections/admin_result.html',
                             election=election,
                             result=result)


# webhook route from kubernetes prow


@APP.route('/v1/webhooks/meta/updated', methods=['POST'])
@webhook_guard
def update_meta():
    store, log = e_meta.update_store()
    return log
