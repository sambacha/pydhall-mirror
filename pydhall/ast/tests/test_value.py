import pytest

from pydhall.parser import Dhall
from pydhall.ast.base import Value
from pydhall.ast.double.base import DoubleLitValue
from pydhall.ast.integer.base import IntegerLitValue
from pydhall.ast.natural.base import NaturalLitValue


# @pytest.mark.parametrize("input,expected", [

def test_natural_lit():
    n = NaturalLitValue(1)
    assert isinstance(n, Value)
    assert isinstance(n, NaturalLitValue)
    assert isinstance(n, int)
    assert repr(n) == "NaturalLitValue(1)"
    assert str(n) == "1"
    assert n.as_dhall() == "1"
    assert NaturalLitValue(0) == NaturalLitValue(0)
    assert NaturalLitValue(0) != NaturalLitValue(1)


def test_integer_lit():
    i = IntegerLitValue(1)
    assert isinstance(i, Value)
    assert isinstance(i, IntegerLitValue)
    assert isinstance(i, int)
    assert repr(i) == "IntegerLitValue(1)"
    assert str(i) == "1"
    assert i.as_dhall() == "+1"
    assert IntegerLitValue(0) == IntegerLitValue(0)
    assert IntegerLitValue(0) != IntegerLitValue(1)


def test_double_lit():
    d = DoubleLitValue(0.1)
    assert isinstance(d, Value)
    assert isinstance(d, DoubleLitValue)
    assert isinstance(d, float)
    assert str(d) == "0.1"
    assert DoubleLitValue(0.1) == DoubleLitValue(0.1)
    assert DoubleLitValue(0.1) != DoubleLitValue(0.2)
