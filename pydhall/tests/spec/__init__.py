FAILURES = [
    # alpha normalization
    "dhall-lang/tests/alpha-normalization/success/regression/preludeBoolFold", # AttributeError: 'NoneType' object has no attribute 'quote'
    "dhall-lang/tests/alpha-normalization/success/unit/FunctionNestedBindingX", # NotImplementedError: Natural.eval
    "dhall-lang/tests/alpha-normalization/success/unit/FunctionNestedBindingXX", # NotImplementedError: AndOp.eval
    "dhall-lang/tests/alpha-normalization/success/unit/FunctionNestedBindingXY", # NotImplementedError: AndOp.eval
    "dhall-lang/tests/alpha-normalization/success/unit/FunctionTypeBindingUnderscore", # parsing error on A
    "dhall-lang/tests/alpha-normalization/success/unit/FunctionTypeBindingX", # parsing on B
    "dhall-lang/tests/alpha-normalization/success/unit/FunctionTypeNestedBindingX", # parsing on A

    # parser
    "dhall-lang/tests/parser/success/quotedLabel",
    "dhall-lang/tests/parser/success/whitespaceBuffet",
    "dhall-lang/tests/parser/success/toMap",
    "dhall-lang/tests/parser/success/largeExpression",
    "dhall-lang/tests/parser/success/collectionImportType",
    "dhall-lang/tests/parser/success/quotedBoundVariable",
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
    "dhall-lang/tests/parser/success/unit/ToMap",
    "dhall-lang/tests/parser/success/unit/FunctionTypeArrow",
    "dhall-lang/tests/parser/success/unit/Assert",
    "dhall-lang/tests/parser/success/unit/MergeXYZ",
    "dhall-lang/tests/parser/success/unit/AssertPrecedence",
    "dhall-lang/tests/parser/success/unit/ToMapAnnot",
    "dhall-lang/tests/parser/success/unit/Merge",
    "dhall-lang/tests/parser/success/unit/MergeParenAnnotation",
    "dhall-lang/tests/parser/success/unit/MergeAnnotationPrecedence",
    "dhall-lang/tests/parser/success/unit/AssertEquivalenceUnicode",
    "dhall-lang/tests/parser/success/unit/Completion",
    "dhall-lang/tests/parser/success/unit/AssertEquivalence",
    "dhall-lang/tests/parser/success/unit/WithPrecedence3",
    "dhall-lang/tests/parser/success/unit/operators/PrecedenceRecord",
    "dhall-lang/tests/parser/success/unit/operators/RightBiasedRecordMergeUnicodeAssoc",
    "dhall-lang/tests/parser/success/unit/operators/RightBiasedRecordMergeAssoc",
    "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordTypeMerge",
    "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordMergeAssoc",
    "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordMerge",
    "dhall-lang/tests/parser/success/unit/operators/RightBiasedRecordMerge",
    "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordTypeMergeAssoc",
    "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordMergeUnicodeAssoc",
    "dhall-lang/tests/parser/success/unit/operators/RecursiveRecordTypeMergeUnicodeAssoc",
    "dhall-lang/tests/parser/success/merge",
    "dhall-lang/tests/parser/success/text/nonAssignedUnicode",
    "dhall-lang/tests/parser/success/text/escapedDoubleQuotedString",
    "dhall-lang/tests/parser/success/functionType",
    "dhall-lang/tests/parser/success/quotedUnionLabel",
    "dhall-lang/tests/parser/success/builtinNameAsField",
    "dhall-lang/tests/parser/success/quotedRecordLabel",
    "dhall-lang/tests/parser/success/usingToMap",

]

