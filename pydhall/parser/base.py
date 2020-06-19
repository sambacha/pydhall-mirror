from pathlib import Path
from urllib.parse import urlparse
from ipaddress import IPv6Address
from io import StringIO
import unicodedata

from fastidious import Parser
from fastidious.fastidious_compiler import FastidiousCompiler

from pydhall.ast.comment import BlockComment, LineComment
from pydhall.ast import (
    Annot,
    App,
    Assert,
    Binding,
    BoolLit,
    Builtin,
    CompleteOp,
    Chunk,
    DoubleLit,
    EmptyList,
    EnvVar,
    Field,
    If,
    Import,
    IntegerLit,
    Kind,
    Lambda,
    Let,
    LocalFile,
    Merge,
    Missing,
    NaturalLit,
    NonEmptyList,
    Op,
    Pi,
    Project,
    ProjectType,
    RecordLit,
    RecordType,
    RecordMergeOp,
    RemoteFile,
    RightBiasedRecordMergeOp,
    Some,
    Sort,
    Term,
    TextLit,
    ToMap,
    Type,
    UnionType,
    Var,
)


class Dhall(Parser):
    # p_compiler = FastidiousCompiler(gen_code=False)
    __grammar__ = r"""
    DhallFile ← e:CompleteExpression EOF { @e }

    EOF ← !.

    EOL <- "\n" / "\r\n" {;"\n"}

    ValidNonAscii <- [\u0080-\uD7FF\uE000-\uFFFD\U00010000-\U0001FFFD\U00020000-\U0002FFFD\U00030000-\U0003FFFD\U00040000-\U0004FFFD\U00050000-\U0005FFFD\U00060000-\U0006FFFD\U00070000-\U0007FFFD\U00080000-\U0008FFFD\U00090000-\U0009FFFD\U000A0000-\U000AFFFD\U000B0000-\U000BFFFD\U000C0000-\U000CFFFD\U000D0000-\U000DFFFD\U000E0000-\U000EFFFD\U000F0000-\U000FFFFD]
      # not supported in python regexps. TODO: Fix fastidious.
      # / [\U000100000-\U00010FFFD]

    BlockComment <- "{-" BlockCommentContinue

    BlockCommentChar <-
          ~"[\\x20-\\x2c]"
          # '-' is maybe the end of the comment
        / ~"[\\x2e-\\x7a]"
          # '{' could open a nested comment
        / ~"[\\x7c-\\x7f]"
        / "-" !"}"
        / "{" !"-"
        / ValidNonAscii
        / "\t"
        / EOL

    BlockCommentContinue <-
          "-}"
        / BlockComment BlockCommentContinue
        / BlockCommentChar+ BlockCommentContinue

    NotEOL <- [\x20-\x7f\t] / ValidNonAscii

    LineComment <- "--" content:(NotEOL*) EOL

    WhitespaceChunk <- " " / "\t" / EOL / LineComment / BlockComment

    _ <- WhitespaceChunk*

    _1 <- WhitespaceChunk+

    Digit <- [0-9]

    HexDig <- Digit / [a-fA-F]

    SimpleLabelFirstChar <- [A-Za-z_]
    SimpleLabelNextChar <- [A-Za-z0-9_/-]

    SimpleLabel <-
        Keyword SimpleLabelNextChar+
        / !Keyword SimpleLabelFirstChar SimpleLabelNextChar*
        { p_flatten }

    QuotedLabelChar <- ~"[\\x20-\\x5f\\x61-\\x7e]"
    QuotedLabel <- QuotedLabelChar* { p_flatten }

    Label <- "`" label:QuotedLabel "`" / label:SimpleLabel { @label }

    NonreservedLabel <-
          &(builtin SimpleLabelNextChar) label:Label
        / !builtin label:Label
        { @label }

    AnyLabel <- Label

    AnyLabelOrSome <- AnyLabel / Some { p_flatten }

    DoubleQuoteChunk <-
         e:Interpolation
       / '\\' e:DoubleQuoteEscaped
       / e:DoubleQuoteChar
       { @e }

    DoubleQuoteEscaped <-
           '"'
         / '$'
         / '\\'
         / '/'
         / 'b'
         / 'f'
         / 'n'
         / 'r'
         / 't'
         / UnicodeEscape { on_DoubleQuoteEscaped }

    UnicodeEscape <- "u" (
            digits:(HexDig HexDig HexDig HexDig)
          / '{' digits:(HexDig+) '}')

    DoubleQuoteChar <-
         ~"[\\x20-\\x21]"
       / ~"[\\x23-\\x5b]"
       / ~"[\\x5d-\\x7f]"
       / ValidNonAscii


    DoubleQuoteLiteral ← '"' chunks:DoubleQuoteChunk* '"' { on_DoubleQuoteLiteral }

    SingleQuoteContinue <-
          Interpolation SingleQuoteContinue
        / EscapedQuotePair SingleQuoteContinue
        / EscapedInterpolation SingleQuoteContinue
        / "''"
        / SingleQuoteChar SingleQuoteContinue

    EscapedQuotePair <- "'''" { ;"''" }

    EscapedInterpolation <- "''${"

    SingleQuoteChar <-
         ~"[\\x20-\\x7f]"
       / '\t'
       / EOL
       / ValidNonAscii

    SingleQuoteLiteral ← "''" EOL content:SingleQuoteContinue { on_SingleQuoteLiteral }

    Interpolation ← "${" e:CompleteExpression "}" { @e }

    TextLiteral ← DoubleQuoteLiteral / SingleQuoteLiteral

    If ← "if"
    Then ← "then"
    Else ← "else"
    Let ← "let"
    In ← "in"
    As ← "as"
    Using ← "using"
    Merge ← "merge"
    Missing ← "missing" !SimpleLabelNextChar { on_Missing }
    Infinity ← "Infinity"
    NaN ← "NaN"
    Some ← "Some"
    toMap ← "toMap"
    assert_ ← "assert"
    with_ ← "with"

    Keyword ←
        If / Then / Else
      / Let / In
      / Using / Missing
      / assert_ / As
      / Infinity / NaN
      / Merge / Some / toMap
      / Forall
      / with_

    builtin "Builtin" ←
        "Natural/fold"
      / "Natural/build"
      / "Natural/isZero"
      / "Natural/even"
      / "Natural/odd"
      / "Natural/toInteger"
      / "Natural/show"
      / "Integer/show"
      / "Integer/negate"
      / "Integer/clamp"
      / "Natural/subtract"
      / "Integer/toDouble"
      / "Double/show"
      / "List/build"
      / "List/fold"
      / "List/length"
      / "List/head"
      / "List/last"
      / "List/indexed"
      / "List/reverse"
      / "Text/show"
      / "Bool"
      / "True"
      / "False"
      / "Optional"
      / "None"
      / "Natural"
      / "Integer"
      / "Double"
      / "Text"
      / "List"
      / "Type"
      / "Kind"
      / "Sort"

    Text ← "Text"
    Location ← "Location"

    Combine ← "/\\" / '∧'
    CombineTypes ← "//\\\\" / '⩓'
    Equivalent ← "===" / '≡'
    Prefer ← "//" / '⫽'
    Lambda ← '\\' / 'λ'
    Forall <- "forall" / "∀"
    Arrow ← "->" / '→'
    Complete ← "::"

    Exponent ← "e"i [+-]? Digit+

    NumericDoubleLiteral ← [+-]? Digit+ ( "." Digit+ Exponent? / Exponent)

    DoubleLiteral ← num:NumericDoubleLiteral
      / minf:("-" Infinity)
      / inf:Infinity
      / nan:NaN { on_DoubleLiteral }

    NaturalLiteral ← HexLiteral / DecLiteral / BannedDecLiteral / Zero
    HexLiteral <- "0x" v:(HexDig+)
    DecLiteral <- [1-9] Digit*
    BannedDecLiteral <- '0' Digit+
    Zero <- '0'

    IntegerLiteral ←
        n:('+' NaturalLiteral)
      / mn:('-' mn:NaturalLiteral) { on_IntegerLiteral }

    DeBruijn ← _ '@' _ index:NaturalLiteral

    Variable ← name:NonreservedLabel index:DeBruijn?

    Identifier ← Variable / builtin

    PathCharacter <-
         '\x21'
       / ~"[\\x24-\\x27]"
       / ~"[\\x2a-\\x2b]"
       / ~"[\\x2d-\\x2e]"
       / ~"[\\x30-\\x3b]"
       / '\x3d'
       / ~"[\\x40-\\x5a]"
       / ~"[\\x5e-\\x7a]"
       / '\x7c'
       / '\x7e'

    QuotedPathCharacter <-
         ~"[\x20-\x21]"
       / ~"[\x23-\x2e]"
       / ~"[\x30-\x7f]"
       / ValidNonAscii

    UnquotedPathComponent <- PathCharacter+ { p_flatten }

    QuotedPathComponent <- QuotedPathCharacter+ { on_QuotedPathComponent }

    PathComponent <- '/' c:UnquotedPathComponent
                  / '/' '"' c:QuotedPathComponent '"' { @c }

    Path <- PathComponent+ { on_Path }

    Local ← ParentPath / HerePath / HomePath / AbsolutePath

    ParentPath ← ".." p:Path { on_ParentPath }
    HerePath ← '.' p:Path { on_HerePath }
    HomePath ← '~' p:Path { on_HomePath }
    AbsolutePath ← p:Path { on_AbsolutePath }

    Scheme <- "http" 's'?

    HttpRaw <- Scheme "://" Authority PathAbEmpty ( '?' Query )?

    PathAbEmpty <- ('/' Segment)*

    Authority <- (Userinfo '@')? Host (':' Port)?

    Userinfo <- ( Unreserved / PctEncoded / SubDelims / ':' )*

    Host <- IPLiteral / RegName

    Port <- Digit*

    IPLiteral <- '[' IPv6address ']'

    IPv6address <- (HexDig)* ':' (HexDig / ':' / '.')* { on_IPv6address }

    RegName <- (Unreserved / PctEncoded / SubDelims)*

    Segment <- PChar*

    PChar <- Unreserved / PctEncoded / SubDelims / [:@]

    Query <- (PChar / [/?])*

    PctEncoded <- '%' HexDig HexDig

    Unreserved <- [A-Za-z0-9._~-]

    SubDelims <- "!" / "$" / "&" / "'" / "*" / "+" / ";" / "="

    Http ← u:HttpRaw using_clause:( _ Using _1 ImportExpression)? { on_Http }

    Env ← "env:" v:(BashEnvironmentVariable / PosixEnvironmentVariable) { on_Env }

    BashEnvironmentVariable ← [A-Za-z_][A-Za-z0-9_]*

    PosixEnvironmentVariable ← '"' v:PosixEnvironmentVariableContent '"' { @v }

    PosixEnvironmentVariableContent ← v:PosixEnvironmentVariableCharacter+

    PosixEnvironmentVariableCharacter ←
        [\x20-\x21\x23-\x3c\x3e-\x5b\x5d-\x7e] / PosixEnvironmentVariableEscape

    PosixEnvironmentVariableEscape <- '\\' c:["\\abfnrtv] { on_PosixEnvironmentVariableEscape }

    ImportType ← Missing / Local / Http / Env

    # // ugh, there seems to be no fixed-repetition operator in pigeon :(
    HashValue <- HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                 HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                 HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                 HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                 HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                 HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                 HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                 HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig

    Hash <- "sha256:" val:HashValue

    ImportHashed ← i:ImportType h:(_1 Hash)? { on_ImportHashed }

    ImportAsText <- i:ImportHashed _ As _1 Text { on_ImportAsText }
    ImportAsLocation <- i:ImportHashed _ As _1 Location { on_ImportAsLocation }
    SimpleImport <- i:ImportHashed { on_SimpleImport }
    Import <-
        ImportAsText
        / ImportAsLocation
        / SimpleImport


    LetBinding ←
        Let _1 label:NonreservedLabel _ a:(Annotation _)? '=' _ v:Expression _ { on_LetBinding }

    LambdaExpression <-
        Lambda _ '(' _ label:NonreservedLabel _ ':' _1 t:Expression _ ')' _
        Arrow _ body:Expression { on_LambdaExpression }
    IfExpression <- If _1 cond:Expression _ Then _1 t:Expression _ Else _1 f:Expression
    Bindings <- bindings:LetBinding+ In _1 b:Expression { on_Bindings }
    ForallExpression <-
        Forall _ '(' _ label:NonreservedLabel _ ':' _1 t:Expression _ ')'
        _ Arrow _ body:Expression { on_ForallExpression }
    AnonPiExpression <- o:OperatorExpression _ Arrow _ e:Expression { on_AnonPiExpression }
    MergeExpression <-
        Merge _1 h:ImportExpression _1 u:ImportExpression _
        ':' _1 a:ApplicationExpression { on_MergeExpr }
    AnnotatedToMap <- toMap _1 e:ImportExpression _ ':' _1 t:ApplicationExpression { on_toMapExpr }
    AssertExpression <- assert_ _ ':' _1 a:Expression { on_AssertExpression }
    Expression <-
        LambdaExpression
        / IfExpression
        / Bindings
        / ForallExpression
        / AnonPiExpression
        / WithExpression
        / MergeExpression
        / EmptyList
        / AnnotatedToMap
        / AssertExpression
        / AnnotatedExpression


    Annotation ← ':' _1 a:Expression { @a }

    AnnotatedExpression ← e:OperatorExpression a:(_ Annotation)? { on_AnnotatedExpression }

    EmptyList ← '[' _ (',' _)? ']' _ ':' _1 a:ApplicationExpression

    WithExpression ← first:ImportExpression rest:(_1 with_ _1 WithClause)+ { on_WithExpression }

    WithClause ← FieldPath _ '=' _ OperatorExpression

    FieldPath ← first:AnyLabelOrSome rest:(_ '.' _ AnyLabelOrSome)* { on_FieldPath }

    OperatorExpression ← EquivalentExpression

    EquivalentExpression   ← first:ImportAltExpression rest:(_ Equivalent _ ImportAltExpression)*
        { on_Op }
    ImportAltExpression    ← first:OrExpression           rest:(_ "?" _1 OrExpression)*
        { on_Op }
    OrExpression           ← first:PlusExpression         rest:(_ "||" _ PlusExpression)*
        { on_Op }
    PlusExpression         ← first:TextAppendExpression   rest:(_ '+' _1 TextAppendExpression)*
        { on_Op }
    TextAppendExpression   ← first:ListAppendExpression   rest:(_ "++" _ ListAppendExpression)*
        { on_Op }
    ListAppendExpression   ← first:AndExpression          rest:(_ '#' _ AndExpression)*
        { on_Op }
    AndExpression          ← first:CombineExpression      rest:(_ "&&" _ CombineExpression)*
        { on_Op }
    CombineExpression      ← first:PreferExpression       rest:(_ Combine _ PreferExpression)*
        { on_Op }
    PreferExpression       ← first:CombineTypesExpression rest:(_ Prefer _ CombineTypesExpression)*
        { on_Op }
    CombineTypesExpression ← first:TimesExpression rest:(_ CombineTypes _ TimesExpression)*
        { on_Op }
    TimesExpression        ← first:EqualExpression rest:(_ '*' _ EqualExpression)*
        { on_Op }
    EqualExpression        ← first:NotEqualExpression rest:(_ "==" _ NotEqualExpression)*
        { on_Op }
    NotEqualExpression     ← first:ApplicationExpression rest:(_ "!=" _ ApplicationExpression)*
        { on_Op }
    ApplicationExpression ← f:FirstApplicationExpression rest:(_1 ImportExpression)* { on_ApplicationExpression }

    MergeExpr <- Merge _1 h:ImportExpression _1 u:ImportExpression { on_MergeExpr }
    SomeExpr <- Some _1 e:ImportExpression { on_SomeExpr } # { return Some{e.(Term)}, nil }
    toMapExpr <- toMap _1 e:ImportExpression { on_toMapExpr } # { return ToMap{Record: e.(Term)}, nil }
    FirstApplicationExpression ← MergeExpr
         / SomeExpr
         / toMapExpr
         / ImportExpression

    ImportExpression ← Import / CompletionExpression

    CompletionExpression ← first:SelectorExpression rest:(_ Complete _ SelectorExpression)? { on_CompletionExpression }

    SelectorExpression ← e:PrimitiveExpression ls:(_ '.' _ Selector)* { on_SelectorExpression }

    Selector ← AnyLabel / Labels / TypeSelector

    Labels ← '{' _ optclauses:( AnyLabelOrSome _ (',' _ AnyLabelOrSome _ )* )? '}' { on_Labels }

    TypeSelector ← '(' _ e:Expression _ ')' { @e }

    Mustache <- '{' _ (',' _)? r:RecordTypeOrLiteral _ '}' { @r }
    UnionDef <- '<' _ ('|' _)? u:UnionType _ '>' { @u }
    Paren <- '(' _ ('|' _)? e:Expression _ ')' { @e }
    PrimitiveExpression ←
          DoubleLiteral
        / NaturalLiteral
        / IntegerLiteral
        / TextLiteral
        / Mustache
        / UnionDef
        / NonEmptyListLiteral
        / Identifier
        / Paren

    EmptyRecord <- "=" { on_EmptyRecord }
    # '=' { return RecordLit{}, nil }
    EmptyRecordType <- "" { on_EmptyRecordType }
    # "" { return RecordType{}, nil }
    RecordTypeOrLiteral ←
        EmptyRecord
        / NonEmptyRecordType
        / NonEmptyRecordLiteral
        / EmptyRecordType

    MoreRecordType ← _ ',' _ f:RecordTypeEntry { @f }
    NonEmptyRecordType ← first:RecordTypeEntry rest:MoreRecordType* { on_NonEmptyRecordType }
    RecordTypeEntry ← name:AnyLabelOrSome _ ':' _1 expr:Expression

    MoreRecordLiteral ← _ ',' _ f:RecordLiteralEntry { @f }
    NonEmptyRecordLiteral ← first:RecordLiteralEntry rest:MoreRecordLiteral* { on_NonEmptyRecordLiteral }

    RecordLiteralEntry ← name:AnyLabelOrSome val:(RecordLiteralNormalEntry / RecordLiteralPunnedEntry) { on_RecordLiteralEntry }

    RecordLiteralNormalEntry ← children:(_ '.' _ AnyLabelOrSome)* _ '=' _ expr:Expression { on_RecordLiteralNormalEntry }
    RecordLiteralPunnedEntry ← ""

    UnionType ← NonEmptyUnionType / EmptyUnionType

    EmptyUnionType ← "" { on_EmptyUnionType }

    NonEmptyUnionType ← first:UnionTypeEntry rest:(_ '|' _ UnionTypeEntry)* { on_NonEmptyUnionType }

    UnionTypeEntry ← AnyLabelOrSome (_ ':' _1 Expression)?

    MoreList ← ',' _ e:Expression _ { @e }

    NonEmptyListLiteral ← '[' _ (',' _)? first:Expression _ rest:MoreList* ']' { on_NonEmptyList }

    CompleteExpression <- _ e:Expression _ { @e }
    """

    def __init__(self, *args, name="<string>", **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)

    def emit(self, node, *args):
        return node(*args)

    def on_UnicodeEscape(self, _, digits):
        digits = self.p_flatten(digits)
        ord_ = int(digits, 16)
        if ord_ & 65534 == 65534:  # 0FFFE mask denotes unicode non-characters
            self.p_parse_error(f"can't encode character '\\u{digits}': non-character")
        if unicodedata.category(chr(ord_)) == "Cs":
            self.p_parse_error(f"can't encode character '\\u{digits}': surrogates not allowed")
        return chr(ord_)

    def on_DoubleQuoteEscaped(self, result):
        if result in r'"$\/':
            return result
        else:
            return dict(
                b='\b',
                f='\f',
                n='\n',
                r='\r',
                t='\t').get(result, result)

    def on_LineComment(self, _, content):
        return self.emit(LineComment, self.p_flatten(content))

    def on_BlockComment(self, value):
        value = self.p_flatten_list(value)
        content = StringIO()
        for i in value:
            if isinstance(i, BlockComment):
                content.write(i.content)
            else:
                content.write(i)
        return self.emit(BlockComment, content.getvalue())

    def on_builtin(self, result):
        result = self.p_flatten(result)
        if result == "True":
            return self.emit(BoolLit, True)
        if result == "False":
            return self.emit(BoolLit, False)
        if result == "Type":
            return self.emit(Type)
        if result == "Kind":
            return self.emit(Kind)
        if result == "Sort":
            return self.emit(Sort)
        return self.emit(Builtin, result)

    def on_Path(self, result):
        return str(Path().joinpath(*result))

    def on_HttpRaw(self, result):
        return urlparse(self.p_flatten(result))

    def on_IPv6address(self, result):
        return self.p_flatten(result)

    def on_EscapedInterpolation(self, _):
        return "${"

    def on_IfExpression(self, _, cond, t, f):
        return self.emit(If, cond, t, f)

    def on_AnnotatedExpression(self, _, e, a=None):
        if not a:
            return e
        return self.emit(Annot, e, a[1])

    def on_Variable(self, _, name, index=None):
        if not index:
            index = 0
        return self.emit(Var, name, index)

    def on_DeBruijn(self, _, index):
        return index.value

    def on_HexLiteral(self, _, v):
        return self.emit(NaturalLit, int(self.p_flatten(v), base=16))

    def on_DecLiteral(self, v):
        return self.emit(NaturalLit, int(self.p_flatten(v)))

    def on_BannedDecLiteral(self, _):
        return self.p_parse_error("Natural literals cannot have leading zeros")

    def on_Zero(self, _):
        return self.emit(NaturalLit, 0)

    def built_text_literal(self, chunks):
        suffix = StringIO()
        out_chunks = []
        for chunk in chunks:
            if isinstance(chunk, str):
                suffix.write(chunk)
            elif isinstance(chunk, Term):
                out_chunks.append((suffix.getvalue(), chunk))
                suffix.seek(0)
                suffix.truncate()
            else:
                assert False  # pragma: no cover
        return out_chunks, suffix.getvalue()

    def on_DoubleQuoteLiteral(self, _, chunks):
        """
        '"' chunks:DoubleQuoteChunk* '"'
        """
        chunks, suffix = self.built_text_literal(chunks)
        return self.emit(TextLit, [Chunk(*c) for c in chunks], suffix)

    def _flatten_single_quote(self, lst):
        lst = self.p_flatten_list(lst)
        string = ""
        for item in lst:
            if isinstance(item, str):
                string += item
            else:
                string += "|"
        lines = string.splitlines()

        def get_line_indent(l):
            li = ""
            for c in l:
                if c in " \t":
                    li += c
                else:
                    break
            return li

        indent = get_line_indent(lines[-1])
        for l in lines:
            li = get_line_indent(l)
            if li and indent.startswith(li):
                indent = li
        return indent, lst[:-1]

    def on_SingleQuoteLiteral(self, _, content):
        indent, content = self._flatten_single_quote(content)
        chunks, suffix = self.built_text_literal(content)
        if chunks:
            if chunks[0][0].startswith(indent):
                chunks[0] = (chunks[0][0].replace(indent, "", 1), chunks[0][1])
        else:
            if suffix.startswith(indent):
                suffix = suffix.replace(indent, "", 1)
        # print(chunks, suffix)
        if indent:
            chunks = [Chunk(c[0].replace("\n"+indent, "\n"), c[1]) for c in chunks]
            suffix = suffix.replace("\n"+indent, "\n")
        else:
            chunks = [Chunk(*c) for c in chunks]
        return self.emit(TextLit, chunks, suffix)

    def on_NumericDoubleLiteral(self, val):
        val = float(self.p_flatten(val))
        if DoubleLit.MAX >= val >= DoubleLit.MIN:
            return self.emit(DoubleLit, val)
        else:
            self.p_parse_error("Literal double out of bounds")

    def on_DoubleLiteral(self, _, num=None, inf=None, minf=None, nan=None):
        if num is not self.NoMatch:
            return num
        if inf is not self.NoMatch and inf is not None:
            return self.emit(DoubleLit, float("inf"))
        if minf is not self.NoMatch and minf is not None:
            return self.emit(DoubleLit, float("-inf"))
        if nan is not self.NoMatch:
            return self.emit(DoubleLit, float("nan"))
        assert False  # pragma: no cover

    def on_IntegerLiteral(self, _, n=None, mn=None):
        if n is not self.NoMatch:
            return self.emit(IntegerLit, n[1].value)
        if mn is not self.NoMatch:
            return self.emit(IntegerLit, -(mn[1].value))
        assert False  # pragma: no cover

    def on_Env(self, _, v):
        return [EnvVar, self.p_flatten(v)]

    def on_LetBinding(self, _, label, a, v):
        if not a:
            a = None
        else:
            a = a[0]
        return self.emit(Binding, label, a, v)

    def on_Bindings(self, _, bindings, b):
        return self.emit(Let, bindings, b)

    op_classes = {}
    for opclass in Op.__subclasses__():
        ops = getattr(opclass, "operators", [])
        for o in ops:
            op_classes[o] = opclass

    def on_Op(self, _, first, rest):
        out = first
        for r in rest:
            out = self.emit(self.op_classes[r[1]], out, r[3])
        return out

    def on_CompletionExpression(self, _, first, rest):
        if not rest:
            return first
        return self.emit(CompleteOp, first, rest[3]) 

    def on_MergeExpr(self, _, h, u, a=None):
        return self.emit(Merge, h, u, a)

    def on_SomeExpr(self, _, e):
        return self.emit(Some, e)

    def on_toMapExpr(self, _, e, t=None):
        return self.emit(ToMap, e, t)

    def on_EmptyList(self, _, a):
        return self.emit(EmptyList, a)

    def on_ParentPath(self, _, p):
        return [LocalFile, Path("..").joinpath(p)]

    def on_HerePath(self, _, p):
        return [LocalFile, Path(".").joinpath(p)]

    def on_HomePath(self, _, p):
        return [LocalFile, Path("~").joinpath(p)]

    def on_AbsolutePath(self, _, p):
        return [LocalFile, Path("/").joinpath(p)]

    def on_ImportHashed(self, _, i, h=None):
        # import ipdb; ipdb.set_trace()
        if not h:
            i.append(None)
        else:
            i.append(bytearray.fromhex("1220" + self.p_flatten(h[1][1])))
        return i

    def on_ImportAsText(self, _, i):
        i.append(Import.Mode.RawText)
        return i

    def on_ImportAsLocation(self, _, i):
        i.append(Import.Mode.Location)
        return i

    def on_SimpleImport(self, _, i):
        i.append(Import.Mode.Code)
        return i

    def on_Import(self, i):
        return self.emit(i.pop(0), *i)

    def on_LambdaExpression(self, _, label, t, body):
        return self.emit(Lambda, label, t, body)

    def on_ForallExpression(self, _, label, t, body):
        return self.emit(Pi, label, t, body)

    def on_ApplicationExpression(self, _, f, rest):
        if not rest:
            return f
        node = App.build(f, *[r[1] for r in rest])
        return node

    def on_NonEmptyList(self, _, first, rest):
        return self.emit(NonEmptyList, [first] + rest)

    def on_AnonPiExpression(self, _, o, e):
        return self.emit(Pi, "_", o, e)

    def on_EmptyRecord(self, _):
        return self.emit(RecordLit, {})

    def on_EmptyRecordType(self, _):
        return self.emit(RecordType, {})

    def on_NonEmptyRecordType(self, _, first, rest):
        content = { first[0]: first[4] }
        for f in rest:
            if f[0] in content:
                self.p_parse_error("Duplicate Field `%s`" % f)
            content[f[0]] = f[4]
        return self.emit(RecordType, content)

    def on_NonEmptyRecordLiteral(self, _, first, rest):
        content = first
        for f in rest:
            for k, v in f.items():
                if k in content:
                    content[k] = RecordMergeOp(content[k], v)
                else:
                    content[k] = v
        return content

    def on_RecordLiteralEntry(self, _, name, val):
        if isinstance(val, str) and val == "":
            return self.emit(RecordLit, {name: Var(name, 0)})
        return self.emit(RecordLit, {name: val})

    def on_RecordLiteralNormalEntry(self, _, children, expr):
        rest = expr
        for c in reversed(children):
            rest = RecordLit({c[3]: rest})
        return rest

    def on_EmptyUnionType(self, _):
        return self.emit(UnionType, [])

    def on_NonEmptyUnionType(self, _, first, rest):
        """NonEmptyUnionType ←
            first:UnionTypeEntry
            rest:(_ '|' _ UnionTypeEntry)*"""
        alternatives = {}
        def add_entry(e):
            type = e[1]
            type = type[3] if type else None
            name = e[0]
            if name in alternatives:
                self.p_parse_error("Duplicate alternative `%s` in union" % name)
            alternatives[name] = type
        add_entry(first)
        for r in rest:
            add_entry(r[3])
        return self.emit(UnionType, alternatives)

    def on_SelectorExpression(self, _, e, ls):
        "SelectorExpression ← e:PrimitiveExpression ls:(_ '.' _ Selector)*"
        for selector in [i[3] for i in ls]:
            if isinstance(selector, str):
                e = Field(e, selector)
                continue
            if isinstance(selector, list):
                e = Project(e, selector)
                continue
            if isinstance(selector, Term):
                e = ProjectType(e, selector)
                continue
            assert False  # pragma: no cover
        return e

    def on_Labels(self, _, optclauses):
        "Labels ← '{' _ optclauses:( AnyLabelOrSome _ (',' _ AnyLabelOrSome _ )* )? '}'"
        if not optclauses:
            return []
        return [optclauses[0]] + [i[2] for i in optclauses[2]]

    def on_AssertExpression(self, _, a):
        return self.emit(Assert, a)

    def desugar_with(self, record, path, value):
        if len(path) == 1:
            return RightBiasedRecordMergeOp(record, RecordLit({path[0]: value}))
        return RightBiasedRecordMergeOp(
            record,
            RecordLit({
                path[0]: self.desugar_with(
                    Field(record, path[0]),
                    path[1:],
                    value)
            })
        )

    def on_WithExpression(self, _, first, rest):
        out = first
        for r in rest:
            out = self.desugar_with(out, r[3][0], r[3][4])
        return out

    def on_FieldPath(self, _, first, rest):
        return [i for i in self.p_flatten_list([first, rest]) if i != "."]

    def on_Http(self, _, u, using_clause=None):
        if using_clause:
            self.p_parse_error("pydhall doesn't support using clause")
        return [RemoteFile, u]

    def on_Missing(self, _):
        return [Missing]

    def on_QuotedPathComponent(self, value):
        "QuotedPathComponent <- QuotedPathCharacter+"
        # TODO: check the specs
        return self.p_flatten(value).replace("?", "%3F")

    _char_escape_map = {
        '"': '"',
        '\\': "\\",
        'a': '\a',
        'b': '\b',
        'f': '\f',
        'n': '\n',
        'r': '\r',
        't': '\t',
        'v': '\v'
    }

    def on_PosixEnvironmentVariableEscape(self, _, c):
        """PosixEnvironmentVariableEscape <- '\\' ["\\abfnrtv] { on_PosixEnvironmentVariableEscape }"""
        return self._char_escape_map[c]
