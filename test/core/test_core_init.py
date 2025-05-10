# Copyright 2025 The Elekto Authors
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
# Author(s):         Carson Weeks <mail@carsonweeks.com>

import os
import sys
import pytest

from elekto.core import schulze_d, schulze_p, schulze_rank  # noqa

def test_schulze_d():
    candidates = ["A", "B", "C"]
    ballots = {
        "voter1": [("A", 3), ("B", 2), ("C", 1)],
        "voter2": [("B", 3), ("C", 2), ("A", 1)]
    }

    expected_d = {
        ("A", "B"): 1,
        ("A", "C"): 1,
        ("B", "A"): 1,
        ("B", "C"): 2,
        ("C", "A"): 1,
        ("C", "B"): 0,
    }

    result = schulze_d(candidates, ballots)
    assert result == expected_d

def test_schulze_p():
    candidates = ["A", "B", "C", "D"]
    d = {
        ("A", "B"): 12, ("B", "A"):  9,
        ("A", "C"):  7, ("C", "A"): 14,
        ("A", "D"): 16, ("D", "A"):  3,
        ("B", "C"):  5, ("C", "B"): 10,
        ("B", "D"): 18, ("D", "B"):  1,
        ("C", "D"):  2, ("D", "C"): 20,
    }

    expected_p = {
        ("A", "B"): 12,
        ("B", "A"): 14,
        ("A", "C"): 16,
        ("C", "A"): 14,
        ("A", "D"): 16,
        ("D", "A"): 14,
        ("B", "C"): 18,
        ("C", "B"): 12,
        ("B", "D"): 18,
        ("D", "B"): 12,
        ("C", "D"): 14,
        ("D", "C"): 20,
    }

    result = schulze_p(candidates, d)
    assert result == expected_p

def test_schulze_rank_simple():
    candidates = ["A", "B", "C"]
    p = {
        ("A", "B"): 10,  ("B", "A"): 5,
        ("A", "C"): 15,  ("C", "A"): 2,
        ("B", "C"):  8,  ("C", "B"): 3,
    }

    expected = [
        (0, ["C"]),
        (1, ["B"]),
        (2, ["A"])
    ]

    result = schulze_rank(candidates, p)
    assert result == expected

def test_schulze_rank_tie():
    candidates = ["A", "B", "C"]
    p = {
        ("A", "B"): 10, ("B", "A"):  5,
        ("B", "C"): 10, ("C", "B"):  5,
        ("C", "A"): 10, ("A", "C"):  5,
    }
    expected = [
        (1, ["A", "B", "C"])
    ]

    result = schulze_rank(candidates, p)
    assert result == expected

