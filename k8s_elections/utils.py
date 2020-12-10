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
import yaml

from k8s_elections import constants
from datetime import datetime


def check_election_status(election):
    """
    Compute and return election's running status

    Args:
        election (dict): dict with required election's info like start, end
                         datetime

    Returns:
        string: status of the election
    """
    start = election['start_datetime']
    end = election['end_datetime']
    now = datetime.now()

    if now < start:
        return constants.ELEC_STAT_UPCOMING
    elif end < now:
        return constants.ELEC_STAT_COMPLETED
    else:
        return constants.ELEC_STAT_RUNNING


def parse_yaml_from_file(yaml_path):
    """
    Loads a yaml from the system and return a dict

    Args:
        yaml_path (os.path): location of the yaml file

    Returns:
        dict: parsed yaml content in a dict
    """
    if os.path.exists(yaml_path) is False:
        return None

    # to preserve the import consistency
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    return yaml.load(open(yaml_path, 'r').read(), Loader=Loader)


def parse_yaml_from_string(yaml_string):
    """
    Convert yaml string to yaml object (dict)

    Args:
        yaml_string (string): yaml string to be converted

    Returns:
        dict: parsed yaml dict object
    """
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    return yaml.load(yaml_string, Loader=Loader)


def extract_candidate_info(md):
    """
    Extract candidates info from the given hybrid string

    Args:
        md (string): markdown string read from the candidate-xxxx.md file

    Returns:
        dict: candidate info as a dict
    """
    # TODO : check for wrong candidates strings
    info = md[md.find(
        constants.CAND_START_DEL) - 1 +
        len(constants.CAND_START_DEL):md.rfind(constants.CAND_END_DEL)]

    info = info.strip('-').strip('\n')

    return parse_yaml_from_string(info)


def extract_candidate_description(md):
    """
    Extract candidates description from the hybrid string

    Args:
        md (string): markdown string read from the candidate-xxxx.md file

    Returns:
        string: mardown description
    """
    desc = md.split(constants.CAND_END_DEL)[-1].strip('-').strip('\n')
    return desc
