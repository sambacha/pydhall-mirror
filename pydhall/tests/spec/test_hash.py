from pathlib import Path

import pytest

from pydhall.parser import Dhall
from pydhall.ast import Term

from . import FAILURES
from .utils import make_test_file_pairs


TEST_DATA_ROOT = Path("dhall-lang/tests/semantic-hash/")


def make_success_simple_params(root):
    simpleroot = Path(root).joinpath("success/simple")
    unitroot = Path(root).joinpath("success/unit")
    simplification = Path(root).joinpath("success/simplifications")
    return make_test_file_pairs(simpleroot) + make_test_file_pairs(unitroot)

# @pytest.mark.parametrize("input,expected", make_success_simple_params(TEST_DATA_ROOT))
# def test_bnorm_simple(input, expected):
#     with open(input) as f:
#         termA = Dhall.p_parse(f.read())
#     with open(expected) as f:
#         termB = Dhall.p_parse(f.read())

#     assert termA.eval().quote() == termB.eval().quote()

@pytest.mark.parametrize("input,expected", make_test_file_pairs(TEST_DATA_ROOT, b_ext=".hash"))
def test_hash(input, expected):
    with open(input) as f:
        termA = Dhall.p_parse(f.read())
    with open(expected) as f:
        hash = f.read().strip()

    assert termA.resolve(input).eval().quote(normalize=True).sha256() == hash
