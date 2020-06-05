from .base import IntegerLitValue, IntegerTypeValue
from ..base import Callable, Builtin, Value
from ..natural.base import NaturalTypeValue, NaturalLitValue
from ...value import Text as TextValue
from ..text import TextTypeValue

class _IntegerClampValue(Callable):
    def __call__(self, i: Value) -> Value:
        if i < 0:
            return NaturalLitValue(-i)
        return NaturalLitValue(i)


IntegerClampValue = _IntegerClampValue()


class IntegerClamp(Builtin):
    _literal_name = "Integer/clamp"
    _eval = IntegerClampValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType
        return FnType("_", IntegerTypeValue, NaturalTypeValue)


class _IntegerNegateValue(Callable):
    def __call__(self, x: IntegerLitValue) -> IntegerLitValue:
        return IntegerLitValue(-x)


IntegerNegateValue = _IntegerNegateValue()


class IntegerNegate(Builtin):
    _literal_name = "Integer/negate"
    _eval = IntegerNegateValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType 
        return FnType("_", IntegerTypeValue, IntegerTypeValue)


class _IntegerToDoubleValue(Callable):
    def __call__(self, x: Value) -> Value:
        return DoubleLitValue(float(x))


IntegerToDoubleValue = _IntegerToDoubleValue()


class IntegerToDouble(Builtin):
    _literal_name = "Integer/toDouble"
    _eval = IntegerToDoubleValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType 
        return FnType("_", IntegerTypeValue, DoubleTypeValue)


class IntegerShow(Builtin):
    _literal_name = "Integer/show"
    
    def type(self, ctx=None):
        from pydhall.ast.value import FnType 
        return FnType("_", IntegerTypeValue, TextTypeValue)
