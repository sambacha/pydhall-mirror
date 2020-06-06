from ..base import Builtin, Callable
from ..text.base import PlainTextLitValue, TextTypeValue

from .base import DoubleTypeValue, DoubleLitValue

class DoubleShow(Builtin):
    _literal_name = "Double/show"
    _type = "Double -> Text"

    def __call__(self, x):
        if not isinstance(x, DoubleLitValue):
            return None
        return PlainTextLitValue(x)
