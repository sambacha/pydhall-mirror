from pydhall.ast.type_error import DhallTypeError, TYPE_ERROR_MESSAGE

from ..base import Op, OpValue, TypeContext, EvalEnv

from .base import RecordLitValue, RecordTypeValue

class RightBiasedRecordMergeOpValue(OpValue):
    pass


class RightBiasedRecordMergeOp(Op):
    precedence = 80
    operators = ("⫽", "//")
    _op_idx = 9

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, RecordLitValue) and len(l) == 0:
            return r
        if isinstance(r, RecordLitValue):
            if len(r) == 0:
                return l
            if isinstance(l, RecordLitValue):
                result = RecordLitValue(l)
                result.update(r)
                return result
        if l @ r:
            return l
        return RightBiasedRecordMergeOpValue(l, r)

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        l_type = self.l.type(ctx)
        if not isinstance(l_type, RecordTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.MUST_COMBINE_A_RECORD)
        r_type = self.r.type(ctx)
        if not isinstance(r_type, RecordTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.MUST_COMBINE_A_RECORD)
        l_type.update(r_type)
        return l_type


class CompleteOp(Op):
    precedence = 140
    operators = ("::",)
    _op_idx = 13

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        from .. import Annot
        from ..field import Field
        annot = Annot(
            RightBiasedRecordMergeOp(
                Field(self.l, "default"),
                self.r),
            Field(self.l, "Type"))
        return annot.eval(env)

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        from .. import Annot
        from ..field import Field
        annot = Annot(
            RightBiasedRecordMergeOp(
                Field(self.l, "default"),
                self.r),
            Field(self.l, "Type"))
        return annot.type(ctx)


class RecordMergeOpValue(OpValue):
    pass

class RecordMergeOp(Op):
    precedence = 70
    operators = ("∧", "/\\")
    _op_idx = 8

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        l_type = self.l.type(ctx)
        r_type = self.r.type(ctx)
        record_type = RecordTypeMergeOp(l_type.quote(), r_type.quote())
        record_type.type(ctx)
        return record_type.eval()

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        # lR, lOk := l.(RecordLit)
        # rR, rOk := r.(RecordLit)
        if isinstance(l, RecordLitValue) and len(l) == 0:
            return r
        if isinstance(r, RecordLitValue):
            if len(r) == 0:
                return l
            if isinstance(l, RecordLitValue):
                return l.merge(r)
        return RecordMergeOpValue(l, r)


class RecordTypeMergeOpValue(OpValue):
    pass


class RecordTypeMergeOp(Op):
    precedence = 90
    operators = ("⩓", r"//\\")
    _op_idx = 10

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()

        l_kind = self.l.type(ctx)
        r_kind = self.r.type(ctx)
        l_val = self.l.eval()
        if not isinstance(l_val, RecordTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.COMBINE_TYPES_REQUIRES_RECORD_TYPE)
        r_val = self.r.eval()
        if not isinstance(r_val, RecordTypeValue):
            raise DhallTypeError(TYPE_ERROR_MESSAGE.COMBINE_TYPES_REQUIRES_RECORD_TYPE)

        # ensure that the records are safe to merge
        l_val.merge(r_val)
        if l_kind > r_kind:
            return l_kind
        return r_kind

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        if isinstance(l, RecordTypeValue) and len(l) == 0:
            return r
        if isinstance(r, RecordTypeValue):
            if len(r) == 0:
                return l
            if isinstance(l, RecordTypeValue):
                return l.merge(r)
        return RecordTypeMergeOpValue(l, r)
