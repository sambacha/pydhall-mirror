from pydhall.ast.union import UnionTypeValue, UnionVal

from ._base import Schema
from .list_ import List

class UnionAlternative:
    def __init__(self, alt, value):
        self.alt = alt
        self.value = alt.type(value) if alt.type is not None else None

    @property
    def name(self):
        return self.alt.name

    def _pydhall_as_value(self, val):
        val = self.alt.type._pydhall_as_value(val) if self.alt.type is not None else None
        return UnionVal(
            self.alt.union_type._pydhall_type,
            self.alt.name,
            val)


class Alt:
    def __init__(self, type_=None, name=None):
        if isinstance(type_, type) and issubclass(type_, List):
            type_ = type_()
        self.type = type_
        self.name = name
        self.union_type = None

    def __set_name__(self, owner, name):
        self.name = name
        self.union_type = owner


class Union(Schema):
    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._pydhall_alternatives = [
            getattr(cls, name) for name in dir(cls)
            if isinstance(getattr(cls, name), Alt)
        ]
        res = {}
        for alt in cls._pydhall_alternatives:
            res[alt.name] = alt.type._pydhall_type if alt.type is not None else None
        cls._pydhall_type = UnionTypeValue(res)


    def __call__(self, value):
        if not isinstance(value, UnionVal):
            raise ValueError(value)
        alt = getattr(self, value.alternative)
        return UnionAlternative(alt, value.val)

    def _pydhall_as_value(self, value):
        return value._pydhall_as_value(value.value)
