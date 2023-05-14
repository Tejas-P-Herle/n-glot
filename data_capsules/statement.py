from dataclasses import dataclass
from typing import Any


@dataclass(repr=False)
class Statement:
    words: list
    start: int = 0
    end: int = -1
    level: int = 0
    stmt_type: Any = None
    is_transition_stmt: bool = False

    def __repr__(self):
        """Override dataclass repr"""

        return repr(self.to_list())

    def __hash__(self):
        """Implement hash method"""

        return id(self)

    def __getitem__(self, item):
        """Implement get item method"""

        return self.to_list()[item]

    def __iter__(self):
        """Implement iterator method"""

        for word in self.to_list():
            yield word

    def to_list(self):
        """Convert Statement ot list"""

        return self.words[self.start:self.end]
