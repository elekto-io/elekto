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

import flask as F
import base64
from functools import wraps
from elekto import APP, constants


def authenticated():
    """
    Check the state of user's authentication

    Returns:
        (bool): user's authentication state
    """
    return hasattr(F.g, 'auth') and F.g.auth is not False


def auth_guard(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not authenticated():
            r = F.request.url.encode('ascii')
            redirect = base64.b64encode(r).decode('ascii').replace('/', '$')
            return F.redirect(F.url_for('render_login_page', r=redirect))
        return f(*args, **kwargs)
    return decorated_function


def csrf_guard(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if constants.CSRF_STATE not in F.request.args.keys() \
                or constants.CSRF_STATE not in F.session.keys() \
                or F.request.args[constants.CSRF_STATE] != F.session[constants.CSRF_STATE]:
            F.flash('Missing or Invalid csrf token')
            return F.redirect(F.url_for('render_login_page'))

        return f(*args, **kwargs)
    return decorated_function


def len_guard(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if F.request.method == "POST":
            passcode = F.request.form["password"]
            min_passcode_len = int(APP.config.get('PASSCODE_LENGTH'))
            if 0 < len(passcode) < min_passcode_len:
                F.flash(f"Please enter a passphrase with minimum {min_passcode_len} characters")
                return F.redirect(F.request.url)
        return f(*args, **kwargs)
    return decorated_function
