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
import config
import markdown2 as markdown

from k8s_elections import utils
from abc import abstractmethod


class Meta:
    """
    Meta is the base class for all the yaml files based backend, the class is
    responsible for syncing application with meta repository (sidecar or local)
    and provides the utils to read data (YAML) files.
    """

    def __init__(self, meta):
        """
        Create a brand new meta backend instance, and check if the cached meta
        is clean.
        """
        self.META = os.path.abspath(meta['PATH'])
        self.REMOTE = meta['REMOTE']
        self.store = {}  # store for the backend, populated by child class
        self.keys = []  # present keys in the store (always populated)

        # Check if meta is cached and clean
        #
        # - for local filesystem - Check if the repository is present locally
        #   or not
        # - for kubernetes - Check if the sidecar has the repository synced
        #   with the self.REMOTE
        if config.META['DEPLOYMENT'] == 'local':
            if os.path.isdir(self.META) is False:
                os.system('/usr/bin/git clone {} {}'.format(self.REMOTE,
                                                            self.META))

        # TODO : implement for sidecar

    @abstractmethod
    def query(self):
        """
        Query the data folder to load all the data objects in the memory

        Raises:
            NotImplementedError: Will raise when the child has not overloaded
            the method.
        """
        raise NotImplementedError("Must override query method")

    @abstractmethod
    def fallback(self, key):
        """
        Fallback to load the data if the store is empty
        """
        raise NotImplementedError("Must override fallback method")

    def all(self):
        """
        Return a list of all resource present in the meta repository

        Returns:
            list: list of all the resouces
        """
        return [self.store[key] for key in self.store.keys()]

    def where(self, key, value):
        """
        Return the list of resource which matches the conditions

        Args:
            key (string): key in the resource whose value will be checked
            value (mixed): value
        """
        return [r for r in self.all() if r[key] == value]

    def get(self, key):
        """
        Get a specific resource from the data store

        Args:
            key (string): primary key for the resource (generally directory
                          or file name)

        Returns:
            dict: resource info as a dict
        """
        if key not in self.keys:
            return None

        if key in self.store.keys():
            print('key in the store')
            return self.store[key]

        return self.fallback(key)


class Election(Meta):
    """
    Election is the application's main file based backend, this is strictly
    read only database managed by GitOps, see the meta repository for more
    information.

    (primary key) : directory name (saves the check for uniqueness)
    """

    def __init__(self, meta):
        """
        Create a brand new Elections backend object

        Args:
            meta (dict): info about the repo required for the creation of
                         datastore.
        """
        Meta.__init__(self, meta)
        self._path = os.path.join(self.META, 'elections')
        self.keys = os.listdir(self._path)

    def query(self):
        """
        Query the data folder and populate the datastore i.e., loads all the
        elections into the store.

        Returns:
            Election: returns the reference to the election object
        """
        for e in self.keys:
            _path = os.path.join(self._path, e)  # yaml path
            self.store[e] = self.build_election_from_yaml(_path)

        return self

    def fallback(self, key):
        """
        Fall back for the get method, when the store is not populated or is in
        between updation from a webhook signal directory load the election into
        the memory.

        Args:
            key (string): primary key / identifier for the election

        Returns:
            dict: Election info in an dict
        """
        _path = os.path.join(self._path, key, 'election.yaml')
        return self.build_election_from_yaml(_path)

    def build_election_from_yaml(self, _path):
        """
        Build the election object from the yam file, add primary key check the
        status and perform other necessary computation.

        Args:
            _path (string): path for the election's yaml
            key (string): primary key given to the election

        Returns:
            dict: Complete Election info in an dict
        """
        election = utils.parse_yaml_from_file(
            os.path.join(_path, 'election.yaml'))
        # Set Status of the election
        election['status'] = utils.check_election_status(election)
        election['key'] = _path.split('/')[-1]
        election['description'] = markdown.markdown(open(os.path.join(
            _path, 'election_desc.md'), 'r').read(), extras=['cuddled-lists'])

        return election

    def voters(self, eid):
        """
        Get all the voters of the election

        Args:
            eid (string): primary key for the election

        Returns:
            list: list of voters
        """
        _path = os.path.join(self._path, eid, 'voters.yaml')
        voters = utils.parse_yaml_from_file(_path)

        return voters

    def candidates(self, eid):
        """
        Get candidates participating in the election

        Args:
            eid (string): primary key for the election

        Returns:
            list: list of the election's candidates
        """
        files = os.listdir(os.path.join(self._path, eid))
        result = []
        for f in files:
            if 'candidate' in f:
                # Read the markdown file
                md = open(os.path.join(self._path, eid, f)).read()
                # Build the candidate Object
                candidate = utils.extract_candidate_info(md)
                candidate['key'] = candidate['ID']
                result.append(candidate)

        return result

    def candidate(self, eid, cid):
        """
        Get a particular candidate participating in the election

        Args:
            eid (string): primary key for the election
            cid (string): primary key for the candidate

        Returns:
            dict: dict containing candidate info
        """
        _path = os.path.join(os.path.join(
            self._path, eid, 'candidate-{}.md'.format(cid)))
        if os.path.exists(_path) is False:
            return None
        md = open(_path).read()
        candidate = utils.extract_candidate_info(md)
        candidate['key'] = cid
        candidate['election_key'] = eid
        candidate['description'] = markdown.markdown(
            utils.extract_candidate_description(md), extras=['cuddled-lists'])

        return candidate
