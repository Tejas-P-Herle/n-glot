"""FunctionStmt Class"""


from obj_classes.var_classes.variable import Variable, VariableValue
from errors import NameNotInScopeError, MissingAttributeError
from helper_classes.indexed_dict import IndexedDict
from obj_classes.func_classes.function import Function
from obj_classes.func_classes.function_usage import FunctionUsage
from type_classes.solve_types import SolveType


class FunctionStmt:
    def __init__(self, state):
        """Initialize new FunctionStmt object"""
        
        # Save function parameters as attributes
        self.state = state

        # Save function parser module

        # TODO: make all from functions into a class
        self.parser = self.state.database.from_["from"]["func_parser"]
        self.func_usages = self.obj_usages = []
        self.usage_type = None

        self.start = -1
        self.end = -1

    @staticmethod
    def get_arg_objs_cls(state, func, args_list, index=-1, start=-1, end=-1,
                         is_ghost=False):
        """Get Argument Objects from args_list"""

        arg_objs, func_ref_loc = IndexedDict(), str(func.ref_loc) + "."
        for arg in args_list:
            arg_name = arg.pop("ref_loc")
            arg_type_from = arg.pop("type_from")
            arg_name = arg_name[0] if isinstance(arg_name, list) else arg_name
            arg_type_from = (
                state.all_types_from[arg_type_from]
                if isinstance(arg_type_from, str) else arg_type_from
            )

            arg_obj = Variable(
                state, func_ref_loc + arg_name,
                type_from=arg_type_from, start=start,
                end=end, use_ref_loc=True, is_ghost=is_ghost)

            for attr_name, attr_value in arg.items():
                setattr(arg_obj, attr_name, attr_value)

            val_index, arg_value = None, None
            if "val_rng" in arg and arg["val_rng"]:
                arg_rng = arg.pop("val_rng")
                val_index = arg_rng.start
                arg_value = state.words[arg_rng.start:arg_rng.stop]

            if "value" in arg:
                val_index, arg_value = None, arg.pop("value")

            if arg_value is not None:
                arg_obj.setup(arg_value, val_index)

                if arg_obj.type_solved:
                    arg_obj.value.type_from = arg_obj.type_from
                    arg_obj.value.type_solved = arg_obj.type_solved

            arg_objs[arg_name] = arg_obj

        return arg_objs

    def get_arg_objs(self, func, args_list, index):
        """Runs get_arg_objs_cls with instance attributes"""

        return self.get_arg_objs_cls(self.state, func, args_list, index=index,
                                     start=self.start, end=self.end)

    def check_obj_with_body(self, i):
        """Check for Function with Body"""
        
        stmt = self.state.execute(self.parser, {"index": i}, "check_body")
        if stmt:
            return self.parse_func_def(i, stmt)

    def parse_func_def(self, i, stmt):
        """Parse Function definition statement"""

        self.usage_type = stmt["usage"]
        self.start = self.state.words.new_index(stmt["start"])
        self.end = self.state.words.new_index(stmt["end"])

        func = Function(
            self.state, stmt["call_path"], lib_path="in+code",
            index=i, start=self.start, end=self.end, scope=stmt["scope"],
            modifier=stmt["modifier"])

        # Set as upper callable
        self.state.add_to_upper(
            func, self.state.words.new_index(stmt["args_range"][0]), "start")

        # Save arguments
        func.args = self.get_arg_objs(func, stmt["args"], index=i)
        func_usage = FunctionUsage(
            self.state, i, stmt["start"], stmt["end"], stmt["words_loc"],
            stmt["call_path"], func, self.usage_type, func.args,
            stmt["args_range"])

        self.parse_def_stmt_args(stmt, func_usage)

        self.func_usages = self.obj_usages = [func_usage]
        return self.func_usages

    @staticmethod
    def parse_def_stmt_args(stmt, func_usage):
        """Parse arguments of def statement"""

        # If function return type is mentioned, save it
        func = func_usage.func
        if "values" in stmt:
            func.values = stmt["values"]
        func.pos_args, func.kw_args = stmt["pos_args"], stmt["kw_args"]

    def check_obj_no_body(self, i, end):
        """Parse usage of Function at given index"""

        stmt = self.state.execute(
            self.parser, {"index": i, "end": end}, "check_no_body")
        if stmt:
            return self.parse_func_call(stmt, i)

    def parse_func_call(self, stmt, index):
        """Parse Function Call"""

        self.usage_type, call_path = stmt["usage"], stmt["call_path"]
        self.start, self.end = stmt["start"], stmt["end"]
        args = self.parse_call_args(stmt["args"])

        # Try to find function in scope
        try:
            func = self.state.find_in_scope(call_path, index)
        except (NameNotInScopeError, MissingAttributeError):

            # If function is not found, then create new function
            func = Function(self.state, call_path)

        func = self.find_prototype(func, args)

        if "values" in stmt:
            func.values = stmt["values"]

        args = self.update_func_args(args, func)
        func_usage = FunctionUsage(
            self.state, index, stmt["start"], stmt["end"], stmt["words_loc"],
            call_path, func, self.usage_type, args, stmt["args_range"])

        self.func_usages = self.obj_usages = [func_usage]

        func.implement()
        return self.func_usages

    def find_prototype(self, func, arg_list):
        """Find matching prototype of function"""

        curr_proto = {}
        for arg_name, arg_val in arg_list.items():

            curr_proto[arg_name] = SolveType(self.state, arg_val).solve()

        curr_proto_keys = list(curr_proto.keys())

        for sign in func.linked_objs:
            req_args = sign.pos_args + sign.kw_args
            for i, key in enumerate(curr_proto_keys):
                if key.startswith("arg-"):
                    if "arg-n" in sign.args:
                        continue
                    if i < len(req_args):

                        arg_type = sign.args[req_args[i]].type_from
                        if (arg_type is None or arg_type == "-Any-"
                                or arg_type.base_eq == "None"
                                or arg_type == curr_proto[key]):
                            continue
                    break
                elif key not in sign.kw_args:
                    break
            else:
                return sign
        raise NameNotInScopeError("No Matching Prototype Found")

    def parse_call_args(self, args):
        """Parse call arguments"""

        arg_objs = IndexedDict()
        for i, arg in enumerate(args):
            arg_i, key, val = arg["index"], arg["ref_loc"], arg["val_rng"]
            if val is None:
                arg_name = f"arg-{i}"
                arg_start, arg_end, val = arg_i, arg_i + len(key), key
            else:
                arg_name, arg_start, arg_end = key[0], val.start, val.stop
                val = self.state.words[arg_start:arg_end]
            self.state.conversions.skimmer.tag_tokens_range(arg_start, arg_end)
            arg_objs[arg_name] = VariableValue(
                val, self.state, arg_start, arg_end)
        return arg_objs

    def update_func_args(self, args, func):
        """Update arguments name and function argument obj usages"""

        func_def, func_args, arg_keys = func.find_def(args), {}, []
        if func_def:
            func_args, arg_keys = func_def.args, self.get_arg_keys(func_def)

        has_args_sink = "arg-n" in func_args
        if not has_args_sink:
            for i, (arg_name, arg_val) in enumerate(args.copy().items()):
                arg_obj = None
                if arg_name.startswith("arg-") and len(func_args) > i:
                    arg_obj = func_args[arg_keys[i]]
                    args[arg_keys[i]] = args.pop(arg_name)
                self.add_arg_usage(arg_val.start, arg_val.end, arg_obj)
        return args

    def add_arg_usage(self, start, end, arg_obj):
        """Add arg usage to variables in given range"""

        var_usages = {w.tags["var_usage"] for w in self.state.words[start:end]
                      if hasattr(w, "tags") and "var_usage" in w.tags}
        for var_usage in var_usages:
            if var_usage.usage_type == "get":
                var_usage.var.usages["func_call"][var_usage] = arg_obj

    @staticmethod
    def get_arg_keys(func_def):
        """Get argument keys of given func_def"""

        return func_def.pos_args + func_def.kw_args
