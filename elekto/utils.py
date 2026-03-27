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
k8s.elections.utils include utils related to flask application
"""

import flask as F
from datetime import datetime

from elekto import constants, SESSION
from elekto.models import meta
from elekto.models.sql import User, Election, Voter


def set_session(app):
    F.session.permanent = True
    if str(F.request.path).find("static") == -1 and \
            constants.AUTH_STATE in F.session.keys() and \
            F.session[constants.AUTH_STATE] is not None:
        # Authenticate with every request if the user's token correct or not
        token = F.session[constants.AUTH_STATE]
        user = SESSION.query(User).filter_by(token=token).first()

        # if unable to fetch the user's info, set auth to False
        if user and user.token_expires_at and user.token_expires_at > datetime.now():
            F.g.user = user
            F.g.user.username = F.g.user.username.lower()
            F.g.auth = True
            # Find all the user's past and all upcoming (meta only) elections
            query = SESSION.query(Election).join(
                Election, Voter.election).filter(Voter.user_id == user.id).all()

            F.g.past_elections = [meta.Election(e.key).get() for e in query]
        else:
            F.g.user = None
            F.g.auth = False
            F.session.pop(constants.AUTH_STATE)
    else:
        F.g.user = None
        F.g.auth = False
