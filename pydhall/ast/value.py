class NaturalLit(int):
    def __new__(cls, val):
        if val < 0:
            raise ValueError("%s < 0" % val)
        return int.__new__(cls, val)

    def __add__(self, other):
        if not isinstance(other, NaturalLit):
            raise ValueError(other)
        return NaturalLit(int.__add__(self, other))
