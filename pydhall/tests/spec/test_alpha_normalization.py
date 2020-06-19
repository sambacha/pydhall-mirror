from pathlib import Path
import os

import pytest

from pydhall.parser import Dhall
from pydhall.ast.import_.base import set_cache_class, InMemoryCache

from .utils import make_test_file_pairs

TEST_DATA_ROOT = Path("dhall-lang/tests/alpha-normalization/success/")


@pytest.mark.parametrize("input,expected", make_test_file_pairs(TEST_DATA_ROOT))
def test_alpha_normalization_unit(input, expected):
    set_cache_class(InMemoryCache)
    with open(input) as f:
        termA = Dhall.p_parse(f.read())
    with open(expected) as f:
        termB = Dhall.p_parse(f.read())

    termA = termA.eval().quote(normalize=True)
    assert termA == termB
