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

import hmac
import hashlib
import flask as F

from functools import wraps
from elekto import APP

def webhook_guard(f):
    """
    Middleware (guard): checks if the current webhook request is valid or not.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # if the development env is local don't verfiy the webhook
        if APP.config['DEBUG']:
            return f(*args, **kwargs)

        # The webhook must be configured with a secret and content type should
        # be set to application/json.
        sign = F.request.headers.get("X-Hub-Signature-256")

        if not sign or not sign.startswith('sha256='):
            return F.abort(400, "X-Hub-Signature-256 is not provided or invalid")

        try:
            digest = hmac.new(APP.config['META']['SECRET'].encode(),
                              F.request.data, hashlib.sha256).hexdigest()
        except AttributeError:
            return F.abort(500, 'Error while creating a digest')

        if not hmac.compare_digest(sign, "sha256=" + digest):
            return F.abort(400, "Invalid X-Hub-Signature-256 ")

        return f(*args, **kwargs)
    return decorated_function
