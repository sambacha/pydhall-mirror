from pydhall.ast.record.base import RecordTypeValue, RecordLitValue

from ._base import Schema
from .optional import Optional


_NoDefault = object()


class Field:
    type = None
    NoDefault = _NoDefault

    def __init_subclass__(cls, /, **kwargs):
        type = kwargs.pop("type", None)
        super().__init_subclass__(**kwargs)
        if type is not None:
            cls.type = type
        else:
            cls.type = type

    def __init__(self, type=None, default=_NoDefault, name=None, optional=False):
        if type is not None:
            if self.type is not None:
                # trying to add a type on a fixed type field class
                raise ValueError(type)
            self.type = type
        if optional:
            # Wrap the type in an optional
            self.type = Optional(self.type)
        self.optional = optional
        self.default = default
        self.values = {}
        self.name = name
        self.attr_name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return self.values[instance]
        except KeyError:
            if self.default is not _NoDefault:
                self.values[instance] = self.default
                return self.default
            raise ValueError(self.name)

    def __set__(self, instance, value):
        if instance in self.values:
            raise ValueError(value)
        self.values[instance] = self.type(value)

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name
        self.attr_name = name


def _get_field(record, name):
    if not isinstance(record, type):
        record = record.__class__
    if name in dir(record):
        return getattr(record, name)
    for f in record._pydhall_fields:
        if f.name == name:
            return f
    raise AttributeError(f"{record.__name__}.{name}")


class Record(Schema):
    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._pydhall_fields = [
            getattr(cls, name) for name in dir(cls)
            if isinstance(getattr(cls, name), Field)
        ]
        cls._pydhall_type = RecordTypeValue({
            attr.name: attr.type._pydhall_type
            for attr in cls._pydhall_fields
        })

    def __dir__(self):
        return [f.attr_name for f in self._pydhall_fields]

    def __init__(self, value):
        if not isinstance(value, RecordLitValue):
            raise ValueError(value)
        for k, v in value.items():
            _get_field(self, k).__set__(self, v)

    @classmethod
    def _pydhall_as_value(cls, val):
        result = {}
        for k, v in val.items():
            result[k] = _get_field(cls, k).type._pydhall_as_value(v)
        return RecordLitValue(result)
