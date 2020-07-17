from ..base import Op, TypeContext, Value, OpValue, EvalEnv

from .base import ListOf, EmptyListValue, NonEmptyListValue, EvalEnv, QuoteContext, TypeContext

from pydhall.core.type_error import DhallTypeError, TYPE_ERROR_MESSAGE


class _ListAppendOpValue(OpValue):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return ListAppendOp(self.l.quote(ctx, normalize), self.r.quote(ctx, normalize))


class ListAppendOp(Op):
    precedence = 50
    operators = ("#",)
    _op_idx = 7


    def type(self, ctx=None) -> Value:
        ctx = ctx if ctx is not None else TypeContext()

        lt = self.l.type(ctx)
        rt = self.r.type(ctx)
        if not isinstance(lt, ListOf):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.CANT_LIST_APPEND)
        if not isinstance(rt, ListOf):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.CANT_LIST_APPEND)
        if not lt.type_ @ rt.type_:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.LIST_APPEND_MISMATCH)
        return lt


    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        # import ipdb; ipdb.set_trace()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, EmptyListValue):
            return r
        if isinstance(r, EmptyListValue):
            return l
        if isinstance(l, NonEmptyListValue) and isinstance(r, NonEmptyListValue):
            return NonEmptyListValue(list(l.content) + list(r.content))
        return _ListAppendOpValue(l, r)
