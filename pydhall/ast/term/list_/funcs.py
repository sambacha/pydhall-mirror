from ..base import Builtin, Value, Callable, Term, QuoteContext
from ..universe import TypeValue
from .base import ListOf, EmptyListValue, NonEmptyListValue
from ..optional import OptionalOf
from ..natural.base import NaturalTypeValue, NaturalLitValue
from ..record.base import RecordTypeValue
from ..optional import NoneOf, SomeValue


class _ListBuildValue(Callable):
    def __call__(self, x: Value):
        raise Exception("*******************************************")


ListBuildValue = _ListBuildValue()


class ListBuild(Builtin):
    _literal_name = "List/build"
    _eval = ListBuildValue
    tp = "∀(a : Type) → (∀(list : Type) → ∀(cons : a → list → list) → ∀(nil : list) → list) → List a"

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Pi
        return Pi(
            "a",
            TypeValue,
            lambda a : FnType(
                "_",
                Pi(
                    "list",
                    TypeValue,
                    lambda lst: FnType(
                        "cons",
                        FnType("_", a, FnType("_", lst, lst)),
                        FnType("nil", lst, lst)
                    )),
                ListOf(a)
            )
        )


_ListBuildValue._quote = ListBuild()


class _ListFoldValue(Callable):
    pass


ListFoldValue = _ListFoldValue()


class ListFold(Builtin):
    _literal_name = "List/fold"
    _eval = ListFoldValue
    tp = "∀(a : Type) → List a → ∀(list : Type) → ∀(cons : a → list → list) → ∀(nil : list) → list"

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Pi
        return Pi(
            "a",
            TypeValue,
            lambda a: FnType(
                "_",
                ListOf(a),
                Pi(
                    "list",
                    TypeValue,
                    lambda lst: FnType(
                        "cons",
                        FnType("_", a, FnType("_", lst, lst)),
                        FnType("nil", lst, lst)
                    )
                )
            )
        )


_ListFoldValue._quote = ListFold()


class ListLength(Builtin):
    _literal_name = "List/length"
    _type = "∀(a : Type) → List a → Natural"

    def __call__(self, type, x):
        if isinstance(x, EmptyListValue):
            return NaturalLitValue(0)
        return NaturalLitValue(len(x.content))


class ListHead(Builtin):
    _literal_name = "List/head"
    _type = "∀(a : Type) → List a → Optional a"

    def __call__(self, type , x):
        if isinstance(x, EmptyListValue):
            return NoneOf(type)
        return SomeValue(x.content[0])


class ListLast(Builtin):
    _literal_name = "List/last"
    _type = "∀(a : Type) → List a → Optional a"

    def __call__(self, type , x):
        if isinstance(x, EmptyListValue):
            return NoneOf(type)
        return SomeValue(x.content[-1])


class _ListIndexedValue(Callable):
    pass


ListIndexedValue = _ListIndexedValue()


class ListIndexed(Builtin):
    _literal_name = "List/indexed"
    _eval = ListIndexedValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Pi
        return Pi(
            "a",
            TypeValue,
            lambda a: FnType(
                "_",
                ListOf(a),
                ListOf(
                    RecordTypeValue({
                        "index": NaturalTypeValue,
                        "value": a})
                )
            )
        )


_ListIndexedValue._quote = ListIndexed()


class _ListReverseValue(Callable):
    def __init__(self, a: Value = None):
        self.a = a

    def __call__(self, x: Value) -> Value:
        # import ipdb; ipdb.set_trace()
        if self.a is None:
            return _ListReverseValue(a=x)
        if isinstance(x, EmptyListValue):
            return x
        if isinstance(x, NonEmptyListValue):
            return NonEmptyListValue(reversed(x.content))
        return None

    def quote(self, ctx: QuoteContext = None, normalize: bool = False) -> Term:
        ctx = ctx if ctx is not None else QuoteContext()
        if self.a is not None:
            from .. import App
            return App(ListReverse(), self.a.quote(ctx, normalize))
        return ListReverse()



ListReverseValue = _ListReverseValue()


class ListReverse(Builtin):
    _literal_name = "List/reverse2"
    _eval = ListReverseValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Pi
        return Pi(
            "a",
            TypeValue,
            lambda a: FnType("_", ListOf(a), ListOf(a)))


class NewReverse(Builtin):
    _literal_name = "List/reverse"
    _type = "∀(a : Type) → List a → List a"

    def __call__(self, type, x):
        if isinstance(x, EmptyListValue):
            return x
        if isinstance(x, NonEmptyListValue):
            return NonEmptyListValue(reversed(x.content))
        return None



assert issubclass(NewReverse, Builtin)
# print(Builtin._by_name)
# print(repr(NewReverse().type()))
