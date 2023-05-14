from dataclasses import dataclass, field
from type_classes.all_types import Type
from errors import NoMatchingPrototypeError
from obj_classes.object import Object


@dataclass
class Function(Object):
    types_to: list = field(default_factory=list)
    types_from: list = field(default_factory=list)

    start: int = -1
    index: int = -1
    body_end: int = field(default=-1, repr=False)

    prototypes: list = field(default_factory=list, repr=False)
    implemented: bool = False

    values: list = field(default_factory=list)

    ret_type_to: Type = None
    ret_type_from: Type = None

    def __post_init__(self):
        """Create new Function Object"""

        if not self.do_setup:
            return

        self.is_func, self.usages = True, {"def": {}, "call": {}}
        self.args, self.pos_args, self.kw_args = {}, [], []

        super().__post_init__()

        if not self.is_lib:
            self.state.func_buff.append(self)

    def __hash__(self):
        """Return ID as hash"""

        return super().__hash__()

    def __eq__(self, other):
        """Check if two Objects are equals"""

        # They are only equal if they are the same object
        return self is other

    @property
    def type_(self):
        # TODO: Implement function pointer fully
        return self.state.all_types_to[f"{self.abs_name}_ptr"]

    @property
    def type_from(self):
        return self.type_

    def find_prototypes(self):
        """Find prototypes for function"""

        if self.state.database.from_meta["allow_overloading"]:
            prototypes = self.pos_args
        else:

            # One base prototype consisting of all arg and kwargs
            # Only one definition in non over-loadable languages
            main_def_names = [(self.args[var].type_, var) for var in
                              self.pos_args + self.kw_args]
            prototypes = [main_def_names]

            for call_usage in self.usages["call"].values():
                new_proto = [(value.type_, str(var_name))
                             for var_name, value in call_usage.args.items()]
                if new_proto not in prototypes:
                    prototypes.append(new_proto)
            prototypes.remove(main_def_names)

        self.prototypes = prototypes

    def add_header(self, lines):
        """Add lines to head of the function"""

        raise NotImplementedError(
            "Add Header not implemented in function_stmt.py")

    def add_footer(self, lines):
        """Add lines to head of the function"""

        raise NotImplementedError(
            "Add Footer not implemented in function_stmt.py")

    def implement(self):
        """Implement all definitions of the function"""

        # Go to start of function definition(s)
        if self.implemented or self.body_end == -1:
            return

        # Add function arguments into scope
        for arg in self.args.values():
            if not arg.value:
                continue

            # Skim through each argument separately
            arg_start, arg_end = arg.value.start, arg.value.end
            if arg_start != -1 and arg_end != -1:
                self.state.conversions.skimmer.tag_tokens_range(
                    arg_start, arg_end)

        # Skim through function
        self.state.conversions.skimmer.tag_tokens(self)

    def find_def(self, args):
        """Find Appropriate function definition for given arguments"""

        # TODO: Precedence of func definition in case of Prototype Collision

        # Get all Function Definitions
        static_types = self.state.database.from_meta["static_types"]
        for func in self.linked_objs:

            # Get current function definition arguments
            len_pos_args = len(func.pos_args)
            len_kw_args = len(func.kw_args)

            # Check if length of arguments matches
            if len(args) in range(len_pos_args,
                                  len_pos_args + len_kw_args + 1):
                if not static_types:
                    return func
            else:
                continue

            # If function arguments are statically typed,
            # then find matching prototype
            for i, func_arg in enumerate(args):
                if func_arg != args[i][1]:
                    continue
            return func

        if self.lib_path == "in+code":
            err_msg = "Prototype not found for {}"
            raise NoMatchingPrototypeError(err_msg.format(self.ref_loc))

    def solve_type(self):
        """Solve type of Function"""

        self.state.solve_func_type(self)
        return self.ret_type_from

    def get_type_from(self):
        """Get type of Function"""

        return self.solve_type()

    def get_type_to(self):
        """Get type to of Function"""

        if self.ret_type_to is None:
            for type_ in self.types_from:
                self.types_to.append(
                    self.state.get_eq_type(type_, self.state.TYPE))
            self.ret_type_to = self.state.get_super_type(self.types_to)

        return self.ret_type_to

