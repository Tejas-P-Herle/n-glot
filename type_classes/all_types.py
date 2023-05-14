"""Type Class"""
import errors
from copy import deepcopy


class AllTypes(dict):
    def __init__(self, state, *args, **kwargs):
        """Initiate AllTypes Class"""

        super().__init__(*args, **kwargs)
        self.state = state
        self.base_types = ["int", "float", "str", "bool", "None"]

    def load_basic_types(self, db="from"):
        """Load all basic types"""

        if db == "from":
            root_path = self.state.database.get_from_funcs_path()
            for types in zip(self.state.database.from_meta["basic_types"],
                             self.base_types):
                self.load_type(*types)
        else:
            root_path = self.state.database.get_to_funcs_path()

            # Get load basic types module (load only to-language types)
            for types in zip(self.state.database.to_meta["basic_types"],
                             self.base_types):
                self.load_type(*types)

        # Load type module
        type_docs = self.state.database.get_docs(root_path, "from/types")
        for type_name, conv in type_docs.items():
            type_name = type_name.replace("-", ".")
            if type_name not in self:
                self.load_type(type_name)
            self[type_name].module_code = conv
            lib_info = self.state.database.get_lib_obj([type_name])
            self[type_name].lib = lib_info

    def __getitem__(self, item):
        """Load item if item is not already loaded"""

        try:
            item = str(item)
            return super().__getitem__(item)
        except KeyError:
            self.load_type(item)
            return super().__getitem__(item)

    def get_basic_type(self, basic_type):
        """Get type object whose basic type is given input"""

        for type_ in self.values():
            if type_.base_eq == basic_type:
                return type_

        raise TypeError("Basic {} has not been loaded Type".format(basic_type))

    def load_type(self, type_name, basic_eq=None):
        """Load given type name into memory"""

        if basic_eq:

            # If type is a basic type, then create a new type
            # for converted type and basic eq
            self[basic_eq] = self[type_name] = Type(self.state, type_name,
                                                    basic_eq, all_types=self)

        # Else Create a new type
        else:
            self[type_name] = Type(self.state, type_name, all_types=self)


class Type:
    RAISE_UNKNOWN_OPR_ERR = True

    def __init__(self, state, type_, basic_eq=None,
                 module_code="", lib=None, all_types=None,
                 val_rng=None, info=None, flags=None, value=None):
        """Initializer for Type Class"""

        # Save input arguments
        self.state = state
        self.type_, self.base_eq = type_, basic_eq
        self.module_code = module_code
        self.lib, self.all_types = lib, all_types
        self.info = {} if info is None else info
        self.flags = set() if flags is None else flags
        self.val_rng = val_rng
        self.value = value

    def __hash__(self):
        """Return Hash of Type"""

        return hash(str(self))

    def __str__(self):
        """Return type name when converted to string"""

        return str(self.type_)

    def __repr__(self):
        """Print type name when representing"""

        return "<Type Obj of {}>".format(self.type_)

    def __eq__(self, other):
        """Implement equals comparison operator"""

        if isinstance(other, str):
            return str(self) == other
        if not isinstance(other, Type):
            return False

        return (self.type_ == other.type_
                and self.base_eq == other.base_eq)

    def __add__(self, other):
        """Implement add method for types"""

        if not isinstance(other, Type):
            raise TypeError("Can only add Type object to another Type Object")

        if self.type_ == other.type_:
            return self

        self.check_module_availability()

        type_ = self.state.execute(
            self.module_code, {"self_type": self, "other_type": other},
            "get_super_type", add_default_args=False)

        if type_ == "":
            raise errors.TypeAdditionError(
                f"Incompatible Type Addition {self} + {other}")
        if isinstance(type_, str):
            return self.all_types[type_]
        return type_

    def __radd__(self, other):
        """Implement radd method for types"""

        return self + other

    def __deepcopy__(self, memodict={}):
        """Override deepcopy default"""

        return self.copy()

    def check_module_availability(self):
        """Check Module Availability"""

        if not self.module_code:
            raise AttributeError(f"Module Not Available for type - '{self}'")

    def reset(self, new_type):
        """Set type to new type"""

        self.type_ = new_type
        if new_type in self.all_types:
            base_type = self.all_types[new_type]
            self.base_eq = base_type.base_eq

    def copy(self, make_deepcopy=False):
        """Create copy of Type"""

        type_ = Type(self.state, self.type_, self.base_eq,
                     self.module_code, self.lib, self.all_types, self.val_rng,
                     flags=self.flags.copy(), value=self.value)
        if self.info:
            type_.info = {}
            for key, value in self.info.items():
                if (make_deepcopy and
                        isinstance(value, list) or isinstance(value, dict)):
                    type_.info[key] = deepcopy(value)
                else:
                    type_.info[key] = value
        return type_

    def get_opr_res(self, opr, rhs=None):
        """Get result on applying operator"""

        self.check_module_availability()
        return self.state.execute(
            self.module_code,
            {"state": self.state, "self": self, "operator": opr, "other": rhs},
            "operate", add_default_args=False)

    def to_str(self, obj_usage, value, raise_error=True):
        """Convert Type into String"""

        try:
            self.check_module_availability()
            return self.state.execute(
                self.module_code,
                {"obj_usage": obj_usage, "value": value, "state": self.state},
                "obj_usg_to_str", add_default_args=False)
        except (AttributeError, errors.MissingFunctionError):
            if raise_error:
                raise
            return

    def typecast(self, value, other_type, raise_error=True):
        """Cast value to other type"""

        if self.type_ == other_type.type_:
            return str(value)

        try:
            self.check_module_availability()
            casted_value = self.state.execute(
                self.module_code,
                {"state": self.state, "value": value,
                 "other_type": other_type},
                "typecast", add_default_args=False)
            if casted_value is None:
                raise AttributeError
            return casted_value
        except AttributeError:
            if not raise_error:
                return
            help_msg = ""

            if self.module_code is None:
                help_msg += "\nCreate new module for '{}' in dir "
                help_msg += "'core_from/types' and define typecast in module"
            else:
                help_msg += "\nAdd typecast func in module(core_from/types/{})"

            raise errors.TypeCastFailureError(
                "Cannot cast type {} to type {}".format(
                    self, other_type) + help_msg.format(self))

    def get_operate_typecast(self, opr, other_types):
        """Cast value to other type"""

        self.check_module_availability()
        try:
            return self.state.execute(
                self.module_code,
                {"state": self.state, "opr": opr, "other_types": other_types},
                "get_operate_typecast", add_default_args=False
            )
        except errors.MissingFunctionError:
            return

    @staticmethod
    def get_super_type(type_list):
        """Get super type of all types in type_list"""

        iter_type_list = iter(type_list)
        return sum(iter_type_list, start=next(iter_type_list))

    def is_super_type(self, sub_type):
        """Check if self if super type of given sub_type"""

        self.check_module_availability()
        return self.state.execute(
            self.module_code, {"sub_type": sub_type}, "is_super_type")
