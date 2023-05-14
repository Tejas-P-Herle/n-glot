"""Class to operate on value to get type"""


from dataclasses import dataclass
from data_capsules.index import Index
from obj_classes.var_classes.variable_value import VariableValue


class TypeSolveList(VariableValue):
    SET_TYPE = 1
    SOLVE_OPR = 2

    def __init__(self, var_value, state):
        """Initiate TypeSolveList"""

        super().__init__(var_value, state, var_value.start, var_value.end)
        self.i0 = var_value.start
        self.var_value = var_value
        for attr_name in dir(var_value):
            if not attr_name.startswith("__") and attr_name != "type_":
                self.__setattr__(attr_name,
                                 var_value.__getattribute__(attr_name))
        self.opr_order = []
        self.mem_map = state.type_solved_rng
        self.state = state
        self.matchable = state.str_funcs.matchable

    def list_copy(self):
        """Get copy of TypeSolveList as a python List"""

        return list(self)

    def set_type(self, range_start, range_end, type_):
        """Set type of given range"""

        if type_.__class__.__name__ != "Type":
            raise ValueError
        type_copy = type_.copy(True)

        start_word, end_word = self[range_start], self[range_end-1]
        if not hasattr(start_word, "index") or not hasattr(end_word, "index"):
            start = end = -1
        else:
            start = start_word.index
            end = end_word.index + 1
        val_rng = slice(start, end)
        type_copy.val_rng = val_rng
        type_copy.value = self.state.words[start:end]
        self.mem_map[(val_rng.start, val_rng.stop)] = type_copy
        self[range_start: range_end: 3.14] = [type_copy]

    def solve_operator(self, opr_range_start, opr_range_end, type_):
        """Save solved operator result"""

        if type_.__class__.__name__ != "Type":
            raise ValueError

        start_word, end_word = self[opr_range_start], self[opr_range_end-1]
        start = (start_word.index if hasattr(start_word, "index")
                 else start_word.val_rng.start)
        end = (end_word.index + 1 if hasattr(end_word, "index")
               else end_word.val_rng.stop)
        val_ref = self[opr_range_start: opr_range_end]
        self.opr_order.append(val_ref)
        type_copy = type_.copy(True)
        val_rng = slice(start, end)
        type_copy.val_rng = val_rng
        type_copy.value = self.state.words[start:end]
        type_copy.opr_capsule = self.get_opr_capsule(
            opr_range_start, opr_range_end)
        self.mem_map[(val_rng.start, val_rng.stop)] = type_copy
        self[opr_range_start: opr_range_end: 2.718] = [type_copy]

    def set_type_solve_list(self, range_start, range_end, type_solve_list,
                            group_opr, all_types, copy_opr_capsule=False):
        """Set type solve list as value for given range"""

        if type_solve_list.__class__.__name__ != "TypeSolveList":
            raise ValueError
        start_word, end_word = self[range_start], self[range_end-1]
        start = (start_word.index if hasattr(start_word, "index")
                 else start_word.val_rng.start)
        end = (end_word.index + 1 if hasattr(end_word, "index")
               else end_word.val_rng.stop)
        val_ref = type_solve_list
        self.opr_order.append(val_ref)
        type_ = (all_types["None"]
                 if not type_solve_list else type_solve_list[0])
        type_copy = type_.copy(True)
        val_rng = slice(start, end)
        type_copy.val_rng = val_rng
        type_copy.value = self.state.words[start:end]
        has_opr_capsule = hasattr(type_, "opr_capsule")
        if copy_opr_capsule:
            if has_opr_capsule:
                type_copy.opr_capsule = type_.opr_capsule
        elif has_opr_capsule:
            term = type_.opr_capsule
            type_copy.opr_capsule = self.get_group_capsule(
                range_start, range_end, term, (term.start, term.end),
                group_opr)
        else:
            term_val_rng = type_.val_rng
            if term_val_rng is None:
                term_val_rng = val_rng
            type_copy.opr_capsule = self.get_group_capsule(
                range_start, range_end, term_val_rng,
                (term_val_rng.start, term_val_rng.stop), group_opr)

        self.mem_map[(val_rng.start, val_rng.stop)] = type_copy
        self[range_start: range_end: 9.8] = [type_copy]

    def get_group_capsule(self, start, end, term, term_rng, group_opr):
        """Get OperationCapsule for grouping operator"""

        start_word, end_word = self[start], self[end-1]
        group_words = [start_word, end_word]
        return OperationCapsule(start_word.index, end_word.index+1, group_opr,
                                group_words, [term], [term_rng])

    def get_opr_capsule(self, start, end):
        """Get OperationCapsule"""

        opr_list = []
        terms = []
        terms_rng = []
        for term in self[start:end]:
            if term.__class__.__name__ == "Word":
                opr_list.append(term)
            else:
                if hasattr(term, "opr_capsule"):
                    terms.append(term.opr_capsule)
                    terms_rng.append(
                        (term.opr_capsule.start, term.opr_capsule.end))
                else:
                    terms.append(term.val_rng)
                    terms_rng.append((term.val_rng.start, term.val_rng.stop))
        start_word, end_word = self[start], self[end-1]
        abs_start = (start_word.index if hasattr(start_word, "index")
                     else start_word.val_rng.start)
        abs_end = (end_word.index + 1 if hasattr(end_word, "index")
                   else end_word.val_rng.stop)
        opr_str = " ".join(opr_list)
        return OperationCapsule(
            abs_start, abs_end, opr_str, opr_list, terms, terms_rng)

    def check_type_setting(self):
        """Check if all required types have been set"""

        for word in self:
            word_type = word.__class__.__name__
            if word_type != "Type" and word_type != "Word":
                raise ValueError("Type setting check failed")

    def __setitem__(self, key, value):
        """Override setitem of VariableValue"""

        valid = 0
        if hasattr(key, "step"):
            if key.step == 3.14:
                valid = 1
                key = slice(key.start, key.stop, 1)
            elif key.step == 2.718:
                valid = 2
                key = slice(key.start, key.stop, 1)
            elif key.step == 9.8:
                valid = 3
                key = slice(key.start, key.stop, 1)

        if not valid:
            raise ValueError

        super().__setitem__(key, value)

    def __getitem__(self, item):
        """Override getitem of VariableValue"""

        if hasattr(item, "start") and hasattr(item, "stop"):
            if self.i0 == -1:
                start = stop = -1
            else:
                start, stop = self.i0 + item.start, self.i0 + item.stop
            return TypeSolveList(VariableValue(
                super().__getitem__(item), self.state, start, stop),
                self.state)
        return super().__getitem__(item)


@dataclass
class OperationCapsule:
    start: Index
    end: Index
    opr_str: str
    opr_words: list
    terms: list
    terms_rng: list
