from ..base import Builtin, Value
from ..universe import TypeValue
from .base import NaturalTypeValue


class _NaturalBuildValue(Value):
    def quote(self, ctx=None, normalize=None):
        return NaturalBuild()


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
			# return NewFnType("_",
			# 	NewPi("natural", Type, func(natural Value) Value {
			# 		return NewFnType("succ",
			# 			NewFnType("_", natural, natural),
			# 			NewFnType("zero", natural, natural))
			# 	}),
			# 	Natural), nil


class NaturalFold(Builtin):
    _literal_name = "Natural/fold"


class NaturalIsZero(Builtin):
    _literal_name = "Natural/isZero"


class NaturalEven(Builtin):
    _literal_name = "Natural/even"


class NaturalOdd(Builtin):
    _literal_name = "Natural/odd"


class NaturalToInteger(Builtin):
    _literal_name = "Natural/toInteger"


class NaturalShow(Builtin):
    _literal_name = "Natural/show"


class NaturalSubtract(Builtin):
    _literal_name = "Natural/substract"
