from dataclasses import dataclass, field
from helper_classes.indexed_dict import IndexedDict
from obj_classes.object_usage import ObjectUsage


@dataclass
class FunctionUsage(ObjectUsage):

    args: IndexedDict
    args_range: tuple = field(repr=False)
    modifier: str = field(default="", repr=False)

    pos_args: list = field(default_factory=lambda: list, repr=False)
    kw_args: list = field(default_factory=lambda: list, repr=False)

    obj_stmt: None = None

    def __post_init__(self):

        super().__post_init__()

        self.func = self.obj

        self.func.usages[self.usage_type][self.index] = self
        if len(self.call_path) > 1:
            self.call_path[-2].usages["mid_man"][self.index] = self
            if self.call_path[-2].is_struct:
                self.call_path[-2].usages["get"][self.index] = self

    def get_obj(self):
        """Return object of ObjectUsage"""

        return self.func
