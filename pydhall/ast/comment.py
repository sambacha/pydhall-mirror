from .base import Node


class Comment(Node):
    attrs = ["content"]


class LineComment(Comment):
    pass


class BlockComment(Comment):
    pass
