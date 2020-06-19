from pathlib import Path
import os

import pytest

from pydhall.parser import Dhall
from pydhall.ast import LocalFile
from pydhall.ast.import_ import base as import_
from pydhall.ast.import_.base import set_cache_class, TestFSCache

from .utils import make_test_file_pairs

TEST_DATA_ROOT = Path("dhall-lang/tests/import")

os.environ["DHALL_TEST_VAR"] = "6 * 7"

@pytest.mark.parametrize("input,expected", make_test_file_pairs(TEST_DATA_ROOT))
def test_import(input, expected):
    set_cache_class(TestFSCache)
    try:
        print(input)
        with open(input) as f:
            termA = Dhall.p_parse(f.read())
        with open(expected) as f:
            termB = Dhall.p_parse(f.read())

        term = termA.resolve(LocalFile(input, None, 0)).eval().quote()
        assert term == termB
    finally:
        import_.CACHE.reset()

