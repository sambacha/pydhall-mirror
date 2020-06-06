from ..base import Value, Node, Term, Builtin, BuiltinValue
from ..universe import TypeValue


TextTypeValue = BuiltinValue("Text")


class Text(Builtin):
    _type = TypeValue
    _eval = TextTypeValue


class Chunk(Node):
    attrs = ["prefix", "expr"]


class PlainTextLitValue(str, Value):

    def quote(self, ctx=None, normalize=False):
        return PlainTextLit(self)


class TextLit(Term):
    attrs = ["chunks", "suffix"]
    _type = TextTypeValue

    def cbor_values(self):
        out = [18]
        for c in self.chunks:
            out.append(c.prefix, c.expr.cbor_values())
        out.append(self.suffix)
        print(out)
        return out

    def eval(self, env=None):
        #TODO: implement this correctly
        return PlainTextLitValue(self.suffix)

    def subst(self, name: str, replacement: Term, level: int = 0):
        if not self.chunks:
            return self
        chunks = []
        for c in self.chunks:
            chunks.append(Chunk(c.Prefix, c.Expr.subts(name, str, level)))
        return TextLit(chunks, self.suffix)
        # result := TextLit{Suffix: t.Suffix}
        # if t.Chunks == nil {
        #     return result
        # }
        # result.Chunks = Chunks{}
        # for _, chunk := range t.Chunks {
        #     result.Chunks = append(result.Chunks,
        #         Chunk{
        #             Prefix: chunk.Prefix,
        #             Expr:   rebindAtLevel(i, local, chunk.Expr),
        #         })
        # }
        # return result

def PlainTextLit(txt):
    return TextLit([], txt)



