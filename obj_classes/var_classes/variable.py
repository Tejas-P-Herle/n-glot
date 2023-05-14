"""Variable Class"""


from dataclasses import dataclass, field
from obj_classes.object import Object
from obj_classes.var_classes.variable_value import VariableValue
from type_classes.all_types import Type
from type_classes.solve_types import SolveType


@dataclass
class Variable(Object):

    index: int = field(default=-1, repr=False)
    usages: dict = field(default_factory=dict, repr=False)

    value: VariableValue or list = field(default=None, repr=False)
    type_to: Type = None
    type_from: Type = None
    type_solved: bool = False

    assignment_type: str = ""

    body_end: int = -1

    collection_attr: str = ""
    type_set_to: set = field(default_factory=set)
    type_set_from: set = field(default_factory=set)

    instances: list = field(default_factory=list, repr=False)
    struct: Object = None
    self_obj: Object = None

    def __post_init__(self):

        if not self.do_setup:
            return

        if not self.usages:
            self.usages = {"set": {}, "get": {}, "func_call": {}}

        if isinstance(self.type_from, str):
            self.type_from = self.state.all_types_from[self.type_from]

        self.is_var = True
        super().__post_init__()

        if not self.is_ghost:
            self.state.var_buff.append(self)

    def __eq__(self, other):
        """Check if two Objects are equals"""

        # They are only equal if they are the same object
        return self is other

    def __hash__(self):
        """Return id as hash"""

        return super().__hash__()

    def setup(self, val, val_index=None):
        """Setup Variable Object"""

        # If value index is given, then create ranged VariableValue
        if val_index:

            # If value is init_call, then set type_ to struct name
            self.value = VariableValue(
                val, self.state, val_index, val_index+len(val))
        else:
            # Else create VariableValue with no range
            self.value = VariableValue(val, self.state)

    def setup_instance(self, struct, is_instance=False):
        """Setup attributes of Instance"""

        for attr_name, attr_value in struct.attrs.items():
            if attr_name not in self.attrs:
                self.attrs[attr_name] = attr_value
        struct_ = struct.struct if is_instance else struct
        if self not in struct_.instances:
            struct_.instances.append(self)
        self.struct = struct_

    def implement(self):
        """Implement Variables with Body"""

        self.state.conversions.skimmer.tag_tokens(self)

    def solve_type(self):
        """Solve type of Variable"""

        return SolveType.get_var_types(self.state, self)

    def get_type_from(self):
        """Return type from"""

        self.solve_type()
        return self.type_from

    @property
    def type_(self):
        """Getter for type_ property"""

        if not isinstance(self.type_to, Type):
            self.type_to = self.state.get_super_type(
                self.get_linked_types_to(), list(self.linked_objs))
        return self.type_to

