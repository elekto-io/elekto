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

import sqlalchemy as S
from k8s_elections.models import BASE


class User(BASE):
    """
    The User class is for storing and validating the user access_token
    """
    __tablename__ = 'users'
    username = S.Column(S.Unicode(150), primary_key=True)
    access_token = S.Column(S.Unicode(150), nullable=True)

    def __init__(self, username, access_token):
        """
        Create a brand new user

        Args:
            username (string): user's github handle
            access_token (string): user's authentication token
        """
        self.username = username
        self.access_token = access_token

    def __repr__(self):
        return '<User {}>'.format(self.username)
