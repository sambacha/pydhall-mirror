import math
import struct
from cbor2 import dumps
from pydhall.utils import cbor_dumps

from ..base import _AtomicLit, BuiltinValue, Builtin, Value, Callable
from ..text.base import PlainTextLitValue, TextTypeValue

from ..universe import TypeValue


## Type
DoubleTypeValue = BuiltinValue("Double")


class Double(Builtin):
    _type = TypeValue
    _eval = DoubleTypeValue


## Literal
class DoubleLitValue(float, Value):

    def __new__(cls, n):
        try:
            return float.__new__(cls, n)
        except OverflowError:
            if n > 0:
                return float.__new__(cls, math.inf)
            return float.__new__(cls, - math.inf)

    def __add__(self, other):
        raise TypeError()

    def as_python(self):
        return float(self)

    def as_dhall(self):
        return str(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({float.__repr__(self)})"

    def quote(self, ctx=None, normalize=False):
        return DoubleLit(float(self))

    def __str__(self):
        if self == math.inf:
            return "Infinity"
        if self  == -math.inf:
            return "-Infinity"
        if math.isnan(self):
            return "NaN"
        return str(float(self))

    def alpha_equivalent(self, other, level: int = 0):
        if not isinstance(other, DoubleLitValue):
            return False
        if math.isnan(self) and math.isnan(other):
            return True
        return self == other

    def copy(self):
        return self


class DoubleLit(_AtomicLit):
    _type = DoubleTypeValue
    _cbor_idx = -3
    MAX = 1.7976931348623157e308
    MIN = -1.7976931348623157e308

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

    def cbor(self):
        return cbor_dumps(self.value)

    def cbor_values(self):
        return self.value




