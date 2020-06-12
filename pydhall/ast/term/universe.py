import cbor

from .base import Value, Builtin, Term

from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE

class UniverseValue(Value):
    def __init__(self, name, type, rank):
        self.name = name
        self._type = type
        self._rank = rank

    def __repr__(self):
        return f"UniverseValue({self.name})"

    def __str__(self):
        return self.name

    def alpha_equivalent(self, other, level=0):
        return other.name == self.name

    def quote(self, ctx=None, normalize=False):
        from . import Universe
        return Universe.from_name(self.name)

    def __lt__(self, other):
        return self._rank < other._rank

    def __gt__(self, other):
        return self._rank > other._rank

    def __eq__(self, other):
        return self._rank == other._rank

    def __le__(self, other):
        return self._rank <= other._rank

    def __ge__(self, other):
        return self._rank >= other._rank


SortValue = UniverseValue("Sort", None, 30)
KindValue = UniverseValue("Kind", SortValue, 20)
TypeValue = UniverseValue("Type", KindValue, 10)

class Universe(Builtin):

    def __init__(self, *args, **kwargs):
        Term.__init__(self, *args, **kwargs)

    def cbor(self):
        return cbor.dumps(self.__class__.__name__)

    @classmethod
    def from_name(cls, name):
        return Builtin(name)

    def cbor_values(self):
        return self.__class__.__name__

    def rebind(self, local, level=0):
        return self


class Sort(Universe):
    _eval = SortValue
    _rank = 30

    def type(self, ctx=None):
        raise DhallTypeError(TYPE_ERROR_MESSAGE.UNTYPED)


class Kind(Universe):
    _eval = KindValue
    _type = SortValue
    _rank = 20


class Type(Universe):
    _type = KindValue
    _eval = TypeValue
    _rank = 10
