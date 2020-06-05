from ..base import Builtin, Value, Callable
from ..universe import TypeValue
from .base import NaturalTypeValue


class _NaturalBuildValue(Callable):
    def quote(self, ctx=None, normalize=None):
        return NaturalBuild()

    # def __call__(self, x: Value) -> Value:
    #     pass


NaturalBuildValue = _NaturalBuildValue()


class NaturalBuild(Builtin):
    _literal_name = "Natural/build"
    _eval = NaturalBuildValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Pi
        return FnType("_",
            Pi("natural", TypeValue, lambda natural:
                FnType("succ",
                    FnType("_", natural, natural),
                    FnType("zero", natural, natural))),
            NaturalTypeValue)


class _NaturalFoldValue(Callable):
    pass


NaturalFoldValue = _NaturalFoldValue()


class NaturalFold(Builtin):
    _literal_name = "Natural/fold"
    _eval = NaturalFoldValue

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Pi
        return FnType("_",
            NaturalTypeValue,
            Pi("natural", TypeValue, lambda natural:
                FnType("succ",
                    FnType("_", natural, natural),
                    FnType("zero", natural, natural))
            )
        )


class NaturalIsZero(Builtin):
    _literal_name = "Natural/isZero"

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Bool
        return FnType("_", NaturalTypeValue, Bool)


class NaturalEven(Builtin):
    _literal_name = "Natural/even"

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Bool
        return FnType("_", NaturalTypeValue, Bool)


class NaturalOdd(Builtin):
    _literal_name = "Natural/odd"

    def type(self, ctx=None):
        from pydhall.ast.value import FnType, Bool
        return FnType("_", NaturalTypeValue, Bool)


class NaturalToInteger(Builtin):
    _literal_name = "Natural/toInteger"

    def type(self, ctx=None):
        from pydhall.ast.value import FnType
        from ..integer import IntegerTypeValue
        return FnType("_", NaturalTypeValue, IntegerTypeValue)


class NaturalShow(Builtin):
    _literal_name = "Natural/show"

    def type(self, ctx=None):
        from pydhall.ast.value import FnType
        return FnType("_", NaturalTypeValue, TextTypeValue)


class NaturalSubtract(Builtin):
    _literal_name = "Natural/subtract"

    def type(self, ctx=None):
        from pydhall.ast.value import FnType
        return FnType("_", NaturalTypeValue, FnType("_", NaturalTypeValue, NaturalTypeValue))
