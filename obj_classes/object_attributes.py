"""Store attributes of object"""


class ObjectAttributes(dict):
    def __init__(self, upper_obj, attrs=None):
        """Initiate new attributes object"""

        self.upper_obj = upper_obj
        super().__init__()

        if attrs:
            self.update(attrs)

    def __delitem__(self, key):
        """Override delitem of dict"""

        super().__delitem__(key)

    def pop(self, key):
        """Override pop of dict"""

        pop_res = super().pop(key)

        if hasattr(self.upper_obj, "instances"):
            for instance in self.upper_obj.instances:
                if key in instance.attrs:
                    instance.attrs.pop(key)

        return pop_res
    
    def rename(self, old_name, new_name):
        """Rename an attribute from old name to new name"""
        
        super().__setitem__(new_name, super().pop(old_name))

        if hasattr(self.upper_obj, "instances"):
            for instance in self.upper_obj.instances:
                if (old_name in instance.attrs
                        and instance.attrs[old_name].abs_name == new_name):
                    instance.attrs.rename(old_name, new_name)

    def __setitem__(self, key, value):
        """Override setitem of dict"""

        super().__setitem__(key, value)

        if hasattr(self.upper_obj, "instances"):
            for instance in self.upper_obj.instances:
                if key not in instance.attrs:
                    instance.attrs[key] = value

    def duplicate(self, upper_obj):
        """Create duplicate of self for given upper_obj"""

        return ObjectAttributes(upper_obj, self)
