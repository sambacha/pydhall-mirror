import pytest

from pydhall.parser import Dhall


@pytest.mark.parametrize("input,expected", [
    ("let a = 42 in a", 42),
    ("let a = 42 in let a = 43 in a", 43),
    ("let a = 42 in let a = 43 in a@1", 42),
])
def test_let(input, expected):
    assert Dhall.p_parse(input).eval() == expected

@pytest.mark.parametrize("input,expected", [
    ("if True then 1 else 2", 1),
    ("if False then 1 else 2", 2),
])
def test_if(input, expected):
    assert Dhall.p_parse(input).eval() == expected
