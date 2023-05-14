from scope_classes.scope_filters import ScopeFilters
from errors import NameNotInScopeError


class Scope:
    def __init__(self, state, scope_map=None):
        """Initiate new Scope object"""

        self.scope_map = scope_map if isinstance(scope_map, dict) else {}
        self.state = state
        self.filters = ScopeFilters(state)

    def add_to_scope(self, obj, create_scope_copies=True):
        """Add Object to Scope"""

        obj_name = obj.abs_name
        if obj_name not in self.scope_map:
            self.scope_map[obj_name] = []

        self.scope_map[obj_name].append(obj)
        scope_copy = self.copy()
        if create_scope_copies:
            self.state.scope_copies.append(scope_copy)
            self.state.stmt_scope = scope_copy

    def copy(self):
        """Get map copy"""

        scope_map = {abs_name: obj_list.copy()
                     for abs_name, obj_list in self.scope_map.items()}
        return Scope(self.state, scope_map)

    def remove_from_scope(self, obj, prev_name=None, strict=False):
        """Remove Object from Scope"""

        if prev_name is None:
            prev_name = obj.abs_name
        if prev_name in self.scope_map:
            obj_name_list = self.scope_map[prev_name]
            if obj in obj_name_list:
                obj_name_list.remove(obj)
                if not obj_name_list:
                    self.scope_map.pop(prev_name)
                return
        if strict:
            raise NameNotInScopeError(
                "Object {} not in Scope".format(prev_name))

    def rename_obj(self, obj, prev_name, strict=False):
        """Rename Object already existing in Scope"""

        self.remove_from_scope(obj, prev_name, strict)
        self.add_to_scope(obj)

    def rename_all_maps(self, obj, prev_name):
        """Rename object in all scope maps"""

        for scope in self.state.scope_copies:
            try:
                scope.rename_obj(obj, prev_name, strict=True)
            except NameNotInScopeError:
                pass

    def add_to_all_scopes(self, obj, cond=None):
        """Add obj to all scopes if given cond is met"""

        def default_cond(_):
            return True

        cond = default_cond if cond is None else cond
        for scope in self.state.scope_copies:
            if cond(scope):
                scope.add_to_scope(obj, create_scope_copies=False)

    def matches(self, includes, excludes):
        """Check if obj matches requirements"""

        for obj in includes:
            if obj.abs_name not in self.scope_map:
                return False

            for obj_ in self.scope_map[obj.abs_name]:
                if obj is obj_:
                    break
            else:
                return False
        for obj in excludes:
            if obj.abs_name not in self.scope_map:
                continue
            for obj_ in self.scope_map[obj.abs_name]:
                if obj is obj_:
                    return False
        return True

    def find_in_scope(self, name, throw_error=True):
        """Find name in scope"""

        try:
            return self.scope_map[name]
        except KeyError:
            if throw_error:
                err_msg = "Unable to Locate '{}'\nScope: {}".format(
                    name, list(self.scope_map.keys()))
                raise NameNotInScopeError(err_msg)
            return []

    def filter(self, obj_list, filter_func):
        """Filter obj_list based on filter_function"""

        return self.filters.filter_by_condition(obj_list, filter_func)
