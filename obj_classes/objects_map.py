"""
Create map of objects to track declarer
and link objects according to name
"""


from obj_classes.object import Object


class ObjectsMap(dict):
    def __init__(self):
        """Initiate new ObjectsMap"""

        # Initiate dictionary
        super().__init__()

    def add_obj(self, obj: Object):
        """Add obj to map"""

        # Search for obj in map
        search_res = self.search(obj)
        if search_res is not None:

            # If obj is found in the map, then link the variables
            obj.linked_objs = search_res.linked_objs

        else:
            # Else create a new entry in map
            self.add_new_entry(obj)

        # Save objet in linked_obj dict
        if obj not in obj.linked_objs:
            obj.linked_objs[obj] = None

    def search(self, obj) -> Object:
        """Search for obj in map"""

        # Return declarer obj of given ref_loc if present
        if str(obj.ref_loc) in self:
            return self[str(obj.ref_loc)]

    def add_new_entry(self, obj: Object) -> None:
        """Add obj to map"""

        # Save obj in map, consider first obj as declarer
        self[str(obj.ref_loc)] = obj

    def delete_obj(self, obj: Object):
        """Delete obj from map"""

        # Delete mapping
        declarer = self.search(obj)
        declarer.linked_objs.pop(obj)

        # If path is empty, remove path in map
        if not len(declarer.linked_objs):
            self.pop(str(obj.ref_loc))

        elif declarer == obj:
            new_declarer = next(iter(declarer.linked_objs.keys()))
            self[str(obj.ref_loc)] = new_declarer

        # Change linked_objs pointer to new dict
        obj.linked_objs = {obj: None}

    def deep_delete(self, obj: Object, attrs: list, linked_objs: dict) -> None:
        """Delete obj and its attrs and linked_objs"""

        for attr in attrs:
            self.delete_obj(attr)
        for linked_obj in linked_objs:
            self.delete_obj(linked_obj)

        self.delete_obj(obj)

    def deep_add(self, obj: Object, attrs: list, linked_objs: dict) -> None:
        """Add obj and its attrs"""

        self.add_obj(obj)
        for linked_obj in linked_objs:
            self.add_obj(linked_obj)
        for attr in attrs:
            self.add_obj(attr)

    def re_ref_loc(self, parent: Object, extension: dict) -> None:
        """Extend linked objs of parent obj to include extension"""

        for obj in extension.copy():
            self.delete_obj(obj)
            obj.ref_loc = parent.ref_loc
            self.add_obj(obj)
