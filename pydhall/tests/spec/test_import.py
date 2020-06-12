from pathlib import Path
import os

import pytest

from pydhall.parser import Dhall
from pydhall.ast import LocalFile

from .utils import make_test_file_pairs

TEST_DATA_ROOT = Path("dhall-lang/tests/import")

os.environ["DHALL_TEST_VAR"] = "6 * 7"

@pytest.mark.parametrize("input,expected", make_test_file_pairs(TEST_DATA_ROOT))
def test_import(input, expected):
    with open(input) as f:
        termA = Dhall.p_parse(f.read())
    with open(expected) as f:
        termB = Dhall.p_parse(f.read())

    termA = termA.resolve(LocalFile(input, None, 0)).eval().quote()
    print(input)
    assert termA == termB

