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

from k8s_elections import APP, SESSION
from k8s_elections.models import meta
from k8s_elections.models.utils import sync_db_with_meta
from k8s_elections.middlewares.webhook import webhook_guard


@APP.route('/v1/webhooks/meta/sync', methods=['POST'])
@webhook_guard
def sync():
    META = APP.config['META']
    if not os.path.exists(META['PATH']) or not os.path.isdir(META['PATH']):
        os.system('/usr/bin/git clone {} {} '.format(
            META['REMOTE'], META['PATH']
        ))
    else:
        os.system('/usr/bin/git --git-dir={}/.git --work-tree={} \
            pull origin main'.format(META['PATH'], META['PATH']))
    return sync_db_with_meta(SESSION, meta.Election.all())
