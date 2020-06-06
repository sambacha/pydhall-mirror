from ..base import Op
from .base import TextTypeValue

class TextAppendOp(Op):
    precedence = 40
    operators = ("++",)
    _op_idx = 6
    _type = TextTypeValue
