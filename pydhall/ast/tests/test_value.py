import pytest

from pydhall.parser import Dhall
from .. import value as v


# @pytest.mark.parametrize("input,expected", [

def test_natural_lit():
    n = v.NaturalLit(1)
    assert isinstance(n, v.Value)
    assert isinstance(n, v.NaturalLit)
    assert isinstance(n, int)
    assert repr(n) == "NaturalLit(1)"
    assert str(n) == "1"
    assert n.as_dhall() == "1"
    assert v.NaturalLit(0) == v.NaturalLit(0)
    assert v.NaturalLit(0) != v.NaturalLit(1)


def test_integer_lit():
    i = v.IntegerLit(1)
    assert isinstance(i, v.Value)
    assert isinstance(i, v.IntegerLit)
    assert isinstance(i, int)
    assert repr(i) == "IntegerLit(1)"
    assert str(i) == "1"
    assert i.as_dhall() == "+1"
    assert v.IntegerLit(0) == v.IntegerLit(0)
    assert v.IntegerLit(0) != v.IntegerLit(1)


def test_double_lit():
    d = v.DoubleLit(0.1)
    assert isinstance(d, v.Value)
    assert isinstance(d, v.DoubleLit)
    assert isinstance(d, float)
    assert str(d) == "0.1"
    assert v.DoubleLit(0.1) == v.DoubleLit(0.1)
    assert v.DoubleLit(0.1) != v.DoubleLit(0.2)
