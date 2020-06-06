import math
import struct
from cbor.cbor import CBOR_FLOAT16, CBOR_FLOAT32, CBOR_FLOAT64

from ..base import _AtomicLit, BuiltinValue, Builtin, Value, Callable
from ..text.base import PlainTextLitValue, TextTypeValue

from ..universe import TypeValue


## Type
DoubleTypeValue = BuiltinValue("Double")


def _float_to_cbor(f):
    try:
        if struct.unpack("e", struct.pack("e", f))[0] == f:
            return struct.pack("!Be", CBOR_FLOAT16, f)
    except OverflowError:
        pass
    try:
        if struct.unpack("f", struct.pack("f", f))[0] == f:
            return struct.pack("!Bf", CBOR_FLOAT32, f)
    except OverflowError:
        pass
    try:
        if struct.unpack("d", struct.pack("d", f))[0] == f:
            return struct.pack("!Bd", CBOR_FLOAT64, f)
    except OverflowError:
        pass
    assert False


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

    def cbor(self):
        return _float_to_cbor(self.value)

    def cbor_values(self):
        return _float_to_cbor(self.value)



