import pytest

from pydhall.parser import Dhall
from pydhall.core import Term
from pydhall.render import render


@pytest.mark.parametrize("input,ascii", [
    ("3", False),
    ("+3", False),
    ("True", False),
    ("1.42", False),
    ("True || False", False),
    ("True || False && True", False),
    ("(True || False) && True", False),
    ("assert : (λ(x : Bool) → x) ≡ (λ(y : Bool) → y)", False),
    ("assert : (\(x : Bool) -> x) === (\(y : Bool) -> y)", True),
    ("""[
, True
, False
, True
, False
, True
, True
, False
, True
, False
, True
, False
, True
, False
, True
, False
, True
, False
, True
, False
, True
, False
]""", False),
    ("[ True, False ]", False),
    ("""let even
    : List Bool → Bool
    = λ(xs : List Bool) →
        List/fold Bool xs Bool (λ(x : Bool) → λ(y : Bool) → x == y) True

let example0 = assert : even [ False, True, False ] ≡ True

in even""", False),
    ("""let map
    : ∀(a : Type) → ∀(b : Type) → (a → b) → List a → List b
    = λ(a : Type) →
      λ(b : Type) →
      λ(f : a → b) →
      λ(xs : List a) →
        List/build
          b
          ( λ(list : Type) →
            λ(cons : b → list → list) →
              List/fold a xs list (λ(x : a) → cons (f x))
          )

let example0 =
        assert
      : map Natural Bool Natural/even [ 2, 3, 5 ] ≡ [ True, False, False ]

in  map""", False),

])
def test_render(input, ascii):
    term = Dhall.p_parse(input)
    rendered = render(term, ascii=ascii)
    assert rendered == input
