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

"""
core module is responsible for handling all the voting election, contains
methods like condorcet, schulze, irv and more.
"""

from collections import defaultdict


def schulze_d(candidates, ballots):
    d = {(V, W): 0 for V in candidates for W in candidates if V != W}
    for voter in ballots.keys():
        for V, Vr in ballots[voter]:
            for W, Wr in ballots[voter]:
                if V != W:
                    d[(V, W)] += 1 if Vr > Wr else 0

    return d


def schulze_p(candidates, d):
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
                        p[Z, Y] = max(p.get((Z, Y), 0), min(
                            p.get((Z, X), 0), p.get((X, Y), 0)))

    return p


def generate_result(candidates, ballots, no_winners):
    # choices = [c['ID'] for c in candidates]  # init all candidates with zero
    preferences = {}  # this contains the voter's preferences
    ballots = [b for b in ballots if b.rank > 0]
    candidates = [c['ID'] for c in candidates]

    for b in ballots:
        if b.voter not in preferences.keys():
            preferences[b.voter] = []
        preferences[b.voter].append(b)

    #  d[V,W] be the number of voters who prefer candidate V to W.
    d = {(V, W): 0 for V in candidates for W in candidates if V != W}

    for voter in preferences.keys():
        for V in preferences[voter]:
            for W in preferences[voter]:
                if (V.candidate != W.candidate):
                    d[(V.candidate, W.candidate)] += 1 if V.rank > W.rank else 0

    # compute p[X, Y]
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
    wins = defaultdict(list)
    for V in candidates:
        n = 0
        for W in candidates:
            if V != W and p.get((V, W), 0) > p.get((W, V), 0):
                n += 1
        wins[n].append(V)

    ranks = sorted(wins.items())

    return ranks[:min(no_winners, len(ranks))]
