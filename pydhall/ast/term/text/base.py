from io import StringIO

from ..base import Value, Node, Term, Builtin, BuiltinValue, EvalEnv
from ..universe import TypeValue


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


class TextLitValue(Value):
    def __init__(self, chunks, suffix):
        self.chunks = chunks
        self.suffix = suffix

    def quote(self, ctx=None, normalize=False):
        ctx = ctx if ctx is not None else QuoteContext()
        return TextLit([c.quote(ctx, normalize) for c in self.chunks], self.suffix)


class TextLit(Term):
    attrs = ["chunks", "suffix"]
    _type = TextTypeValue

    def cbor_values(self):
        out = [18]
        for c in self.chunks:
            out.extend([c.prefix, c.expr.cbor_values()])
        out.append(self.suffix)
        print(out)
        return out

    def eval(self, env=None):
        env = env if env is not None else EvalEnv()
        #TODO: implement this correctly
        # return PlainTextLitValue(self.suffix)
        # var str strings.Builder
        # var newChunks chunks
        str_ = StringIO()
        new_chunks = []

        # for _, chk := range t.Chunks {
        #     str.WriteString(chk.Prefix)
        #     normExpr := evalWith(chk.Expr, e)
        #     if text, ok := normExpr.(PlainTextLit); ok {
        #         str.WriteString(string(text))
        #     } else if text, ok := normExpr.(interpolatedText); ok {
        #         // first chunk gets the rest of str
        #         str.WriteString(text.Chunks[0].Prefix)
        #         newChunks = append(newChunks,
        #             chunk{Prefix: str.String(), Expr: text.Chunks[0].Expr})
        #         newChunks = append(newChunks,
        #             text.Chunks[1:]...)
        #         str.Reset()
        #         str.WriteString(text.Suffix)
        #     } else {
        #         newChunks = append(newChunks, chunk{Prefix: str.String(), Expr: normExpr})
        #         str.Reset()
        #     }
        # }
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

        # str.WriteString(t.Suffix)
        str_.write(self.suffix)

        # newSuffix := str.String()
        new_suffix = str_.getvalue()

        # Special case: "${<expr>}" → <expr>
        # if len(newChunks) == 1 && newChunks[0].Prefix == "" && newSuffix == "" {
        #     return newChunks[0].Expr
        # }
        if len(new_chunks) == 1 and new_chunks[0].prefix == "" and new_suffix == "":
            return new_chunks[0].expr

        # Special case: no chunks -> PlainTextLit
        # if len(newChunks) == 0 {
        #     return PlainTextLit(newSuffix)
        # }
        if len(new_chunks) == 0:
            return PlainTextLitValue(new_suffix)

        # return interpolatedText{Chunks: newChunks, Suffix: newSuffix}
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
