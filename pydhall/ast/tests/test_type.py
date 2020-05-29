import pytest

from pydhall.parser import Dhall
from pydhall.ast.value import Bool
from pydhall.ast.term.universe import TypeValue, KindValue, SortValue


@pytest.mark.parametrize("input,expected", [
    ("True", Bool),
    ("False", Bool),
    ("Bool", TypeValue),
])
def test_bool(input, expected):
    assert Dhall.p_parse(input).type() == expected


@pytest.mark.parametrize("input,expected", [
    ("Type", KindValue),
    ("Kind", SortValue),
])
def test_universe(input, expected):
    assert Dhall.p_parse(input).type() == expected
