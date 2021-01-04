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

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

BASE = declarative_base()


def create_session(url):
    """
    Create the session object to use to query the database

    Args:
        url (string): the URL used to connect the application to the
            database. The URL contains information with regards to the database
            engine, the host, user and password and the database name.
            ie: <engine>://<user>:<password>@<host>/<dbname>
    Returns:
        (scoped_session): session for the database
    """
    engine = S.create_engine(url, pool_pre_ping=True)
    session = scoped_session(sessionmaker(bind=engine))

    return session


def migrate(url):
    """
    Create the tables in the database using the url

    Args:
        url (string): the URL used to connect the application to the
            database. The URL contains information with regards to the database
            engine, the host, user and password and the database name.
            ie: <engine>://<user>:<password>@<host>/<dbname>
    """
    engine = S.create_engine(url)
    BASE.metadata.create_all(bind=engine)

    session = scoped_session(sessionmaker(bind=engine,
                                          autocommit=False,
                                          autoflush=False))
    return session


class User(BASE):
    __tablename__ = 'user'

    id = S.Column(S.Integer, primary_key=True)
    username = S.Column(S.String(255), unique=True)
    name = S.Column(S.String(255), nullable=True)
    token = S.Column(S.String(255), nullable=True)
    token_expires_at = S.Column(S.DateTime, nullable=True)
    created_at = S.Column(S.DateTime, default=S.func.now())

    def github_compatible(self):
        return {
            'login': self.username,
            'name': self.name
        }


class Election(BASE):
    __tablename__ = 'election'

    id = S.Column(S.Integer, primary_key=True)
    key = S.Column(S.String(255), nullable=False, unique=True)
    name = S.Column(S.String(255), nullable=True)
    ballots = S.orm.relationship('Ballot')
    voters = S.orm.relationship('Voter')
    requests = S.orm.relationship('Request')
    created_at = S.Column(S.DateTime, default=S.func.now())

    def __repr__(self):
        return "<Election(election_id={}, key={}, name={})>".format(
            self.id, self.key, self.name)


class Voter(BASE):
    """
    Voters that have already voted
    """
    __tablename__ = 'voter'

    id = S.Column(S.Integer, primary_key=True)
    handle = S.Column(S.String(255), nullable=False)
    election_id = S.Column(S.Integer, S.ForeignKey('election.id'))

    def __repr__(self):
        return "<Voter(election_id={}, handle={})>".format(
            self.election_id, self.handle)

class Ballot(BASE):
    """
    Ballot to store the voter's choice, give an election(E) and candidates(C)
    the voter(V) can have up-to (|C|) ballots(B) for E.
        - No entry will be done for no opinion
        - Single entry for each candidate's rank

    therefore, B(i) = C + rank + V given (0 < i,j <= |C|)

    There should not be any mapping between Ballot and User/Voter or any other
    model that can lead to the identification of the voter.
    """
    __tablename__ = 'ballot'

    id = S.Column(S.Integer, primary_key=True)
    election_id = S.Column(S.Integer, S.ForeignKey('election.id'))
    rank = S.Column(S.Integer, default=0)
    candidate = S.Column(S.String(255), nullable=False)
    voter = S.Column(S.String(255), nullable=False)
    created_at = S.Column(S.DateTime, default=S.func.now())

    def __repr__(self):
        return "<Ballot(election_id={}, candidate={}, rank={})>".format(
            self.election_id, self.candidate, self.rank)

class Request(BASE):
    __tablename__ = 'request'

    id = S.Column(S.Integer, primary_key=True)
    handle = S.Column(S.String(255), nullable=False)
    election_id = S.Column(S.Integer, S.ForeignKey('election.id'))
    name = S.Column(S.String(255), nullable=True)
    email = S.Column(S.String(255), nullable=True)
    chat = S.Column(S.String(255), nullable=True)
    description = S.Column(S.Text, nullable=True)
    comments = S.Column(S.Text, nullable=True)
