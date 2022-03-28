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

import uuid
import sqlalchemy as S

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator, CHAR


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

    session = scoped_session(
        sessionmaker(bind=engine, autocommit=False, autoflush=False)
    )
    return session


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses CHAR(32), storing as stringified hex values.

    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class User(BASE):
    """
    User Schema - registered from the oauth external application - github
    """

    __tablename__ = "user"

    # Attributes
    id = S.Column(S.Integer, primary_key=True)
    username = S.Column(S.String(255), unique=True)
    name = S.Column(S.String(255), nullable=True)
    token = S.Column(S.String(255), nullable=True)
    token_expires_at = S.Column(S.DateTime, nullable=True)
    created_at = S.Column(S.DateTime, default=S.func.now())
    updated_at = S.Column(S.DateTime, default=S.func.now())

    # Relationships
    voters = S.orm.relationship(
        "Voter", cascade="all, delete", back_populates="user", passive_deletes=True
    )
    requests = S.orm.relationship(
        "Request", cascade="all, delete", back_populates="user", passive_deletes=True
    )

    def __repr__(self):
        return "<User(id={}, username={}, name={})>".format(
            self.id, self.username, self.name
        )


class Election(BASE):
    """
    Election Schema - build and synced from meta repository.

    Attributes:
        - key: slugified directory name from election meta.
        - name: name of the election synced from election meta.
        - created_at: descriptive attributes

    Relationships:
        - ballots: Election has many Ballot
        - voters: Election has many Voter (that have voted)
        - requests: Election has many Request
    """

    __tablename__ = "election"

    # Attributes
    id = S.Column(S.Integer, primary_key=True)
    key = S.Column(S.String(255), nullable=False, unique=True)
    name = S.Column(S.String(255), nullable=True)
    created_at = S.Column(S.DateTime, default=S.func.now())
    updated_at = S.Column(S.DateTime, default=S.func.now())

    # Relationships
    ballots = S.orm.relationship(
        "Ballot", cascade="all, delete", back_populates="election", passive_deletes=True
    )
    voters = S.orm.relationship(
        "Voter", cascade="all, delete", back_populates="election", passive_deletes=True
    )
    requests = S.orm.relationship(
        "Request",
        cascade="all, delete",
        back_populates="election",
        passive_deletes=True,
    )

    def __repr__(self):
        return "<Election(election_id={}, key={}, name={})>".format(
            self.id, self.key, self.name
        )


class Voter(BASE):
    """
    Voter Schema - Voters that have already voted for the election.

    Relationships:
        - election_id: inverse of the (Election has many Voter) relation
        - user_id: inverse of the (User has many Voter) relation
    """

    __tablename__ = "voter"

    id = S.Column(S.Integer, primary_key=True)
    user_id = S.Column(S.Integer, S.ForeignKey("user.id", ondelete="CASCADE"))
    election_id = S.Column(S.Integer, S.ForeignKey("election.id", ondelete="CASCADE"))
    created_at = S.Column(S.DateTime, default=S.func.now())
    updated_at = S.Column(S.DateTime, default=S.func.now())
    salt = S.Column(S.LargeBinary, nullable=False)
    key = S.Column(S.LargeBinary, nullable=False)

    # Relationships

    user = S.orm.relationship("User", back_populates="voters")
    election = S.orm.relationship("Election", back_populates="voters")

    def __repr__(self):
        return "<Voter(election_id={}, user_id={})>".format(
            self.election_id, self.user_id
        )


class Ballot(BASE):
    """
    Ballot Schema - stores  the voter's choice, for a given election(E)
    and candidates(C), the voter(V) can have up-to (|C|) ballots(B) for E.
        - No entry will be done for no opinion
        - Single entry for each candidate's rank

    therefore, B(i) = C + rank + V given (0 < i,j <= |C|)

    There should not be any mapping between Ballot and User/Voter or any other
    model that can lead to the identification of the voter.

    Attributes:
        - rank: rank of the candidate
        - candidate: election's candidate
        - voter: uuid per ballot

    Relationships:
        - election_id: inverse of the (Election has many Ballot) relation
    """

    __tablename__ = "ballot"

    # Attributes
    id = S.Column(GUID, primary_key=True)
    election_id = S.Column(S.Integer, S.ForeignKey("election.id", ondelete="CASCADE"))
    rank = S.Column(S.Integer, default=100000000)
    candidate = S.Column(S.String(255), nullable=False)
    voter = S.Column(GUID, nullable=False)  # uuid

    # Relationships
    election = S.orm.relationship("Election", back_populates="ballots")

    def __repr__(self):
        return "<Ballot(election_id={}, candidate={}, rank={})>".format(
            self.election_id, self.candidate, self.rank
        )


class Request(BASE):
    """
    Request Schema - Exception request for voters who are not in the eligible
    voters list.

    Attributes:
        - name: Name of the requester
        - email: email of the requester
        - chat: chat ID of the requester
        - description: description provided by the requester
        - comments: any optional comments

    Relationships:
        - election_id: inverse of the (Election has many Request) relation
        - user_id: inverse of the (User has many Request) relation
    """

    __tablename__ = "request"

    # Attributes
    id = S.Column(S.Integer, primary_key=True)
    user_id = S.Column(S.Integer, S.ForeignKey("user.id", ondelete="CASCADE"))
    election_id = S.Column(S.Integer, S.ForeignKey("election.id", ondelete="CASCADE"))
    name = S.Column(S.String(255), nullable=True)
    email = S.Column(S.String(255), nullable=True)
    chat = S.Column(S.String(255), nullable=True)
    description = S.Column(S.Text, nullable=True)
    comments = S.Column(S.Text, nullable=True)
    reviewed = S.Column(S.Boolean, default=False)
    created_at = S.Column(S.DateTime, default=S.func.now())
    updated_at = S.Column(S.DateTime, default=S.func.now())

    # Relationships
    user = S.orm.relationship("User", back_populates="requests")
    election = S.orm.relationship("Election", back_populates="requests")

    def __repr__(self):
        return "<Request election_id={}, user_id={}, name={}".format(
            self.election_id, self.user_id, self.name
        )
