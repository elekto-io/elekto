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
import markdown2 as markdown

from k8s_elections import constants
from k8s_elections.models.sql import Election

# to preserve the import consistency
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def parse_yaml(yaml_path):
    """
    Loads a yaml from the system and return a dict

    Args:
        yaml_path (os.path): location of the yaml file

    Returns:
        dict: parsed yaml content in a dict
    """
    if os.path.exists(yaml_path) is False:
        return None

    return yaml.load(open(yaml_path, 'r').read(), Loader=Loader)


def parse_yaml_from_string(yaml_string):
    """
    Convert yaml string to yaml object (dict)

    Args:
        yaml_string (string): yaml string to be converted

    Returns:
        dict: parsed yaml dict object
    """
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


def sync_db_with_meta(session, elections):
    try:
        log = ""
        for e in elections:
            query = session.query(Election).filter_by(key=e['key']).first()
            if query:
                query.name = e['name']
            else:
                session.add(Election(key=e['key'], name=e['name']))
                log += "{} added in the db.\n".format(e['key'])
        session.commit()
        return log + "Synced DB with META"
    except:
        return "Tables does not exists yet"


def parse_md(md, path=True):
    try:
        if path:
            md = open(md, 'r').read()
        return markdown.markdown(md, extras=['cuddled-lists'])
    except FileNotFoundError:
        return None
    except:
        return 'Markdown format not Correct'
