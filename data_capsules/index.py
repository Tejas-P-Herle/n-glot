

from dataclasses import dataclass, field


@dataclass
class Index:
    indexes: dict = field(repr=False)
    word_space: int or str
    index: int

    def __new__(cls, indexes, word_space, index):
        """Create new index only if equal Index value doesn't already exist"""

        if (word_space, index) in indexes:
            return indexes[(word_space, index)]
        index_obj = super().__new__(cls)
        indexes[(word_space, index)] = index_obj
        return index_obj

    def __index__(self):
        """Implement index method (Used to convert Index to int)"""

        return self.index

    def __lt__(self, other):
        """Implement Greater than"""

        self_i, other_i = self.get_eq_index(other)
        return self_i < other_i

    def __gt__(self, other):
        """Implement Greater than"""

        self_i, other_i = self.get_eq_index(other)
        return self_i > other_i

    def __le__(self, other):
        """Implement Greater than"""

        self_i, other_i = self.get_eq_index(other)
        return self_i <= other_i

    def __ge__(self, other):
        """Implement Greater than"""

        self_i, other_i = self.get_eq_index(other)
        return self_i >= other_i

    def __add__(self, other):
        """Implement add method"""

        if isinstance(other, Index):
            return Index(self.indexes,
                         self.word_space, self.index + other.index)
        return Index(self.indexes, self.word_space, self.index + other)

    def __radd__(self, other):
        """Implement radd method"""

        return self + other

    def __sub__(self, other):
        """Implement sub method"""

        if isinstance(other, Index):
            return Index(self.indexes,
                         self.word_space, self.index - other.index)
        return Index(self.indexes, self.word_space, self.index - other)

    def __rsub__(self, other):
        """Implement rsub method"""

        return -(self - other)

    def __neg__(self):
        """Implement negative method"""

        return Index(self.indexes, self.word_space, -self.index)

    def __hash__(self):
        """Implement hash method"""

        return id(self)

    def __eq__(self, other):
        """Implement eq method"""

        if isinstance(other, int):
            return other == self.index
        elif isinstance(other, Index):
            return (self.word_space == other.word_space
                    and other.index == self.index)
        return False

    def shift(self, count):
        """Shift index value by count"""

        new_index = (self.word_space, self.index+count)
        if new_index in self.indexes:
            self.indexes.pop(new_index)
        self.index += count
        self.indexes[(self.word_space, self.index)] = self

    def get_eq_index(self, other):
        """Get equivalent indexes for comparison"""

        if isinstance(other, int):
            return self.index, other

        if self.word_space == other.word_space:
            return self.index, other.index

        word_space_stack = [[self], [other]]
        word_space_stack_len = []
        for i, index in enumerate([self, other]):
            curr_word_space = index.word_space
            k = 1
            while curr_word_space != "base":
                word_space_stack[i].insert(0, curr_word_space)
                curr_word_space = curr_word_space.word_space
                k += 1
            word_space_stack_len.append(k)

        j = -1
        while j+1 < min(word_space_stack_len):
            if (word_space_stack[0][j+1].word_space
                    != word_space_stack[1][j+1].word_space):
                break
            j += 1

        self_i = word_space_stack[0][j].index
        other_i = word_space_stack[1][j].index

        return self_i, other_i
