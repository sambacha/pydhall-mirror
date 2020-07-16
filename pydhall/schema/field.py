from .record import Field
from .primitive import Text, Natural, Bool
from .list_ import List, ListOf, MapOf
from .union import Union, Alt, UnionAlternative

from ._base import Schema

class TextField(Field, type=Text):
    pass


class NaturalField(Field, type=Natural):
    pass


class BoolField(Field, type=Bool):
    pass


class RecordField(Field):
    pass


class ListField(Field):
    def __init__(self, type, **kwargs):
        if not isinstance(type, List):
            raise ValueError(type)
        super().__init__(type, **kwargs)


class ListOfField(ListField):
    def __init__(self, item_type, **kwargs):
        if not isinstance(item_type, Schema):
            if isinstance(item_type, type) and issubclass(item_type, Schema):
                pass
            else:
                raise ValueError(item_type)
        super().__init__(ListOf("_anonList", item_type)(), **kwargs)


class MapOfField(ListField):
    def __init__(self, type, **kwargs):
        try:
            default = kwargs["default"]
        except KeyError:
            pass
        else:
            if default is not None:
                kwargs["default"] = [dict(mapKey=k, mapValue=v) for k, v in default.items()]
        super().__init__(MapOf("_anonMap", type)(), **kwargs)


class Nested:
    def __init__(self, alt_field: str, value_field=None):
        self.alt_field = alt_field
        self.value_field = value_field

    def __call__(self, alt_name, alt_value, parent_field, parent):
        if self.value_field is None:
            alt_value[self.alt_field] = alt_name
            parent[parent_field] = alt_value
        else:
            parent[parent_field] = {self.alt_field: alt_name, self.value_field: alt_value}


class SimpleRenderer:
    def __call__(self, alt_name, alt_value, parent_field, parent):
        if alt_value is None:
            parent[parent_field] = alt_name
        else:
            parent[parent_field] = alt_value


class UnionField(Field):
    def __init__(self, u, renderer=None, **kwargs):
        self.renderer = SimpleRenderer() if renderer is None else renderer
        if isinstance(u, type):
            if not issubclass(u, Union):
                raise ValueError(u)
            u = u()
        if isinstance(u, list):
            u = {i: None for i in u}
        if isinstance(u, dict):
            alts = {k: Alt(v, k) for k, v in u.items()}
            u = type(f"_anonUnion", (Union,), alts)
            for alt in alts.values():
                alt.union_type = u
            u = u()
        if not isinstance(u, Union):
            raise ValueError(u)
        default = kwargs.setdefault("default", self.NoDefault)
        if isinstance(default, dict):
            if len(default) != 1:
                raise ValueError("only one default is allowed")
            for k, v in default.items():
                alt = getattr(u, k)
                kwargs["default"] = UnionAlternative(alt, alt.type._pydhall_as_value(v))

        super().__init__(u, **kwargs)


# TODO: UnionField with anonymous union passed as a dict (latter included in the shema)
