from ..base import Builtin, Value, Callable
from ..universe import TypeValue
from .base import NaturalTypeValue, NaturalLitValue
from .ops import _PlusOp
from ..integer.base import IntegerLitValue
from ..boolean.base import True_, False_
from ..text.base import PlainTextLitValue
from ..function.app import AppValue
from ..function.lambda_ import LambdaValue


class NaturalBuild(Builtin):
    _literal_name = "Natural/build"
    _type = "(∀(natural : Type) → ∀(succ : natural → natural) → ∀(zero : natural) → natural) → Natural"

    def __call__(self, x):
        def fn(n):
            if isinstance(n, NaturalLitValue):
                return NaturalLitValue(int(n)+1)
            return _PlusOp(n, NaturalLitValue(1))
        succ = LambdaValue(
            "x",
            NaturalTypeValue,
            fn)
        return AppValue.build(x, NaturalTypeValue, succ, NaturalLitValue(0))


class NaturalFold(Builtin):
    _literal_name = "Natural/fold"
    _type = "Natural → ∀(natural : Type) → ∀(succ : natural → natural) → ∀(zero : natural) → natural"

    def __call__(self, n, typ, succ, zero):
        if isinstance(n, NaturalLitValue):
            result = zero
            for i in range(n):
                result = AppValue.build(succ, result)
            return result


class NaturalIsZero(Builtin):
    _literal_name = "Natural/isZero"
    _type = "Natural -> Bool"

    def __call__(self, x):
        if isinstance(x, NaturalLitValue):
            return True_ if x == 0 else False_


class NaturalEven(Builtin):
    _literal_name = "Natural/even"
    _type = "Natural -> Bool"

    def __call__(self, x):
        if isinstance(x, NaturalLitValue):
            return True_ if x % 2 == 0 else False_


class NaturalOdd(Builtin):
    _literal_name = "Natural/odd"
    _type = "Natural -> Bool"

    def __call__(self, x):
        if isinstance(x, NaturalLitValue):
            return True_ if x % 2 == 1 else False_


class NaturalToInteger(Builtin):
    _literal_name = "Natural/toInteger"
    _type = "Natural → Integer"

    def __call__(self, x):
        if isinstance(x, NaturalLitValue):
            return IntegerLitValue(int(x))


class NaturalShow(Builtin):
    _literal_name = "Natural/show"
    _type = "Natural → Text"

    def __call__(self, x):
        if isinstance(x, NaturalLitValue):
            return PlainTextLitValue(int(x))


class NaturalSubtract(Builtin):
    _literal_name = "Natural/subtract"
    _type = "Natural → Natural → Natural"

    def __call__(self, x, y):
        if isinstance(x, NaturalLitValue):
            if isinstance(y, NaturalLitValue):
                if y >= x:
                    return NaturalLitValue(int(y) - int(x))
                return NaturalLitValue(0)
            if x == 0:
                return y
        if isinstance(y, NaturalLitValue):
            if y == 0:
                return y
        if x @ y:
            return NaturalLitValue(0)
        return None
