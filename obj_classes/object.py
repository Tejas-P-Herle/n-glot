"""Create Object class for common functions and attributes"""

from dataclasses import dataclass, field
from obj_classes.object_call_path import ObjectCallPath
from obj_classes.object_ref_loc import ObjectRefLoc
from obj_classes.object_attributes import ObjectAttributes
from typing import Any


@dataclass
class Object:
    state: Any = field(repr=False)
    ref_loc: str or ObjectCallPath

    abs_name: str = ""
    scope: str = ""
    modifier: str = ""

    linked_objs: dict = field(default_factory=dict)
    usages: dict = field(default_factory=dict)

    dec_index: int = -2
    eol_index: int = -2

    start: int = -1
    end: int = -1

    # TODO: Make into Flags, Property
    is_global: bool = False
    is_struct: bool = False
    is_func: bool = False
    is_var: bool = False
    is_lib: bool = False
    is_instance: bool = False
    is_const: bool = False
    is_word_coll: bool = False
    implemented: bool = False

    is_ghost: bool = False
    is_declared: bool = False

    do_setup: bool = True

    lib_path: str or list or ObjectCallPath = field(default_factory=list)
    lib_conv: Any = None
    word_coll: list = field(default_factory=list)
    use_ref_loc: bool = False

    info: dict = field(default_factory=dict)
    attrs: dict = field(default_factory=dict, repr=False)
    const_word: Any = None

    obj_usages: list = field(default_factory=list)

    INDEPENDENT = 1
    LOCAL = 2
    ATTR = 4
    ARG = 8

    def __post_init__(self):
        """Initialize object"""

        if not self.do_setup:
            return

        if "mid_man" not in self.usages:
            self.usages["mid_man"] = {}
        if "get" not in self.usages:
            self.usages["get"] = {}

        self.attrs = ObjectAttributes(self, self.attrs)

        if self.lib_path and self.lib_path != "in+code":
            if isinstance(self.lib_path, list):
                self.lib_path = ObjectCallPath(self.state, self.lib_path)
            self.is_lib = self.implemented = True
            self.lib_conv = self.state.database.get_lib_obj(self.lib_path)

        if not(isinstance(self.ref_loc, ObjectCallPath)
               or isinstance(self.ref_loc, list)
               or isinstance(self.ref_loc, str)
               or isinstance(self.ref_loc, ObjectRefLoc)):
            raise ValueError(
                "Ref Loc must be a str, list, ObjectCallPath or ObjectRefLoc")

        if isinstance(self.ref_loc, list) or isinstance(self.ref_loc, str):
            self.ref_loc = ObjectCallPath(self.state, self.ref_loc)
        self.abs_name = str(self.ref_loc[-1])
        self.ref_loc = ObjectRefLoc(self.state, self, self.use_ref_loc)

        if self.const_word is not None:
            const_type = self.const_word.tok_type
            self.type_to = self.state.all_types_to[const_type]
            self.type_from = self.state.all_types_from[const_type]

        if len(self.ref_loc) > 1:
            self.get_upper().attrs[self.abs_name] = self

        self.setup_obj()

    def __hash__(self):
        """Return ID as Object hash"""

        return id(self)

    def get_obj_properties(self):
        """Get Properties of Object"""

        upper = self.get_upper()
        if upper:
            if upper.is_struct or upper.is_instance:
                return self.ATTR
            elif hasattr(upper, "args") and self.abs_name in upper.args:
                return self.ARG
            return self.LOCAL
        return self.INDEPENDENT

    def is_attr(self):
        """Check if variable is attribute"""

        return self.get_obj_properties() & self.ATTR

    def is_arg(self):
        """Check if variable is attribute"""

        return bool(self.get_obj_properties() & self.ARG)

    def setup_obj(self):
        """Setup Object"""

        # Add object to scope only if it is not an attribute
        upper = self.get_upper()
        if self.dec_index == -2:
            self.dec_index = upper.start if upper else -1

        if self.eol_index == -2:
            self.eol_index = -1
            if len(self.ref_loc) > 1 and hasattr(upper, "body_end"):
                self.eol_index = upper.body_end
        if (not self.is_ghost and
                (self.is_var or self.is_func
                 or self.is_struct or self.is_lib)):
            self.state.add_to_scope(self)

            # Add object to obj_map
            self.state.obj_map.add_obj(self)

    def get_upper(self):
        """Get upper of object"""

        if len(self.ref_loc) > 1:
            return self.ref_loc[-2]

    def get_root(self):
        """Get Root of object"""

        if self.ref_loc:
            return self.ref_loc[0]
        return ""

    def get_path(self):
        """Get Path of Object"""

        return self.ref_loc[1:]

    def rename(self, new_name, propagate_down=True, all_traces=False):
        """Rename object to new_name"""

        keys = list(self.linked_objs.keys())
        attrs = list(self.attrs.values())
        linked_objs = keys[keys.index(self)+1:] if propagate_down else {}
        old_name = self.abs_name

        # Delete Obj from obj_map
        self.state.obj_map.deep_delete(self, attrs, linked_objs)

        # Rename function
        prev_name = self.abs_name
        self.abs_name = new_name
        for linked_obj in linked_objs:
            linked_obj.abs_name = new_name

        # Rename all traces of object to new name
        if all_traces:

            # Rename in state scope
            self.state.scope.rename_all_maps(self, prev_name)

            def rename_usages(obj):
                for usage in obj.usages["set"]:
                    old_name_ = self.state.words[usage.index]
                    self.state.words[usage.index] = (
                        old_name_.get_altered_str(new_name))
                for usage in obj.usages["get"]:
                    old_name_ = self.state.words[usage.index]
                    self.state.words[usage.index] = (
                        old_name_.get_altered_str(new_name))

            # Rename in get usages
            rename_usages(self)
            for linked_obj in linked_objs:
                rename_usages(linked_obj)

        # Re add renamed objects
        self.state.obj_map.deep_add(self, attrs, linked_objs)

        upper = self.get_upper()
        if hasattr(upper, "attrs") and old_name in upper.attrs:
            upper.attrs.rename(old_name, new_name)

    def copy(self, abs_name=""):
        """Create a copy of object"""

        if self.is_var:
            obj = self.state.new_capsule.variable(
                self.state, self.ref_loc, do_setup=False)
        elif self.is_func:
            obj = self.state.new_capsule.function(
                self.state, self.ref_loc, do_setup=False)
        else:
            raise ValueError("Unable to make Copy")

        for attr_name in self.__dir__():
            if attr_name.startswith("__"):
                continue

            attr = getattr(self, attr_name)
            if attr.__class__.__name__ == "method":
                continue
            setattr(obj, attr_name, attr)

        if abs_name:
            obj.abs_name = abs_name
        return obj

    def get_linked_objs(self):
        """Get all linked from types"""

        linked_objs = list(self.linked_objs)
        upper = self.get_upper()
        if (upper is not None and upper.is_struct
                and hasattr(upper, "instances")):
            for instance in upper.instances:
                if self.abs_name not in instance.attrs:
                    continue
                attr = instance.attrs[self.abs_name]
                if attr is self:
                    continue
                linked_objs += attr.get_linked_objs()
        return linked_objs

    def get_linked_types_to(self):
        """Get all linked from types"""

        return [self.state.get_eq_type(obj, self.state.OBJECT)
                for obj in self.get_linked_objs()]
