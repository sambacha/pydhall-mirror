FAILURES = [

    # Low priority (mostly rare edge cases and fetures that
    # are not supported by the builtin python libs)

    # urllib doesn't make the difference between /foo? and /foo
    # should be implemented in the parser and adding an attribute
    # to RemoteFile.
    "dhall-lang/tests/parser/success/unit/import/urls/emptyQuery",
    # either urllib doesn't allow this, either we missed something in
    # the standard. Sould not hurt in the wild.
    "dhall-lang/tests/parser/success/unit/import/urls/emptyPathSegment",
    # turns out that -0.0 ≠ 0.0 :/ figure how to handle that (hint: 1/math.inf == -1/math.inf
    # don't have the same repr)
    "dhall-lang/tests/type-inference/failure/unit/AssertDoubleZeros",
    # rework the multiline WS algorithm
    "dhall-lang/tests/parser/success/text/multilineCorruptedLeadingWhitespace",


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
