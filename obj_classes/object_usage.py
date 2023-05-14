"""Create ObjectUsage class for common functions and attributes"""

from dataclasses import dataclass, field
from obj_classes.object import Object, ObjectCallPath
from data_capsules.index import Index


@dataclass
class ObjectUsage:
    state: None = field(repr=False)

    # start and end equate to words which belong to ObjectUsage instance
    index: Index
    start: Index
    end: Index

    # words_loc defines location of call path in state.words
    words_loc: tuple

    call_path: ObjectCallPath

    obj: Object

    usage_type: str = field(repr=False)

    def __post_init__(self):
        """Create new ObjectUsage Object"""

        self.has_lib_conv = False
        if isinstance(self.index, int):
            self.index = self.state.words.new_index(self.index)
        if isinstance(self.start, int):
            self.start = self.state.words.new_index(self.start)
        if isinstance(self.end, int):
            self.end = self.state.words.new_index(self.end)

        if not self.call_path:
            raise ValueError("Call Path not given")
        if self.obj.is_const:
            self.call_path = ObjectCallPath(self.state, [self.obj], True)
        elif (isinstance(self.call_path, str)
                or isinstance(self.call_path, list)):
            self.call_path = ObjectCallPath(self.state, self.call_path)
            self.call_path_length = int(self.words_loc[1]-self.words_loc[0])
            self.call_path.setup(self.index, self.obj)

    def get_call_path_length(self):
        """Get range in which given call path exists"""

        start_index = self.index
        call_path_str = str(self.call_path)
        i, k = 0, 0
        curr_word = None
        for char in call_path_str:
            if curr_word is None:
                curr_word = self.state.words[start_index+i]
            if char != curr_word[k]:
                # TODO: TEST WITH SKIPPING MISMATCHED WORD
                return i
            k += 1
            if k == len(curr_word):
                curr_word = None
                i += 1
                k = 0

        return i

    def __hash__(self):
        """Hash Object Usage"""

        return id(self)
