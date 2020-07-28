from io import StringIO

from pydhall.utils import Visitor, visitor
from pydhall.core import (
    NaturalLit,
    IntegerLit,
    BoolLit,
    DoubleLit,
    Op,
    Assert,
    Lambda,
    Builtin,
    Var,
    Let,
    Binding,
    Pi,
    App,
    NonEmptyList,
)


class Arrow:
    pass


class ForAll:
    pass


class Blank:
    pass


class Chunk:
    def __init__(self, parent=None, indent="", separator="\n", first_indent=None):
        self.content = []
        self.indent = indent
        self.parent = parent
        self.separator = separator
        self.first_indent = first_indent if first_indent is not None else indent

    def new_chunk(self, indent, separator="\n", first_indent=None):
        new = Chunk(parent=self, indent=indent, separator=separator, first_indent=first_indent)
        self.content.append(new)
        return new

    def append(self, txt):
        if self.content and isinstance(self.content[-1], str):
            self.content[-1] = self.content[-1] + txt
        else:
            self.content.append(txt)

    def blank(self):
        self.content.append(Blank())

    def _as_list(self):
        lst = [self.indent]
        for c in self.content:
            if isinstance(c, Chunk):
                lst.append(c._as_list())
            else:
                lst.append(c)
        return lst

    def __str__(self):
        return repr(self._as_list())

    def __repr__(self):
        return str(self)


class ChunkVisitor(Visitor):
    def __init__(self, ascii=False):
        self.chunk = Chunk()
        self.ascii = ascii

    def visit_with_precedence(self, term, base):
        if base.commutative and term.precedence < base.precedence or term.precedence <= base.precedence:
            self.new_chunk("  ", first_indent="( ")
            # self.append("(")
            self.visit(term)
            self.chunk = self.chunk.parent
            self.new_chunk()
            self.append(")")
            self.chunk = self.chunk.parent
        else:
            self.visit(term)

    def new_chunk(self, indent="", separator="\n", first_indent=None):
        self.chunk = self.chunk.new_chunk(indent, separator, first_indent)

    def blank(self):
        self.chunk.blank()

    def visit(self, term):
        orig = self.chunk
        super().visit(term)
        while self.chunk is not orig:
            self.chunk = self.chunk.parent

    def append(self, txt):
        self.chunk.append(txt)

    @visitor(NaturalLit)
    def visit_natural_lit(self, term):
        self.append(str(term.value))

    @visitor(DoubleLit)
    def visit_double_lit(self, term):
        self.append(str(term.value))

    @visitor(BoolLit)
    def visit_bool_lit(self, term):
        self.append(str(term.value))

    @visitor(IntegerLit)
    def visit_integer_lit(self, term):
        if term.value >= 0:
            self.append("+")
        else:
            self.append("-")
        self.append(str(term.value))

    @visitor(Op)
    def visit_op(self, term):
        self.visit_with_precedence(term.l, term)
        self.append(" ")
        if self.ascii and len(term.operators) == 2:
            self.append(term.operators[1])
        else:
            self.append(term.operators[0])
        self.append(" ")
        self.visit_with_precedence(term.r, term)

    @visitor(Assert)
    def visit_assert(self, term):
        "assert : (λ(x : Bool) → x) ≡ (λ(y : Bool) → y)"
        self.new_chunk(" : ", first_indent="  ")
        self.append("assert")
        self.new_chunk()
        self.visit(term.annotation)

    @visitor(Var)
    def visit_var(self, term):
        self.append(term.name)
        if term.index:
            self.append("@")
            self.append(str(term.index))

    @visitor(Let)
    def visit_let(self, term):
        self.new_chunk()
        for b in term.bindings:
            self.new_chunk()
            self.visit(b)
            self.chunk = self.chunk.parent
            self.blank()
        self.new_chunk()
        self.append("in ")
        self.visit(term.body)

    @visitor(Binding)
    def visit_body(self, term):
        self.new_chunk("    ", first_indent="")
        self.append("let ")
        self.append(term.variable)
        if term.annotation:
            self.new_chunk("  ", first_indent=": ")
            self.visit(term.annotation)
            self.chunk = self.chunk.parent
        self.new_chunk("  ", first_indent="= ")
        self.visit(term.value)

    @visitor(Builtin)
    def visit_builtin(self, term):
        if term._literal_name:
            self.append(term._literal_name)
        else:
            self.append(term.__class__.__name__)

    @visitor(Lambda)
    def visit_lambda(self, term):
        self.new_chunk()
        if self.ascii:
            self.append(r"\(")
        else:
            self.append("λ(")
        self.append(term.label)
        self.append(" : ")
        self.visit(term.type_)
        self.append(")")
        if self.ascii:
            self.append(" ->")
        else:
            self.append(" →")
        self.chunk = self.chunk.parent
        if isinstance(term.body, Lambda):
            self.visit(term.body)
            # term = term.body
        else:
            self.new_chunk(first_indent="  ")
            self.visit(term.body)

    @visitor(Pi)
    def visit_pi(self, term):
        self.new_chunk()
        if term.label != "_":
            if self.ascii:
                self.append("forall(")
            else:
                self.append("∀(")
            self.append(term.label)
            self.append(" : ")
            self.visit_with_precedence(term.type_, term)
            self.append(")")
        else:
            self.visit_with_precedence(term.type_, term)
        if self.ascii:
            self.append(" ->")
        else:
            self.append(" →")
        self.chunk = self.chunk.parent
        if isinstance(term.body, Pi):
            self.visit(term.body)
        else:
            self.new_chunk(first_indent="  ")
            self.visit(term.body)

    @visitor(App)
    def visit_app(self, term):
        self.new_chunk("  ", first_indent="")
        self.visit(term.fn)
        if isinstance(term.arg, App):
            self.chunk = self.chunk.parent
        self.new_chunk()
        self.visit_with_precedence(term.arg, term)

    @visitor(NonEmptyList)
    def visit_nonempty_list(self, term):
        self.new_chunk()
        self.chunk = self.chunk.parent
        self.new_chunk(", ", first_indent="[ ")
        for item in term.content:
            self.new_chunk("")
            self.visit(item)
            self.chunk = self.chunk.parent
        self.chunk = self.chunk.parent
        self.new_chunk()
        self.append("]")

    def __call__(self, term):
        self.visit(term)
        return self.chunk

    def visit_generic(self, term):
        raise ValueError(f"Unhandled class: `{repr(term.__class__)}`")


class RenderVisitor(Visitor):
    def __init__(self, wrap=80, raise_on_overflow=False):
        self.indent_stack = [""]
        self.out = StringIO()
        self.line_len = 0
        self.wrap = wrap
        self.raise_ = raise_on_overflow
        self.on_nl = False
        self.last_char = ""

    def write(self, txt):
        if not txt:
            return
        if self.on_nl:
            self.on_nl = False
        self.out.write(txt)
        self.line_len += len(txt)
        if self.raise_ and self.line_len > self.wrap:
            raise OverflowError()
        self.last_char = txt[-1]

    def full_indent(self):
        result = ""
        for i in self.indent_stack:
            result += i
        return result

    def render_chunk(self, chunk):
        if self.raise_ and self.wrap < 0:
            raise OverflowError()
        for c in chunk.content:
            self.visit(c)
        self.indent_stack.pop()
        return self.out.getvalue()

    @visitor(Chunk)
    def visit_chunk(self, chunk):
        # try to inline the chunk
        split = False
        try:
            RenderVisitor(wrap=self.wrap - self.line_len, raise_on_overflow=True).render_chunk(chunk)
        except OverflowError:
            if self.raise_:
                raise
            split = True
        if split:
            self.indent_stack.append(chunk.indent)
            for idx, c in enumerate(chunk.content):
                if isinstance(c, Blank):
                    self.out.write("\n")
                    self.line_len = 0
                    continue
                if idx:
                    self.out.write("\n")
                    self.line_len = 0
                if idx and self.line_len == 0:
                        # if self.full_indent():
                        #     print(f"INDENT `{self.full_indent()}`")
                        for i in self.indent_stack:
                            self.write(i)
                if not idx:
                    self.write(chunk.first_indent)
                self.on_nl = True
                self.visit(c)
            self.indent_stack.pop()
        else:
            for idx, c in enumerate(chunk.content):
                if isinstance(c, Blank):
                    continue
                if not idx:
                    if chunk.first_indent != chunk.indent and (self.on_nl or chunk.first_indent.strip()):
                        if chunk.first_indent == "( ":
                            self.write("(")
                        else:
                            self.write(chunk.first_indent)
                elif isinstance(c, Chunk):
                    if not chunk.indent.strip():
                        if self.last_char not in " (" and c.content != [")"]:
                            self.write(" ")
                    else:
                        self.write(chunk.indent)
                self.visit(c)

    @visitor(str)
    def visit_str(self, txt):
        self.write(txt)

    def __call__(self, chunk):
        self.visit(chunk)
        return self.out.getvalue().strip()


def render(term, ascii=False):
    chunks = ChunkVisitor(ascii=ascii)(term)
    return RenderVisitor()(chunks)
