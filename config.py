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

import os

from utils import env
from distutils.util import strtobool

# Application Name
#
# This value is the name of this appliation, the value will be used when the
# server needs to place appliation's name in the Ui or any other place.
NAME = env('APP_NAME', 'k8s.elections')

# Encryption Key
#
# This is used by the Flask server and should be set to a random character
# string, please do not deploy before doing this!.
SECRET_KEY = env('APP_KEY', 'test')

# Application Debug Mode
#
# When the application is in debug mode, all the development functionalities
# like printing detailed error stack trace, reloading css on change etc are
# enabled.
DEBUG = bool(strtobool(env('APP_DEBUG', 'False')))

# Auto Reload Templates
#
# Enable templates auto reloading, when the template is changed C + R will
# update the template code in the browser.
TEMPLATES_AUTO_RELOAD = True if DEBUG is True else False

# Default Database Connection
#
# Here is the database connection is specified, currently the application
# supports MySQL and can be extended to any other SQLAlchemy supported data-
# base, the format for database connection url is
#   <engine>://<user>:<password>@<host>/<dbname>
if env('DB_CONNECTION') == 'mysql':
    DATABASE_URL = "mysql://{user}:{password}@{host}:{port}/{dbname}".format(
        user=env('DB_USERNAME', 'root'),
        password=env('DB_PASSWORD', ''),
        host=env('DB_HOST', 'localhost'),
        port=env('DB_PORT', 3306),
        dbname=env('DB_DATABASE'),
    )
elif env('DB_CONNECTION') == 'postgresql':
    DATABASE_URL = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
        user=env('DB_USERNAME', 'root'),
        password=env('DB_PASSWORD', ''),
        host=env('DB_HOST', 'localhost'),
        port=env('DB_PORT', 3306),
        dbname=env('DB_DATABASE'),
    )
elif env('DB_CONNECTION') == 'sqlite':
    DATABASE_URL = "sqlite:///{path}".format(
        path=env('DB_PATH', os.path.join(
            os.path.split(os.path.abspath(__file__))[0],
            'test',
            'test.db'
        ))
    )
else:
    raise "Invalid DB engine"

# Meta repository
#
# The application uses a meta repository for handling the admin part of the
# application via gitops, see the design documentation [/docs/DESIGN.md] for
# more detailed information on working.
# - REMOTE : Remote repository url
# - PATH : Where the meta repository is cloned (if development is local)
# - DEPLOYMENT : mode of deployment (local, sidecar)
META = {
    'REMOTE': env('META_REPO'),
    'ELECDIR': env('ELECTION_DIR'),
    'PATH': env('META_PATH', 'meta'),
    'DEPLOYMENT': env('META_DEPLOYMENT', 'local'),
    'BRANCH': env('META_BRANCH', 'main'),
    'SECRET': env('META_SECRET')
}

# Third Party Integrations
#
# This section is for storing the credentials for third party integrations
# such as Github, Gitlab and more.
GITHUB = {
    'client_id': env('GITHUB_CLIENT_ID'),
    'client_secret': env('GITHUB_CLIENT_SECRET'),
    'redirect': env('GITHUB_REDIRECT', '/oauth/github/callback'),
    'scope': 'user:login,name',
}
