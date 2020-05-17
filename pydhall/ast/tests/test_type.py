import pytest

from pydhall.parser import Dhall
from pydhall.ast.value import (Bool, Type, Kind, Sort)


@pytest.mark.parametrize("input,expected", [
    ("True", Bool),
    ("False", Bool),
    ("Bool", Type),
])
def test_bool(input, expected):
    assert Dhall.p_parse(input).type == expected


@pytest.mark.parametrize("input,expected", [
    ("Type", Kind),
    ("Kind", Sort),
])
def test_universe(input, expected):
    assert Dhall.p_parse(input).type == expected
