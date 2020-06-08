from .base import IntegerLitValue, IntegerTypeValue
from ..base import Callable, Builtin, Value
from ..natural.base import NaturalTypeValue, NaturalLitValue
from ..double.base import DoubleLitValue
from ..text.base import PlainTextLitValue


class IntegerClamp(Builtin):
    _literal_name = "Integer/clamp"
    _type = "Integer -> Natural"

    def __call__(self, i: Value) -> Value:
        if isinstance(i, IntegerLitValue):
            if i < 0:
                return NaturalLitValue(0)
            return NaturalLitValue(i)


class IntegerNegate(Builtin):
    _literal_name = "Integer/negate"
    _type = "Integer -> Integer"

    def __call__(self, x: Value) -> Value:
        if isinstance(x, IntegerLitValue):
            return IntegerLitValue(-x)


class IntegerToDouble(Builtin):
    _literal_name = "Integer/toDouble"
    _type = "Integer -> Double"

    def __call__(self, x: Value) -> Value:
        if isinstance(x, IntegerLitValue):
            return DoubleLitValue(float(x))


class IntegerShow(Builtin):
    _literal_name = "Integer/show"
    _type = "Integer -> Text"

    def __call__(self, x):
        if isinstance(x, IntegerLitValue):
            prefix = x > 0 and "+" or ""
            return PlainTextLitValue(prefix + str(x))
        return None
