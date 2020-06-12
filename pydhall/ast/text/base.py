from io import StringIO

from ..base import Value, Node, Term, Builtin, BuiltinValue, EvalEnv, TypeContext
from ..universe import TypeValue

from pydhall.ast.type_error import TYPE_ERROR_MESSAGE


TextTypeValue = BuiltinValue("Text")


class Text(Builtin):
    _type = TypeValue
    _eval = TextTypeValue


class Chunk(Node):
    attrs = ["prefix", "expr"]

    def quote(self, ctx=None, normalize=False):
        assert ctx is not None
        return Chunk(self.prefix, self.expr.quote(ctx, normalize))

    def subst(self, name: str, replacement: Term, level: int = 0):
        return Chunk(self.prefix, self.expr.subst(name, replacement, level))

    def rebind(self, local, level=0):
        return Chunk(self.prefix, self.expr.rebind(local, level))


class PlainTextLitValue(str, Value):

    def quote(self, ctx=None, normalize=False):
        return PlainTextLit(self)

    def alpha_equivalent(self, other, level=0):
        return self.__class__ == other.__class__ and self == other

    def copy(self):
        # TODO : return self ?
        return self


class TextLitValue(Value):
    def __init__(self, chunks, suffix):
        self.chunks = chunks
        self.suffix = suffix

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return TextLit([c.quote(ctx, normalize) for c in self.chunks], self.suffix)

    def alpha_equivalent(self, other, level=0):
        if not isinstance(other, TextLitValue):
            return False
        if self.suffix != other.suffix:
            return False
        if len(self.chunks) != len(other.chunks):
            return False
        for i, c in enumerate(self.chunks):
            oc = other.chunks[i]
            if c.prefix != oc.prefix:
                return False
            if not c.expr.alpha_equivalent(oc.expr, level):
                return False
        return True

    def copy(self):
        return self


class TextLit(Term):
    attrs = ["chunks", "suffix"]

    def type(self, ctx=None):
        ctx = ctx if ctx is not None else TypeContext()
        for c in self.chunks:
            c.expr.assertType(TextTypeValue, ctx, TYPE_ERROR_MESSAGE.CANT_INTERPOLATE)
        return TextTypeValue

    def cbor_values(self):
        out = [18]
        for c in self.chunks:
            out.extend([c.prefix, c.expr.cbor_values()])
        out.append(self.suffix)
        return out

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        str_ = StringIO()
        new_chunks = []
        for chk in self.chunks:
            str_.write(chk.prefix)
            norm_expr = chk.expr.eval(env)
            if isinstance(norm_expr, PlainTextLitValue):
                str_.write(norm_expr)
            elif isinstance(norm_expr, TextLitValue):
                str_.write(norm_expr.chunks[0].prefix)
                new_chunks.append(Chunk(str_.getvalue(), norm_expr.chunks[0].expr))
                new_chunks.extend(norm_expr.chunks[1:])
                str_.seek(0)
                str_.truncate()
                str_.write(norm_expr.suffix)
            else:
                new_chunks.append(Chunk(str_.getvalue(), norm_expr))
                str_.seek(0)
                str_.truncate()

        str_.write(self.suffix)

        new_suffix = str_.getvalue()

        # Special case: "${<expr>}" → <expr>
        if len(new_chunks) == 1 and new_chunks[0].prefix == "" and new_suffix == "":
            return new_chunks[0].expr

        # Special case: no chunks -> PlainTextLit
        if len(new_chunks) == 0:
            return PlainTextLitValue(new_suffix)

        return TextLitValue(new_chunks, new_suffix)

    def subst(self, name: str, replacement: Term, level: int = 0):
        if not self.chunks:
            return self
        return TextLit(
            [c.subst(name, replacement, level) for c in self.chunks],
            self.suffix)

    def rebind(self, local, level=0):
        if not self.chunks:
            return self
        return TextLit(
            [c.rebind(local, level) for c in self.chunks],
            self.suffix)


def PlainTextLit(txt):
    return TextLit([], txt)
