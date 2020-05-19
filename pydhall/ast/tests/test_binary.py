import pytest

from pydhall import loads

# this is more of an integration test as the sha256 values
# are the results of dahll-haskell's hash command.
@pytest.mark.parametrize("input,expected", [
    ("True",
     "sha256:27abdeddfe8503496adeb623466caa47da5f63abd2bc6fa19f6cfcb73ecfed70"),
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
    (r"let fn = \(a: Bool) -> a in fn True",
     "sha256:27abdeddfe8503496adeb623466caa47da5f63abd2bc6fa19f6cfcb73ecfed70"),
])
def test_sha256(input, expected):
    result = loads(input)
    assert result.eval().quote(normalize=True).sha256() == expected
