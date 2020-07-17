class DhallTypeError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class TYPE_ERROR_MESSAGE:
    IF_BRANCH_MISMATCH = "❰if❱ branches must have matching types"
    IF_BRANCH_MUST_BE_TERM = "❰if❱ branch is not a term"
    INVALID_FIELD_TYPE = "Invalid field type"
    INVALID_LIST_TYPE = "Invalid type for ❰List❱"
    INVALID_INPUT_TYPE = "Invalid function input"
    INVALID_OUTPUT_TYPE = "Invalid function output"
    INVALID_PREDICATE = "Invalid predicate for ❰if❱"
    INVALID_SOME = "❰Some❱ argument has the wrong type"

    INVALID_ALTERNATIVE_TYPE = "Invalid alternative type"
    ALTERNATIVE_ANNOTATION_MISMATCH = "Alternative annotation mismatch"

    NOT_A_FUNCTION = "Not a function"
    UNTYPED = "❰Sort❱ has no type, kind, or sort"

    INCOMPARABLE_EXPRESSION = "Incomparable expression"
    EQUIVALENCE_TYPE_MISMATCH = ("The two sides of the equivalence have "
                                 "different types")

    INVALID_TO_MAP_RECORD_KIND = "❰toMap❱ expects a record of kind ❰Type❱"
    HETEROGENOUS_RECORD_TO_MAP = "❰toMap❱ expects a homogenous record"
    MISSING_TO_MAP_TYPE = "An empty ❰toMap❱ requires a type annotation"

    MUST_MERGE_A_RECORD = "❰merge❱ expects a record of handlers"
    MUST_MERGE_UNION = "❰merge❱ expects a union or Optional"
    MISSING_MERGE_TYPE = "An empty ❰merge❱ requires a type annotation"
    UNUSED_HANDLER = "Unused handler"
    MISSING_HANDLER = "Missing handler"
    HANDLER_NOT_A_FUNCTION = "Handler is not a function"
    DISALLOWED_HANDLER_TYPE = "Disallowed handler type"

    CANT_INTERPOLATE = "You can only interpolate ❰Text❱"

    CANT_TEXT_APPEND = "❰++❱ only works on ❰Text❱"
    CANT_LIST_APPEND = "❰#❱ only works on ❰List❱s"
    LIST_APPEND_MISMATCH = "You can only append ❰List❱s with matching element types"

    MUST_COMBINE_A_RECORD = "You can only combine records"

    COMBINE_TYPES_REQUIRES_RECORD_TYPE = "❰⩓❱ requires arguments that are record types"

    CANT_ACCESS = "Not a record or a union"
    CANT_PROJECT = "Not a record"
    CANT_PROJECT_BY_EXPRESSION = "Selector is not a record type"
    MISSING_FIELD = "Missing record field"
    MISSING_CONSTRUCTOR = "Missing constructor"

    UNHANDLED_TYPE_CASE = "Internal error: unhandled case in TypeOf()"

    NOT_AN_EQUIVALENCE = "Not an equivalence"

    ANNOT_MISMATCH = """Expression doesn't match annotation

Expression of type %s was annotated %s"""

    TYPE_MISMATCH = """Wrong type of function argument

expected %s but got %s"""

    UNBOUND_VARIABLE = "Unbound variable: %s"
    MISMATCH_LIST_ELEMENTS = """List elements should all have the same type

first element had type %s but there was an element of type %s"""
    CANT_OP = "❰%s❱ only works on ❰%s❱s"
    ASSERTION_FAILED = """Assertion failed

%s is not equivalent to %s"""

    PROJECTION_TYPE_MISMATCH = """Projection type mismatch

tried to project a %s but the field had type %s"""

    INVALID_TO_MAP_TYPE = """An empty ❰toMap❱ was annotated with an invalid type

"%s"""
    MAP_TYPE_MISMATCH = """❰toMap❱ result type doesn't match annotation

map had type %s but was annotated %s"""
    DUPLICATE_PROJECT_FIELD = "Duplicate field ❰%s❱ in projection expression"
    HANDLER_OUTPUT_TYPE_MISMATCH = """Handlers should have the same output type

Saw handlers of types %s and %s"""
    HANDLER_INPUT_TYPE_MISMATCH = """Wrong handler input type

Expected input type %s but saw %s"""
    MISSING_CONSTRUCTOR = "Missing constructor"
