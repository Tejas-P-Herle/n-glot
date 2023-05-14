"""Class to manage converted file lines"""


from data_capsules.index import Index


class Words:

    def __init__(self, words):
        """Initiation Function for Lines class"""

        self.word_spaces = {"base": words}
        self.chosen_word_space = "base"
        self.indexes = {}

    def __iter__(self):
        """Implement iter method"""

        word_iter = self.word_spaces[self.chosen_word_space]
        for word in word_iter:
            yield word

    def __setitem__(self, key, value):
        """Implement setitem method"""

        word_space, key = self.get_word_space(key)
        self.word_spaces[word_space][key] = value

    def __getitem__(self, item):
        """Implement setitem method"""

        word_space, item = self.get_word_space(item)
        return self.word_spaces[word_space][item]

    def __len__(self):
        """Implement len method"""

        return len(self.word_spaces[self.chosen_word_space])

    def __str__(self):
        """Return str function of chosen_word_space"""

        return str(self.word_spaces[self.chosen_word_space])

    def __repr__(self):
        """Return repr function of chosen_word_space"""

        return repr(self.word_spaces[self.chosen_word_space])

    def get_word_space(self, key):
        """Get word space for given key"""

        if isinstance(key, slice):
            word_space_start, key_start = self.get_word_space(key.start)
            word_space_stop, key_stop = self.get_word_space(key.stop)
            if word_space_start != word_space_stop:
                err_header = "Mismatching Word Spaces"
                err_desc = "Cannot get slice between two different Word Spaces"
                raise ValueError(f"{err_header}, {err_desc}")
            key = slice(key_start, key_stop, key.step)
            return word_space_stop, key
        if isinstance(key, Index):
            return key.word_space, key.index
        if not isinstance(key, tuple) or len(key) != 2:
            return self.chosen_word_space, key
        return key

    def append(self, item):
        """Implement append method"""

        self.word_spaces[self.chosen_word_space].append(item)

    def pop(self, index):
        """Implement pop method"""

        return self.word_spaces[self.chosen_word_space].pop(index)

    def extend(self, words):
        """Implement extend method"""

        self.word_spaces[self.chosen_word_space].extend(words)

    def clear(self):
        """Implement clear method"""

        self.word_spaces[self.chosen_word_space].clear()

    def copy(self):
        """Implement copy method"""

        self.word_spaces[self.chosen_word_space].copy()

    def iterate(self):
        """Return word with its index"""

        for i, word in enumerate(self):
            yield Index(self.indexes, self.chosen_word_space, i), word

    def add_word_space(self, i, words):
        """Add new word space at index"""

        self.word_spaces[i] = words

    def iterate_range(self, start, end):
        """Iterate range in chosen word space"""

        start_word_space = end_word_space = self.chosen_word_space
        if isinstance(start, Index):
            start_word_space = start.word_space
        if isinstance(end, Index):
            end_word_space = end.word_space
        if start_word_space != end_word_space:
            raise ValueError("Mismatching word spaces")
        for i in range(start, end):
            yield Index(self.indexes, start_word_space, i)

    def new_index(self, j):
        """Create new index object"""

        if isinstance(j, Index):
            return j
        return Index(self.indexes, self.chosen_word_space, j)
