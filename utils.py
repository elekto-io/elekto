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
from dotenv import load_dotenv, set_key

# Load the custom environment file into the program
isTesting = os.getenv('TESTING') or "PYTEST_VERSION" in os.environ
targetenv = ".env.testing" if isTesting else ".env"

# By default, values from .env take precedence over variables already set in the environment. This has been and still is
# the desired behaviour when running Elekto to serve users. When running in Docker, it is crucial that the env vars are
# honoured (especially DB_HOST as it must point to the Docker host name).
#
# Set DONT_OVERRIDE_ENV_VARS=true to prevent env vars from being overridden by .env values.
override_env_vars = not os.getenv("DONT_OVERRIDE_ENV_VARS", default=False)
load_dotenv(os.path.join(os.path.dirname(__file__), targetenv), override=override_env_vars)

def strtobool(value: str) -> bool:
  value = value.lower()
  if value in ("y", "yes", "on", "1", "true", "t"):
    return True
  return False

def generate_app_key():
    key = os.urandom(32).hex()
    set_key(targetenv, "APP_KEY", key)


def env(key, default=None):
    v = os.getenv(key)
    return default if v is None or v == '' else v
