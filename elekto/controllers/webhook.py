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

import os

from elekto import APP, SESSION, csrf
from elekto.models import meta
from elekto.models.utils import sync
from elekto.middlewares.webhook import webhook_guard


@APP.route('/v1/webhooks/meta/sync', methods=['POST'])
@webhook_guard
@csrf.exempt
def webhook_sync():
    backend = meta.Meta(APP.config['META'])
    if not os.path.exists(backend.META) or not os.path.isdir(backend.META):
        backend.clone()
    else:
        backend.pull()
    # FIXME: sync(...) returns a string, not a response.
    return sync(SESSION, meta.Election.all())
