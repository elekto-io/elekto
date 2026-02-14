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

# Application's CSRF Security
CSRF_STATE = 'state'
AUTH_STATE = 'authentication'

# GitHub Endpoints
# TODO: Make the GitHub externally configurable/overridable. If not specified in env, use github.com
github_host = 'https://github.com'
# github_host = 'http://localhost:9000'

if os.environ.get('INTEGRATION_TEST') == 'true':
    github_host = 'http://github:9000'

GITHUB_AUTHORIZE = f'{github_host}/login/oauth/authorize'
GITHUB_ACCESS = f'{github_host}/login/oauth/access_token'
GITHUB_PROFILE = f'{github_host}/user'

# Election attributes related constants
ELEC_STAT_COMPLETED = 'completed'
ELEC_STAT_RUNNING = 'running'
ELEC_STAT_UPCOMING = 'upcoming'

# Candidates attribiutes related constants
CAND_START_DEL = '--n'
CAND_END_DEL = '---'
