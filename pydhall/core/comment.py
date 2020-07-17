from .base import Node


class Comment(Node):
    # attrs = ['content']
    __slots__ = ['content']

    def __init__(self, content, **kwargs):
        self.content = content

    def copy(self, **kwargs):
        new = Comment(
            self.content
        )
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new



class LineComment(Comment):
    pass


class BlockComment(Comment):
    pass
