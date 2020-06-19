from pathlib import Path

import pytest

from pydhall.parser import Dhall
from pydhall.ast import Term
from pydhall.ast.import_.base import set_cache_class, InMemoryCache

from . import FAILURES
from .utils import make_test_file_pairs


TEST_DATA_ROOT = Path("dhall-lang/tests/normalization/")


@pytest.mark.parametrize("input,expected", make_test_file_pairs(TEST_DATA_ROOT))
def test_bnorm(input, expected):
    set_cache_class(InMemoryCache)
    with open(input) as f:
        termA = Dhall.p_parse(f.read())
    with open(expected) as f:
        termB = Dhall.p_parse(f.read())

    assert termA.resolve(input).eval().quote() == termB.resolve(expected).eval().quote()
