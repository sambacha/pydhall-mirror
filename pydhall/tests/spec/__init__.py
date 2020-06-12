FAILURES = [
    # Beta-norm
    # Unicode quirks
    "dhall-lang/tests/normalization/success/unit/TextShowAllEscapes",
    # missing remote import implementation
    "dhall-lang/tests/type-inference/success/CacheImports",
    "dhall-lang/tests/type-inference/success/CacheImportsCanonicalize",

    # Bug in prelude eval
    # "dhall-lang/tests/type-inference/success/prelude",

    ## parser
    # Using is not implemented. Not planned yet
    "dhall-lang/tests/parser/success/unit/import/Headers",
    "dhall-lang/tests/parser/success/unit/import/inlineUsing",
    "dhall-lang/tests/parser/success/usingToMap",

    # urllib doesn't make the difference between /foo? and /foo
    # should be implemented in the parser and adding an attribute
    # to RemoteFile.
    "dhall-lang/tests/parser/success/unit/import/urls/emptyQuery",

    # missing import implementation
    "dhall-lang/tests/parser/success/unit/import/quotedPaths",
    "dhall-lang/tests/parser/success/unit/import/environmentVariablePosix",
    "dhall-lang/tests/parser/success/unit/import/HeadersHashPrecedence",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv6withipv4",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv6verylong",
    "dhall-lang/tests/parser/success/unit/import/urls/ipv6long",
    "dhall-lang/tests/parser/success/unit/import/urls/quotedPathFakeUrlEncode",
    "dhall-lang/tests/parser/success/unit/import/HeadersInteriorHash",
    "dhall-lang/tests/parser/success/unit/import/HeadersDoubleHashPrecedence",
    "dhall-lang/tests/parser/success/unit/import/HeadersDoubleHash",

    # Unicode quirks (requires fixes in fastidious)
    "dhall-lang/tests/parser/success/text/nonAssignedUnicode",
    "dhall-lang/tests/parser/success/text/escapedDoubleQuotedString",

    # TODO
    "dhall-lang/tests/parser/success/quotedRecordLabel",
    "dhall-lang/tests/parser/success/text/multilineCorruptedLeadingWhitespace",

    # parser failures.
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

    # TODO: should fail but don't
    "dhall-lang/tests/parser/failure/doubleBoundsPos",
    "dhall-lang/tests/parser/failure/doubleBoundsNeg",

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

    # TODO: turns out that -0.0 ≠ 0.0 :/ figure how to handle that
    "dhall-lang/tests/type-inference/failure/unit/AssertDoubleZeros",


    ## imports
    "dhall-lang/tests/import/success/noHeaderForwarding",
    "dhall-lang/tests/import/success/headerForwarding",
    "dhall-lang/tests/import/success/customHeaders",
    # "dhall-lang/tests/import/success/unit/AlternativeNestedImportError",
    "dhall-lang/tests/import/success/unit/AlternativeNoError3",
    "dhall-lang/tests/import/success/unit/RemoteAsText",
    "dhall-lang/tests/import/success/unit/EnvSetAsText",
    # "dhall-lang/tests/import/success/unit/Normalize",
    # "dhall-lang/tests/import/success/unit/AlternativeNoError1",
    # "dhall-lang/tests/import/success/unit/Simple",
    # "dhall-lang/tests/import/success/unit/AlternativeEnv",
    # "dhall-lang/tests/import/success/unit/SimpleHash",
    # "dhall-lang/tests/import/success/unit/AlternativeSubExpr",
    # "dhall-lang/tests/import/success/unit/AlternativeNoError2",
    # "dhall-lang/tests/import/success/unit/AlternativeChain1",
    "dhall-lang/tests/import/success/unit/EnvSet",
    # "dhall-lang/tests/import/success/unit/AlternativeChain2",
    # "dhall-lang/tests/import/success/unit/QuotedPath",
    # "dhall-lang/tests/import/success/unit/FilenameWithSpaces",
    # "dhall-lang/tests/import/success/unit/IgnorePoisonedCache",
    "dhall-lang/tests/import/success/unit/AlternativeHashMismatch",
    # "dhall-lang/tests/import/success/unit/AlternativeImportError",
    "dhall-lang/tests/import/success/unit/SimpleRemote",
    # "dhall-lang/tests/import/success/unit/AlternativeParseError",
    "dhall-lang/tests/import/success/unit/asLocation/RemoteChainEnv",
    "dhall-lang/tests/import/success/unit/asLocation/RemoteCanonicalize4",
    "dhall-lang/tests/import/success/unit/asLocation/RemoteCanonicalize2",
    "dhall-lang/tests/import/success/unit/asLocation/RemoteChain2",
    "dhall-lang/tests/import/success/unit/asLocation/Canonicalize1",
    "dhall-lang/tests/import/success/unit/asLocation/RemoteChain3",
    "dhall-lang/tests/import/success/unit/asLocation/Chain1",
    "dhall-lang/tests/import/success/unit/asLocation/Relative2",
    "dhall-lang/tests/import/success/unit/asLocation/Home",
    # "dhall-lang/tests/import/success/unit/asLocation/Missing",
    "dhall-lang/tests/import/success/unit/asLocation/Relative1",
    "dhall-lang/tests/import/success/unit/asLocation/RemoteChainMissing",
    "dhall-lang/tests/import/success/unit/asLocation/Canonicalize4",
    "dhall-lang/tests/import/success/unit/asLocation/Env",
    "dhall-lang/tests/import/success/unit/asLocation/Chain3",
    "dhall-lang/tests/import/success/unit/asLocation/Remote",
    "dhall-lang/tests/import/success/unit/asLocation/Chain2",
    "dhall-lang/tests/import/success/unit/asLocation/Canonicalize2",
    "dhall-lang/tests/import/success/unit/asLocation/Canonicalize3",
    "dhall-lang/tests/import/success/unit/asLocation/Hash",
    "dhall-lang/tests/import/success/unit/asLocation/Absolute",
    "dhall-lang/tests/import/success/unit/asLocation/RemoteCanonicalize1",
    "dhall-lang/tests/import/success/unit/asLocation/RemoteCanonicalize3",
    # "dhall-lang/tests/import/success/unit/asLocation/DontTryResolving",
    "dhall-lang/tests/import/success/unit/asLocation/Canonicalize5",
    "dhall-lang/tests/import/success/unit/asLocation/RemoteChain1",
    # "dhall-lang/tests/import/success/unit/AsText",
    # "dhall-lang/tests/import/success/unit/AlternativeTypeError",
    # "dhall-lang/tests/import/success/nestedHash",
    "dhall-lang/tests/import/success/hashFromCache",


]
