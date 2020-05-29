from pathlib import Path
import os

import pytest

from pydhall.parser import Dhall

from . import FAILURES

TEST_DATA_ROOT = Path("dhall-lang/tests/type-inference/success/")


def make_test_file_pair(root):
    root = Path(root)
    pairs = []
    for dir in ["unit", "simple"]:
        dir = root.joinpath(dir)
        files = os.listdir(dir)
        for name1 in files:
            name2 = name1.replace("A.", "B.")
            if (name1 != name2) and (name2 in files):
                if str(dir.joinpath(name1)).replace("A.dhall", "") in FAILURES:
                    pairs.append(
                        pytest.param(
                            dir.joinpath(name1),
                            dir.joinpath(name2),
                            marks=pytest.mark.xfail(strict=True)))
                else:
                    pairs.append((dir.joinpath(name1), dir.joinpath(name2)))
    return pairs

@pytest.mark.parametrize("input,expected", make_test_file_pair(TEST_DATA_ROOT))
def test_type_simple(input, expected):
    with open(input) as f:
        termA = Dhall.p_parse(f.read())
    with open(expected) as f:
        termB = Dhall.p_parse(f.read())

    assert termA.type().quote() == termB

