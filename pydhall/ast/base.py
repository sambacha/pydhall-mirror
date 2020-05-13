class Node:
    hash_attrs = []

    def __init__(self, parser=None, offset=None):
        self.offset = offset
        if parser is None:
            self.src = "<string>"
        else:
            self.src = parser.name

    def __hash__(self):
        return hash(
            (self.__class__, self.offset)
            + tuple(self._hash_attr(attr) for attr in self.hash_attrs))

    def _hash_attr(self, name):
        attr = getattr(self, name)
        if isinstance(attr, list):
            return hash(tuple(item for item in attr))
        return hash(attr)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        offset = ", offset=%s" % self.offset if self.offset is not None else ""
        return self.__class__.__name__ + "(%s%s)" % (
            ", ".join(["%s=%s" % (
                    attr, repr(getattr(self, attr))
                    ) for attr in self.hash_attrs
                ]), offset)


class Term(Node):
    pass


class Fetchable(Node):
    pass
