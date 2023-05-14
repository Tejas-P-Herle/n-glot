"""Creates new Word class to store strings as mutable objects with tags"""


class Word(str):
    def __new__(cls, *args, **kwargs):
        """Create new Word Object"""

        # Initiate str class
        type_ = None
        if "type_" in kwargs:
            type_ = kwargs.pop("type_")
        string = str.__new__(cls, *args, **kwargs)
        string.tok_type = type_
        string.tags = {}
        string.index = -1
        return string

    def __eq__(self, other):
        """Override equals comparison operator"""

        if isinstance(other, Word):
            return super().__eq__(other) and self.tok_type == other.tok_type
        if isinstance(other, str):
            return super().__eq__(other)
        return False

    def __hash__(self):
        """Call super class hash function"""

        return super().__hash__()

    def get_altered_str(self, new_str_value):
        """Alter only the string value of word and return the altered word"""

        new_word = Word(new_str_value)
        new_word.tags = self.tags
        new_word.tok_type = self.tok_type
        new_word.index = self.index
        return new_word
