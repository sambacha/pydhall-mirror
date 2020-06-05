from ..base import Op, TypeContext, Value

from .base import ListOf

from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE

class ListAppendOp(Op):
    precedence = 50
    operators = ("#",)
    _op_idx = 7


    def type(self, ctx=None) -> Value:
        ctx = ctx if ctx is not None else TypeContext()

        lt = self.l.type()
        rt = self.r.type()
        if not isinstance(lt, ListOf):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.CANT_LIST_APPEND)
        if not isinstance(rt, ListOf):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.CANT_LIST_APPEND)
        if not lt.type_ @ rt.type_:
            raise DhallTypeError(TYPE_ERROR_MESSAGE.LIST_APPEND_MISMATCH)
        return lt
