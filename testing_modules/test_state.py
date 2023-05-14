import unittest
from database import DataBase
from state import State
from obj_classes.var_classes.variable_stmt import Variable
from obj_classes.func_classes.function_stmt import Function
from errors import (ObjDelWithoutDecError, MultipleObjDecError,
                    NameNotInScopeError, MissingAttributeError)


def print_flag_msg(expected_flags, received_flags):
    if received_flags != expected_flags:
        print("{:b}".format(received_flags))
        max_ = expected_flags
        n = 1
        while n < max_:
            if not (received_flags & n):
                print("N", n)
            n *= 2


def print_executed(flags, **kwargs):
    flags[0] |= 1
    if "state" in kwargs:
        flags[0] |= 2
    if "words" in kwargs:
        flags[0] |= 4
    if "str_funcs" in kwargs:
        flags[0] |= 8
    if "unused_kw" in kwargs:
        flags[0] |= 16


class TestState(unittest.TestCase):
    def __init__(self, test_method):
        """Initiate new State object for testing"""

        db = DataBase()
        db.setup("python", "java")
        self.state = State(db, "test")
        # i: 0 -> 4
        self.test_objs = [Variable(self.state, "test_var_" + str(i))
                          for i in range(5)]

        # i: 5 -> 6
        self.test_objs += [Variable(self.state, "test_var_0")]
        self.test_objs += [Variable(self.state, "test_var_2")]

        # i: 7 -> 8
        self.test_objs += [Function(self.state, "test_func_" + str(i))
                           for i in range(2)]

        # i : 9
        struct = Variable(self.state, "struct_0", is_struct=True)
        struct.attrs["attr_0"] = Variable(self.state, "attr_0")
        struct.attrs["attr_1"] = Function(self.state, "attr_1")
        self.test_objs.append(struct)

        super().__init__(test_method)

    def test_get_upper(self):

        self.state.upper.append(self.test_objs[8])
        self.assertEqual(self.state.get_upper(), self.test_objs[8],
                         "Failed to Get Upper which is a Function")

        self.state.upper.append(self.test_objs[9])
        self.assertEqual(self.state.get_upper(), self.test_objs[9],
                         "Failed to get Upper which is a Structure")

        self.state.upper.append(self.test_objs[0])
        self.assertEqual(self.state.get_upper(), self.test_objs[0],
                         "Failed to get Upper Which is a Variable")

    def test_get_struct_upper(self):

        self.state.upper.append(self.test_objs[8])
        self.assertIsNone(self.state.get_struct_upper(),
                          "Failed to segregate Function from Structure")

        self.state.upper.append(self.test_objs[9])
        self.assertEqual(self.state.get_struct_upper(), self.test_objs[9],
                         "Failed to get Structure in Upper")

        self.state.upper.append(self.test_objs[0])
        self.assertIsNone(self.state.get_struct_upper(),
                          "Failed to segregate Variable from Structure")

    def test_add_to_scope(self):

        # RESET SCOPE
        self.state.reset()

        test_objs = self.test_objs
        self.state.add_to_scope(test_objs[0])
        self.assertDictEqual(self.state.scope_map, {
            'start': {-1: [test_objs[0]]},
            'end': {-1: [test_objs[0]]},
            'temp_end': set()
        }, "Failed to Set Object with Default Start and End Params")

        self.state.add_to_scope(self.test_objs[1], 1)
        self.assertDictEqual(self.state.scope_map, {
            'start': {-1: [test_objs[0]], 1: [test_objs[1]]},
            'end': {-1: [test_objs[0], test_objs[1]]},
            'temp_end': set()
        }, "Failed to Set object Start with Default End")

        self.state.add_to_scope(self.test_objs[2], 1, 2)
        self.assertDictEqual(self.state.scope_map, {
            'start': {-1: [test_objs[0]], 1: [test_objs[1], test_objs[2]]},
            'end': {-1: [test_objs[0], test_objs[1]], 2: [test_objs[2]]},
            'temp_end': set()
        }, "Failed to Set Object start and end together")

        self.state.add_to_scope(self.test_objs[3], 3, edge="start")
        self.assertDictEqual(self.state.scope_map, {
            'start': {-1: [test_objs[0]], 1: [test_objs[1], test_objs[2]],
                      3: [test_objs[3]]},
            'end': {-1: [test_objs[0], test_objs[1]], 2: [test_objs[2]]},
            'temp_end': {test_objs[3]}
        }, "Failed to Add only Start of Object(ie. No Add or No Temp End)")

        self.state.add_to_scope(self.test_objs[3], 4, edge="end")
        self.assertDictEqual(self.state.scope_map, {
            'start': {-1: [test_objs[0]], 1: [test_objs[1], test_objs[2]],
                      3: [test_objs[3]]},
            'end': {-1: [test_objs[0], test_objs[1]], 2: [test_objs[2]],
                    4: [test_objs[3]]},
            'temp_end': set()
        }, "Failed to Change from Temp End to given End")

        self.assertRaises(
            ObjDelWithoutDecError,
            self.state.add_to_scope,
            self.test_objs[4], 4, edge="end"
        )

        self.assertRaises(
            MultipleObjDecError,
            self.state.add_to_scope,
            self.test_objs[1], 0, edge="start"
        )

        self.assertRaises(
            ObjDelWithoutDecError,
            self.state.add_to_scope,
            self.test_objs[1], 9, edge="end"
        )

    def test_find_obj_in_scope(self):

        test_objs = self.test_objs
        self.state.scope_map = {
            'start': {-1: [test_objs[0], test_objs[1], test_objs[5]],
                      1: [test_objs[2]], 4: [test_objs[6]],
                      5: [test_objs[3]], 8: [test_objs[4]]},
            'end': {-1: [test_objs[0]], 5: [test_objs[5]],
                    6: [test_objs[1]], 7: [test_objs[2]],
                    8: [test_objs[6]], 10: [test_objs[3]]},
            'temp_end': {test_objs[4]}
        }

        self.assertIs(self.state.find_obj_in_scope("test_var_0", -1, -1, -1),
                      test_objs[5],
                      "Local Scope Checking Order Problem")

        self.state.scope_map['end'][4] = self.state.scope_map['end'].pop(-1)
        self.assertIs(self.state.find_obj_in_scope("test_var_0", -1, -1, -1),
                      test_objs[0],
                      "Local Scope Checking Order Problem")

        expected_list = [test_objs[0], test_objs[5]]
        for i, obj in enumerate(self.state.find_obj_in_scope(
                "test_var_0", -1, -1, -1, all_=True)):

            self.assertIs(obj, expected_list[i],
                          "All Objects Found Return Problem: " + str(i))

        self.assertIs(self.state.find_obj_in_scope("test_var_0", 4, -1, -1),
                      test_objs[0],
                      "Scope Filtering Problem")

        self.assertIs(self.state.find_obj_in_scope("test_var_0", -1, 100, 0),
                      test_objs[0],
                      "Index Override Not Working Problem")

        self.assertIs(self.state.find_obj_in_scope("test_var_2", 6, 3, -1),
                      test_objs[6],
                      "Start Filtering Not Working")

        self.assertIs(self.state.find_obj_in_scope("test_var_2", 6, -1, 8),
                      test_objs[2],
                      "End Filtering Not Working")

        self.assertIs(self.state.find_obj_in_scope("test_var_4", 9, -1, -1),
                      test_objs[4],
                      "Temp End Addition Not Working")

        self.assertIsNone(
            self.state.find_obj_in_scope("test_var_-1", -1, -1, -1),
            "No Object Found Respond not matching")

    def test_find_in_scope(self):

        test_objs = self.test_objs
        self.state.scope_map = {
            'start': {-1: [test_objs[9]],
                      1: [test_objs[2]], 4: [test_objs[6]]},
            'end': {7: [test_objs[2]], 8: [test_objs[6]], 10: [test_objs[9]]},
            'temp_end': {}
        }

        self.assertIs(self.state.find_in_scope("test_var_2", 6, 3, 8),
                      test_objs[6],
                      "find_obj_in_scope not working")

        self.assertRaises(NameNotInScopeError,
                          self.state.find_in_scope, "NonExistent")

        self.assertIsNone(self.state.find_in_scope("NonExistent",
                                                   throw_error=False))

        self.assertListEqual(
            self.state.find_in_scope("test_var_2", 6, all_parts=True),
            [test_objs[2]],
            "All Flag Not Working"
        )

        self.assertIs(
            self.state.find_in_scope("struct_0"),
            test_objs[9],
            "Structure Search Failure"
        )

        self.assertRaises(MissingAttributeError,
                          self.state.find_in_scope,
                          "struct_0.attr_absent")

        self.assertIs(self.state.find_in_scope("struct_0.attr_0"),
                      test_objs[9].attrs["attr_0"],
                      "Attribute Fetch Error")

        self.assertListEqual(
            self.state.find_in_scope("struct_0.attr_0", all_parts=True),
            [test_objs[9], test_objs[9].attrs["attr_0"]],
            "All parts with attribute failed"
        )

        # Get Struct Object Block is Untested

        # FLAGS_EXPECTED = 31
        # print_flag_msg(FLAGS_EXPECTED, self.state.test_flags)
        # self.assertEqual(self.state.test_flags, FLAGS_EXPECTED)

    def test_add_line_after(self):
        pos, line = 1, ["Suffix Line"]
        self.state.add_line_after(pos, line)
        self.assertListEqual(self.state.suffix_lns, [(pos, line)])

    def test_add_line_before(self):
        pos, line = 1, ["Prefix Line"]
        self.state.add_line_before(pos, line)
        self.assertListEqual(self.state.prefix_lns, [(pos, line)])

    def test_reset(self):

        # Reset all file based attributes
        self.state.scope_map = self.state.all_objs = self.state.words = False
        self.state.upper = self.state.var_buff = self.state.func_buff = False
        self.state.prefix_lns = self.state.suffix_lns = False

        self.state.reset()

        self.assertEqual(self.state.scope_map,
                         {"start": {}, "end": {}, "temp_end": {}})
        self.assertEqual(self.state.all_objs, set())
        self.assertEqual(self.state.words, [])
        self.assertEqual(self.state.upper, [])
        self.assertEqual(self.state.var_buff, {})
        self.assertEqual(self.state.func_buff, {})
        self.assertEqual(self.state.prefix_lns, [])
        self.assertEqual(self.state.suffix_lns, [])

    def test_execute(self):
        flags = [0]
        self.state.execute("testing_modules/test_state",
                           {"flags": flags, "unused_kw": 0},
                           func="print_executed")

        self.assertEqual(flags, [31], "Execute Method of State is Not Working")


if __name__ == '__main__':
    unittest.main()
