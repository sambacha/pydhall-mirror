import pytest

from pydhall.parser import Dhall


@pytest.mark.parametrize("input,expected", [
    ("let a = 42 in a", 42),
    ("let a = 42 in let a = 43 in a", 43),
    ("let a = 42 in let a = 43 in a@1", 42),
])
def test_let(input, expected):
    p = Dhall(input)
    result = p.Bindings().eval()
    assert result == expected
