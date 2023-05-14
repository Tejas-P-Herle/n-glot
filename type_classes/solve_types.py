
import errors
from errors import SkimOverIndexError, TypeAdditionError
from data_capsules.type_solve_list import TypeSolveList
from type_classes.all_types import Type


class SolveTypes:
    def __init__(self, state):
        """Initiate SolveTypes Object"""

        self.state = state

    def solve(self, main_solve=False):
        """Solves the types of all Variable Values"""

        if main_solve:
            self.state.type_solved_objs.clear()
            self.state.type_solved_values.clear()
            self.state.type_solved_funcs.clear()

            [SolveType(self.state, val).solve()
             for (val, _) in self.state.type_solved_values.copy().values()]

        self.state.progress_bar.increment()
        [var.solve_type() for var in self.state.var_buff]
        self.state.progress_bar.increment()
        [func.solve_type() for func in self.state.func_buff]

        [SolveType(self.state, eqn).solve() for eqn in self.state.equations]

    @staticmethod
    def assignment_stmt_mod(state, type_, var):
        """Modify types based on assignment operator"""

        return state.execute(
            state.conversions.get_type_from,
            {"type_": type_, "state": state, "words": state.words,
             "var": var, "all_types": state.all_types_from},
            "assignment_stmt_mod", add_default_args=False
        )

    @staticmethod
    def get_super_type(types, causes=None, state=None):
        """Get super type of given types"""

        types_iter = iter(types)
        super_type = next(types_iter)
        for i, type_ in enumerate(types_iter):
            try:
                super_type += type_
            except TypeAdditionError:
                if causes is None or causes[i+1] is None or state is None:
                    raise
                cause_obj = causes[i+1]
                new_name = state.get_new_obj_name(
                    cause_obj.index, [cause_obj.abs_name], cause_obj.abs_name)
                cause_obj.rename(new_name, all_traces=True)
        return super_type


class SolveType:
    def __init__(self, state, value):
        """Setup SolveType for given object"""

        self.state = state
        self.value = value
        self.get_type_from = self.state.conversions.get_type_from

    def solve(self):
        """Solve for types of object"""

        if self.value in self.state.call_stack:
            if self.value.type_solved:
                return self.value.type_from
            return

        if self.value in self.state.type_solved_objs:
            return self.value.type_from

        self.state.call_stack.add(self.value)
        
        value_from = TypeSolveList(self.value.duplicate(), self.state)
        for i, word in enumerate(value_from):
            word_type = (word.tok_type if hasattr(word, "tok_type") else
                         word.type_)
            if word_type in self.state.all_types_from:
                value_from.set_type(
                    i, i+1, self.state.all_types_from[word_type])

            elif word_type == "name":
                if "func_usage" in word.tags:
                    self.set_func_type(value_from, i)
                elif "var_usage" in word.tags:
                    self.set_var_type(value_from, i)
                elif "obj_usage" in word.tags:
                    obj_usage = word.tags["obj_usage"]
                    if (hasattr(obj_usage, "type_")
                            and hasattr(obj_usage, "type_from")):
                        value_from.set_type(obj_usage.start, obj_usage.end,
                                            obj_usage.type_from)
                    else:
                        raise ValueError(
                            f"Object {obj_usage.obj.ref_loc} missing types")
                elif word not in self.state.database.from_reserved_kw:
                    raise SkimOverIndexError(
                        f"Index {word.index} has not been Skimmed")

        value_from.check_type_setting()

        value_from = self.state.execute(
            self.get_type_from,
            {"value": value_from, "state": self.state},
            "preprocess_val"
        )

        type_from = self.state.execute(
            self.get_type_from,
            {"value": value_from, "state": self.state,
             "words": self.state.words, "str_funcs": self.state.str_funcs},
            "solve_types"
        )

        if hasattr(type_from, "opr_capsule"):
            opr_capsule = type_from.opr_capsule
            self.tag_opr_capsules(opr_capsule)
            opr_stmt_start_word = self.state.words[opr_capsule.start]
            opr_stmt_start_word.tags["root_opr_capsule"] = opr_capsule

        if type_from is None:
            raise errors.TypeSolveFailureError(
                f"Unable to solve type of {self.value}")

        value = self.value
        value.type_from = type_from
        value.type_solved = True
        self.state.type_solved_values[self.value.start] = (
            value, type_from)
        self.state.type_solved_objs.add(value)

        if type_from in self.state.all_types_from:
            struct_type = self.state.all_types_from[type_from]
            if "struct" in struct_type.info:
                value.type_to = self.state.all_types_to[str(type_from)]

        self.state.call_stack.remove(self.value)
        return type_from

    def tag_opr_capsules(self, opr_capsule):
        """Tag all appropriate words with corresponding opr capsules"""

        self.state.words[opr_capsule.start].tags["opr_capsule"] = opr_capsule
        for term in opr_capsule.terms:
            if hasattr(term, "terms"):
                self.tag_opr_capsules(term)

    @staticmethod
    def get_func_types(state, func):
        """Get Function type"""

        if func in state.type_solved_funcs:
            return func.ret_type_from

        all_types_from = set()

        for j, func_value in enumerate(func.values):

            solved_type = (func_value if isinstance(func_value, Type) else
                           SolveType(state, func_value).solve())
            if solved_type is not None:
                all_types_from.add(solved_type)

        if not len(all_types_from):
            all_types_from = {state.all_types_from["None"]}

        func.types_from = list(all_types_from)
        all_types_from = SolveTypes.get_super_type(all_types_from)
        state.type_solved_funcs.add(func)
        func.ret_type_from = all_types_from
        return all_types_from

    def set_func_type(self, value_from, i):
        """Set Type of Function"""

        func_usage = value_from[i].tags["func_usage"]
        func = func_usage.func

        all_types_from = self.get_func_types(self.state, func)
        index, start, end = func_usage.index, func_usage.start, func_usage.end
        value_from.set_type(i+(start-index), i+(end-index), all_types_from)

    @classmethod
    def solve_var_type(cls, state, var):
        """Solve type of variable"""

        if var.value is None:
            if var.type_from is not None:
                return var.type_from
            raise ValueError(
                f"Variable {var.ref_loc} has neither value or type")

        if var in state.type_solved_objs:
            return var.type_from

        type_ = SolveType(state, var.value).solve()
        if type_ is None:
            raise ValueError(f"Unable to Solve type of {var.ref_loc}")

        type_ = SolveTypes.assignment_stmt_mod(state, type_, var)
        var.type_solved = True
        state.type_solved_objs.add(var)

        if type_ is None:
            raise ValueError(f"Assignment Mod for {var.ref_loc} returned None")
        return type_

    @classmethod
    def get_var_types(cls, state, var):
        """Get Variable type"""

        # If type is solved, return it
        if var in state.type_solved_objs:
            return var.type_from
        if var.is_arg():
            type_ = cls.solve_arg_type(state, var)
        else:
            type_ = cls.solve_var_type(state, var)
            if var.type_from is None or var.type_from.base_eq == "None":
                var.type_from = type_
            state.type_solved_objs.add(var)

        if type_ is not None and "struct" in type_.info and not var.is_struct:
            var.is_instance = True
            var.type_to = state.all_types_to[str(type_)]
            var.setup_instance(type_.info["struct"])

        return type_

    def set_var_type(self, value_from, i):
        """Set Type of Variable"""

        var_usage = value_from[i].tags["var_usage"]
        call_path_len = var_usage.call_path_length
        var = var_usage.var
        type_ = self.get_var_types(self.state, var)
        value_from.set_type(i, i+call_path_len, type_)

    @staticmethod
    def get_lib_attr_req(state, var, max_type_from):
        """Get type based on attributes of library which are used"""

        req_types = set()
        for mid_man_usage in var.usages["mid_man"].values():
            type_lib = var.type_from.lib
            if type_lib and "get_req_type" in type_lib:
                ref_loc = mid_man_usage.obj.ref_loc
                part_i = ref_loc.find(var)
                type_ = state.execute(
                    type_lib,
                    {"state": state, "type_": max_type_from,
                     "attr": ref_loc[part_i+1], "usage": mid_man_usage},
                    "get_req_type"
                )
                if type_ is not None:
                    req_types.add(type_)
        return list(req_types)

    @classmethod
    def solve_arg_type(cls, state, var):
        """Get type of argument"""

        if isinstance(var.type_from, Type):
            return var.type_from

        func = var.get_upper()
        values = [var.value] if var.value else []
        for func_usage in func.usages["call"].values():
            if var.abs_name in func_usage.args:
                values.append(func_usage.args[var.abs_name])

        val_type_from = []
        for value in values:
            try:
                val_type_from.append(SolveType(state, value).solve())
            except SkimOverIndexError:
                pass

        if not val_type_from:
            val_type_from = [state.all_types_from["None"]]

        type_from = SolveTypes.get_super_type(val_type_from)

        var.type_from = type_from
        state.type_solved_objs.add(var)

        return type_from
