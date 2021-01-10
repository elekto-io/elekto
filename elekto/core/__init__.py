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


def schulze_rank(candidates, p, no_winners=1):
    wins = defaultdict(list)

    for V in candidates:
        n = 0
        for W in candidates:
            if V != W and p.get((V, W), 0) > p.get((W, V), 0):
                n += 1
        wins[n].append(V)

    ranks = sorted(wins.items())
    return ranks
