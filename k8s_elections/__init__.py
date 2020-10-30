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

from flask import Flask, render_template, request, redirect
from authlib.integrations.requests_client import OAuth2Session

APP = Flask(__name__)
APP.config.from_object('config')

# config
github = APP.config.get('GITHUB')


@APP.before_request
def before_request():
    # When you import jinja2 macros, they get cached which is annoying for
    # local development, so wipe the cache every request.
    if APP.config.get('DEBUG') or 'localhost' in request.host_url:
        APP.jinja_env.cache = {}


@APP.route('/')
def welcome():
    return render_template('welcome.html', name=APP.config.get('NAME'))


@APP.route('/login', methods=['POST'])
def login():
    scope = 'user:email'
    client = OAuth2Session(github['client_id'],
                           github['client_secret'],
                           scope=scope)
    authorization_endpoint = 'https://github.com/login/oauth/authorize'
    uri, state = client.create_authorization_url(authorization_endpoint)

    return redirect(uri)


@APP.route(github['redirect'])
def github_redirect():
    scope = 'user:email'
    client = OAuth2Session(github['client_id'],
                           github['client_secret'],
                           scope=scope)
    token_endpoint = 'https://github.com/login/oauth/access_token'
    token = client.fetch_token(
        token_endpoint, authorization_response=request.url)
    return redirect('/app')

@APP.route('/app')
def app():
    return 'Dashboard'
