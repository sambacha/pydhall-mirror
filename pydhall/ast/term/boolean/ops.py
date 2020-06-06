from ..base import Op, Value, OpValue, EvalEnv, QuoteContext
from .base import BoolTypeValue, BoolLitValue, True_, False_


class OrOpValue(OpValue):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return OrOp(self.l.quote(ctx, normalize), self.r.quote(ctx, normalize))


class OrOp(Op):
    precedence = 20
    operators = ("||",)
    _op_idx = 0
    _type = BoolTypeValue

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, BoolLitValue):
            if l:
                return True_
            return r
        if isinstance(r, BoolLitValue):
            if r:
                return True_
            return l
        if l @ r:
            return l
        return OrOpValue(l, r)


class NeOpValue(OpValue):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return NeOp(self.l.quote(ctx, normalize), self.r.quote(ctx, normalize))


class AndOpValue(OpValue):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return AndOp(self.l.quote(ctx, normalize), self.r.quote(ctx, normalize))


class AndOp(Op):
    precedence = 60
    operators = ("&&",)
    _op_idx = 1
    _type = BoolTypeValue

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, BoolLitValue):
            if l:
                return r
            return False_
        if isinstance(r, BoolLitValue):
            if r:
                return l
            return False_
        if l @ r:
            return l
        return AndOpValue(l,r)

    def format_dhall(self):
        return (self.l.format_dhall(), "&&", self.r.format_dhall())


class EqOpValue(OpValue):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return EqOp(self.l.quote(ctx, normalize), self.r.quote(ctx, normalize))

class EqOp(Op):
    precedence = 110
    operators = ("==",)
    _op_idx = 2
    _type = BoolTypeValue

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, BoolLitValue) and l:
            return r
        if isinstance(r, BoolLitValue) and r:
            return l
        if l @ r:
            return True_
        return EqOpValue(l,r)


class NeOp(Op):
    precedence = 120
    operators = ("!=",)
    _op_idx = 3
    _type = BoolTypeValue

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, BoolLitValue) and not l:
            return r
        if isinstance(r, BoolLitValue) and not r:
            return l
        if l @ r:
            return False_
        return NeOpValue(l,r)


