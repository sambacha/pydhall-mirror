from pydhall.core.list_.base import ListOf as ListOfValue, EmptyListValue, NonEmptyListValue

from ._base import Schema
from .record import Record, Field

class List(Schema):
    def __init_subclass__(cls, /, type_=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if type_ is None:
            return
        from .union import Union
        if isinstance(type_, type) and issubclass(type_, Union):
            type_ = type_()
        cls._pydhall_item_type = type_
        cls._pydhall_type = ListOfValue(type_._pydhall_type)

    def __call__(self, value):
        if isinstance(value, EmptyListValue):
            content = []
        elif isinstance(value, NonEmptyListValue):
            content = value.content
        else:
            raise ValueError(value)
        return [self._pydhall_item_type(val) for val in content]

    def _pydhall_as_value(self, val):
        if not len(val):
            return EmptyListValue(self._pydhall_type)
        return NonEmptyListValue([self._pydhall_item_type._pydhall_as_value(i) for i in val])


def ListOf(name: str, type_: Schema):
    return type(name, (List,), {}, type_=type_)


class Map(List):
    def __call__(self, value):
        return {item.mapKey: item.mapValue for item in super().__call__(value)}

    def _pydhall_as_value(self, val):
        if isinstance(val, dict):
            val = [dict(mapKey=k, mapValue=v) for k, v in val.items()]
        return super()._pydhall_as_value(val)


def MapOf(name: str, type_: Schema):
    from .field import TextField
    field_type = type("_anonField", (Field,), {}, type=type_)()
    type_ = type("_anonMapItem", (Record,), {
        "mapKey": TextField(),
        "mapValue": field_type})
    return type(name, (Map, List), {}, type_=type_)
