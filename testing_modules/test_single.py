import unittest
import ILC
import sys
import os
from io import StringIO
from unittest.mock import patch


def get_test_params():
    conv_inputs = []
    ILC_path = "/home/tejaspherle/Programming/n-glot/ILC/"
    file_format = ILC_path + "/testing_modules/conv_test_prgm_res/t{}_pj.out"
    for i in ["r", "0", "1", "3", "4", "5", "6", "7", "8"]:
        with open(file_format.format(i)) as file:
            conv_inputs.append([
                ["test_examples/t" + i + ".py", "java",
                 "test_examples/t" + i + ".java"],
                file.read()
            ])
    file_path = ILC_path + "beginner_programs/py_java_sols/"
    for file_name in os.listdir(file_path):
        full_path = file_path + file_name
        with open(full_path) as file:
            conv_inputs.append([
                [f"{full_path.replace('_sols', '')}.py",
                 "java",
                 f"{full_path.replace('_sols', '')}.java"],
                file.read()
            ])
    return conv_inputs


class TestSingle(unittest.TestCase):
    def test_single(self):
        # Store default stderr and stdout values
        self.default_stderr = sys.stderr
        self.default_stdout = sys.stdout

        # Replace system stderr and stdout to StringIO
        sys.stderr = StringIO()
        sys.stdout = StringIO()

        ip, op = get_test_params()[27]

        # Run test for all tests in valid_test_set
        with patch('builtins.input', side_effect=ip):
            ILC.run_ILC_CLI()
            conv_out = sys.stdout.getvalue().strip()
            self.assertEqual(
                op, conv_out.split("\n")[-1])
            sys.stdout.truncate(0)
            sys.stdout.seek(0)

        # Reset stdout to default value
        sys.stderr = self.default_stderr
        sys.stdout = self.default_stdout


if __name__ == '__main__':
    unittest.main()
