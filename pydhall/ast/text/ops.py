from ..base import Op, OpValue, QuoteContext, TypeContext, EvalEnv
from .base import TextTypeValue, TextLit, Chunk

from pydhall.ast.type_error import TYPE_ERROR_MESSAGE


class TextAppendOpValue(OpValue):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return TextAppendOp(self.l.quote(ctx, normalize), self.r.quote(ctx, normalize))


class TextAppendOp(Op):
    precedence = 40
    operators = ("++",)
    _op_idx = 6

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        self.l.assertType(TextTypeValue, ctx, TYPE_ERROR_MESSAGE.CANT_TEXT_APPEND)
        self.r.assertType(TextTypeValue, ctx, TYPE_ERROR_MESSAGE.CANT_TEXT_APPEND)
        return TextTypeValue

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        return TextLit([Chunk("", self.l), Chunk("", self.r)], "").eval(env)
