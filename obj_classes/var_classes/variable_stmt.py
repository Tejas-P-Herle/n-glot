"""VariableStmt Class"""
import errors
from obj_classes.var_classes.variable import Variable
from obj_classes.var_classes.variable_usage import VariableUsage
from obj_classes.object_usage import ObjectUsage


class VariableStmt:
    start = -1
    equals = -1
    end = -1
    usage_type = None

    def __init__(self, state):
        """Create new VariableStmt Object"""

        # Save, Initiate all required variables
        self.state = state

        # Create variable for var_usage parser functions
        self.parser = self.state.database.from_["from"]["var_parser"]
        self.get_val = self.state.database.from_["from"]["get_val"]
        self.var_usages = self.obj_usages = []

    def parse(self, index, end, func):
        """Parse VariableStmt usage and get value and other parameters"""

        stmt = self.state.execute(
            self.parser, {"index": index, "end": end}, func)
        if stmt:

            self.start = self.state.words.new_index(stmt["start"])
            self.end = self.state.words.new_index(stmt["end"])
            self.usage_type = stmt["usage"]

            if stmt["usage"] == "set":
                self.var_usages.extend(self.parse_set(stmt))
            else:
                self.var_usages.append(self.parse_struct(index, stmt)
                                       if stmt["usage"] == "struct" else
                                       self.parse_get(index, stmt))
            return self.var_usages

    def parse_struct(self, index, stmt):
        """Parse struct usage"""

        var = Variable(self.state, stmt["name"], attrs=stmt["attrs"],
                       start=self.start, index=index, end=self.end,
                       is_struct=True, self_obj=stmt["self_obj"])

        var_ref_loc_str = var.ref_loc.get_str_struct()

        var.type_to = self.state.all_types_to[var_ref_loc_str]
        var.type_from = self.state.all_types_from[var_ref_loc_str]

        var.type_.info["struct"] = var.type_from.info["struct"] = var

        struct_upper = var.get_upper()
        if struct_upper:
            struct_upper.attrs[var.abs_name] = var

        self.state.add_to_upper(var, self.start, "start")

        return VariableUsage(
            self.state, index, self.start, self.end, stmt["words_loc"],
            stmt["call_path"], var, stmt["usage"])

    def parse_get(self, index, stmt):
        """Parse get usage"""

        stmt_start = self.state.str_funcs.find_start(index) + 1
        s_tags = self.state.words[stmt_start].tags
        set_use = (s_tags["var_stmt"].usage_type == "set"
                   if "var_stmt" in s_tags else False)

        in_stmt = stmt_start if set_use else None
        if not stmt["future_dec"]:
            var = self.state.find_in_scope("".join(stmt["call_path"]),
                                           in_stmt=in_stmt)
            return self.create_obj_get_usage(var, stmt, index)

        var = self.state.new_capsule.variable(self.state, "Future Dec",
                                              is_ghost=True)

        var_usage = self.create_obj_get_usage(var, stmt, index)
        var_usage.call_path = self.state.new_capsule.object_call_path(
            self.state, stmt["call_path"])
        abs_name = var_usage.call_path[-1]
        if abs_name not in self.state.future_objs:
            self.state.future_objs[abs_name] = []
        self.state.future_objs[abs_name].append(var_usage)
        return var_usage

    def create_obj_get_usage(self, var, stmt, index):
        """Creates new object(variable) get usage"""

        if isinstance(var, Variable):
            return VariableUsage(self.state, index, stmt["start"],
                                 stmt["end"], stmt["words_loc"],
                                 stmt["call_path"], var, "get")
        else:
            return ObjectUsage(self.state, index, stmt["start"],
                               stmt["end"], (stmt["start"], stmt["end"]),
                               stmt["call_path"], var, "get")

    def parse_set(self, stmt):
        """Parse set usage"""

        # Get value of variable
        self.equals = stmt["equals"]
        var_usages = self.state.execute(
            self.get_val,
            {"stmt": stmt, "var_usage": self, "new_var": self.new_var}
        )
        for var_usage in var_usages:
            if var_usage.var.abs_name in self.state.future_objs:
                for future_var_usage in self.state.future_objs[
                        var_usage.var.abs_name]:
                    try:
                        var = self.state.find_in_scope(
                            str(future_var_usage.call_path))
                        if var is not None:
                            future_var_usage.obj = var
                            future_var_usage.__post_init__()
                            self.state.future_objs[var_usage.var.abs_name].pop(
                                future_var_usage)
                    except self.state.errors.NameNotInScopeError:
                        pass
        return var_usages

    def check_obj_with_body(self, i):
        """Check for Variable with Body"""

        # TODO: Change to end
        return self.parse(i, len(self.state.words), func="check_body")

    def check_obj_no_body(self, i, end):
        """Check for Variable with no Body"""

        return self.parse(i, end, func="check_no_body")

    def new_var(self, *args, **kwargs):
        """Create new Variable Object"""

        kwargs["start"] = self.start
        kwargs["end"] = self.end
        return Variable(self.state, *args, **kwargs)
