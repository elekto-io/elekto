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
import yaml


class Meta:
    """
    Meta (YAML) File based backend for the application
    """

    def __init__(self):
        """
        Create a brand new meta backend instance
        """
        self.META = os.path.abspath(config.META['PATH'])
        self.REMOTE = config.META['REMOTE']

        if os.path.isdir(self.META) is False:
            os.system('/usr/bin/git clone {} {}'.format(self.REMOTE,
                                                        self.META))


class Elections(Meta):

    def __init__(self):
        Meta.__init__(self)
        self.path = os.path.join(self.META, 'elections')
        self.store = {}

    def query(self):

        # to preserve the import consistency
        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader

        # ############################## #
        # TODO : cache for faster access #
        # ############################## #

        for e in os.listdir(self.path):
            # The main thing to notice here is that we need a primary key for
            # faster searching to elections. As by the design of application
            # yaml is read only therefore the directory name is used as primary
            # key.
            with open(os.path.join(self.path, e, 'election.yaml'), 'r') as f:
                election = yaml.load(f.read(), Loader=Loader)
                election['key'] = e
                self.store[e] = election

        return self

    def all(self):
        """
        Return a list of all elections present in the meta repository

        Returns:
            list: list of all the elections
        """

        # ############################## #
        # TODO : cache for faster access #
        # ############################## #

        result = []
        for key, value in self.store.items():
            result.append(value)
        return result

    def get(self, key):
        if key in self.store.keys():
            return self.store[key]
        
        return None

    # def where(key, value):
    #     return print()
