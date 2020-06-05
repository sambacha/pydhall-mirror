from .base import _AtomicLit, BuiltinValue, Builtin, Value, Callable
from .text import PlainTextLitValue

from .universe import TypeValue
from ..value import Text as TextValue
from .natural.base import NaturalTypeValue, NaturalLitValue
from .double import DoubleTypeValue, DoubleLitValue
from .text import TextTypeValue


## Type
IntegerTypeValue = BuiltinValue("Integer")


class Integer(Builtin):
    _type = TypeValue
    _eval = IntegerTypeValue


## Literal
class IntegerLitValue(int, Value):

    def __add__(self, other):
        raise TypeError()

    def as_python(self):
        return int(self)

    def as_dhall(self):
        sign = "+" if self >= 0 else "-"
        return f"{sign}{str(self)}"

    def __repr__(self):
        return f"{self.__class__.__name__}({int.__repr__(self)})"

    def quote(self, ctx=None, normalize=False):
        return IntegerLit(int(self))

    def alpha_equivalent(self, other, level=0):
        return self == other


class IntegerLit(_AtomicLit):
    _type = IntegerTypeValue
    _cbor_idx = 16

    def eval(self, env=None):
        return IntegerLitValue(self.value)


## Functions
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
