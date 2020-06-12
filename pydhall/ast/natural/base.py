from ..base import _AtomicLit, Value, BuiltinValue, Builtin
from ..universe import TypeValue


NaturalTypeValue = BuiltinValue("Natural")


class Natural(Builtin):
    _type = TypeValue
    _eval = NaturalTypeValue


class NaturalLitValue(int, Value):

    def __new__(cls, val):
        if val < 0:
            raise ValueError("%s < 0" % val)
        return int.__new__(cls, val)

    def __add__(self, other):
        if not isinstance(other, NaturalLit):
            raise ValueError(other)
        return NaturalLit(int.__add__(self, other))

    def as_python(self):
        return int(self)

    def as_dhall(self):
        return str(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({int.__repr__(self)})"

    def quote(self, ctx=None, normalize=False):
        return NaturalLit(int(self))

    def alpha_equivalent(self, other, level=0):
        return self == other


class NaturalLit(_AtomicLit):
    _type = NaturalTypeValue
    _cbor_idx = 15

    def eval(self, env=None):
        return NaturalLitValue(self.value)
