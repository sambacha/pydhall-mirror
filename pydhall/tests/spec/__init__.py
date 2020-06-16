FAILURES = [
    # Various parser issues
    "dhall-lang/tests/parser/success/unit/import/environmentVariablePosix",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv6withipv4",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv6verylong",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv6long",
    "dhall-lang/tests/parser/success/unit/import/urls/quotedPathFakeUrlEncode",
    "dhall-lang/tests/parser/success/quotedRecordLabel",
    "dhall-lang/tests/parser/success/text/multilineCorruptedLeadingWhitespace",
    "dhall-lang/tests/parser/success/unit/import/quotedPaths",

    # TODO: those fail but with another error than a parser error. should investigate.
    "dhall-lang/tests/parser/failure/surrogatePairUnbraced",
    "dhall-lang/tests/parser/failure/nonCharacter",
    "dhall-lang/tests/parser/failure/incompleteIf",
    "dhall-lang/tests/parser/failure/nonCharacterUnbraced",
    "dhall-lang/tests/parser/failure/unit/ListLitEmptyMissingAnnotation",
    "dhall-lang/tests/parser/failure/unit/MergeOneArgument",
    "dhall-lang/tests/parser/failure/unit/SomeAlone",
    "dhall-lang/tests/parser/failure/unit/MergeAlone",
    "dhall-lang/tests/parser/failure/unit/AssertNoAnnotation",
    "dhall-lang/tests/parser/failure/nonUtf8",


    # Unicode
    "dhall-lang/tests/semantic-hash/success/prelude/Text/show/0",
    "dhall-lang/tests/semantic-hash/success/prelude/Text/show/1",
    "dhall-lang/tests/normalization/success/unit/TextShowAllEscapes",
    "dhall-lang/tests/type-inference/success/prelude",
    # require fixes in fastidious
    "dhall-lang/tests/parser/success/text/nonAssignedUnicode",
    "dhall-lang/tests/parser/success/text/escapedDoubleQuotedString",

    # Double
    # turns out that -0.0 ≠ 0.0 :/ figure how to handle that
    "dhall-lang/tests/type-inference/failure/unit/AssertDoubleZeros",
    "dhall-lang/tests/semantic-hash/success/simple/integerToDouble",
    # TODO: should fail but don't
    "dhall-lang/tests/parser/failure/doubleBoundsPos",
    "dhall-lang/tests/parser/failure/doubleBoundsNeg",

    # Cache


    ## Type inference
    # Failures
    # TODO: Easy stuff : Missing error messages
    "dhall-lang/tests/type-inference/failure/unit/RecordSelectionTypeNotUnionType",
    "dhall-lang/tests/type-inference/failure/unit/MergeHandlerNotMatchAlternativeType",
    "dhall-lang/tests/type-inference/failure/unit/UnionConstructorFieldNotPresent",
    "dhall-lang/tests/type-inference/failure/unit/RecordSelectionNotRecord",
    "dhall-lang/tests/type-inference/failure/unit/MergeHandlersWithDifferentType",
    "dhall-lang/tests/type-inference/failure/unit/RecordProjectionDuplicateFields",
    "dhall-lang/tests/type-inference/failure/unit/UnionTypeDuplicateVariants2",
    "dhall-lang/tests/type-inference/failure/unit/UnionTypeDuplicateVariants1",
    "dhall-lang/tests/type-inference/failure/unit/RecordTypeDuplicateFields",


    ## imports
    # "dhall-lang/tests/import/success/unit/AlternativeHashMismatch",

    # Low priority

    # urllib doesn't make the difference between /foo? and /foo
    # should be implemented in the parser and adding an attribute
    # to RemoteFile.
    "dhall-lang/tests/parser/success/unit/import/urls/emptyQuery",
    # either urllib doesn't allow this, either we missed something in
    # the standard. Sould not hurt in the wild.
    "dhall-lang/tests/parser/success/unit/import/urls/emptyPathSegment",


    # WONT FIX.

    # Using is not implemented. The feature may be dropped from the standard,
    # at some point.
    "dhall-lang/tests/parser/success/unit/import/HeadersInteriorHash",
    "dhall-lang/tests/parser/success/unit/import/HeadersDoubleHashPrecedence",
    "dhall-lang/tests/parser/success/unit/import/HeadersDoubleHash",
    "dhall-lang/tests/parser/success/unit/import/HeadersHashPrecedence",
    "dhall-lang/tests/parser/success/unit/import/Headers",
    "dhall-lang/tests/parser/success/unit/import/inlineUsing",
    "dhall-lang/tests/parser/success/usingToMap",

    "dhall-lang/tests/import/success/noHeaderForwarding",
    "dhall-lang/tests/import/success/headerForwarding",
    "dhall-lang/tests/import/success/customHeaders",

]
