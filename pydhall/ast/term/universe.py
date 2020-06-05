from .base import Value

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
        return other is self

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
