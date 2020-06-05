from pathlib import Path
import os

import pytest

from pydhall.parser import Dhall
from pydhall.ast.term import Term

from . import FAILURES


TEST_DATA_ROOT = Path("dhall-lang/tests/parser/")


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
                # continue
                pairs.append(
                    pytest.param(
                        path1,
                        path2,
                        marks=pytest.mark.xfail(strict=True)))
            else:
                pairs.append((path1, path2))
    return pairs


def make_success_params(root):
    root = Path(root).joinpath("success")
    return make_test_file_pairs(root)

# @pytest.mark.skip()
@pytest.mark.parametrize("input,expected", make_success_params(TEST_DATA_ROOT))
def test_parse_success(input, expected):
    with open(input) as f:
        termA = Dhall.p_parse(f.read())
    with open(expected, "rb") as f:
        assert isinstance(termA, Term)
        bin = termA.cbor()
        try:
            assert termA.cbor() == f.read()
        except AssertionError:
            print("")
            print(input)
            print(repr(termA))
            print(termA.cbor_values())
            with open(expected.replace(".dhallb", ".diag")) as f:
                print(f.read())
            raise

