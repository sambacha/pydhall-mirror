from ..type_error import DhallTypeError, TYPE_ERROR_MESSAGE

from .base import Term, EvalEnv, Value, QuoteContext, TypeContext
from .boolean.base import True_, False_, BoolTypeValue, TypeValue


class IfValue(Value):
    def __init__(self, cond, true, false):
        self.cond = cond
        self.true = true
        self.false = false

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return If(
            self.cond.quote(ctx, normalize),
            self.true.quote(ctx, normalize),
            self.false.quote(ctx, normalize))


class If(Term):
    attrs = ["cond", "true", "false"]
    _rebindable = ["cond", "true", "false"]
    _cbor_idx = 14

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        cond = self.cond.eval(env)
        # print(repr(cond))
        if cond == True_:
            return self.true.eval(env)
        elif cond == False_:
            return self.false.eval(env)
        t = self.true.eval(env)
        f = self.false.eval(env)
        if t == True_ and f == False_:
            return cond
        if t @ f:
            return t
        return IfValue(cond, t, f)

    def cbor_values(self):
        return [14, self.cond.cbor_values(), self.true.cbor_values(), self.false.cbor_values()]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        cond = self.cond.type(ctx)
        if cond != BoolTypeValue:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.INVALID_PREDICATE)
        t = self.true.type(ctx)
        f = self.false.type(ctx)
        if t.quote().type(ctx) != TypeValue or f.quote().type(ctx) != TypeValue:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.IF_BRANCH_MUST_BE_TERM)
        if not t @ f:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.IF_BRANCH_MISMATCH)
        return t

    def subst(self, name, replacement, level=0):
        return If(
            self.cond.subst(name, replacement, level),
            self.true.subst(name, replacement, level),
            self.false.subst(name, replacement, level),
        )

    def format_dhall(self):
        return (("if", self.cond.format_dhall()), ("then", self.true.format_dhall()), ("else", self.false.format_dhall()))
