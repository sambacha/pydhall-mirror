import pytest

from pydhall.parser import Dhall
from pydhall.ast.term.boolean.base import BoolTypeValue
from pydhall.ast.term.universe import TypeValue, KindValue, SortValue


@pytest.mark.parametrize("input,expected", [
    ("True", BoolTypeValue),
    ("False", BoolTypeValue),
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
