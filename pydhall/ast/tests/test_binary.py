import pytest

from pydhall import loads
from pydhall.ast.term import Term
from pydhall.ast.term import NaturalLit

# this is more of an integration test as the sha256 values
# are the results of dahll-haskell's hash command.
@pytest.mark.parametrize("input,expected", [
    ("42",
     "sha256:c39cde2e11e3d5a57cccbc06f6599256ece67b3d16d1bc1df1d0cfa79d9be605"),
    ("forall (a: Type) -> a",
     "sha256:1d8bb5b446ef7ca849c66a5b319d69b1e133b86b0d9f290d423ed0494b0d7c3d"),
    ("forall (_: Type) -> _",
     "sha256:1d8bb5b446ef7ca849c66a5b319d69b1e133b86b0d9f290d423ed0494b0d7c3d"),
    (r"\(a: Bool) -> a",
     "sha256:400a629db0d5af895d438acf74d60a07c0315c88b17cd541ae182d7dfc3247d6"),
    (r"\(_: Bool) -> _",
     "sha256:400a629db0d5af895d438acf74d60a07c0315c88b17cd541ae182d7dfc3247d6"),
    ("True",
     "sha256:27abdeddfe8503496adeb623466caa47da5f63abd2bc6fa19f6cfcb73ecfed70"),
    (r"let fn = \(a: Bool) -> a in fn True",
     "sha256:27abdeddfe8503496adeb623466caa47da5f63abd2bc6fa19f6cfcb73ecfed70"),
    (r"let fn = \(a: Bool) -> \(b: Bool) -> a in fn True False",
     "sha256:27abdeddfe8503496adeb623466caa47da5f63abd2bc6fa19f6cfcb73ecfed70"),
    ("[1,2]",
     "sha256:5fcae452b143221b8500ae6ff76efa56105d702e413e4365ee20a4c93226d224"),
])
def test_sha256(input, expected):
    result = loads(input)
    assert result.eval().quote(normalize=True).sha256() == expected


@pytest.mark.parametrize("input", [
    NaturalLit(1),
])
def test_encode_decode(input):
    result = Term.from_cbor(input.cbor())
    assert result == input
