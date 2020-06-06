from ..base import Builtin
from .base import PlainTextLitValue
from io import StringIO


class TextShow(Builtin):
    _literal_name = "Text/show"
    _type = "Text -> Text"

    def __call__(self, x):
        if isinstance(x, PlainTextLitValue):
            char_map = {
                '"': r'\"',
                '$': r'\u0024',
                '\\': r'\\',
                '\b': r'\b',
                '\f': r'\f',
                '\n': r'\n',
                '\r': r'\r',
                '\t': r'\t',
            }
            out = StringIO()
            out.write('"')
            # TODO: fix pydhall/tests/spec/test_beta_normalization.py::test_parse_success_simple[input411-expected411] 
            for char in x:
                # print("*******************")
                # print(char)
                ch = char_map.get(char, None)
                if not ch:
                    ch = char
                    if ord(ch) < 31:
                        ch = r'\u{:04x}'.format(ord(ch))
                # print(ch)
                out.write(ch)
            return PlainTextLitValue(out.getvalue())

