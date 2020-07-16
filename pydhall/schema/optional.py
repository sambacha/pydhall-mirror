from pydhall.ast.optional.base import OptionalOf, SomeValue, NoneOf

from ._base import Schema


class Optional(Schema):
    def __init__(self, type):
        self.type = type
        self._pydhall_type = OptionalOf(type._pydhall_type)

    def __call__(self, value):
        if isinstance(value, NoneOf):
            return None
        if isinstance(value, SomeValue):
            return self.type(value.value)
        raise ValueError(value)

    def _pydhall_as_value(self, val):
        if val is None:
            return NoneOf(self.type._pydhall_type)
        return SomeValue(self.type._pydhall_as_value(val))
