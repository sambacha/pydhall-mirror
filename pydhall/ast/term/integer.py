from .base import _AtomicLit, BuiltinValue, Builtin, Value, Callable
from .text import PlainTextLitValue

from .universe import TypeValue
from ..value import Text as TextValue


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
class IntegerClamp(Builtin):
    _literal_name = "Integer/clamp"


class IntegerNegate(Builtin):
    _literal_name = "Integer/negate"


class IntegerToDouble(Builtin):
    _literal_name = "Integer/toDouble"


class IntegerShow(Builtin):
    _literal_name = "Integer/show"


class TextShow(Builtin):
    _literal_name = "Text/show"


