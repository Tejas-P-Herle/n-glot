from dataclasses import dataclass, field
from obj_classes.object_usage import ObjectUsage, Object


@dataclass
class VariableUsage(ObjectUsage):

    info: dict = field(default_factory=dict)

    obj_stmt: None = None

    var: Object = None

    def __post_init__(self):
        """Create new VariableUsage Object"""

        super().__post_init__()
        self.var = self.obj

        usage_type = "get" if self.usage_type == "get" else "set"
        self.var.usages[usage_type][self.index] = self

        if len(self.call_path) > 1:
            self.call_path[-2].usages["mid_man"][self.index] = self

    def __hash__(self):
        """Hash Object Usage"""

        return super().__hash__()

    def get_obj(self):
        """Return object of ObjectUsage"""

        return self.var

    def change_obj(self, new_obj):
        """Change which object's usage it is"""

        if self.usage_type != "get":
            raise AttributeError("Can only change get usages' variable")

        self.var.usages["get"].pop(self.index)
        self.var = self.obj = new_obj
        self.call_path[-1] = new_obj
