from ..base import Builtin, Value, Callable, Term, QuoteContext
from ..universe import TypeValue
from .base import ListOf, EmptyListValue, NonEmptyListValue
from .ops import _ListAppendOpValue
from ..optional import OptionalOf
from ..natural.base import NaturalTypeValue, NaturalLitValue
from ..record.base import RecordTypeValue, RecordLitValue
from ..optional import NoneOf, SomeValue
from ..function.lambda_ import LambdaValue
from ..function.pi import PiValue, FnType
from ..function.app import AppValue


class ListBuild(Builtin):
    _literal_name = "List/build"
    _type = "∀(a : Type) → (∀(list : Type) → ∀(cons : a → list → list) → ∀(nil : list) → list) → List a"

    def __call__(self, typ, x):
        def fn(a):
            def inner(as_):
                if isinstance(as_, EmptyListValue):
                    return NonEmptyListValue([a])
                if isinstance(as_, NonEmptyListValue):
                    return NonEmptyListValue([a] + list(as_.content))
                return _ListAppendOpValue(NonEmptyListValue([a]), as_)
            return LambdaValue("as", ListOf(typ), inner)
        cons = LambdaValue(
            "a",
            typ,
            fn)
        return AppValue.build(x, ListOf(typ), cons, EmptyListValue(ListOf(typ)))


class ListFold(Builtin):
    _literal_name = "List/fold"
    _type = "∀(a : Type) → List a → ∀(list : Type) → ∀(cons : a → list → list) → ∀(nil : list) → list"


    def __call__(self, typ1, list_, typ2, cons, empty):
        if isinstance(list_, EmptyListValue):
            return empty
        if isinstance(list_, NonEmptyListValue):
            result = empty
            for i in reversed(list_.content):
                result = AppValue.build(cons, i, result)
            return result


class ListLength(Builtin):
    _literal_name = "List/length"
    _type = "∀(a : Type) → List a → Natural"

    def __call__(self, type, x):
        if isinstance(x, EmptyListValue):
            return NaturalLitValue(0)
        if isinstance(x, NonEmptyListValue):
            return NaturalLitValue(len(x.content))


class ListHead(Builtin):
    _literal_name = "List/head"
    _type = "∀(a : Type) → List a → Optional a"

    def __call__(self, type , x):
        if isinstance(x, EmptyListValue):
            return NoneOf(type)
        if isinstance(x, NonEmptyListValue):
            return SomeValue(x.content[0])


class ListLast(Builtin):
    _literal_name = "List/last"
    _type = "∀(a : Type) → List a → Optional a"

    def __call__(self, type , x):
        if isinstance(x, EmptyListValue):
            return NoneOf(type)
        if isinstance(x, NonEmptyListValue):
            return SomeValue(x.content[-1])


class ListIndexed(Builtin):
    _literal_name = "List/indexed"
    _type = "∀(a : Type) → List a → List { index : Natural, value : a }"

    def __call__(self, typ, x):
        if isinstance(x, EmptyListValue):
            return EmptyListValue(
                ListOf(
                    RecordTypeValue(
                        {"index": NaturalTypeValue,
                         "value": typ}
                     )
                 )
             )
        if isinstance(x, NonEmptyListValue):
            result = [RecordLitValue({"index": NaturalLitValue(i), "value": val})
                      for i, val in enumerate(x.content)]
            return NonEmptyListValue(result)
        return None
        


class ListReverse(Builtin):
    _literal_name = "List/reverse"
    _type = "∀(a : Type) → List a → List a"

    def __call__(self, type, x):
        if isinstance(x, EmptyListValue):
            return x
        if isinstance(x, NonEmptyListValue):
            return NonEmptyListValue(list(reversed(x.content)))
        return None
