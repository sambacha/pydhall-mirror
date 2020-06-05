from ..base import Op, OpValue, TypeContext, EvalEnv
from .base import NaturalTypeValue, NaturalLitValue

class _PlusOp(OpValue):
    pass


class PlusOp(Op):
    precedence = 30
    operators = ("+",)
    _op_idx = 4
    _type = NaturalTypeValue

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, NaturalLitValue):
            if isinstance(r, NaturalLitValue):
                return NaturalLitValue(l + r)
            if l == 0:
                return r
        if isinstance(r, NaturalLitValue):
            if r == 0:
                return l
        return _PlusOp(l,r)


class _TimesOp(OpValue):
    pass


class TimesOp(Op):
    precedence = 100
    operators = ("*",)
    _op_idx = 5
    _type = NaturalTypeValue

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, NaturalLitValue) and isinstance(r, NaturalLitValue):
            return NaturalLitValue(l * r)
        if l == 0 or r == 0:
            return NaturalLitValue(0)
        if l == 1:
            return r
        if r == 1:
            return l
        return _TimesOp(l,r)
