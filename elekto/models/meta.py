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
import random
import flask as F

from datetime import datetime

from elekto import APP, constants
from elekto.models import utils


class Meta:
    """
    Meta is the base class for all the yaml files based backend, the class is
    responsible for syncing application with meta repository (sidecar or local)
    and provides the utils to read data (YAML) files.
    """

    def __init__(self, config):
        self.META = os.path.abspath(config['PATH'])
        self.REMOTE = config['REMOTE']
        self.BRANCH = config['BRANCH']
        self.SECRET = config['SECRET']
        self.git = '/usr/bin/git'
        self.pref = "/usr/bin/git --git-dir={}/.git --work-tree={}\
            ".format(self.META, self.META)

    def clone(self):
        os.system('{} clone {} {}'.format(self.git, self.REMOTE, self.META))

    def pull(self):
        os.system('{} pull origin {}'.format(self.pref, self.BRANCH))


class Election(Meta):
    DES = 'election_desc.md'
    RES = 'results.md'
    YML = 'election.yaml'
    VOT = 'voters.yaml'

    def __init__(self, key):
        Meta.__init__(self, APP.config['META'])
        self.store = os.path.join(self.META, 'elections')
        self.path = os.path.join(self.store, key)
        self.key = key
        self.election = {}

        if not os.path.exists(self.path):
            F.abort(404)

    @staticmethod
    def all():
        """
        Get all elections in the repository

        Returns:
            list: list of all the elections
        """
        meta = Meta(APP.config['META'])
        path = os.path.join(meta.META, 'elections')
        keys = [k for k in os.listdir(
            path) if os.path.isdir(os.path.join(path, k)) and os.path.exists(os.path.join(path, k, 'election.yaml'))]

        return [Election(k).get() for k in keys]

    @staticmethod
    def where(key, value):
        return [r for r in Election.all() if r[key] == value]

    def get(self):
        if not os.path.exists(self.path) or not os.path.isdir(self.path):
            return F.abort(404)
        return self.build()

    def build(self):
        self.election = utils.parse_yaml(os.path.join(self.path, Election.YML))
        self.election['status'] = self.status()
        self.election['key'] = self.key
        self.election['description'] = self.description()
        self.election['results'] = self.results()

        if 'exception_due' not in self.election.keys():
            self.election['exception_due'] = self.election['start_datetime']
        return self.election

    def status(self):
        start = self.election['start_datetime']
        end = self.election['end_datetime']
        now = datetime.now()

        if now < start:
            return constants.ELEC_STAT_UPCOMING
        elif end < now:
            return constants.ELEC_STAT_COMPLETED
        else:
            return constants.ELEC_STAT_RUNNING

    def description(self):
        return utils.parse_md(os.path.join(self.path, Election.DES))

    def results(self):
        return utils.parse_md(os.path.join(self.path, Election.RES))

    def voters(self):
        return utils.parse_yaml(os.path.join(self.path, Election.VOT))

    def candidates(self):
        """
        Build candidates and a list of candidates in random order
        """
        files = [k for k in os.listdir(self.path) if 'candidate' in k]
        candidates = []
        for f in files:
            md = open(os.path.join(self.path, f)).read()
            c = utils.extract_candidate_info(md)
            c['key'] = c['ID']
            candidates.append(c)

        # As per the specifications the candidates must!! be in random order
        random.shuffle(candidates)

        return candidates

    def candidate(self, cid):
        path = os.path.join(self.path, 'candidate-{}.md'.format(cid))
        if not os.path.exists(path) or not os.path.isfile(path):
            return F.abort(404)

        md = open(path).read()
        candidate = utils.extract_candidate_info(md)
        candidate['key'] = cid
        candidate['description'] = utils.parse_md(
            utils.extract_candidate_description(md), False)

        return candidate
