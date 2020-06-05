from ..base import Builtin, Value, Callable, Term, QuoteContext
from ..universe import TypeValue
from .base import ListOf, EmptyListValue, NonEmptyListValue
from ..optional import OptionalOf
from ..natural.base import NaturalTypeValue
from ..record.base import RecordTypeValue


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


class _ListLengthValue(Callable):
    pass


ListLengthValue = _ListLengthValue()


class ListLength(Builtin):
    _literal_name = "List/length"
    _eval = ListLengthValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Pi
        return Pi(
            "a",
            TypeValue,
            lambda a: FnType("_", ListOf(a), NaturalTypeValue))


_ListLengthValue._quote = ListLength()


class _ListHeadValue(Callable):
    pass


ListHeadValue = _ListHeadValue()


class ListHead(Builtin):
    _literal_name = "List/head"
    _eval = ListHeadValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Pi
        return Pi(
            "a",
            TypeValue,
            lambda a: FnType(
                "_",
                ListOf(a),
                OptionalOf(a)
            )
        )


_ListHeadValue._quote = ListHead()


class _ListLastValue(Callable):
    pass


ListLastValue = _ListLastValue()


class ListLast(Builtin):
    _literal_name = "List/last"
    _eval = ListLastValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Pi
        return Pi(
            "a",
            TypeValue,
            lambda a: FnType(
                "_",
                ListOf(a),
                OptionalOf(a)
            )
        )


_ListLastValue._quote = ListLast()


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


class BuiltinMeta(type):
    @classmethod
    def _get_arrity(cls, tp):
        from .. import Pi, App
        if isinstance(tp, Pi):
            return 1 + cls._get_arrity(tp.body)
        return 0
        
    def __new__(cls, name, bases, attrs):
        print(cls, name, bases, attrs)
        if name == "NewBuiltin":
            return type.__new__(cls, name, bases, attrs)
        bases = bases + (Builtin,)

        if not ("_type" in attrs and isinstance(attrs["_type"], str)):
            return type.__new__(cls, name, bases, attrs)

        from pydhall.parser.base import Dhall
        _type_ast = Dhall.p_parse(attrs.pop("_type"))
        _type = _type_ast.eval()
        # import ipdb; ipdb.set_trace()

        def _new_type_fn(self, ctx=None):
            return _type

        class val(Callable):
            def __init__(self, arrity, call, fn_class, args=None):
                self.arrity = arrity
                self._call = call
                self.fn_class = fn_class
                self.args = args if args is not None else []

            def __call__(self, x: Value) -> Value:
                # import ipdb; ipdb.set_trace()
                self.args.append(x)
                if len(self.args) < self.arrity:
                    return self.__class__(self.arrity, self._call, self.fn_class, self.args)
                return self._call(self, *self.args)

            def quote(self, ctx: QuoteContext = None, normalize: bool = False) -> Term:
                ctx = ctx if ctx is not None else QuoteContext()
                from .. import App
                return App.build(self.fn_class, *[a.quote(ctx, normalize) for a in self.args])

        call = attrs.pop("__call__")

        new_cls = type.__new__(cls, name, bases, attrs)

        new_cls.type = _new_type_fn
        new_cls._eval = val(cls._get_arrity(_type_ast), call, new_cls)

        return new_cls


class NewBuiltin(metaclass=BuiltinMeta):
    pass


class NewReverse(NewBuiltin):
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
