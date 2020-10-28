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

# import os
import argparse

from k8s_elections import APP

parser = argparse.ArgumentParser(description='Run the k8s.elections app')

parser.add_argument(
    '--port', '-p', default=5005,
    help='Port for the flask application.')
parser.add_argument(
    '--host', default="127.0.0.1",
    help='Hostname to listen on. When set to 0.0.0.0 the server is available \
    externally. Defaults to 127.0.0.1 making the it only visable on localhost')

args = parser.parse_args()

APP.run(host=args.host, port=args.port)
