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

def generate_result(candidates, ballots, no_winners):
    choices = [c['ID'] for c in candidates]  # init all candidates with zero
    print(choices)
    preferences = {}  # this contains the voter's preferences
    # G = {}
    for b in ballots:
        # wins[b.candidate] += 1 if b.rank == 1 else 0  # populate wins
        if b.voter not in preferences.keys():
            preferences[b.voter] = []
        preferences[b.voter].append(b)
        # print(b.voter, b.election_id, b.candidate)
    
    print(preferences)
    # ranks = {k: v for k, v in sorted(
        # wins.items(), key=lambda item: item[1], reverse=True)}
    # print(ranks)

    return []
