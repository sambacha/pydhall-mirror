from ..base import Op, OpValue, EvalEnv, QuoteContext
from .base import DhallImportError
from pydhall.core.type_error import DhallTypeError
from pydhall.parser.exceptions import DhallParseError

class ImportAltOpValue(OpValue):
    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return ImportAltOp(
            self.l.quote(ctx, normalize),
            self.r.quote(ctx, normalize))

class ImportAltOp(Op):
    precedence = 10
    operators = ("?",)
    _op_idx = 11

    def type(self, ctx=None):
        return self.l.type(ctx)

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        l = self.l.eval(env)
        r = self.r.eval(env)
        return ImportAltOpValue(l, r)

    def resolve(self, *ancestors):
        # print(repr(self))
        try:
            return self.l.resolve(*ancestors)
        # TODO: finer execption handling
        except (DhallImportError, DhallTypeError, DhallParseError):
            # let raise.
            return self.r.resolve(*ancestors)
