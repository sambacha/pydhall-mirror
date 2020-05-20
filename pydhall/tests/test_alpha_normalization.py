from pathlib import Path
import os

import pytest

import pydhall as dhall

from . import FAILURES

TEST_DATA_ROOT = Path("dhall-lang/tests/alpha-normalization/success/unit")


def make_test_file_pair(root):
    root = Path(root)
    files = os.listdir(root)
    success = []
    failures = []
    for name1 in files:
        name2 = name1.replace("A.", "B.")
        if (name1 != name2) and (name2 in files):
            if str(root.joinpath(name1)).replace("A.dhall", "") in FAILURES:
                failures.append((root.joinpath(name1), root.joinpath(name2)))
            else:
                success.append((root.joinpath(name1), root.joinpath(name2)))
    return success, failures

SUC, FAIL = make_test_file_pair(TEST_DATA_ROOT)

def do_test_alpha_normalization(input, expected):
    with open(input) as f:
        termA = dhall.load(f)
    with open(expected) as f:
        termB = dhall.load(f)

@pytest.mark.parametrize("input,expected", SUC)
def test_alpha_normalization(input, expected):
    do_test_alpha_normalization(input, expected)

@pytest.mark.parametrize("input,expected", FAIL)
@pytest.mark.xfail
def test_alpha_normalization_fail(input, expected):
    do_test_alpha_normalization(input, expected)
