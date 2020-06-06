from ..base import Term, Value, Var

class _QuoteVar(Value):

    def __init__(self, name, index):
        self.name = name
        self.index = index

    def quote(self, ctx=None, normalize=False):
        assert ctx is not None
        return Var(self.name, ctx[self.name] - self.index - 1)

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        return other.__class__ is _QuoteVar and self.index == other.index and self.name == other.name
