from pathlib import Path
import os

import pytest

from pydhall.parser import Dhall
from pydhall.core import Term
from pydhall.core.type_error import DhallTypeError
from pydhall.core.import_.base import set_cache_class, InMemoryCache

from .utils import make_test_file_pairs, collect_test_files
from fastidious.parser_base import ParserError


TEST_DATA_ROOT = Path("dhall-lang/tests/type-inference/")


def make_success_simple_params(root):
    simpleroot = Path(root).joinpath("success/simple")
    unitroot = Path(root).joinpath("success/unit")
    return make_test_file_pairs(simpleroot) + make_test_file_pairs(unitroot)

# @pytest.mark.parametrize("input,expected", make_success_simple_params(TEST_DATA_ROOT))
# def test_type_inference_simple_success(input, expected):
#     with open(input) as f:
#         termA = Dhall.p_parse(f.read())
#     with open(expected) as f:
#         termB = Dhall.p_parse(f.read())

#     assert termA.resolve(input).type().quote() == termB

@pytest.mark.parametrize("input,expected", make_test_file_pairs(TEST_DATA_ROOT))
def test_type_inference_success(input, expected):
    set_cache_class(InMemoryCache)
    with open(input) as f:
        termA = Dhall.p_parse(f.read())
    with open(expected) as f:
        termB = Dhall.p_parse(f.read())

    assert termA.resolve(input).type().quote() == termB


@pytest.mark.parametrize("input", collect_test_files(TEST_DATA_ROOT.joinpath("failure")))
def test_type_inference_failure(input):
    set_cache_class(InMemoryCache)
    with open(input) as f:
        with pytest.raises(Exception) as info:
            term = Dhall.p_parse(f.read())
            term.resolve(input).type()
        if info.type not in (DhallTypeError, ParserError):
            print(info.traceback)
            assert False, info.value
