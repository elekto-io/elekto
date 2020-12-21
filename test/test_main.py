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
import sys
import pytest

# Workaround to safely import the k8s_elections module
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from k8s_elections import APP  # noqa
from k8s_elections.models.sql import migrate  # noqa

# ############################################################################
# suite: main
# description: Testing of the application's lowest layers componentes
# ############################################################################


@pytest.fixture
def client():
    # Generate Database
    db = os.path.abspath('./test.db')
    os.system('touch {}'.format(db))

    with APP.test_client() as client:
        with APP.app_context():
            migrate(APP.config['DATABASE_URL'])
        yield client

    os.system('rm {}'.format(db))
    # os.system('rm -rf {}'.format(APP.config['META']['PATH']))


def test_clone(client):
    """
    Tests the cloing of the meta repo
    """
    assert os.path.isdir(APP.config['META']['PATH'])


def test_welcome(client):
    """
    Tests the welcome route i.e., '/'
    """
    rv = client.get('/')
    assert rv.status_code == 200
    assert str.encode(APP.config['NAME']) in rv.data


def test_custom(client):
    import pandas as pd
    df = pd.read_csv('BALLOTS.csv')

    candidates = list(df.columns)
    print('\n')
    ballots = {}
    for v, row in df.iterrows():
        ballots[v] = []
        for c in candidates:
            if row[c] == 'No opinion':
                continue
            ballots[v].append((c, int(row[c])))

    d = {(V, W): 0 for V in candidates for W in candidates if V != W}
    for voter in ballots.keys():
        for V in ballots[voter]:
            for W in ballots[voter]:
                if V[0] != W[0]:
                    d[(V[0], W[0])] += 1 if V[1] > W[1] else 0

    # # # compute p[X, Y]
    p = {}
    for X in candidates:
        for Y in candidates:
            if X != Y:
                strength = d.get((X, Y), 0)
                p[X, Y] = strength if strength > d.get((Y, X), 0) else 0

    for X in candidates:
        for Z in candidates:
            if X != Z:
                for Y in candidates:
                    if X != Y and Z != Y:
                        p[Z, Y] = max(p.get((Z, Y)), min(
                            p.get((Z, X), 0), p.get((X, Y), 0)))

    # Rank p
    from collections import defaultdict
    wins = defaultdict(list)
    for V in candidates:
        n = 0
        for W in candidates:
            if V != W and p.get((V, W), 0) > p.get((W, V), 0):
                n += 1
        wins[n].append(V)

    ranks = sorted(wins.items())
    results = []

    for i in range(1, min(10, len(ranks))):
        results.append(ranks[i - 1][1])

    for i in range(len(results)):
        if (i == 0):
            print('{} {} is the condorcet winner'.format(i + 1, results[i][0]))
        else:
            print('{} {} loses to {} by {} {}'.format(
                i + 1,
                results[i][0],
                results[i - 1][0],
                d.get((results[i][0], results[i - 1][0]), 0),
                d.get((results[i - 1][0], results[i][0]), 0)
            ))

    # print(results)
