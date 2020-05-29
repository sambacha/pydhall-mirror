from pathlib import Path
import os

import pytest

from pydhall.parser import Dhall
from pydhall.ast.term import Term

from . import FAILURES


TEST_DATA_ROOT = Path("dhall-lang/tests/normalization/")


def make_test_file_pairs(dir):
    pairs = []
    files = os.listdir(dir)
    for name1 in files:
        path1 = dir.joinpath(name1)
        if os.path.isdir(path1):
            pairs.extend(make_test_file_pairs(path1))
            continue
        name2 = name1.replace("A.", "B.")
        path2 = dir.joinpath(name2)
        if not os.path.exists(path2):
            name2 = name2 + "b"
            path2 = str(path2) + "b"
        if (name1 != name2) and (name2 in files):
            if str(path1).replace("A.dhall", "") in FAILURES:
                pairs.append(
                    pytest.param(
                        path1,
                        path2,
                        marks=pytest.mark.xfail(strict=True)))
            else:
                pairs.append((path1, path2))
    return pairs


def make_success_simple_params(root):
    simpleroot = Path(root).joinpath("success/simple")
    unitroot = Path(root).joinpath("success/unit")
    return make_test_file_pairs(root) + make_test_file_pairs(unitroot)

# @pytest.mark.skip()
@pytest.mark.parametrize("input,expected", make_success_simple_params(TEST_DATA_ROOT))
def test_parse_success_simple(input, expected):
    with open(input) as f:
        termA = Dhall.p_parse(f.read())
    with open(expected) as f:
        termB = Dhall.p_parse(f.read())

    # TODO: bypasses incomplete parsing. remove this
    # if not isinstance(termA, Term):
    #     return

    termA.type()

    assert termA.eval().quote() == termB.eval().quote()
