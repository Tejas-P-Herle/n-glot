
from data_capsules.index import Index


class VariableValue:
    def __init__(self, value, state, start=-1, end=-1):
        if not(isinstance(value, list) or isinstance(value, VariableValue)):
            raise TypeError(
                "Value Argument Must be of type 'list' or 'VariableValue'")

        super().__init__()

        if start != -1 and end == -1 or end != -1 and start == -1:
            err_msg = "Either start and end must not be provided or both must"
            err_msg += " be provided"
            raise TypeError(err_msg)

        self.is_live_pointer = (start >= 0 and end < len(state.words)
                                and value == state.words[start:end])

        self.value = list(value)

        word_space = state.words.chosen_word_space
        start_i = (start if isinstance(start, Index)
                   else Index(state.words.indexes, word_space, start))
        end_i = (end if isinstance(end, Index)
                 else Index(state.words.indexes, word_space, end))
        self.start, self.end = start_i, end_i
        self.state = state
        self.type_to = None
        self.type_from = value
        self.type_set_to = set()
        self.type_set_from = set()
        self.type_solved = False
        self.iter_count = 0

    def __iter__(self):
        """Iterate Variable Value"""

        self.iter_count = 0
        if self.is_live_pointer:
            for word_i in self.state.words.iterate_range(self.start, self.end):
                if not self.is_live_pointer:
                    break
                self.iter_count += 1
                yield self.state.words[word_i]
            else:
                return

        value_iter = iter(self.value)
        while self.iter_count:
            self.iter_count -= 1
            try:
                next(value_iter)
            except StopIteration:
                return
        for word in value_iter:
            yield word

    def __add__(self, other):
        """Implement add method"""

        return list(self) + list(other)

    def __getitem__(self, item):
        """Get Item from VariableValue"""

        if self.is_live_pointer:
            return self.state.words[self.start:self.end][item]
        return self.value[item]

    def __eq__(self, other):
        """Implement equals method"""

        return list(self) == list(other)

    def __setitem__(self, key, value):
        """Set Item of VariableValue"""

        if self.is_live_pointer:
            self.value = self.state.words[self.start:self.end]
            self.is_live_pointer = False
        self.value[key] = value

    def __hash__(self):
        # if self.start != -1 and self.end != -1:
        #     # * 100 is to raise hash value above max value possible by id()
        #     # as max of id value is 18,446,744,073,709,551,616 for 64-bit
        #     return hash((self.start, self.end)) * 100
        return id(self)

    def __deepcopy__(self, memodict={}):
        """Override deepcopy method"""

        return self.duplicate()

    def __len__(self):
        """Returns length of Variable Value"""

        if self.is_live_pointer:
            return self.end - self.start
        return len(self.value)

    def __repr__(self):
        """Implement Repr method"""

        if self.is_live_pointer:
            return repr(self.state.words[self.start:self.end])
        return repr(self.value)

    def __str__(self):
        """Implement str method"""

        if self.is_live_pointer:
            return str(self.state.words[self.start:self.end])
        return str(self.value)

    def copy(self):
        """Alias for duplicate"""

        return self.duplicate()

    def index(self, word):
        """Implement index method"""

        if self.is_live_pointer:
            return self.state.words[self.start:self.end].index(word)
        return self.value.index(word)

    def duplicate(self):
        """Make duplicate of VariableValue"""

        if self.is_live_pointer:
            value_copy = self.state.words[self.start:self.end]
        else:
            value_copy = self.value.copy()
        var_val = VariableValue(value_copy, self.state, start=self.start,
                                end=self.end)

        var_val.type_to = (self.type_to.copy()
                           if hasattr(self.type_to, "copy") else self.type_to)
        var_val.type_from = self.type_from.copy()
        return var_val

    def get_type_from(self):
        """Get type from value"""
        
        self.type_from = self.state.solve_type(self)
        return self.type_from

    @property
    def type_(self):
        """Get type to"""

        if self.type_to is None:
            self.type_to = self.state.get_eq_type(self, self.state.VALUE)
        return self.type_to
