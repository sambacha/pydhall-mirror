from fastidious import Parser
from pydhall.ast.nodes import LineComment, BlockComment, Builtin


class _DhallCharClasses(Parser):
    """
    DoubleQuoteEscaped ←
           '"'
         / '$'
         / '\\'
         / '/'
         / 'b' { return []byte("\b"), nil }
         / 'f' { return []byte("\f"), nil }
         / 'n' { return []byte("\n"), nil }
         / 'r' { return []byte("\r"), nil }
         / 't' { return []byte("\t"), nil }
         / 'u' u:UnicodeEscape { return u, nil }
    UnicodeEscape ←
            HexDig HexDig HexDig HexDig {
                return parseCodepoint(string(c.text))
            }
          / '{' HexDig+ '}' {
                return parseCodepoint(string(c.text[1:len(c.text)-1]))
            }
    DoubleQuoteChar ←
         [\x20-\x21]
       / [\x23-\x5b]
       / [\x5d-\x7f]
       / ValidNonAscii
    EscapedQuotePair ← "'''" { return []byte("''"), nil }
    // \u007b == '{'. This is needed because pigeon gets confused
    // parsing the code block otherwise.
    EscapedInterpolation ← "''${" { return []byte("$\u007b"), nil }
    SingleQuoteChar ←
         [\x20-\x7f]
       / ValidNonAscii
       / '\t'
       / EOL
   """
    __grammar__ = r"""
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

    Digit <- [0-9]

    HexDig <- Digit / [a-f]i

    SimpleLabelFirstChar <- [A-Za-z_]
    SimpleLabelNextChar <- [A-Za-z0-9_/-]
    QuotedLabelChar <- ~"[\x20-\x5f\x61-\x7e]"
    DoubleQuoteEscaped <-
           '"'
         / '$'
         / '\'
         / '/'
         / 'b'
         / 'f' 
         / 'n' 
         / 'r' 
         / 't' 
         / UnicodeEscape 
    UnicodeEscape <- u (
            digits:(HexDig HexDig HexDig HexDig)
          / '{' digits:(HexDig+) '}') 
    DoubleQuoteChar <-
         ~"[\x20-\x21]"
       / ~"[\x23-\x5b]"
       / ~"[\x5d-\x7f]"
       / ValidNonAscii
    """

    def on_UnicodeEscapte(self, _, digits):
        digits = self.p_flatten(digits)
        return bytearray.fromhex(digits).decode("utf-8")

    def on_DoubleQuoteEscape(self, result):
        if result in r'"$\/':
            return result
        else:
            return dict(
                b='\b',
                f='\f',
                n='\n',
                r='\r',
                t='\t').get(result, result)


class _DhallWhiteSpace(_DhallCharClasses):
    __grammar__ = r"""
    EOL <- "\n" / "\r\n" {;"\n"}
    NotEOL <- ~"[\\x20-\\x7f]" / ValidNonAscii / "\t"

    block_comment <- "{-" BlockCommentContinue
    BlockCommentChar <- ~"[\\x20-\\x7f]" / ValidNonAscii / "\t" / EOL
    BlockCommentContinue <- "-}" / block_comment BlockCommentContinue / BlockCommentChar BlockCommentContinue

    line_comment <- "--" content:(NotEOL*) EOL

    WhitespaceChunk <- " " / "\t" / EOL / line_comment / block_comment
    _ <- WhitespaceChunk*
    _1 <- WhitespaceChunk+

    """

    def on_line_comment(self, _, content):
        return LineComment(self.p_flatten(content), offset=self.p_start)

    def on_block_comment(self, value):
        return BlockComment(self.p_flatten(value), offset=self.p_start)


class _DhallKeyword(_DhallCharClasses):
    # Missing <- "missing" !SimpleLabelNextChar { return Missing{}, nil }
    __grammar__ = r"""
    If <- "if"
    Then <- "then"
    Else <- "else"
    Let <- "let"
    In <- "in"
    As <- "as"
    Using <- "using"
    Merge <- "merge"
    Missing <- "missing" !SimpleLabelNextChar
    True_ <- "True"
    False_ <- "False"
    Infinity <- "Infinity"
    NaN <- "NaN"
    Some <- "Some"
    toMap <- "toMap"
    assert_ <- "assert"
    with_ <- "with"
    Forall <- "forall" / "∀"

    Keyword <-
        If / Then / Else
      / Let / In
      / Using / Missing
      / assert_ / As
      / Infinity / NaN
      / Merge / Some / toMap
      / Forall
      / with_

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
    """

    def on_Reserved(self, result):
        return Builtin(self.p_flatten(result), offset=self.p_start)


class _DhallLabel(_DhallKeyword):
    __grammar__ = r"""
    SimpleLabel <-
        Keyword SimpleLabelNextChar+
        / !Keyword SimpleLabelFirstChar SimpleLabelNextChar*
        { p_flatten }
    QuotedLabel <- QuotedLabelChar+ { p_flatten }
    Label <- "`" label:QuotedLabel "`" / label:SimpleLabel { @label }
    NonreservedLabel <-
          &(Reserved SimpleLabelNextChar) label:Label
        / !Reserved label:Label
        { @label }
    AnyLabel <- Label
    AnyLabelOrSome <- AnyLabel / Some { p_flatten }
    """


class _DhallPath(_DhallCharClasses):
    __grammar__ = r"""
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
    """

    def on_Path(self, result):
        from pathlib import Path
        return str(Path().joinpath(result))


class _DhallURL(_DhallPath):
    __grammar__ = r"""
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
    """

    def on_HttpRaw(self, result):
        from urllib.parse import urlparse
        return urlparse(self.p_flatten(result))

    def on_IPv6address(self, result):
        # validate and normalize the address
        from ipaddress import IPv6Address
        return str(IPv6Address(self.p_flatten(result)))

    def on_UrlPath(self, result):
        result = self.p_flatten(result)
        if not result.startswith("/"):
            return "/" + result
        return result


class _DhallTextLiteral():
    """
    DoubleQuoteChunk ←
         Interpolation
       / '\\' e:DoubleQuoteEscaped { return e, nil }
       / DoubleQuoteChar
    DoubleQuoteLiteral ← '"' chunks:DoubleQuoteChunk* '"' {
        var str strings.Builder
        var outChunks Chunks
        for _, chunk := range chunks.([]interface{}) {
            switch e := chunk.(type) {
            case []byte:
                    str.Write(e)
            case Term:
                    outChunks = append(outChunks, Chunk{str.String(), e})
                    str.Reset()
            default:
                    return nil, errors.New("can't happen")
            }
        }
        return TextLit{Chunks: outChunks, Suffix: str.String()}, nil
    }
    SingleQuoteContinue ←
          Interpolation SingleQuoteContinue
        / EscapedQuotePair SingleQuoteContinue
        / EscapedInterpolation SingleQuoteContinue
        / "''"
        / SingleQuoteChar SingleQuoteContinue
    SingleQuoteLiteral ← "''" EOL content:SingleQuoteContinue {
        var str strings.Builder
        var outChunks Chunks
        chunk, ok := content.([]interface{})
        for ; ok; chunk, ok = chunk[1].([]interface{}) {
            switch e := chunk[0].(type) {
            case []byte:
                str.Write(e)
            case Term:
                    outChunks = append(outChunks, Chunk{str.String(), e})
                    str.Reset()
            default:
                return nil, errors.New("unimplemented")
            }
        }
        return removeLeadingCommonIndent(TextLit{Chunks: outChunks, Suffix: str.String()}), nil
    }
    Interpolation ← "${" e:CompleteExpression "}" { return e, nil }
    TextLiteral ← DoubleQuoteLiteral / SingleQuoteLiteral
    """

    __grammar__ = r"""
    DoubleQuoteChunk <-
         Interpolation
       / '\\' e:DoubleQuoteEscaped 
       / DoubleQuoteChar
    DoubleQuoteLiteral <- '"' chunks:DoubleQuoteChunk* '"' 
    SingleQuoteContinue <-
          Interpolation SingleQuoteContinue
        / EscapedQuotePair SingleQuoteContinue
        / EscapedInterpolation SingleQuoteContinue
        / "''"
        / SingleQuoteChar SingleQuoteContinue
    SingleQuoteLiteral <- "''" EOL content:SingleQuoteContinue 
    Interpolation <- "${" e:CompleteExpression "}"
    TextLiteral <- DoubleQuoteLiteral / SingleQuoteLiteral
    """


class Dhall():
    __grammar__ = r"""
        DhallFile ← e:CompleteExpression EOF { return e, nil }

        CompleteExpression ← _ e:Expression _ { return e, nil }

        Optional ← "Optional"
        Text ← "Text"
        List ← "List"
        Location ← "Location"

        Combine ← "/\\" / '∧'
        CombineTypes ← "//\\\\" / '⩓'
        Equivalent ← "===" / '≡'
        Prefer ← "//" / '⫽'
        Lambda ← '\\' / 'λ'
        Arrow ← "->" / '→'
        Complete ← "::"

        Exponent ← "e"i [+-]? Digit+

        NumericDoubleLiteral ← [+-]? Digit+ ( "." Digit+ Exponent? / Exponent) {
              d, err := strconv.ParseFloat(string(c.text), 64)
              if err != nil {
                 return nil, err
              }
              return DoubleLit(d), nil
        }

        DoubleLiteral ← d:NumericDoubleLiteral
          / Infinity { return DoubleLit(math.Inf(1)), nil }
          / "-" Infinity { return DoubleLit(math.Inf(-1)), nil }
          / NaN { return DoubleLit(math.NaN()), nil }

        NaturalLiteral ←
          // Hex or decimal Natural literals
          ("0x" HexDig+ / [1-9] Digit* ) {
              i, err := strconv.ParseInt(string(c.text), 0, 0)
              return NaturalLit(i), err
          }
          // Leading zeros are banned
          / '0' Digit+ { return nil, errors.New("Natural literals cannot have leading zeros") } 
          / '0' { return NaturalLit(0), nil }

        IntegerLiteral ←
            '+' n:NaturalLiteral { return IntegerLit(n.(NaturalLit)), nil }
          / '-' n:NaturalLiteral { return IntegerLit(-(n.(NaturalLit))), nil }

        DeBruijn ← _ '@' _ index:NaturalLiteral { return int(index.(NaturalLit)), nil }

        Variable ← name:NonreservedLabel index:DeBruijn? {
            if index != nil {
                return Var{Name:name.(string), Index:index.(int)}, nil
            } else {
                return Var{Name:name.(string)}, nil
            }
        }

        Identifier ← Variable / Reserved

        Local ← ParentPath / HerePath / HomePath / AbsolutePath

        ParentPath ← ".." p:Path { return LocalFile(path.Join("..", p.(string))), nil }
        HerePath ← '.' p:Path { return LocalFile(p.(string)), nil }
        HomePath ← '~' p:Path { return LocalFile(path.Join("~", p.(string))), nil }
        AbsolutePath ← p:Path { return LocalFile(path.Join("/", p.(string))), nil }
        Http ← u:HttpRaw usingClause:( _ Using _1 ImportExpression)? {
          if usingClause != nil {
            return NewRemoteFile(u.(*url.URL)), errors.New("dhall-golang does not support ❰using❱ clauses")
          }
          return NewRemoteFile(u.(*url.URL)), nil
        }

        Env ← "env:" v:(BashEnvironmentVariable / PosixEnvironmentVariable) { return v, nil }

        BashEnvironmentVariable ← [A-Za-z_][A-Za-z0-9_]* {
          return EnvVar(string(c.text)), nil
        }

        PosixEnvironmentVariable ← '"' v:PosixEnvironmentVariableContent '"' {
          return v, nil
        }

        PosixEnvironmentVariableContent ← v:PosixEnvironmentVariableCharacter+ {
          var b strings.Builder
          for _, c := range v.([]interface{}) {
            _, err := b.Write(c.([]byte))
            if err != nil { return nil, err }
          }
          return EnvVar(b.String()), nil
        }

        PosixEnvironmentVariableCharacter ←
              `\"` { return []byte{0x22}, nil }
            / `\\` { return []byte{0x5c}, nil }
            / `\a` { return []byte{0x07}, nil }
            / `\b` { return []byte{0x08}, nil }
            / `\f` { return []byte{0x0c}, nil }
            / `\n` { return []byte{0x0a}, nil }
            / `\r` { return []byte{0x0d}, nil }
            / `\t` { return []byte{0x09}, nil }
            / `\v` { return []byte{0x0b}, nil }
            / [\x20-\x21]
            / [\x23-\x3c]
            / [\x3e-\x5b]
            / [\x5d-\x7e]

        ImportType ← Missing / Local / Http / Env

        // ugh, there seems to be no fixed-repetition operator in pigeon :(
        HashValue = HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                    HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                    HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                    HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                    HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                    HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                    HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig
                    HexDig HexDig HexDig HexDig HexDig HexDig HexDig HexDig {
            out := make([]byte, sha256.Size)
            _, err := hex.Decode(out, c.text)
            if err != nil { return nil, err }
            return out, nil
        }
        Hash = "sha256:" val:HashValue { return append([]byte{0x12,0x20}, val.([]byte)...), nil }

        ImportHashed ← i:ImportType h:(_1 Hash)? {
            out := ImportHashed{Fetchable: i.(Fetchable)}
            if h != nil {
                out.Hash = h.([]interface{})[1].([]byte)
            }
            return out, nil
        }

        Import ← i:ImportHashed _ As _1 Text { return Import{ImportHashed: i.(ImportHashed), ImportMode: RawText}, nil }
               / i:ImportHashed _ As _1 Location { return Import{ImportHashed: i.(ImportHashed), ImportMode: Location}, nil }
               / i:ImportHashed { return Import{ImportHashed: i.(ImportHashed), ImportMode: Code}, nil }


        LetBinding ← Let _1 label:NonreservedLabel _ a:(Annotation _)?
                    '=' _ v:Expression _ {
            if a != nil {
                return Binding{
                    Variable: label.(string),
                    Annotation: a.([]interface{})[0].(Term),
                    Value: v.(Term),
                }, nil
            } else {
                return Binding{
                    Variable: label.(string),
                    Value: v.(Term),
                }, nil
            }
        }

        Expression ←
              Lambda _ '(' _ label:NonreservedLabel _ ':' _1 t:Expression _ ')' _ Arrow _ body:Expression {
                  return Lambda{Label:label.(string), Type:t.(Term), Body: body.(Term)}, nil
              }
            / If _1 cond:Expression _ Then _1 t:Expression _ Else _1 f:Expression {
                  return If{cond.(Term),t.(Term),f.(Term)},nil
              }
            / bindings:LetBinding+ In _1 b:Expression {
                bs := make([]Binding, len(bindings.([]interface{})))
                for i, binding := range bindings.([]interface{}) {
                    bs[i] = binding.(Binding)
                }
                return NewLet(b.(Term), bs...), nil
              }
            / Forall _ '(' _ label:NonreservedLabel _ ':' _1 t:Expression _ ')' _ Arrow _ body:Expression {
                  return Pi{Label:label.(string), Type:t.(Term), Body: body.(Term)}, nil
              }
            / o:OperatorExpression _ Arrow _ e:Expression { return NewAnonPi(o.(Term),e.(Term)), nil }
            / Merge _1 h:ImportExpression _1 u:ImportExpression _ ':' _1 a:ApplicationExpression {
                  return Merge{Handler:h.(Term), Union:u.(Term), Annotation:a.(Term)}, nil
              }
            / EmptyList
            / toMap _1 e:ImportExpression _ ':' _1 t:ApplicationExpression { return ToMap{e.(Term), t.(Term)}, nil }
            / assert _ ':' _1 a:Expression { return Assert{Annotation: a.(Term)}, nil }
            / AnnotatedExpression

        Annotation ← ':' _1 a:Expression { return a, nil }

        AnnotatedExpression ←
        e:OperatorExpression a:(_ Annotation)? {
                if a == nil { return e, nil }
                return Annot{e.(Term), a.([]interface{})[1].(Term)}, nil
            }

        EmptyList ← '[' _ (',' _)? ']' _ ':' _1 a:ApplicationExpression {
                  return EmptyList{a.(Term)},nil
        }

        OperatorExpression ← ImportAltExpression

        ImportAltExpression    ← first:OrExpression           rest:(_ "?" _1 OrExpression)*
          {return parseOperator(ImportAltOp, first, rest), nil}
        OrExpression           ← first:PlusExpression         rest:(_ "||" _ PlusExpression)*
          {return parseOperator(OrOp, first, rest), nil}
        PlusExpression         ← first:TextAppendExpression   rest:(_ '+' _1 e:TextAppendExpression)*
          {return parseOperator(PlusOp, first, rest), nil}
        TextAppendExpression   ← first:ListAppendExpression   rest:(_ "++" _ e:ListAppendExpression)*
          {return parseOperator(TextAppendOp, first, rest), nil}
        ListAppendExpression   ← first:AndExpression          rest:(_ '#' _ e:AndExpression)*
          {return parseOperator(ListAppendOp, first, rest), nil}
        AndExpression          ← first:CombineExpression      rest:(_ "&&" _ e:CombineExpression)*
          {return parseOperator(AndOp, first, rest), nil}
        CombineExpression      ← first:PreferExpression       rest:(_ Combine _ e:PreferExpression)*
          {return parseOperator(RecordMergeOp, first, rest), nil}
        PreferExpression       ← first:CombineTypesExpression rest:(_ Prefer _ e:CombineTypesExpression)*
          {return parseOperator(RightBiasedRecordMergeOp, first, rest), nil}
        CombineTypesExpression ← first:TimesExpression        rest:(_ CombineTypes _ e:TimesExpression)*
          {return parseOperator(RecordTypeMergeOp, first, rest), nil}
        TimesExpression        ← first:EqualExpression        rest:(_ '*' _ e:EqualExpression)*
          {return parseOperator(TimesOp, first, rest), nil}
        EqualExpression        ← first:NotEqualExpression     rest:(_ "==" _ e:NotEqualExpression)*
          {return parseOperator(EqOp, first, rest), nil}
        NotEqualExpression     ← first:EquivalentExpression   rest:(_ "!=" _ e:EquivalentExpression)*
          {return parseOperator(NeOp, first, rest), nil}
        EquivalentExpression   ← first:WithExpression         rest:(_ Equivalent _ e:WithExpression)*
          {return parseOperator(EquivOp, first, rest), nil}
        WithExpression         ← first:ApplicationExpression  rest:(_1 with _1 FieldPath _ '=' _ e:ApplicationExpression)*
          {
            out := first.(Term)
            if rest == nil { return out, nil }
            for _, b := range rest.([]interface{}) {
                path := b.([]interface{})[3].([]string)
                value := b.([]interface{})[7].(Term)
                out = desugarWith(out, path, value)
            }
            return out, nil
          }

        FieldPath ← first:AnyLabelOrSome rest:(_ '.' _ AnyLabelOrSome)* {
          out := []string{first.(string)}
          if rest == nil { return out, nil }
          for _, b := range rest.([]interface{}) {
            nextField := b.([]interface{})[3].(string)
            out = append(out, nextField)
          }
          return out, nil
        }

        ApplicationExpression ← f:FirstApplicationExpression rest:(_1 ImportExpression)* {
                  e := f.(Term)
                  if rest == nil { return e, nil }
                  for _, arg := range rest.([]interface{}) {
                      e = Apply(e, arg.([]interface{})[1].(Term))
                  }
                  return e,nil
              }

        FirstApplicationExpression ←
               Merge _1 h:ImportExpression _1 u:ImportExpression {
                     return Merge{Handler:h.(Term), Union:u.(Term)}, nil
                  }
             / Some _1 e:ImportExpression { return Some{e.(Term)}, nil }
             / toMap _1 e:ImportExpression { return ToMap{Record: e.(Term)}, nil }
             / ImportExpression

        ImportExpression ← Import / CompletionExpression

        CompletionExpression ← a:SelectorExpression b:(_ Complete _ SelectorExpression)? {
            if b == nil {
                return a, nil
            }
            return Op{OpCode:CompleteOp ,L:a.(Term),R:b.([]interface{})[3].(Term)},nil
        }

        SelectorExpression ← e:PrimitiveExpression ls:(_ '.' _ Selector)* {
            expr := e.(Term)
            labels := ls.([]interface{})
            for _, labelSelector := range labels {
                selectorIface := labelSelector.([]interface{})[3]
                switch selector := selectorIface.(type) {
                    case string:
                        expr = Field{expr, selector}
                    case []string:
                        expr = Project{expr, selector}
                    case Term:
                        expr = ProjectType{expr, selector}
                    default:
                        return nil, errors.New("unimplemented")
                }
            }
            return expr, nil
        }

        Selector ← AnyLabel / Labels / TypeSelector

        Labels ← '{' _ optclauses:( AnyLabelOrSome _ (',' _ AnyLabelOrSome _ )* )? '}' {
            if optclauses == nil { return []string{}, nil }
            clauses := optclauses.([]interface{})
            labels := []string{clauses[0].(string)}
            for _, next := range clauses[2].([]interface{}) {
                labels = append(labels, next.([]interface{})[2].(string))
            }
            return labels, nil
        }

        TypeSelector ← '(' _ e:Expression _ ')' { return e, nil }

        PrimitiveExpression ←
              DoubleLiteral
            / NaturalLiteral
            / IntegerLiteral
            / TextLiteral
            / '{' _ (',' _)? r:RecordTypeOrLiteral _ '}' { return r, nil }
            / '<' _ ('|' _)? u:UnionType _ '>' { return u, nil }
            / NonEmptyListLiteral
            / Identifier
            / '(' _ ('|' _)? e:Expression _ ')' { return e, nil }

        RecordTypeOrLiteral ←
              '=' { return RecordLit{}, nil }
            / NonEmptyRecordType
            / NonEmptyRecordLiteral
            / "" { return RecordType{}, nil }

        MoreRecordType ← _ ',' _ f:RecordTypeEntry {return f, nil}
        NonEmptyRecordType ←
              first:RecordTypeEntry rest:MoreRecordType* {
                  fields := rest.([]interface{})
                  content := first.(RecordType)
                  for _, field := range fields {
                      for k, v := range field.(RecordType) {
                          if _, ok := content[k]; ok {
                              return nil, fmt.Errorf("Duplicate field %s in record", k)
                          }
                          content[k] = v
                      }
                  }
                  return content, nil
              }

        RecordTypeEntry ← name:AnyLabelOrSome _ ':' _1 expr:Expression {
            return RecordType{name.(string): expr.(Term)}, nil
        }

        MoreRecordLiteral ← _ ',' _ f:RecordLiteralEntry {return f, nil}
        NonEmptyRecordLiteral ←
              first:RecordLiteralEntry rest:MoreRecordLiteral* {
                  fields := rest.([]interface{})
                  content := first.(RecordLit)
                  for _, field := range fields {
                      for k, v := range field.(RecordLit) {
                          if _, ok := content[k]; ok {
                              content[k] = Op{
                                  OpCode: RecordMergeOp,
                                  L: content[k],
                                  R: v,
                              }
                          } else {
                              content[k] = v
                          }
                      }
                  }
                  return content, nil
              }

        RecordLiteralEntry ← name:AnyLabelOrSome val:(RecordLiteralNormalEntry / RecordLiteralPunnedEntry) {
            if _, ok := val.([]byte); ok {
                // punned entry
                return RecordLit{name.(string): Var{Name: name.(string)}}, nil
            }
            return RecordLit{name.(string): val.(Term)}, nil
        }

        RecordLiteralNormalEntry ← children:(_ '.' _ AnyLabelOrSome)* _ '=' _ expr:Expression {
            rest := expr.(Term)
            for i := len(children.([]interface{}))-1; i>=0; i-- {
                child := children.([]interface{})[i].([]interface{})[3].(string)
                rest = RecordLit{child: rest}
            }
            return rest, nil
        }

        RecordLiteralPunnedEntry ← ""

        UnionType ← NonEmptyUnionType / EmptyUnionType

        EmptyUnionType ← "" { return UnionType{}, nil }

        NonEmptyUnionType ← first:UnionTypeEntry rest:(_ '|' _ UnionTypeEntry)* {
            alternatives := make(UnionType)
            first2 := first.([]interface{})
            if first2[1] == nil {
                alternatives[first2[0].(string)] = nil
            } else {
                alternatives[first2[0].(string)] = first2[1].([]interface{})[3].(Term)
            }
            if rest == nil { return UnionType(alternatives), nil }
            for _, alternativeSyntax := range rest.([]interface{}) {
                alternative := alternativeSyntax.([]interface{})[3].([]interface{})
                name := alternative[0].(string)
                if _, ok := alternatives[name]; ok {
                    return nil, fmt.Errorf("Duplicate alternative %s in union", name)
                }

                if alternative[1] == nil {
                    alternatives[name] = nil
                } else {
                    alternatives[name] = alternative[1].([]interface{})[3].(Term)
                }
            }
            return alternatives, nil
        }

        UnionTypeEntry ← AnyLabelOrSome (_ ':' _1 Expression)?

        MoreList ← ',' _ e:Expression _ {return e, nil}

        NonEmptyListLiteral ←
              '[' _ (',' _)? first:Expression _ rest:MoreList* ']' {
                  exprs := rest.([]interface{})
                  content := make(NonEmptyList, len(exprs)+1)
                  content[0] = first.(Term)
                  for i, expr := range exprs {
                      content[i+1] = expr.(Term)
                  }
                  return content, nil
              }

        EOF ← !.
        """
