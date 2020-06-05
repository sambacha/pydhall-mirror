from .base import Value, Node, Term, Builtin
from ..value import Text as TextTypeValue

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


def PlainTextLit(txt):
    return TextLit([], txt)


class TextShow(Builtin):
    _literal_name = "Text/show"
