from .term.base import Node


class Comment(Node):
    hash_attrs = ["content"]

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = content


class LineComment(Comment):
    pass


class BlockComment(Comment):
    pass
