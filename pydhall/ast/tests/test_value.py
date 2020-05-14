import pytest

from pydhall.parser import Dhall
from .. import value as v


# @pytest.mark.parametrize("input,expected", [

def test_natural_lit():
    n = v.NaturalLit(1)
    assert isinstance(n, v.Value)
    assert repr(n) == "NaturalLit(1)"
    assert str(n) == "1"
    assert v.NaturalLit(0) == v.NaturalLit(0)
    assert v.NaturalLit(0) != v.NaturalLit(1)
