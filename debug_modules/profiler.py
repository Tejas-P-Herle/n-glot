
import cProfile
# from database import DataBase
# from code_processor import CodeProcessor

import test_all


def run_ILC():
    # database = DataBase()

    # code_processor = CodeProcessor("test_examples/t0.py",
    #                                "test_examples/t0.java",
    #                                "python", "java", database)
    #                                
    # code_processor.convert()

    runner = test_all.unittest.TextTestRunner()
    runner.run(test_all.load_all_tests())


pr = cProfile.Profile()
pr.enable()
run_ILC()
pr.disable()

pr.print_stats(sort="tottime")
