from bisect import bisect_left


class ScopeFilters:
    def __init__(self, state):
        """Initiate new ScopeFilters Object"""

        self.state = state

    @staticmethod
    def filter_by_condition(obj_list, cond):
        """Filter based on if object satisfies given condition"""

        filtered_objs = []
        index_list = []
        for obj in obj_list:
            if cond(obj):
                if obj.eol_index == -1:
                    index = len(filtered_objs)
                else:
                    index = bisect_left(index_list, obj.eol_index)
                filtered_objs.insert(index, obj)
        return filtered_objs

    @classmethod
    def filter_callable_in_range(cls, obj_list, start, end):
        """Filter Objects based on if they are callable in given range"""

        def cond(obj):
            return ((start == -1 or obj.start <= start)
                    and (end == -1 or obj.end >= end))

        return cls.filter_by_condition(obj_list, cond)

    @classmethod
    def filter_declared_before(cls, obj_list, index):
        """Filter Objects based on if they were declared before given index"""

        def cond():
            return (lambda _: True if index == -1 else
                    lambda o: o.dec_index >= index)

        return cls.filter_by_condition(obj_list, cond())

    @classmethod
    def filter_eol_after(cls, obj_list, index):
        """Filter Objects based on if their eol is after given index"""

        def cond():
            return (lambda _: True if index == -1 else
                    lambda o: o.eol_index < index)

        return cls.filter_by_condition(obj_list, cond())

    def filter_with_env(self, obj_list, index, start, end):
        """
        Filter Objects based on if their environment is in area
        constrained by index, start, end
        """

        def cond1(obj):
            return ((index == -1 or index >= obj.dec_index)
                    and (obj.eol_index == -1 or index <= obj.eol_index))

        filtered_obj_list = self.filter_callable_in_range(obj_list, start, end)
        return self.filter_by_condition(filtered_obj_list, cond1)

    def filter_same_stmt(self, obj_list, index, stmt_start=None):
        """Filter Objects based on if obj.start is in less than index"""

        if stmt_start is None:
            stmt_start = self.state.str_funcs.find_start(index)

        def cond(obj):
            return obj.start < stmt_start

        return self.filter_by_condition(obj_list, cond)
