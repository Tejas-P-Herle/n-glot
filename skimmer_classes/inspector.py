"""Inspect Tokens"""


from obj_classes.var_classes.variable_value import VariableValue
from obj_classes.var_classes.variable_stmt import VariableStmt
from obj_classes.func_classes.function_stmt import FunctionStmt
from obj_classes.object_call_path import ObjectCallPath
from obj_classes.func_classes.function import Function
from obj_classes.var_classes.variable import Variable, Object
from data_capsules.statement import Statement


class Inspector:
    def __init__(self, state):
        self.state = state

        self.words = state.conversions.to_words()

        self.reserved_kw = state.database.from_reserved_kw
        self.import_kw = state.from_meta["import"]
        self.lib_parser = state.database.from_["from"]["lib_parser"]
        conv_space = self.state.conversions.conversions_space

        # TODO: TEST IF REQUIRED LIB CONVS
        self.lib_convs = conv_space.lib_convs

        self.value_tags = ["str", "float", "int", "None", "bool", "name"]

        self.body_objs, self.struct_objs, self.stmts = [], [], {}
        self.visited, self.new_stmts = set(), False

        self.matchable_chars = set(
            list(self.state.str_funcs.matchable.keys())
            + list(self.state.str_funcs.matchable.values())
        )
        self.matchable_stack, self.level_stack = [], []
        self.stmts_stack = [self.stmts]
        self.stmt_end = [self.state.database.from_meta["stmt_term"],
                         self.state.database.from_meta["stmt_sep"]]

        self.curr_stmt = Statement(state.words)
        self.stmt_classifier = self.state.conversions.stmt_classifier
        self.iter_rng = self.state.words.iterate_range

        self.level, self.obj_levels = 0, []

    def inspect(self, start=0, end=-1, level=0):

        # Defaults to True due to prepended new line
        in_transition = True
        self.level = level

        while start:
            start -= 1
            if self.state.words[start].tags["stmt"].is_transition_stmt:
                start += 1
                break

        len_words = len(self.state.words)
        end = len_words if end == -1 else end

        for i in self.words.iterate_range(start, len_words):

            word = self.state.words[i]
            if not word.tok_type:
                raise ValueError(f"Word - '{repr(word)}' Doesn't Have Type")

            word.index = i

            in_transition = self.handle_stmt_buffering(word, in_transition)
            if i >= end and self.curr_stmt.start >= end:
                break
            word.tags["stmt"] = self.curr_stmt

            self.state.cursor = i
            if word.tok_type in self.value_tags:
                self.handle_value(word)
            if word.tok_type == "blk_start":
                self.handle_blk_start(word)

            self.stmts[i] = word

            if word.tok_type == "blk_end":
                self.handle_blk_end(word)
            if word.tok_type == "name" and word not in self.reserved_kw:
                self.parse_obj_with_body(i)
            if word in self.matchable_chars:
                self.handle_matchable(word)
            if word == self.import_kw:
                self.handle_import_stmt(i)

    def handle_stmt_buffering(self, word, in_transition):
        """Handle buffering of word"""

        is_trans_word = (word in self.stmt_end or word.tok_type == "blk_start"
                         or word.tok_type == "blk_end")
        if ((not in_transition and is_trans_word)
                or (in_transition and not is_trans_word)):
            self.create_new_stmt(word.index, not in_transition)
            return not in_transition
        return in_transition

    def create_new_stmt(self, i, is_transition_stmt):
        """Create new statement"""

        self.curr_stmt.end = i
        self.state.execute(self.stmt_classifier,
                           {"stmt": self.curr_stmt}, func="classify")
        self.curr_stmt = Statement(self.state.words, i, level=self.level,
                                   is_transition_stmt=is_transition_stmt)

    def parse_obj_with_body(self, i):
        """Parse object only if it has a body"""

        check_res = self.check_obj_with_body(i)
        if check_res:
            obj_stmt, obj_usages, tag_prefix = check_res

            if obj_usages:
                obj = obj_usages[0].obj
                self.body_objs.append(obj)
                if obj.is_struct:
                    self.struct_objs.append(obj)

            usage_tag_name = tag_prefix + "_usage"
            self.words[obj_stmt.start].tags[tag_prefix + "_stmt"] = obj_stmt
            for obj_usage in obj_usages:
                self.words[obj_usage.index].tags[usage_tag_name] = obj_usage
                self.obj_levels.append((self.level, obj_usage.obj))
                self.visited = self.visited.union(
                    self.iter_rng(obj_usage.start, obj_usage.end))
            self.new_stmts = True

    def check_obj_with_body(self, i):
        """Check if is object with body"""

        func_stmt = FunctionStmt(self.state)
        func_usages = func_stmt.check_obj_with_body(i)
        if func_usages:
            return func_stmt, func_usages, "func"

        var_stmt = VariableStmt(self.state)
        var_usages = var_stmt.check_obj_with_body(i)
        if var_usages:
            return var_stmt, var_usages, "var"

    def handle_value(self, word):
        """Handle tagging value at given index"""

        i = word.index

        if word in self.reserved_kw:
            word.tags["kw_follower_value"] = self.get_kw_follower_value(i+1)

        if word.tok_type == "assignment_op":
            word.tags["assignment_value"] = self.get_assignment_value(i)
        else:
            word_value = VariableValue([word], self.state, i, i+1)
            if word.tok_type != "name":
                word.tags["const"] = word.tok_type
                word.tags["const_obj"] = Object(
                    self.state, word, const_word=word,
                    is_const=True)
                word.tags["const_obj"].obj_usages = [
                    self.state.new_capsule.object_usage(
                        self.state, word.index, word.index, word.index+1,
                        (word.index, word.index+1), word,
                        word.tags["const_obj"], ""
                    )]
                word_value.type_from = self.state.all_types_from[word.tok_type]
                word_value.type_solved = True

    def get_pair_value(self, i):
        value_body, end = self.state.str_funcs.pair_char(self.words, i)
        return VariableValue(value_body, self.state, i+1, end)

    def get_kw_follower_value(self, i):
        end = self.state.str_funcs.find_end(i)
        return VariableValue(self.words[i:end], self.state, i, end)

    def get_assignment_value(self, i):
        end = self.state.str_funcs.find_end(i)
        return VariableValue(self.words[i:end], self.state, i, end)

    def handle_matchable(self, word):
        """Handle Matchable Characters"""

        if word in self.state.str_funcs.matchable:
            self.matchable_stack.append(word)
        else:
            start_word = self.matchable_stack.pop(-1)
            start_word.tags["pair"] = word.index
            word.tags["pair"] = start_word.index
            start_word.tags["pair_value"] = self.get_pair_value(
                start_word.index)

    @staticmethod
    def handle_const(word):
        """Handle Constant Word"""

        word.tags["const"] = word.tok_type

    def handle_blk_start(self, word):
        """Handle Block Start Word"""

        self.level += 1
        self.level_stack.append(word)

        if self.new_stmts:
            self.stmts, self.new_stmts = {}, False
            self.stmts_stack.append(self.stmts)

        if not(self.obj_levels and self.obj_levels[-1][0] == self.level-1):
            word_index = self.state.str_funcs.find_start(word.index-2)
            word = self.state.words[word_index+1]
            self.state.add_to_str_upper(
                f"{word.index.index} {word}", word.index, "start")

    def handle_blk_end(self, word):
        """Handle Block End Word"""

        self.level -= 1
        self.handle_upper_map(word.index, self.pop_upper())
        self.handle_blk_paring(word)

    def pop_upper(self):
        """Pop out current upper if it exists"""

        if self.obj_levels and self.obj_levels[-1][0] == self.level:
            return self.obj_levels.pop(-1)[1]

    def handle_upper_map(self, index, upper):
        """Handle Upper Map Indexing"""

        if upper is None:
            self.state.add_to_str_upper("", index+1, "end")
            return

        upper.body_end, upper.stmts = index+1, self.stmts_stack.pop(-1)
        if hasattr(upper, "args"):
            for arg in upper.args.values():
                arg.eol_index = upper.body_end
        self.stmts = self.stmts_stack[-1]
        self.state.add_to_upper(upper, index+1, "end")

    def handle_blk_paring(self, word):
        """Handle adding pair tags"""

        start_word = self.level_stack.pop(-1)
        start_word.tags["blk_pair"] = word.index
        word.tags["blk_pair"] = start_word.index

    def handle_import_stmt(self, index):
        """Handle import Statement"""

        libs = self.state.execute(self.lib_parser, {"index": index}, "parse")
        for start, end, lib_path, lib_name in libs:
            self.get_lib_obj(self.state, lib_name,
                             ObjectCallPath(self.state, lib_path))
            self.visited = self.visited.union(self.iter_rng(start, end))

    @classmethod
    def get_lib_obj(cls, state, lib_name, lib_path, call_path=None):
        """Get Lib Object"""

        if not call_path:
            call_path = lib_path

        lib_conv_id = state.database.get_lib_obj(lib_path)
        if lib_conv_id is None:
            raise ValueError(f"Missing Library: {lib_path}")
        obj_signs = state.execute(lib_conv_id, {}, "get_sign")
        return cls.process_obj_signs(state, obj_signs, lib_name,
                                     lib_path, call_path)

    @staticmethod
    def process_obj_signs(state, obj_signs, lib_name, lib_path, call_path):
        """Process Object Signatures"""

        def segregate_args(args):
            pos_args_, kw_args_ = [], []
            for arg_ in args:
                if "value" in arg_:
                    kw_args_.append(arg_["ref_loc"])
                else:
                    pos_args_.append(arg_["ref_loc"])
            return pos_args_, kw_args_

        obj_type = obj_signs[0]
        if obj_type & state.FUNC:
            funcs = []
            for obj_sign in obj_signs[1]:
                obj_ret_from, obj_args = obj_sign
                fn = Function(state, call_path, use_ref_loc=True,
                              lib_path=lib_path, start=1, body_end=0)

                obj_arg_dicts = []
                for arg in obj_args:
                    if isinstance(arg, tuple):
                        obj_arg_dicts.append(
                            {"ref_loc": arg[0], "type_from": arg[1]})
                    else:
                        obj_arg_dicts.append(arg.copy())

                fn.pos_args, fn.kw_args = segregate_args(obj_arg_dicts)
                fn.args = FunctionStmt.get_arg_objs_cls(
                    state, fn, obj_arg_dicts, is_ghost=True)

                if isinstance(obj_ret_from, str):
                    fn.values.append(state.all_types_from[obj_ret_from])
                else:
                    fn.values.append(obj_ret_from)
                funcs.append(fn)
            return funcs[-1]
        elif obj_type & state.VAR:
            print("VAR")
            raise NotImplementedError
        elif obj_type & state.STRUCT:
            return Variable(state, lib_name, lib_path=lib_path,
                            is_struct=True, is_lib=True)
        elif obj_type & state.MODULE:
            lib_obj = Object(state, lib_name, lib_path=lib_path)
            lib_obj.type_ = state.all_types_to[str(lib_obj.ref_loc)]
            lib_obj.type_from = state.all_types_from[str(lib_obj.ref_loc)]

            return lib_obj
        raise ValueError("Unknown Type of Object")
