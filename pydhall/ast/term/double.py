import math

from .base import _AtomicLit, BuiltinValue, Builtin, Value, Callable
from .text import PlainTextLitValue

from .universe import TypeValue
from ..value import Text as TextValue


## Type
DoubleTypeValue = BuiltinValue("Double")


class Double(Builtin):
    _type = TypeValue
    _eval = DoubleTypeValue


## Literal
class DoubleLitValue(float, Value):

    def __add__(self, other):
        raise TypeError()

    def as_python(self):
        return float(self)

    def as_dhall(self):
        return str(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({float.__repr__(self)})"

    def quote(self, ctx=None, normalize=False):
        return DoubleLit(self)

    def __str__(self):
        if self == math.inf:
            return "Infinity"
        if self  == -math.inf:
            return "-Infinity"
        if math.isnan(self):
            return "NaN"
        return str(float(self))


class DoubleLit(_AtomicLit):
    _type = DoubleTypeValue
    _cbor_idx = -3

    def eval(self, env=None):
        return DoubleLitValue(self.value)

    def __str__(self):
        if self.value == math.inf:
            return "Infinity"
        if self.value == -math.inf:
            return "-Infinity"
        if math.isnan(self.value):
            return "NaN"
        return str(self.value)


## Functions
class _DoubleShowValue(Callable):
    def __call__(self, x: Value):
        # print("call...............")
        # print(x)
        if not isinstance(x, DoubleLitValue):
            return None
        return PlainTextLitValue(x)

    def quote(self, ctx=None, normalize=None):
        return DoubleShow()


DoubleShowValue = _DoubleShowValue()


class DoubleShow(Builtin):
    _literal_name = "Double/show"
    _eval = DoubleShowValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType
        return FnType("_", DoubleTypeValue, TextValue)
