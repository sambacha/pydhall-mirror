from pathlib import Path
import os

import pytest

from pydhall.parser import Dhall
from pydhall.ast import Term
from pydhall.ast.type_error import DhallTypeError

from .utils import make_test_file_pairs, collect_test_files


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
    with open(input) as f:
        termA = Dhall.p_parse(f.read())
    with open(expected) as f:
        termB = Dhall.p_parse(f.read())

    assert termA.resolve(input).type().quote() == termB


@pytest.mark.parametrize("input", collect_test_files(TEST_DATA_ROOT.joinpath("failure")))
def test_type_inference_failure(input):
    with open(input) as f:
        term = Dhall.p_parse(f.read())
        with pytest.raises(DhallTypeError):
            term.resolve(input).type()
