"""ObjectCallPath Class"""


from typing import List


class ObjectCallPath:
    is_setup = False
    is_const = False

    def __init__(self, state, name: str or List, is_const: bool = False):
        """Initialize ObjectCallPath"""

        if not(isinstance(name, list) or isinstance(name, str)):
            raise TypeError("name parameter must be a list or a string")

        self.state = state
        self.is_const = is_const
        if is_const:
            self.parts = self.name_parts = name
        elif isinstance(name, str):
            self.split_name = state.database.from_["from"]["split_name"]
            self.name_parts, self.parts = self.state.execute(
                self.split_name, {"name": name}, func="split")
        else:
            self.parts = name
            self.name_parts = [
                p for p in self.parts
                if (hasattr(p, "tok_type") and p.tok_type == "name"
                    or hasattr(p, "tags") and "const" in p.tags
                    or hasattr(p, "abs_name"))
            ]

    def __copy__(self, start, end):
        """Create a copy of ObjectCallPath"""

        return ObjectCallPath(self.state, self.parts[start:end])

    def copy(self, start=0, end=None):
        """Returns copy of object"""

        if end is None:
            end = len(self.name_parts)
        rel_start, rel_end = start*2, end*2
        return self.__copy__(rel_start, rel_end)

    def setup(self, index, obj):
        """Change strings in ObjectCallPath into Object Pointers"""

        if self.is_const:
            return

        parts = []
        ref_loc_parts = obj.ref_loc
        j = 0
        len_parts = len(self.parts)

        # Untested Assumption: Only the first and last parts in
        # any identifier is usage dependent,
        # then rest are just used for referencing - PART RIGHT ASSUMPTION
        name_parts = []
        if len(self) > 1:
            name_part = self.state.find_in_scope(self[0], index)
            name_parts.append(name_part)
            parts.append(name_part)
            j += 1

        len_ref_loc = len(ref_loc_parts)

        # + 1 to skip the first part already added previously
        start_i = len_ref_loc - len(self.name_parts) + 1
        for i in range(start_i, len_ref_loc - 1):
            j = self.add_to_parts(ref_loc_parts[i], i-start_i+1,
                                  j, name_parts, parts, index)
        j = self.add_to_parts(obj, -1, j, name_parts, parts, index)

        while j < len_parts:
            parts.append(self.parts[j])
            j += 1

        self.parts = parts
        self.name_parts = name_parts

        self.is_setup = True

    def add_to_parts(self, obj, i, j, name_parts, parts, index):
        """Add object to parts"""

        if obj.abs_name.endswith("["):
            if isinstance(self[i], str):
                obj = self.state.find_in_scope(self[i], index)
                start, end = obj.start, obj.end
            else:
                obj = self[i]
                start, end = obj.word_coll[0].index, obj.word_coll[-1].index+1
            if start != -1 != end:
                self.state.conversions.skimmer.tag_tokens_range(start, end)

        name_parts.append(obj)
        while self.parts[j] != self.name_parts[i]:
            parts.append(self.parts[j])
            j += 1
        parts.append(obj)
        return j+1

    @staticmethod
    def always_true(*args, **kwargs):
        """Returns True"""

        return True

    def get_str(self, cond=None) -> str:
        """Get string for parts when condition is true"""

        if not self.parts:
            raise ValueError("Name parts not found")

        # Set default condition
        if cond is None:
            cond = self.always_true

        def get_abs_name(name_):
            return name_ if isinstance(name_, str) else name_.abs_name

        # Iterate over parts in name
        str_parts, abs_parts = [], [get_abs_name(part) for part in self.parts]
        abs_name_parts = [get_abs_name(part) for part in self.name_parts]
        j, true_end = 0, False
        for i, name in enumerate(self.name_parts):

            # Run only while condition is true
            abs_name = get_abs_name(name)
            if cond(i, name):

                # Save object name
                str_parts.append(abs_name)
                try:
                    end = abs_parts.index(abs_name_parts[i+1], j)
                except (ValueError, IndexError):
                    end, true_end = len(self.parts), True
                str_parts.extend(self.parts[j+1:end])
                j = end

        return "".join(str_parts) if true_end else "".join(str_parts[:-1])

    def get_str_till(self, index: int) -> str:
        """Get string of parts till given index"""

        # Get string till required index
        if index == -1:
            return self.get_str()
        return self.get_str(lambda i, p: i < index)

    def __len__(self):
        """Return word length of name"""

        return len(self.name_parts)

    def __eq__(self, other):
        """Implement equals method for ObjectCallPath"""

        return str(self) == other

    def __add__(self, other):
        """Implement add method for ObjectCallPath"""

        if isinstance(other, str):
            return str(self) + other
        elif isinstance(other, list):
            return ObjectCallPath(self.state, str(self) + "".join(other))
        raise TypeError("Can Only Add string and list with ObjectCallPath")

    def __radd__(self, other):
        """Implement radd method for ObjectCallPath"""

        return other + str(self)

    def __repr__(self):
        return str(self)

    def __str__(self):
        """Convert Object name to string"""

        return self.get_str_till(-1)

    def __getitem__(self, item):
        """Implement get item method for ObjectCallPath"""

        return self.name_parts[item]

    def __setitem__(self, key, value):
        """Implement set item method for ObjectCallPath"""

        self.name_parts[key] = value
