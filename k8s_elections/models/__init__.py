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
    engine = S.create_engine(url)
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


# These circular imports are fine
import k8s_elections.models.users  # noqa
import k8s_elections.models.elections  # noqa