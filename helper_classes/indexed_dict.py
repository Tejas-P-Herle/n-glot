class IndexedDict(dict):
    def __init__(self):
        self.order = []
        super().__init__()

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.order[key]
        else:
            return super().__getitem__(str(key))

    def __setitem__(self, key, value):
        self.order.append(value)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        if isinstance(key, int):
            target = self[key]
            for key, value in self.items():
                if value == target:
                    super().__delitem__(key)
                    break
            self.order.remove(target)
        else:
            self.order.remove(self[key])
            super().__delitem__(key)

    def insert(self, pos, key, value):
        """Insert key value pair in given position"""

        self.order.insert(pos, value)
        super().__setitem__(key, value)
