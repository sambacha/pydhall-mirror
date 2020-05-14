class Value:
    def __str__(self):
        return str(self.as_python())

    @classmethod
    def from_python(cls, value):
        cls(value)


class NaturalLit(int, Value):
    def __new__(cls, val):
        if val < 0:
            raise ValueError("%s < 0" % val)
        return int.__new__(cls, val)

    def __add__(self, other):
        if not isinstance(other, NaturalLit):
            raise ValueError(other)
        return NaturalLit(int.__add__(self, other))

    def as_python(self):
        return int(self)

    def as_dhall(self):
        return str(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({int.__repr__(self)})"


class IntegerLit(int, Value):
    def __add__(self, other):
        raise TypeError()

    def as_python(self):
        return int(self)

    def as_dhall(self):
        sign = "+" if self >= 0 else "-"
        return f"{sign}{str(self)}"

    def __repr__(self):
        return f"{self.__class__.__name__}({int.__repr__(self)})"


class DoubleLit(float, Value):
    def __add__(self, other):
        raise TypeError()

    def as_python(self):
        return float(self)

    def as_dhall(self):
        return str(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({float.__repr__(self)})"


class _FreeVar(Value):
    pass
