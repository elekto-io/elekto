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
k8s.elections.utils include utils related to flask application
"""

import flask as F

from k8s_elections import constants, SESSION
from k8s_elections.models.sql import User


def set_session(app):
    F.session.permanent = True
    if constants.AUTH_STATE in F.session.keys() and \
            F.session[constants.AUTH_STATE] is not None:
        # Authenticate with every request if the user's token correct or not
        query = SESSION.query(User).filter_by(
            token=F.session[constants.AUTH_STATE]).first()

        # if unable to fetch the user's info, set auth to False
        if not query:
            F.g.user = None
            F.g.auth = False
            F.session.pop(constants.AUTH_STATE)
        else:
            F.g.user = query.github_compatible()
            F.g.auth = True
    else:
        F.g.user = None
        F.g.auth = False
