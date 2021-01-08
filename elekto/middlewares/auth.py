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

import flask as F
from functools import wraps


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
            # r = str(base64.b64encode(
            #     F.request.url.encode("ascii"))).replace('/', '$')
            return F.redirect(F.url_for('render_login_page'))
        return f(*args, **kwargs)
    return decorated_function
