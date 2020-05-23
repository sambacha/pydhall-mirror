from pathlib import Path
from urllib.parse import urlparse
from ipaddress import IPv6Address
from io import StringIO

from fastidious import Parser

from pydhall.ast.node import BlockComment, LineComment
from pydhall.ast.fetchable import ImportHashed, EnvVar, LocalFile
from pydhall.ast.term import (
    Annot,
    App,
    Binding,
    BoolLit,
    Builtin,
    CompleteOp,
    Chunk,
    DoubleLit,
    EmptyList,
    If,
    Import,
    IntegerLit,
    Kind,
    Lambda,
    Let,
    Merge,
    NaturalLit,
    NonEmptyList,
    Op,
    Pi,
    Some,
    Sort,
    Term,
    TextLit,
    ToMap,
    Type,
    Var,
)


class Dhall(Parser):
    __grammar__ = r"""
    DhallFile ← e:CompleteExpression EOF { @e }

    CompleteExpression <- _ e:Expression _ { @e }

    EOL <- "\n" / "\r\n" {;"\n"}

    # fastidious doesn't play well with unicode ranges. Fallback to
    # regexps
    ValidNonAscii <-
          ~"[\\u0080-\\uD7FF]"
        / ~"[\\uE000-\\uFFFD]"
        / ~"[\\U00010000-\\U0001FFFD]"
        / ~"[\\U00020000-\\U0002FFFD]"
        / ~"[\\U00030000-\\U0003FFFD]"
        / ~"[\\U00040000-\\U0004FFFD]"
        / ~"[\\U00050000-\\U0005FFFD]"
        / ~"[\\U00060000-\\U0006FFFD]"
        / ~"[\\U00070000-\\U0007FFFD]"
        / ~"[\\U00080000-\\U0008FFFD]"
        / ~"[\\U00090000-\\U0009FFFD]"
        / ~"[\\U000A0000-\\U000AFFFD]"
        / ~"[\\U000B0000-\\U000BFFFD]"
        / ~"[\\U000C0000-\\U000CFFFD]"
        / ~"[\\U000D0000-\\U000DFFFD]"
        / ~"[\\U000E0000-\\U000EFFFD]"
        / ~"[\\U000F0000-\\U000FFFFD]"
      # not supported in python regexps. TODO: Fix fastidious.
      # / [\U000100000-\U00010FFFD]

    BlockComment <- "{-" BlockCommentContinue

    BlockCommentChar <-
          ~"[\\x20-\\x7f]"
        / ValidNonAscii
        / "\t"
        / EOL

    BlockCommentContinue <-
          "-}"
        / BlockComment BlockCommentContinue
        / BlockCommentChar BlockCommentContinue

    NotEOL <- ~"[\\x20-\\x7f]" / ValidNonAscii / "\t"

    LineComment <- "--" content:(NotEOL*) EOL

    WhitespaceChunk <- " " / "\t" / EOL / LineComment / BlockComment

    _ <- WhitespaceChunk*

    _1 <- WhitespaceChunk+

    Digit <- [0-9]

    HexDig <- Digit / [a-f]i

    SimpleLabelFirstChar <- [A-Za-z_]
    SimpleLabelNextChar <- [A-Za-z0-9_/-]

    SimpleLabel <-
        Keyword SimpleLabelNextChar+
        / !Keyword SimpleLabelFirstChar SimpleLabelNextChar*
        { p_flatten }

    QuotedLabelChar <- ~"[\x20-\x5f\x61-\x7e]"
    QuotedLabel <- QuotedLabelChar+ { p_flatten }

    Label <- "`" label:QuotedLabel "`" / label:SimpleLabel { @label }

    NonreservedLabel <-
          &(Reserved SimpleLabelNextChar) label:Label
        / !Reserved label:Label
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
         ~"[\x20-\x21]"
       / ~"[\x23-\x5b]"
       / ~"[\x5d-\x7f]"
       / ValidNonAscii


    DoubleQuoteLiteral ← '"' chunks:DoubleQuoteChunk* '"'

    SingleQuoteContinue <-
          Interpolation SingleQuoteContinue
        / EscapedQuotePair SingleQuoteContinue
        / EscapedInterpolation SingleQuoteContinue
        / "''"
        / SingleQuoteChar SingleQuoteContinue

    EscapedQuotePair <- "'''" { ;"''" }

    EscapedInterpolation <- "''${"

    SingleQuoteChar <-
         ~"[\x20-\x7f]"
       / ValidNonAscii
       / '\t'
       / EOL

    SingleQuoteLiteral ← "''" EOL content:SingleQuoteContinue
    # {
    #     var str strings.Builder
    #     var outChunks Chunks
    #     chunk, ok := content.([]interface{})
    #     for ; ok; chunk, ok = chunk[1].([]interface{}) {
    #         switch e := chunk[0].(type) {
    #         case []byte:
    #             str.Write(e)
    #         case Term:
    #                 outChunks = append(outChunks, Chunk{str.String(), e})
    #                 str.Reset()
    #         default:
    #             return nil, errors.New("unimplemented")
    #         }
    #     }
    #     return removeLeadingCommonIndent(TextLit{Chunks: outChunks, Suffix: str.String()}), nil
    # }


    Interpolation <- "${" e:CompleteExpression "}" { @e }

    TextLiteral <- DoubleQuoteLiteral / SingleQuoteLiteral

    Reserved <-
        "Natural/build"
      / "Natural/fold"
      / "Natural/isZero"
      / "Natural/even"
      / "Natural/odd"
      / "Natural/toInteger"
      / "Natural/show"
      / "Natural/subtract"
      / "Integer/clamp"
      / "Integer/negate"
      / "Integer/toDouble"
      / "Integer/show"
      / "Double/show"
      / "List/build"
      / "List/fold"
      / "List/length"
      / "List/head"
      / "List/last"
      / "List/indexed"
      / "List/reverse"
      / "Optional/build"
      / "Optional/fold"
      / "Text/show"
      / "Bool"
      / "True"
      / "False"
      / "Optional"
      / "Natural"
      / "Integer"
      / "Double"
      / "Text"
      / "List"
      / "None"
      / "Type"
      / "Kind"
      / "Sort"

    If <- "if"
    Then <- "then"
    Else <- "else"
    Let <- "let"
    In <- "in"
    As <- "as"
    Using <- "using"
    Merge <- "merge"
    # Missing ← "missing" !SimpleLabelNextChar { return Missing{}, nil }
    Missing <- "missing" !SimpleLabelNextChar
    True_ <- "True"
    False_ <- "False"
    Infinity <- "Infinity"
    NaN <- "NaN"
    Some <- "Some"
    toMap <- "toMap"
    assert_ <- "assert"
    with_ <- "with"

    Keyword <-
        If / Then / Else
      / Let / In
      / Using / Missing
      / assert_ / As
      / Infinity / NaN
      / Merge / Some / toMap
      / Forall
      / with_

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
      / inf:Infinity
      / minf:("-" Infinity)
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

    Identifier ← Variable / Reserved

    PathCharacter <-
         '\x21'
       / ~"[\x24-\x27]"
       / ~"[\x2a-\x2b]"
       / ~"[\x2d-\x2e]"
       / ~"[\x30-\x3b]"
       / '\x3d'
       / ~"[\x40-\x5a]"
       / ~"[\x5e-\x7a]"
       / '\x7c'
       / '\x7e'

    QuotedPathCharacter <-
         ~"[\x20-\x21]"
       / ~"[\x23-\x2e]"
       / ~"[\x30-\x7f]"
       / ValidNonAscii

    UnquotedPathComponent <- PathCharacter+ { p_flatten }

    QuotedPathComponent <- QuotedPathCharacter+ { p_flatten }

    PathComponent <- '/' c:UnquotedPathComponent
                  / '/' '"' c:QuotedPathComponent '"' { @c }

    Path <- PathComponent+

    Local ← ParentPath / HerePath / HomePath / AbsolutePath

    ParentPath ← ".." p:Path { on_ParentPath }
    HerePath ← '.' p:Path { on_HerePath }
    HomePath ← '~' p:Path { on_HomePath }
    AbsolutePath ← p:Path { on_AbsolutePath }

    Scheme <- "http" 's'?

    HttpRaw <- Scheme "://" Authority UrlPath ( '?' Query )?

    UrlPath <- (PathComponent / '/' Segment)*

    Authority <- (Userinfo '@')? Host (':' Port)?

    Userinfo <- ( Unreserved / PctEncoded / SubDelims / ':' )*

    Host <- IPLiteral / RegName

    Port <- Digit*

    IPLiteral <- '[' IPv6address ']'

    IPv6address <- (HexDig)* ':' (HexDig / ':' / '.')*

    RegName <- (Unreserved / PctEncoded / SubDelims)*

    Segment <- PChar*

    PChar <- Unreserved / PctEncoded / SubDelims / [:@]

    Query <- (PChar / [/?])*

    PctEncoded <- '%' HexDig HexDig

    Unreserved <- [A-Za-z0-9._~-]

    SubDelims <- "!" / "$" / "&" / "'" / "*" / "+" / ";" / "="

    Http ← u:HttpRaw usingClause:( _ Using _1 ImportExpression)?
    # {
    #   if usingClause != nil {
    #     return NewRemoteFile(u.(*url.URL)), errors.New("dhall-golang does not support ❰using❱ clauses")
    #   }
    #   return NewRemoteFile(u.(*url.URL)), nil
    # }

    Env ← "env:" v:(BashEnvironmentVariable / PosixEnvironmentVariable) { @v }

    BashEnvironmentVariable ← [A-Za-z_][A-Za-z0-9_]* { on_BashEnvironmentVariable }

    PosixEnvironmentVariable ← '"' v:PosixEnvironmentVariableContent '"' { @v }

    PosixEnvironmentVariableContent ← v:PosixEnvironmentVariableCharacter+
    # {
    #   var b strings.Builder
    #   for _, c := range v.([]interface{}) {
    #     _, err := b.Write(c.([]byte))
    #     if err != nil { return nil, err }
    #   }
    #   return EnvVar(b.String()), nil
    # }

    PosixEnvironmentVariableCharacter ←
        [a-z] # TODO
    #       `\"` { return []byte{0x22}, nil }
    #     / `\\` { return []byte{0x5c}, nil }
    #     / `\a` { return []byte{0x07}, nil }
    #     / `\b` { return []byte{0x08}, nil }
    #     / `\f` { return []byte{0x0c}, nil }
    #     / `\n` { return []byte{0x0a}, nil }
    #     / `\r` { return []byte{0x0d}, nil }
    #     / `\t` { return []byte{0x09}, nil }
    #     / `\v` { return []byte{0x0b}, nil }
    #     / [\x20-\x21]
    #     / [\x23-\x3c]
    #     / [\x3e-\x5b]
    #     / [\x5d-\x7e]

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
    # {
    #     out := make([]byte, sha256.Size)
    #     _, err := hex.Decode(out, c.text)
    #     if err != nil { return nil, err }
    #     return out, nil
    # }
    Hash <- "sha256:" val:HashValue
    # { return append([]byte{0x12,0x20}, val.([]byte)...), nil }

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

    # Expression ←
    #       Lambda _ '(' _ label:NonreservedLabel _ ':' _1 t:Expression _ ')' _ Arrow _ body:Expression {
    #           return Lambda{Label:label.(string), Type:t.(Term), Body: body.(Term)}, nil
    #       }
    #     / If _1 cond:Expression _ Then _1 t:Expression _ Else _1 f:Expression {
    #           return If{cond.(Term),t.(Term),f.(Term)},nil
    #       }
    #     / bindings:LetBinding+ In _1 b:Expression {
    #         bs := make([]Binding, len(bindings.([]interface{})))
    #         for i, binding := range bindings.([]interface{}) {
    #             bs[i] = binding.(Binding)
    #         }
    #         return NewLet(b.(Term), bs...), nil
    #       }
    #     / Forall _ '(' _ label:NonreservedLabel _ ':' _1 t:Expression _ ')' _ Arrow _ body:Expression {
    #           return Pi{Label:label.(string), Type:t.(Term), Body: body.(Term)}, nil
    #       }
    #     / o:OperatorExpression _ Arrow _ e:Expression { return NewAnonPi(o.(Term),e.(Term)), nil }
    #     / Merge _1 h:ImportExpression _1 u:ImportExpression _ ':' _1 a:ApplicationExpression {
    #           return Merge{Handler:h.(Term), Union:u.(Term), Annotation:a.(Term)}, nil
    #       }
    #     / EmptyList
    #     / toMap _1 e:ImportExpression _ ':' _1 t:ApplicationExpression { return ToMap{e.(Term), t.(Term)}, nil }
    #     / assert _ ':' _1 a:Expression { return Assert{Annotation: a.(Term)}, nil }
    #     / AnnotatedExpression

    LambdaExpression <-
        Lambda _ '(' _ label:NonreservedLabel _ ':' _1 t:Expression _ ')' _
        Arrow _ body:Expression { on_LambdaExpression }
    Bindings <- bindings:LetBinding+ In _1 b:Expression { on_Bindings }
    ForallExpression <-
        Forall _ '(' _ label:NonreservedLabel _ ':' _1 t:Expression _ ')'
        _ Arrow _ body:Expression { on_ForallExpression }
    AnonPiExpression <- o:OperatorExpression _ Arrow _ e:Expression { on_AnonPiExpression }
    MergeExpression <-  Merge _1 h:ImportExpression _1 u:ImportExpression _ ':' _1 a:ApplicationExpression { on_MergeExpr }
    IfExpression <- If _1 cond:Expression _ Then _1 t:Expression _ Else _1 f:Expression
    Expression <-
        LambdaExpression
        / IfExpression
        / Bindings
        / ForallExpression
        / AnonPiExpression
        / MergeExpression
        / EmptyList
        / AnnotatedExpression


    Annotation ← ':' _1 a:Expression { @a }

    AnnotatedExpression ← e:OperatorExpression a:(_ Annotation)? { on_AnnotatedExpression }

    EmptyList ← '[' _ (',' _)? ']' _ ':' _1 a:ApplicationExpression

    OperatorExpression ← ImportAltExpression

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
    NotEqualExpression     ← first:EquivalentExpression rest:(_ "!=" _ EquivalentExpression)*
        { on_Op }
    EquivalentExpression   ← first:WithExpression rest:(_ Equivalent _ WithExpression)*
        { on_Op }
    WithExpression         ← first:ApplicationExpression rest:(_1 with_ _1 FieldPath _ '=' _ ApplicationExpression)* { @first }
    #   {
    #     out := first.(Term)
    #     if rest == nil { return out, nil }
    #     for _, b := range rest.([]interface{}) {
    #         path := b.([]interface{})[3].([]string)
    #         value := b.([]interface{})[7].(Term)
    #         out = desugarWith(out, path, value)
    #     }
    #     return out, nil
    #   }

    FieldPath ← first:AnyLabelOrSome rest:(_ '.' _ AnyLabelOrSome)*
    # {
    #   out := []string{first.(string)}
    #   if rest == nil { return out, nil }
    #   for _, b := range rest.([]interface{}) {
    #     nextField := b.([]interface{})[3].(string)
    #     out = append(out, nextField)
    #   }
    #   return out, nil
    # }

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

    SelectorExpression ← e:PrimitiveExpression ls:(_ '.' _ Selector)* { @e }
    # {
    #     expr := e.(Term)
    #     labels := ls.([]interface{})
    #     for _, labelSelector := range labels {
    #         selectorIface := labelSelector.([]interface{})[3]
    #         switch selector := selectorIface.(type) {
    #             case string:
    #                 expr = Field{expr, selector}
    #             case []string:
    #                 expr = Project{expr, selector}
    #             case Term:
    #                 expr = ProjectType{expr, selector}
    #             default:
    #                 return nil, errors.New("unimplemented")
    #         }
    #     }
    #     return expr, nil
    # }

    Selector ← AnyLabel / Labels / TypeSelector

    Labels ← '{' _ optclauses:( AnyLabelOrSome _ (',' _ AnyLabelOrSome _ )* )? '}'
    # {
    #     if optclauses == nil { return []string{}, nil }
    #     clauses := optclauses.([]interface{})
    #     labels := []string{clauses[0].(string)}
    #     for _, next := range clauses[2].([]interface{}) {
    #         labels = append(labels, next.([]interface{})[2].(string))
    #     }
    #     return labels, nil
    # }

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

    EmptyRecord <- "="
    # '=' { return RecordLit{}, nil }
    EmptyRecordType <- ""
    # "" { return RecordType{}, nil }
    RecordTypeOrLiteral ←
        EmptyRecord
        / NonEmptyRecordType
        / NonEmptyRecordLiteral
        / EmptyRecordType

    MoreRecordType ← _ ',' _ f:RecordTypeEntry { @f }
    NonEmptyRecordType ← first:RecordTypeEntry rest:MoreRecordType*
    # {
    #           fields := rest.([]interface{})
    #           content := first.(RecordType)
    #           for _, field := range fields {
    #               for k, v := range field.(RecordType) {
    #                   if _, ok := content[k]; ok {
    #                       return nil, fmt.Errorf("Duplicate field %s in record", k)
    #                   }
    #                   content[k] = v
    #               }
    #           }
    #           return content, nil
    #       }

    RecordTypeEntry ← name:AnyLabelOrSome _ ':' _1 expr:Expression
    # {
    #     return RecordType{name.(string): expr.(Term)}, nil
    # }

    MoreRecordLiteral ← _ ',' _ f:RecordLiteralEntry { @f }
    NonEmptyRecordLiteral ← first:RecordLiteralEntry rest:MoreRecordLiteral*
    #       {
    #           fields := rest.([]interface{})
    #           content := first.(RecordLit)
    #           for _, field := range fields {
    #               for k, v := range field.(RecordLit) {
    #                   if _, ok := content[k]; ok {
    #                       content[k] = Op{
    #                           OpCode: RecordMergeOp,
    #                           L: content[k],
    #                           R: v,
    #                       }
    #                   } else {
    #                       content[k] = v
    #                   }
    #               }
    #           }
    #           return content, nil
    #       }

    RecordLiteralEntry ← name:AnyLabelOrSome val:(RecordLiteralNormalEntry / RecordLiteralPunnedEntry)
    # {
    #     if _, ok := val.([]byte); ok {
    #         // punned entry
    #         return RecordLit{name.(string): Var{Name: name.(string)}}, nil
    #     }
    #     return RecordLit{name.(string): val.(Term)}, nil
    # }

    RecordLiteralNormalEntry ← children:(_ '.' _ AnyLabelOrSome)* _ '=' _ expr:Expression
    # {
    #     rest := expr.(Term)
    #     for i := len(children.([]interface{}))-1; i>=0; i-- {
    #         child := children.([]interface{})[i].([]interface{})[3].(string)
    #         rest = RecordLit{child: rest}
    #     }
    #     return rest, nil
    # }

    RecordLiteralPunnedEntry ← ""

    UnionType ← NonEmptyUnionType / EmptyUnionType

    EmptyUnionType ← ""
    # { return UnionType{}, nil }

    NonEmptyUnionType ← first:UnionTypeEntry rest:(_ '|' _ UnionTypeEntry)*
    # {
    #     alternatives := make(UnionType)
    #     first2 := first.([]interface{})
    #     if first2[1] == nil {
    #         alternatives[first2[0].(string)] = nil
    #     } else {
    #         alternatives[first2[0].(string)] = first2[1].([]interface{})[3].(Term)
    #     }
    #     if rest == nil { return UnionType(alternatives), nil }
    #     for _, alternativeSyntax := range rest.([]interface{}) {
    #         alternative := alternativeSyntax.([]interface{})[3].([]interface{})
    #         name := alternative[0].(string)
    #         if _, ok := alternatives[name]; ok {
    #             return nil, fmt.Errorf("Duplicate alternative %s in union", name)
    #         }
    #         if alternative[1] == nil {
    #             alternatives[name] = nil
    #         } else {
    #             alternatives[name] = alternative[1].([]interface{})[3].(Term)
    #         }
    #     }
    #     return alternatives, nil
    # }

    UnionTypeEntry ← AnyLabelOrSome (_ ':' _1 Expression)?

    MoreList ← ',' _ e:Expression _ { @e }

    NonEmptyListLiteral ← '[' _ (',' _)? first:Expression _ rest:MoreList* ']' { on_NonEmptyList }
    # {
    #           exprs := rest.([]interface{})
    #           content := make(NonEmptyList, len(exprs)+1)
    #           content[0] = first.(Term)
    #           for i, expr := range exprs {
    #               content[i+1] = expr.(Term)
    #           }
    #           return content, nil
    #       }

    EOF ← !.
    """

    def __init__(self, *args, name="<string>", **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)

    def emit(self, node, *args):
        return node(*args, parser=self, offset=self.p_start)

    def on_UnicodeEscape(self, _, digits):
        digits = self.p_flatten(digits)
        return bytearray.fromhex(digits).decode("utf-8")

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
        return self.emit(BlockComment, self.p_flatten(value))

    def on_Reserved(self, result):
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
        return str(Path().joinpath(result))

    def on_HttpRaw(self, result):
        return urlparse(self.p_flatten(result))

    def on_IPv6address(self, result):
        # validate and normalize the address
        return str(IPv6Address(self.p_flatten(result)))

    def on_UrlPath(self, result):
        result = self.p_flatten(result)
        if not result.startswith("/"):
            return "/" + result
        return result

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

    def on_DoubleQuoteLiteral(self, _, chunks):
        """
        '"' chunks:DoubleQuoteChunk* '"'
        """
        suffix = StringIO()
        out_chunks = []
        for chunk in chunks:
            if isinstance(chunk, str):
                suffix.write(chunk)
            elif isinstance(chunk, Term):
                out_chunks.append(self.emit(Chunk, suffix.getvalue(), chunk))
                suffix.seek(0)
                suffix.truncate()
            else:
                assert False
        return self.emit(TextLit, out_chunks, suffix.getvalue())

    def on_NumericDoubleLiteral(self, val):
        return self.emit(DoubleLit, float(self.p_flatten(val)))

    def on_DoubleLiteral(self, _, num=None, inf=None, minf=None, nan=None):
        if num is not self.NoMatch:
            return num
        if inf is not self.NoMatch:
            return self.emit(DoubleLit, float("inf"))
        if minf is not self.NoMatch:
            return self.emit(DoubleLit, float("-inf"))
        if nan is not self.NoMatch:
            return self.emit(DoubleLit, float("nan"))
        assert False

    def on_IntegerLiteral(self, _, n=None, mn=None):
        if n is not self.NoMatch:
            return self.emit(IntegerLit, n[1].value)
        if mn is not self.NoMatch:
            return self.emit(IntegerLit, -(mn[1].value))
        assert False

    def on_BashEnvironmentVariable(self, v):
        return self.emit(EnvVar, self.p_flatten(v))

    def on_LetBinding(self, _, label, a, v):
        if not a:
            a = None
        elif a is self.NoMatch:
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
        return self.emit(Merge, h, u, a=None)

    def on_SomeExpr(self, _, e):
        return self.emit(Some, e)

    def on_toMapExpr(self, _, e):
        return self.emit(ToMap, e)

    def on_EmptyList(self, _, a):
        return self.emit(EmptyList, a)

    def on_ParentPath(self, _, p):
        return self.emit(LocalFile, str(Path("..").joinpath(p)))

    def on_HerePath(self, _, p):
        return self.emit(LocalFile, str(Path(".").joinpath(p)))

    def on_HomePath(self, _, p):
        return self.emit(LocalFile, str(Path("~").joinpath(p)))

    def on_AbsolutePath(self, _, p):
        return self.emit(LocalFile, str(Path("/").joinpath(p)))

    def on_ImportHashed(self, _, i, h=None):
        if not h:
            h = None
        else:
            h = h[1]
        return self.emit(ImportHashed, i, h)

    def on_ImportAsText(self, _, i):
        return self.emit(Import, i, Import.Mode.RawText)

    def on_ImportAsLocation(self, _, i):
        return self.emit(Import, i, Import.Mode.Location)

    def on_SimpleImport(self, _, i):
        return self.emit(Import, i, Import.Mode.Code)

    def on_LambdaExpression(self, _, label, t, body):
        return self.emit(Lambda, label, t, body)

    def on_ForallExpression(self, _, label, t, body):
        return self.emit(Pi, label, t, body)

    def on_ApplicationExpression(self, _, f, rest):
        if not rest:
            return f
        node = App.build(f, *[r[1] for r in rest])
        node.parser=self
        node.offset=self.p_start
        return node

    def on_NonEmptyList(self, _, first, rest):
        return self.emit(NonEmptyList, [first] + rest)

    def on_AnonPiExpression(self, _, o, e):
        return self.emit(Pi, "_", o, e)
