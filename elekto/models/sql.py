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
from sqlalchemy import event


BASE = declarative_base()

"""
schema version, remember to update this
whenever you make changes to the schema
"""
schema_version = 2


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
    Check if we need to upgrade the schema, and do that as well

    Args:
        url (string): the URL used to connect the application to the
            database. The URL contains information with regards to the database
            engine, the host, user and password and the database name.
            ie: <engine>://<user>:<password>@<host>/<dbname>
    """
    engine = S.create_engine(url)
    update_schema(engine, schema_version)
    BASE.metadata.create_all(bind=engine)
    

    session = scoped_session(
        sessionmaker(bind=engine, autocommit=False, autoflush=False)
    )
    return session
    
    
def update_schema(engine, schema_version):
    """
    Primitive database schema upgrade facility, designed to work
    with production Elekto databases
    
    Currently only works with PostgreSQL due to requiring transaction
    support for DDL statements.  MySQL, SQLite backends will error.
    
    Start by figuring out our schema version, and then upgrade 
    stepwise until we match
    """
    db_version = 1
    db_schema = S.inspect(engine)
    
    if db_schema.has_table("election"):
        if db_schema.has_table("schema_version"):
            with engine.connect() as connection:
                db_version = connection.execute(S.text('select version from schema_version')).scalar()
                if db_version is None:
                    """ intialize the table, if necessary """
                    connection.execute(S.text('insert into schema_version ( version ) values ( 2 )'))
    else:
        """ new, empty db """
        return schema_version
    
    while db_version < schema_version:    
        if engine.dialect.name != "postgresql":
            raise RuntimeError('Upgrading the schema is required, but the database is not PostgreSQL.  You will need to upgrade manually.')
        
        if db_version < 2:
            db_version = update_schema_2(engine)
            continue
            
    return db_version


def update_schema_2(engine):
    """
    update from schema version 1 to schema version 2
    as a set of raw SQL statements
    currently only works for PostgreSQL
    written this way because SQLalchemy can't handle the
    steps involved without data loss
    """
    session = scoped_session(sessionmaker(bind=engine))
    
    session.execute('CREATE TABLE schema_version ( version INT PRIMARY KEY);')
    session.execute('INSERT INTO schema_version VALUES ( 2 );')
    session.execute('ALTER TABLE voter ADD COLUMN salt BYTEA, ADD COLUMN ballot_id BYTEA;')
    session.execute('CREATE INDEX voter_election_id ON voter(election_id);')
    session.execute('ALTER TABLE ballot DROP COLUMN created_at, DROP COLUMN updated_at;')
    session.execute('ALTER TABLE ballot DROP CONSTRAINT ballot_pkey;')
    session.execute("ALTER TABLE ballot ALTER COLUMN id TYPE CHAR(32) USING to_char(id , 'FM00000000000000000000000000000000');")
    session.execute('ALTER TABLE ballot ALTER COLUMN id DROP DEFAULT;')
    session.execute('ALTER TABLE ballot ADD CONSTRAINT ballot_pkey PRIMARY KEY ( id );')
    session.execute('CREATE INDEX ballot_election_id ON ballot(election_id);')
    session.commit()
    
    return 2

def drop_all(url: str):
    engine = S.create_engine(url)
    BASE.metadata.drop_all(bind=engine)

class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses CHAR(32), storing as stringified hex values.

    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class Version(BASE):
    """
    Stores Elekto schema version in the database for ad-hoc upgrades
    """
    __tablename__ = "schema_version"
    
    # Attributes
    version = S.Column(S.Integer, default=schema_version, primary_key=True)
    
@event.listens_for(Version.__table__, 'after_create')
def create_version(target, connection, **kwargs):
    connection.execute(S.text(f"INSERT INTO schema_version ( version ) VALUES ( {schema_version} )"))

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

    Attributes:
        - salt: byte string for encryption
        - ballot_id: byte string obtained after encrypting ballot.voter

    Relationships:
        - election_id: inverse of the (Election has many Voter) relation
        - user_id: inverse of the (User has many Voter) relation
    """

    __tablename__ = "voter"

    id = S.Column(S.Integer, primary_key=True)
    user_id = S.Column(S.Integer, S.ForeignKey("user.id", ondelete="CASCADE"))
    election_id = S.Column(S.Integer, S.ForeignKey("election.id", ondelete="CASCADE"), index=True)
    created_at = S.Column(S.DateTime, default=S.func.now())
    updated_at = S.Column(S.DateTime, default=S.func.now())
    salt = S.Column(S.LargeBinary)
    ballot_id = S.Column(S.LargeBinary)  # encrypted

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
        - voter: uuid (same for all ballots of a voter in an election)

    Relationships:
        - election_id: inverse of the (Election has many Ballot) relation
    """

    __tablename__ = "ballot"

    # Attributes
    id = S.Column(UUID(), primary_key=True, default=uuid.uuid4)
    election_id = S.Column(S.Integer, S.ForeignKey("election.id", ondelete="CASCADE"), index=True)
    rank = S.Column(S.Integer, default=100000000)
    candidate = S.Column(S.String(255), nullable=False)
    voter = S.Column(S.String(255), nullable=False)  # uuid

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
