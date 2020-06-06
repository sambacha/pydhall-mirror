FAILURES = [
    # Beta-norm
    "dhall-lang/tests/normalization/success/remoteSystems",
    # "dhall-lang/tests/normalization/success/WithRecordValue",

    # parser
    # easy
    # "dhall-lang/tests/parser/success/whitespaceBuffet",

    # "dhall-lang/tests/parser/success/toMap",
    "dhall-lang/tests/parser/success/largeExpression",
    "dhall-lang/tests/parser/success/collectionImportType",
    # "dhall-lang/tests/parser/success/quotedBoundVariable",
    "dhall-lang/tests/parser/success/nestedBlockComment",
    "dhall-lang/tests/parser/success/unit/import/pathHome",
    "dhall-lang/tests/parser/success/unit/import/pathParent",
    "dhall-lang/tests/parser/success/unit/import/hash",
    "dhall-lang/tests/parser/success/unit/import/quotedPaths",
    "dhall-lang/tests/parser/success/unit/import/environmentVariablePosix",
    "dhall-lang/tests/parser/success/unit/import/pathTerminationUnion",
    "dhall-lang/tests/parser/success/unit/import/AsLocationAbsolute",
    "dhall-lang/tests/parser/success/unit/import/AsLocationLocal",
    "dhall-lang/tests/parser/success/unit/import/pathTerminationList",
    "dhall-lang/tests/parser/success/unit/import/AsLocationHash",
    "dhall-lang/tests/parser/success/unit/import/pathTerminationLambda",
    "dhall-lang/tests/parser/success/unit/import/pathTerminationRecord",
    "dhall-lang/tests/parser/success/unit/import/unicodePaths",
    "dhall-lang/tests/parser/success/unit/import/inlineUsing",
    "dhall-lang/tests/parser/success/unit/import/pathAbsolute",
    "dhall-lang/tests/parser/success/unit/import/ImportAsNoSpace",
    "dhall-lang/tests/parser/success/unit/import/pathHere",
    "dhall-lang/tests/parser/success/unit/MergeAnnotation",
    # "dhall-lang/tests/parser/success/unit/ToMap",
    "dhall-lang/tests/parser/success/unit/Assert",
    "dhall-lang/tests/parser/success/unit/MergeXYZ",
    "dhall-lang/tests/parser/success/unit/AssertPrecedence",
    "dhall-lang/tests/parser/success/unit/ToMapAnnot",
    "dhall-lang/tests/parser/success/unit/Merge",
    "dhall-lang/tests/parser/success/unit/MergeParenAnnotation",
    "dhall-lang/tests/parser/success/unit/MergeAnnotationPrecedence",
    "dhall-lang/tests/parser/success/unit/AssertEquivalenceUnicode",
    # "dhall-lang/tests/parser/success/unit/Completion",
    "dhall-lang/tests/parser/success/unit/AssertEquivalence",
    "dhall-lang/tests/parser/success/unit/WithPrecedence3",
    "dhall-lang/tests/parser/success/unit/operators/PrecedenceRecord",
    # "dhall-lang/tests/parser/success/unit/operators/RightBiasedRecordMergeUnicodeAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/RightBiasedRecordMergeAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordTypeMerge",
    # "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordMergeAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordMerge",
    # "dhall-lang/tests/parser/success/unit/operators/RightBiasedRecordMerge",
    # "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordTypeMergeAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordMergeUnicodeAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordTypeMergeUnicodeAssoc",
    "dhall-lang/tests/parser/success/merge",
    "dhall-lang/tests/parser/success/text/nonAssignedUnicode",
    "dhall-lang/tests/parser/success/text/escapedDoubleQuotedString",
    # "dhall-lang/tests/parser/success/functionType",
    "dhall-lang/tests/parser/success/quotedUnionLabel",
    "dhall-lang/tests/parser/success/builtinNameAsField",
    "dhall-lang/tests/parser/success/quotedRecordLabel",
    "dhall-lang/tests/parser/success/usingToMap",
    "dhall-lang/tests/parser/success/leadingTabs",
    "dhall-lang/tests/parser/success/missingInParentheses",
    # "dhall-lang/tests/parser/success/builtins",
    # "dhall-lang/tests/parser/success/reservedPrefix",
    # "dhall-lang/tests/parser/success/forall",
    # "dhall-lang/tests/parser/success/record",
    # "dhall-lang/tests/parser/success/label",
    "dhall-lang/tests/parser/success/fields",
    "dhall-lang/tests/parser/success/recordProjectionByExpression",
    "dhall-lang/tests/parser/success/leadingSeparators",
    # "dhall-lang/tests/parser/success/unit/DoubleLit16bit",
    # "dhall-lang/tests/parser/success/unit/LetMulti",
    # "dhall-lang/tests/parser/success/unit/FunctionApplicationMultipleArgs",
    # "dhall-lang/tests/parser/success/unit/EmptyRecordLiteral",
    "dhall-lang/tests/parser/success/unit/import/HeadersHashPrecedence",
    "dhall-lang/tests/parser/success/unit/import/asText",
    "dhall-lang/tests/parser/success/unit/import/AsLocationRemote",
    "dhall-lang/tests/parser/success/unit/import/urls/basicHttp",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv6withipv4",
    "dhall-lang/tests/parser/success/unit/import/urls/basicHttps",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv4",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv6short",
    "dhall-lang/tests/parser/success/unit/import/urls/port",
    "dhall-lang/tests/parser/success/unit/import/urls/userinfo",
    "dhall-lang/tests/parser/success/unit/import/urls/potPourri",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv6verylong",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv4upperoctets",
    "dhall-lang/tests/parser/success/unit/import/urls/emptyQuery",
    "dhall-lang/tests/parser/success/unit/import/urls/emptyPathSegment",
    "dhall-lang/tests/parser/success/unit/import/urls/emptyPath1",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv6medium",
    "dhall-lang/tests/parser/success/unit/import/urls/escapedQuery",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv6long",
    "dhall-lang/tests/parser/success/unit/import/urls/quotedPathFakeUrlEncode",
    "dhall-lang/tests/parser/success/unit/import/urls/emptyPath0",
    "dhall-lang/tests/parser/success/unit/import/urls/escapedPath",
    "dhall-lang/tests/parser/success/unit/import/urls/fragmentParsesAsListAppend",
    "dhall-lang/tests/parser/success/unit/import/importAlt",
    "dhall-lang/tests/parser/success/unit/import/Missing",
    "dhall-lang/tests/parser/success/unit/import/HeadersInteriorHash",
    "dhall-lang/tests/parser/success/unit/import/AsLocationMissing",
    "dhall-lang/tests/parser/success/unit/import/Headers",
    "dhall-lang/tests/parser/success/unit/import/AsLocationEnv",
    "dhall-lang/tests/parser/success/unit/import/environmentVariableBash",
    "dhall-lang/tests/parser/success/unit/import/HeadersDoubleHashPrecedence",
    "dhall-lang/tests/parser/success/unit/import/HeadersDoubleHash",
    "dhall-lang/tests/parser/success/unit/WithMultiple",
    "dhall-lang/tests/parser/success/unit/Field",
    # "dhall-lang/tests/parser/success/unit/FunctionTypePiNested",
    # "dhall-lang/tests/parser/success/unit/RecordLitPunMixed",
    # "dhall-lang/tests/parser/success/unit/RecordLitPunSome",
    # "dhall-lang/tests/parser/success/unit/DoubleLitNegative",
    # "dhall-lang/tests/parser/success/unit/RecordType",
    "dhall-lang/tests/parser/success/unit/UnionTypeXTY",
    # "dhall-lang/tests/parser/success/unit/FunctionTypePi",
    # "dhall-lang/tests/parser/success/unit/SomeX",
    # "dhall-lang/tests/parser/success/unit/ListLitEmpty1",
    "dhall-lang/tests/parser/success/unit/UnionTypeXY",
    "dhall-lang/tests/parser/success/unit/UnionTypeSome",
    # "dhall-lang/tests/parser/success/unit/DoubleLit64bit",
    "dhall-lang/tests/parser/success/unit/Projection",
    # "dhall-lang/tests/parser/success/unit/SomeXYZ",
    "dhall-lang/tests/parser/success/unit/With",
    "dhall-lang/tests/parser/success/unit/UnionTypeEmpty",
    # "dhall-lang/tests/parser/success/unit/RecordLitDottedEscape",
    "dhall-lang/tests/parser/success/whitespaceBuffet",
    # "dhall-lang/tests/parser/success/unit/ForallNested",
    "dhall-lang/tests/parser/success/unit/UnionTypeX",
    # "dhall-lang/tests/parser/success/unit/FunctionTypePiUnicode",
    # "dhall-lang/tests/parser/success/unit/ListLitEmpty2",
    "dhall-lang/tests/parser/success/unit/WithPrecedence2",
    # "dhall-lang/tests/parser/success/unit/RecordLitPunDuplicate",
    # "dhall-lang/tests/parser/success/unit/ListLitEmptyPrecedence",
    # "dhall-lang/tests/parser/success/unit/DoubleLitSecretelyInt",
    "dhall-lang/tests/parser/success/unit/RecordProjectFields",
    # "dhall-lang/tests/parser/success/unit/DoubleLitNegZero",
    # "dhall-lang/tests/parser/success/unit/RecordLitPun",
    # "dhall-lang/tests/parser/success/unit/RecordLitSome",
    "dhall-lang/tests/parser/success/unit/UnionTypeXYT",
    # "dhall-lang/tests/parser/success/unit/LetNested",
    # "dhall-lang/tests/parser/success/unit/DoubleLitZero",
    # "dhall-lang/tests/parser/success/unit/LetNoAnnot",
    # "dhall-lang/tests/parser/success/unit/DoubleLitExponentNoDot",
    "dhall-lang/tests/parser/success/unit/DoubleLitNegInfinity",
    # "dhall-lang/tests/parser/success/unit/DoubleLitExponent",
    "dhall-lang/tests/parser/success/unit/SelectionSome",
    "dhall-lang/tests/parser/success/unit/FieldBuiltinName",
    # "dhall-lang/tests/parser/success/unit/LetAnnot",
    # "dhall-lang/tests/parser/success/unit/Let",
    # "dhall-lang/tests/parser/success/unit/DoubleLitInfinity",
    # "dhall-lang/tests/parser/success/unit/DoubleLitExponentNegative",
    # "dhall-lang/tests/parser/success/unit/RecordLit",
    # "dhall-lang/tests/parser/success/unit/Annotation",
    # "dhall-lang/tests/parser/success/unit/ListLitNonEmptyAnnotated",
    "dhall-lang/tests/parser/success/unit/DoubleLitNaN",
    # "dhall-lang/tests/parser/success/unit/ifThenElse",
    "dhall-lang/tests/parser/success/unit/WithPrecedence1",
    # "dhall-lang/tests/parser/success/unit/RecordLitNixLike",
    "dhall-lang/tests/parser/success/unit/RecordProjectionByType",
    "dhall-lang/tests/parser/success/unit/UnionTypeXTYU",
    # "dhall-lang/tests/parser/success/unit/RecordLitDotted",
    "dhall-lang/tests/parser/success/unit/FieldQuoted",
    # "dhall-lang/tests/parser/success/unit/Forall",
    # "dhall-lang/tests/parser/success/unit/DoubleLit32bit",
    "dhall-lang/tests/parser/success/unit/RecordProjectionByTypeEmpty",
    "dhall-lang/tests/parser/success/unit/RecordFieldAccess",
    # "dhall-lang/tests/parser/success/unit/RecordLitDuplicates",
    # "dhall-lang/tests/parser/success/unit/operators/PrecedenceEquivalence",
    # "dhall-lang/tests/parser/success/unit/operators/PrecedenceBool",
    # "dhall-lang/tests/parser/success/unit/operators/NaturalPlus",
    # "dhall-lang/tests/parser/success/unit/operators/Equivalence",
    # "dhall-lang/tests/parser/success/unit/operators/BoolNEAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/ImportAlt",
    # "dhall-lang/tests/parser/success/unit/operators/ListAppendAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/BoolOr",
    # "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordTypeMergeUnicode",
    # "dhall-lang/tests/parser/success/unit/operators/NaturalTimesAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/BoolEQAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/ListAppend",
    # "dhall-lang/tests/parser/success/unit/operators/TextAppend",
    # "dhall-lang/tests/parser/success/unit/operators/RightBiasedRecordMergeUnicode",
    # "dhall-lang/tests/parser/success/unit/operators/ImportAltAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/BoolAndAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/BoolEQ",
    # "dhall-lang/tests/parser/success/unit/operators/BoolOrAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/NaturalPlusAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/TextAppendAssoc",
    # "dhall-lang/tests/parser/success/unit/operators/NaturalTimes",
    # "dhall-lang/tests/parser/success/unit/operators/BoolAnd",
    # "dhall-lang/tests/parser/success/unit/operators/BoolNE",
    # "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordMergeUnicode",
    # "dhall-lang/tests/parser/success/unit/operators/PrecedenceNat",
    # "dhall-lang/tests/parser/success/unit/DoubleLitPositive",
    # "dhall-lang/tests/parser/success/operators",
    # "dhall-lang/tests/parser/success/annotations",
    "dhall-lang/tests/parser/success/text/preserveComment",
    "dhall-lang/tests/parser/success/text/multilineBlankLine",
    "dhall-lang/tests/parser/success/text/interpolatedDoubleQuotedString",
    "dhall-lang/tests/parser/success/text/multilineMismatchedLeadingWhitespace",
    "dhall-lang/tests/parser/success/text/escapedSingleQuotedString",
    "dhall-lang/tests/parser/success/text/escape",
    # "dhall-lang/tests/parser/success/text/unicodeDoubleQuotedString",
    "dhall-lang/tests/parser/success/text/multilineIndentedAndAligned",
    "dhall-lang/tests/parser/success/text/twoLines",
    "dhall-lang/tests/parser/success/text/singleQuotedString",
    "dhall-lang/tests/parser/success/text/interpolatedSingleQuotedString",
    # "dhall-lang/tests/parser/success/text/doubleQuotedString",
    "dhall-lang/tests/parser/success/text/interpolation",
    "dhall-lang/tests/parser/success/text/interiorIndent",
    "dhall-lang/tests/parser/success/text/singleQuoteConcat",
    "dhall-lang/tests/parser/success/text/singleLine",
    # "dhall-lang/tests/parser/success/text/dollarSign",
    "dhall-lang/tests/parser/success/text/template",
    "dhall-lang/tests/parser/success/text/multilineTabs",
    "dhall-lang/tests/parser/success/text/interesting",
    "dhall-lang/tests/parser/success/text/multilineBlankLineCrlf",
    "dhall-lang/tests/parser/success/text/multilineCorruptedLeadingWhitespace",
    # "dhall-lang/tests/parser/success/list",
    # "dhall-lang/tests/parser/success/hexadecimal",

    ## types
    # "dhall-lang/tests/type-inference/success/unit/RecordLitDuplicateFieldsAbstract",
]
