#!/usr/bin/env python3

"""Stores the state of variables and callable during conversion"""

import string
from data_capsules.lines import Lines
from type_classes.all_types import AllTypes
from type_classes.solve_types import SolveType, SolveTypes
import errors
from obj_classes.object_call_path import ObjectCallPath
from obj_classes.objects_map import ObjectsMap
from scope_classes.scope import Scope
from data_capsules.new_capsule import NewCapsule
from data_capsules.words import Words


class State:
    converting_snippet = False

    indents = []

    conversions = None
    str_funcs = None

    obj_map = None
    scope = None
    upper_map = None
    upper_map_str = None
    upper_name_stack = None
    all_objs = None
    words = None
    upper = None
    var_buff = None
    func_buff = None
    equations = None
    eq_ranges = None
    sorted_eq = None
    type_solved_values = None
    type_solved_objs = None
    type_solved_funcs = None
    type_solved_rng = None
    prefix_lns = None
    suffix_lns = None
    imported_libs = None
    get_lib_obj = None
    call_stack = None
    visited = None
    cursor = -1
    module_envs = None

    # TODO: Remove allow_type_solve
    allow_type_solve = True

    global_stmts = None
    nglot_funcs = None
    helper_class_name = ""
    paste_bottom_code = None
    cpc_info = None
    range_flags = None
    corrections = None
    future_objs = None
    recently_added_objs = None
    stmt_scope = None
    scope_copies = None
    module_mem = None

    FUNC = 1
    VAR = 2
    STRUCT = 4
    OBJECT = 7
    MODULE = 8
    VALUE = 16
    TYPE = 32

    test_flags = 0

    def __init__(self, database, out_file_path, progress_bar):
        """Initiation callable for State class"""

        # Create all state attributes
        self.cnv_file_lns = Lines(self)
        self.new_capsule = NewCapsule()
        self.database = database
        self.progress_bar = progress_bar
        self.from_meta = database.from_meta
        self.to_meta = database.to_meta
        self.out_file_path = out_file_path
        self.errors = errors

        # Initialize new Types object to store all types
        self.all_types_to = AllTypes(self)
        self.all_types_to.load_basic_types(db="to")

        # Initialize new Types object to store all types
        self.all_types_from = AllTypes(self)
        self.all_types_from.load_basic_types()

        # Reset File Dependent Attributes
        self.reset()

    def solve_type(self, value):
        """Solve type of given VariableValue"""

        return SolveType(self, value).solve()

    def solve_var_type(self, var):
        """Solve type of given variable"""

        return SolveType.get_var_types(self, var)

    def solve_func_type(self, func):
        """Solve type of given function"""

        return SolveType.get_func_types(self, func)

    def get_super_type(self, type_list, causes=None, throw_error=True):
        """Get super type of type list"""

        try:
            return SolveTypes.get_super_type(type_list, causes, self)
        except errors.TypeAdditionError:
            if not throw_error:
                return
            raise

    def file_lns_to_words(self, file_lns):
        """Convert File Lines to Words"""

        return Words(self.str_funcs.get_words(file_lns))

    def add_to_str_upper(self, name, pos, edge="start"):
        """Add object name to upper with body extent between start and end"""

        if edge == "end":
            name = self.upper_name_stack.pop(-1)
            self.upper_map_str[edge][name] = pos
        else:
            self.upper_map_str[edge][pos] = name
            self.upper_name_stack.append(name)

    def add_to_upper(self, obj, pos, edge=""):
        """Add object to upper scope with life between start and end"""

        if edge == "start":
            self.upper_map[edge][pos] = obj
        else:
            self.upper_map[edge][obj] = pos

        self.add_to_str_upper(obj.ref_loc, pos, edge)

    def get_level_prev_body(self, index):
        """Get previous body which is at the same level as index"""

        self_level = len(self.get_upper(index, all_=True, map_type="str")) + 1
        return self.get_upper(index-2, all_=True, map_type="str")[-self_level]

    def get_upper(self, index, all_=False, reverse=True, map_type="obj"):
        """Get current upper"""

        upper_map = self.upper_map if map_type == "obj" else self.upper_map_str

        if index < 0:
            if all_:
                return []
            return

        # TODO: Increase efficiency
        objs_before = []
        for pos, obj in upper_map["start"].items():
            if pos < index:
                objs_before.append(obj)

        upper_objs = []
        end_map = upper_map["end"]
        if reverse:
            objs_before = reversed(objs_before)
        for obj in objs_before:
            if obj not in end_map or end_map[obj] > index or index == -1:
                upper_objs.append(obj)
        if all_:
            return upper_objs
        if upper_objs:
            return upper_objs[0]

    def get_struct_upper(self, index):
        """Return upper only if upper is struct"""

        upper = self.get_upper(index)
        if hasattr(upper, "is_struct") and upper.is_struct:
            return upper

    def add_to_scope(self, obj):
        """Add object to scope with life between start and end"""

        self.recently_added_objs.add(obj)
        self.scope.add_to_scope(obj)

    def find_in_scope_rel(self, name, index=-1, start=-1, end=-1,
                          throw_error=True, filters=None):
        """Find variable or function given relative name"""

        if not name:
            return []

        # Go through all the functions and variables starting
        # from then lowest scope
        parts = []
        var_name = ObjectCallPath(self, name)
        root, path = var_name[0], var_name[1:]

        if hasattr(root, "tags") and "const" in root.tags:
            root = root.tags["const_obj"].type_from

        obj_list = self.scope.find_in_scope(root, throw_error)
        objs = self.scope.filters.filter_with_env(obj_list, index, start, end)
        if filters is not None:
            for filter_ in filters:
                objs = filter_(objs, index)
        if not objs:
            if throw_error:
                raise errors.NameNotInScopeError(
                    name, self.scope.scope_map.keys())
            return []

        try:
            sorted_objs = sorted(objs, key=lambda o: o.dec_index, reverse=True)
            same_dec_objs = []
            if (len(sorted_objs) > 1
                    and sorted_objs[0].dec_index == sorted_objs[1].dec_index):
                ref_dec_index = sorted_objs[0].dec_index
                for obj in sorted_objs:
                    if obj.dec_index == ref_dec_index:
                        same_dec_objs.append(obj)
                    else:
                        break
                sorted_objs = sorted(same_dec_objs, key=lambda o: o.index,
                                     reverse=True)
            obj = sorted_objs[0]
        except AttributeError:
            obj = objs[0]

        parts.append(obj)
        if not path:
            return parts

        if not obj.is_lib:
            while path:
                attr = path.pop(0)
                if attr not in obj.attrs and not obj.implemented:
                    if obj.is_struct:
                        obj.implement()
                    else:
                        struct = self.get_struct(obj)
                        if struct:
                            struct.implement()
                        else:
                            full_path = [attr] + path
                            str_path = ".".join(full_path)
                            lib_path = ObjectCallPath(
                                self, f"{obj.get_type_from()}.{str_path}")
                            func = self.get_lib_obj(
                                self, full_path[-1], lib_path, name)
                            if func is not None and func.is_func:
                                return [func]
                if attr not in obj.attrs:
                    if throw_error:
                        err_msg = "{} doesn't have attribute {}"
                        raise errors.MissingAttributeError(
                            err_msg.format(str(obj.ref_loc), attr))
                    return []
                obj = list(obj.attrs[attr].linked_objs.keys())[-1]
                parts.append(obj)
        else:

            if var_name[-1] in obj.attrs:
                return [obj.attrs[var_name[-1]]]
            full_ref_loc = ObjectCallPath(
                self, obj.lib_path + "".join(var_name.parts[1:]))
            lib_obj = self.get_lib_obj(
                self, full_ref_loc[-1], full_ref_loc, name)
            obj.attrs[lib_obj.abs_name] = lib_obj
            return [lib_obj]

        return parts

    def get_obj_buffs(self):
        """Get object buffers"""

        return [self.var_buff, self.func_buff, self.equations,
                self.sorted_eq, self.eq_ranges, self.global_stmts]

    def set_obj_buffs(self, obj_buffs):
        """Set object buffers"""

        [self.var_buff, self.func_buff, self.equations,
         self.sorted_eq, self.eq_ranges, self.global_stmts] = obj_buffs

    def reset_obj_buffs(self):
        """Reset object buffers"""

        self.set_obj_buffs([[], [], [], [], [], {}])

    def find_in_scope(self, name, index=-1, start=-1, end=-1, throw_error=True,
                      all_parts=False, in_stmt=None):
        """Find variable or function with given name"""

        if hasattr(name, "tags") and "const" in name.tags:
            return name.tags["const_obj"]

        if index == -1:
            index = self.cursor

        filters = []
        if in_stmt is not None:
            filters += [lambda obj, i:
                        self.scope.filters.filter_same_stmt(obj, i, in_stmt)]

        # Use relative matching
        res = self.find_in_scope_rel(
            name, index, start, end, throw_error, filters)

        # If all parts are not required then return only the last part of path
        if all_parts:
            return res
        if res:
            return res[-1]

    def get_new_obj_name(self, index=-1, preferred=None, prefix="",
                         max_char_lim=30):
        """Get new free name for identifier"""

        if preferred is None:
            preferred = ["i", "j"]

        def is_free(name):
            return not self.find_in_scope(name, index, throw_error=False)

        if prefix and is_free(prefix):
            return prefix

        for preference in preferred:
            if is_free(preference):
                return preference

        def n_letter_iter(n):
            for c in string.ascii_lowercase:
                if n == 1:
                    yield c
                else:
                    for c_n_1 in n_letter_iter(n-1):
                        yield c + c_n_1

        for i in range(1, max_char_lim - len(prefix)):
            for obj_name in n_letter_iter(i):
                if is_free(prefix + obj_name):
                    return prefix + obj_name
        raise ValueError("Unable to find Free Object Name")

    @staticmethod
    def get_struct(obj):
        """Get struct from object"""

        # In case of Test.attribute
        if obj.is_struct:
            return obj

        # Check if object value is determined
        obj.solve_type()

        # In case of self.attribute
        if hasattr(obj, "is_instance") and obj.is_instance:
            return obj.struct

    def add_line_after(self, pos, line):
        """Add lines after the given position"""

        # Save to buffer
        self.suffix_lns.append((pos, line))

    def add_line_before(self, pos, line):
        """Add lines before the given position"""

        # Save to buffer
        self.prefix_lns.append((pos, line))

    def paste_bottom(self, code, word_space="base"):
        """Paste code at bottom of converted code"""

        # Save code
        if word_space not in self.paste_bottom_code:
            self.paste_bottom_code[word_space] = ""
        self.paste_bottom_code[word_space] += code

    def reset(self):
        """Reset state attributes for new file conversion"""

        # Initialize object map
        self.obj_map = ObjectsMap()

        # Reset all file based attributes
        self.scope = Scope(self)
        self.upper_map = {"start": {}, "end": {}}
        self.upper_map_str = {"start": {}, "end": {}}
        self.upper_name_stack = []
        self.all_objs = set()
        self.words = []
        self.upper = []
        self.call_stack = set()
        self.visited = set()
        self.var_buff = []
        self.func_buff = []
        self.equations = []
        self.eq_ranges = []
        self.sorted_eq = []
        self.type_solved_values = {}
        self.type_solved_rng = {}
        self.prefix_lns = []
        self.suffix_lns = []
        self.imported_libs = set()
        self.type_solved_objs = set()
        self.type_solved_funcs = set()
        self.cursor = -1
        self.module_envs = {}
        self.indents = [0]
        self.converting_snippet = False
        self.global_stmts = {}
        self.nglot_funcs = {}
        self.paste_bottom_code = {}
        self.cpc_info = {}
        self.range_flags = {}
        self.corrections = []
        self.future_objs = {}
        self.recently_added_objs = set()
        self.stmt_scope = {}
        self.scope_copies = []
        self.module_mem = {}

    def import_lib(self, lib):
        """Add import statement for given library"""

        return self.conversions.import_lib(lib)

    def import_default_lib(self, lib_name):
        """Add lib with given lib_name to scope"""

        self.get_lib_obj(self, lib_name, ObjectCallPath(self, lib_name))

    def convert_snippet(self, code, index):
        """Convert a snippet of code from from-language to to-language"""

        return self.conversions.convert_snippet(code, index)

    def get_default_args(self):
        """Get Default Arguments for Code Executions"""
        
        conv_func = self.conversions.convert if self.conversions else None
        conv_obj = self.conversions.convert_obj if self.conversions else None
        return {
            "words": self.words, "convert": conv_func, "convert_obj": conv_obj,
            "str_funcs": self.str_funcs, "state": self,
            "new_capsule": self.new_capsule, "solve_type": self.solve_type
        }

    def add_nglot_func(self, func_name, func_code):
        """Adds new helper n-glot function into converted source code"""

        self.nglot_funcs[func_name] = func_code

    def get_helper_class_identifier(self):
        """Get new identifier for N Glot helper class"""

        self.helper_class_name = self.get_new_obj_name(
            len(self.words) - 1, ["NGlotHelperFuncs"])

    def set_CPC_info(self, key, value):
        """Sets Cross Program Communication(CPC) Info"""

        self.cpc_info[key] = value

    def check_CPC_flag(self, key, value):
        """Returns True if key and value match"""

        flag_status = key in self.cpc_info and self.cpc_info[key] == value
        if flag_status is True:
            self.cpc_info.pop(key)
        return flag_status

    def execute(self, code_obj, args=None, func="main", add_default_args=True):
        """Execute code"""

        # Set global variable
        all_args = {}
        if add_default_args:
            all_args = self.get_default_args()
            if code_obj["path"] not in self.module_mem:
                self.module_mem[code_obj["path"]] = {}
            all_args["module_mem"] = self.module_mem[code_obj["path"]]
        all_args.update(args if args else {})

        if not isinstance(code_obj["code"], str):
            raise ValueError(code_obj)
        module_env = self.get_module_env(code_obj)

        if func not in module_env:
            raise errors.MissingFunctionError(
                f"Function {func} not in module {code_obj['path']}")
        module_env["all_args"] = all_args
        exec(f"res={func}(**all_args)", module_env)
        return module_env["res"]

    def func_in_module(self, module, func):
        """Check if module has function"""

        if not module or "code" not in module:
            return False
        return func in self.get_module_env(module)

    def get_module_env(self, module):
        """Get module environment"""

        if module["path"] not in self.module_envs:
            module_env = self.database.get_module_env(module["code"])
            self.module_envs[module["path"]] = module_env
        return self.module_envs[module["path"]]

    def add_correction(self, start, end, new_value):
        """Correct words"""

        self.corrections.append(((start, end), new_value))

    def apply_corrections(self):
        """Apply all corrections"""

        corrected_words = []

        sorted_corrections = sorted(self.corrections, key=lambda x: x[0])
        prev_end = 0
        for correction_range, correction in sorted_corrections:
            corrected_words += self.words[prev_end:correction_range[0]]
            corrected_words += self.str_funcs.get_words(correction)
            prev_end = correction_range[1]
        corrected_words += self.words[prev_end:]
        for word in self.words:
            word.tags = {}
        return Words(corrected_words)

    def get_file(self, filepath):
        """Returns imported module at given filepath"""

        return self.database.get_conv(filepath)

    def get_eq_type(self, obj, obj_type):
        """Get equivalent type to of given object"""

        type_from = obj if obj_type == self.TYPE else obj.get_type_from()
        if "struct" in type_from.info:
            return self.all_types_to[str(type_from)]
        eq_conv = self.database.get_eq_conv(type_from)
        if eq_conv is None:
            raise ValueError(f"Missing Equivalent Type for {type_from}")
        type_ = self.execute(eq_conv, {"obj": obj, "obj_type": obj_type},
                             "get_eq_type")
        if isinstance(type_, str):
            return self.all_types_to[type_]

        if obj_type == self.TYPE:
            obj.info["converged_type"] = type_
        return type_
