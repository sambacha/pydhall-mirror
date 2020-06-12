from ..base import Term, Builtin, Value, EvalEnv, Callable, QuoteContext, DependentValue, TypeContext
from ..universe import TypeValue
from ..function.pi import FnType

from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE


class _ListValue(Callable):
    def __call__(self, x: Value):
        return ListOf(x)

    def quote(self, ctx=None, normalize=False):
        return List()


ListValue = _ListValue()


class ListOf(Value):
    def __init__(self, type_):
        self.type_ = type_

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        from .. import App
        return App.build(List(), self.type_.quote(ctx, normalize))

    def alpha_equivalent(self, other: Value, level: int = 0) -> bool:
        if not isinstance(other, ListOf):
            return False
        return self.type_.alpha_equivalent(other.type_, level)

    def copy(self):
        return ListOf(self.type_.copy())


class NonEmptyListValue(Value):

    def __init__(self, content):
        self.content = content

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return NonEmptyList([e.quote(ctx, normalize) for e in self.content])

    def alpha_equivalent(self, other: Value, level: int = 0):
        if not isinstance(other, self.__class__):
            return False
        if len(self.content) != len(other.content):
            return False
        for i, item in enumerate(self.content):
            if not item.alpha_equivalent(other.content[i], level):
                return False
        return True

    def copy(self):
        return NonEmptyListValue([i.copy() for i in self.content])


class EmptyListValue(Value):
    def __init__(self, type_):
        self.type_ = type_

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return EmptyList(self.type_.quote(ctx, normalize))

    def alpha_equivalent(self, other: Value, level: int = 0):
        if not isinstance(other, self.__class__):
            return False
        return self.type_.alpha_equivalent(other.type_, level)

    def copy(self):
        return EmptyListValue(self.type_.copy())


# Terms
class List(Builtin):
    _eval = ListValue

    def type(self, ctx=None):
        return FnType("_", TypeValue, TypeValue)


class EmptyList(Term):
    attrs = ["type_"]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        self.type_.type(ctx)
        tp = self.type_.eval()
        if not isinstance(tp, ListOf):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_LIST_TYPE)
        return tp

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return EmptyListValue(self.type_.eval(env))

    def cbor_values(self):
        from .. import App
        if isinstance(self.type_, App) and isinstance(self.type_.fn, List):
            return [4, self.type_.arg.cbor_values()]
        return [28, self.type_.cbor_values()]

    def format_dhall(self):
        return ("[]", ":", self.type_.format_dhall())

    def subst(self, name: str, replacement: Term, level: int = 0):
        return EmptyList(self.type_.subst(name, replacement, level))

    def rebind(self, local, level=0):
        return EmptyList(self.type_.rebind(local, level))


class NonEmptyList(Term):
    attrs = ["content"]
    _cbor_idx = 4

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        t0 = self.content[0].type(ctx)
        t0.quote().assertType(TypeValue, ctx, TYPE_ERROR_MESSAGE.INVALID_LIST_TYPE)
        for e in self.content[1:]:
            t1  = e.type(ctx)
            if not t0 @ t1:
                raise DhallTypeError(TYPE_ERROR_MESSAGE.MISMATCH_LIST_ELEMENTS % ( t0.quote(), t1.quote()))

        return ListOf(t0)

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return NonEmptyListValue([e.eval(env) for e in self.content])

    def cbor_values(self):
        return [4, None] + [e.cbor_values() for e in self.content]

    def subst(self, name: str, replacement: Term, level: int = 0):
        return NonEmptyList([i.subst(name, replacement, level) for i in self.content])

    def rebind(self, local, level=0):
        return NonEmptyList([i.rebind(local, level) for i in self.content])

