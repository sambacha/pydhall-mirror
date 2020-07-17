from pydhall.core.natural.base import NaturalLitValue, NaturalTypeValue
from pydhall.core.integer.base import IntegerLitValue, IntegerTypeValue
from pydhall.core.double.base import DoubleLitValue, DoubleTypeValue
from pydhall.core.text.base import PlainTextLitValue, TextTypeValue
from pydhall.core.boolean.base import BoolTypeValue, BoolLitValue

from ._base import Schema


class Primitive(Schema):
    "marker class for primitive types"
    def __call__(self, value):
        if not isinstance(value, self._pydhall_dhall_type):
            raise TypeError(value)
        return self._pydhall_python_type(value)

    def _pydhall_as_value(self, val):
        return self._pydhall_dhall_type(val)


class _Text(Primitive):
    _pydhall_type = TextTypeValue
    _pydhall_dhall_type = PlainTextLitValue
    _pydhall_python_type = str


Text = _Text()


class _Natural(Primitive):
    _pydhall_type = NaturalTypeValue
    _pydhall_dhall_type = NaturalLitValue
    _pydhall_python_type = int


Natural = _Natural()


class _Integer(Primitive):
    _pydhall_type = IntegerTypeValue
    _pydhall_dhall_type = IntegerLitValue
    _pydhall_python_type = int


Integer = _Integer()


class _Double(Primitive):
    _pydhall_type = DoubleTypeValue
    _pydhall_dhall_type = DoubleLitValue
    _pydhall_python_type = float


Double = _Double()


class _Bool(Primitive):
    _pydhall_type = BoolTypeValue
    _pydhall_dhall_type = BoolLitValue
    _pydhall_python_type = bool


Bool = _Bool()
