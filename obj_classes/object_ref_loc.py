"""ObjectRefLoc Class"""


class ObjectRefLoc:
    def __init__(self, state, obj, use_ref_loc):
        """Initiate new ObjectRefLoc"""

        # Store attributes
        self.state = state
        self.obj = obj
        self.use_ref_loc = use_ref_loc
        if isinstance(obj.ref_loc, ObjectRefLoc):
            self.full_ref_loc = obj.ref_loc.full_ref_loc
            self.struct_ref_loc = obj.ref_loc.struct_ref_loc
        else:
            self.full_ref_loc = self.struct_ref_loc = []
            self.setup()

    def __getitem__(self, item):
        """Get item from full ref loc"""

        return self.full_ref_loc[item]

    def __len__(self):
        """Return word length of name"""

        return len(self.full_ref_loc)

    def __eq__(self, other):
        """Implement equals method for ObjectRefLoc"""

        return str(self) == other

    def __add__(self, other):
        """Implement add method for ObjectRefLoc"""

        return str(self) + other

    def __radd__(self, other):
        """Implement radd method for ObjectRefLoc"""

        return other + str(self)

    def __repr__(self):
        return str(self)

    def __str__(self):
        """Convert Object name to string"""

        return self.get_str_till(-1)

    def __setitem__(self, key, value):
        """Implement setitem method for ObjectRefLoc"""

        self.full_ref_loc[key] = value

    def __hash__(self):
        """Implement hash for ObjectRefLoc"""

        return hash(str(self))

    def get_cls_obj(self):
        """Get class object"""

        ref_loc = self.obj.ref_loc
        index = self.obj.index if hasattr(self.obj, "index") else -1

        upper_obj = self.state.find_in_scope(
            ref_loc.get_str_till(len(ref_loc)-1), index=index,
            throw_error=False
        )
        if hasattr(upper_obj, "type_solved") and not upper_obj.type_solved:
            upper_obj.solve_type()
        if (hasattr(upper_obj, "is_instance")
                and (upper_obj.is_struct or upper_obj.is_instance)):
            return upper_obj
        if hasattr(upper_obj, "is_lib") and upper_obj.is_lib:
            return upper_obj
        elif self.obj.ref_loc[-1].endswith("["):
            if not upper_obj:
                upper_obj = self.create_coll_index_chain()
            return upper_obj

    def create_coll_index_chain(self):
        """Create full chain of attributes for collection indexing"""

        ref_loc = self.obj.ref_loc
        coll_name, start = ref_loc[-1].rstrip("["), -1
        for i, part in enumerate(reversed(ref_loc)):
            if str(part) == coll_name:
                start = -(i+1)

        var = self.state.find_in_scope(
            ref_loc.get_str_till(len(ref_loc)+start+1), self.obj.index)
        upper_obj = None
        for ptr in range(start, -1):
            attr = str(self.obj.ref_loc[ptr + 1])
            if attr not in var.attrs:
                upper_obj = var
                var = self.state.new_capsule.variable(
                    self.state, ref_loc.get_str_till(len(ref_loc)+ptr+2))
                var.attrs[attr] = var
        return upper_obj

    def setup(self):
        """Setup RefLoc Object"""

        # If object is an attribute, then set ref_loc to attribute's ref_loc
        # get_upper fetches call path prefix, if it exists
        cls_obj = self.get_cls_obj()

        # If first object is a constant, then substitute constant class
        ref_loc_0 = self.obj.ref_loc[0]
        const_obj = None
        if hasattr(ref_loc_0, "tags") and "const" in ref_loc_0.tags:
            self.obj.ref_loc[0] = ref_loc_0.tags["const"]
            const_obj = ref_loc_0.tags["const_obj"]
        if cls_obj:
            self.full_ref_loc = cls_obj.ref_loc.full_ref_loc.copy()

        # Add all upper scopes to ref loc lists
        elif self.obj.start == -1 or self.use_ref_loc:
            self.full_ref_loc = self.state.find_in_scope(
                self.obj.ref_loc.get_str_till(len(self.obj.ref_loc)-1),
                throw_error=False, all_parts=True)
        else:
            self.full_ref_loc = self.state.get_upper(
                self.obj.start, all_=True, reverse=False)

        if const_obj is not None:
            self.full_ref_loc[0] = const_obj

        # Filter list
        self.struct_ref_loc = [p for p in self.full_ref_loc if p.is_struct]
        self.full_ref_loc += [self.obj]
        self.struct_ref_loc += [self.obj]

    @staticmethod
    def always_true(*args, **kwargs):
        """Returns True"""

        return True

    def get_str(self, cond=None, full_ref: bool = True) -> str:
        """Get string for parts when condition is true"""

        str_name = ""

        ref_list = self.full_ref_loc if full_ref else self.struct_ref_loc

        # Set default condition
        if cond is None:
            cond = self.always_true

        # Iterate over parts in name
        for i, part in enumerate(ref_list):

            # Run only while condition is true
            if cond(i, part):

                # For object names
                str_name += part.abs_name + "."

        return str_name[:-1]

    def get_str_till(self, index: int, full_ref: bool = True) -> str:
        """Get string of parts till given index"""

        # Get string till required index
        if index == -1:
            return self.get_str(full_ref=full_ref)
        return self.get_str(lambda i, p: i < index, full_ref=full_ref)

    def get_str_from(self, index: int, full_ref: bool = True) -> str:
        """Get string of parts from given index(inclusive)"""

        # Get string till required index
        if index == -1:
            return self.get_str(full_ref=full_ref)
        return self.get_str(lambda i, p: i >= index, full_ref=full_ref)

    def get_str_struct(self, full_ref: bool = True) -> str:
        """Get string of parts including only consecutive structs"""

        j = [i for i, part in enumerate(self)
             if not hasattr(part, "is_struct") or not part.is_struct]
        j = j[-1]+1 if j else 0
        return self.get_str_from(j, full_ref)

    def find(self, obj):
        """Find matching obj in ref loc"""

        return list(self).index(obj)

    def get_path_parts(self):
        """Get parts of path"""

        prev_part = ""
        len_prev_part = 0
        for part in self:
            part_str = part.abs_name
            if (not len_prev_part
                    or (not part_str.startswith(prev_part)
                        or part_str[len_prev_part:].isalnum())):
                yield part_str
                prev_part = part_str
                len_prev_part = len(prev_part)
            # yield part.abs_name
