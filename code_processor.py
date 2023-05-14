#!/usr/bin/env python3

"""Convert input code between languages"""
from conversions import Conversions
from debug_modules.logger import Logger
from simplify import Simplify
from state import State, Lines
from progress_bar import ProgressBar


# SKIM: Scan and convert variables and save function information
# RESOLVE: Resolve library functions, statements and return types

# TODO: GENERAL
# TODO: CURRENT GOAL: Create Conversions Space, Conversion Options
#                     and convert successfully
# TODO: CURRENT SUBTASK:
#       1. Remove modifier attribute of func_usage
#       2. Change double to float for java basic types
#       3. Link based on to-language scope,
#            ie. var declared in if body in python when conv to java
#            should not be considered as the same object as var outside
#       4. Generic collection types and wildcard types
#       5. Split up state class into sub classes
#       6. Write Test Classes
#       7. Add Conversion Memory(Memory accessible by all conv funcs)
#       8. enforce one function name all function definitions
#       9. implement area based conversions(conversion selection)
#      10. Add global keyword support(Create assume_global buffer)
#      11. make separate tok_type for reserved keywords
#
#  CleanUps:
#     MAJOR:
#       change function defs to function linked_objs
#         ie. enforce one definition per function, overloading to be
#             handled by linked_objs
#       split conversions methods into multiple files
#     MID:
#       self object value and type standardization
#       Usage of minimum possible hardcoded constants w/ explanation
#       Standardize Usage of state param, state should always be 1st
#       parameter of func def
#     MINOR:
#       Add is_struct attribute to all classes
#
#  Minor Tasks:
#  * Multi Conversion Storage, Assembler
#  * Variable Set's with function values already have a semicolon
#  * Add Multiline Comments Support
#  * Multiline Conversions
#  * Convert Replacement Type to Index Type
#  * Upgrade to Declare, Initialize and Call (and Declare, Set and Get)
#  * Bug Fix: Missing class __init__ conv first line
#  * Testing Modules
#  * GUI
#  * Chose conversion based on requirement (speed, readability etc)
#  * Credit based System for conversion acceptance
#  * Previous input testing for conversions
#  * Predictor
#  * Auto-Learn Compatibility
#  * Goal: Self Conversion (Preferably after Auto-Learn)


class CodeProcessor:
    converted_code = ""

    def __init__(self, in_file, out_file, lang_from, lang_to, database,
                 progress_bar):
        """Initiation function for CodeProcessor class"""

        # Set class attributes
        self.in_file = in_file
        self.out_file = out_file
        database.setup(lang_from, lang_to)
        self.database = database
        self.logger = Logger("CodeProcessor", tee=False)
        self.logger.log("STARTED")
        self.progress_bar = progress_bar

        # Open database
        self.state = State(database, out_file, progress_bar)

        # Initiate conversions class
        self.conversions = Conversions(self)
        self.state.conversions = self.conversions

    def convert(self, code="", index=None):
        """Initiate file conversion"""

        # Read input file and simplify it
        remove_extra_nl = False
        if code == "":
            with open(self.in_file) as file:
                code = file.readlines()

            # Reset state if not running code snippet
            self.state.reset()
        elif isinstance(code, str):
            code = [code]
            remove_extra_nl = True

        # Set file lines in state
        is_base_run = index is None
        prev_word_space = "base"
        prev_cnv_file_lns = prev_conv_lns_buff = prev_pathways = None
        prev_core_comps = prev_progress_bar = prev_locked_convs = None
        prev_obj_buffs = scope_copy = None

        simplify = Simplify(code, self.database.from_, self.state)
        file_lns = simplify.isolate()

        if remove_extra_nl:
            file_lns[-2] = file_lns[-2][:-1]

        # Preprocess string lines of file for splitting into words
        self.logger.log("Preprocessing file lines...")
        file_lns = self.conversions.preprocess(file_lns)

        words = self.state.file_lns_to_words(file_lns)

        if is_base_run:
            self.state.reset()
            self.state.words = words
        else:

            prev_word_space = self.state.words.chosen_word_space
            scope_copy = self.state.scope.copy()
            self.state.scope = self.state.words[index].tags["stmt"].scope_copy
            self.state.words.add_word_space(index, words)
            self.state.words.chosen_word_space = index
            prev_cnv_file_lns = self.state.cnv_file_lns

            convs = self.state.conversions
            prev_pathways = convs.pathways
            prev_core_comps = convs.core_comps
            prev_conv_lns_buff = convs.conv_lns_buff
            prev_progress_bar = self.state.progress_bar
            prev_locked_convs = convs.conversions_space.locked_convs

            prev_obj_buffs = self.state.get_obj_buffs()
            self.state.reset_obj_buffs()

            convs.conversions_space.locked_convs = set()
            self.state.cnv_file_lns = Lines(self.state)
            self.state.converting_snippet = True
            self.state.progress_bar = ProgressBar()

        # Standardize file
        self.logger.log("Standardizing file...")
        self.conversions.standardize()

        # Skim over file
        self.logger.log("Skimming over file...")
        self.conversions.skim()

        if is_base_run:
            self.state.get_helper_class_identifier()

        self.logger.log("Setting up for Conversions...")
        self.conversions.setup_conversion()

        self.logger.log("Find Object Modifier Conversions")
        conv_filters = self.conversions.conversions_space.conversion_filters
        self.conversions.find_mod_convs()

        # Run Object Modifier Conversions
        self.logger.log("Running Object Modifier Conversions...")
        conv_filters.default_settings = conv_filters.LARGEST_SIZE
        self.conversions.run_mod_conv()

        # Solve types
        self.state.allow_type_solve = True
        self.logger.log("Solving Types...")
        self.conversions.solve_types(
            main_solve=(not self.state.converting_snippet))

        # Find all Available conversions for words
        self.logger.log("Find Conversions...")
        self.conversions.find_conversions()

        # Single out the best conversion from all found conversions
        self.logger.log("Check Conversions...")
        # settings = conv_filters.SAFE
        self.conversions.check_conversions()

        # Find type based conversions
        self.logger.log("Finding Type Conversions...")
        self.conversions.find_type_convs()

        # Convert using best found conversion
        self.logger.log("Converting Source Code...")
        self.conversions.convert_base()

        # Add N-Glot Helper functions
        if is_base_run:
            self.state.execute(
                self.conversions.add_nglot_funcs, func="add_funcs")

        # print("{:4}| {:22}| {}".format("Sl", "Word", "Tags"))
        # print("\n".join(["{:4}| {:22}| {}".format(i, str([w]), w.tags)
        #                for i, w in enumerate(self.conversions.state.words)]))
        self.converted_code = self.conversions.get_result(
            main_str_build=prev_cnv_file_lns is None)

        self.state.words.chosen_word_space = prev_word_space
        if prev_cnv_file_lns is not None:
            self.state.scope = scope_copy
            self.state.cnv_file_lns = prev_cnv_file_lns
            convs = self.state.conversions
            convs.pathways = prev_pathways
            convs.core_comps = prev_core_comps
            convs.conv_lns_buff = prev_conv_lns_buff
            convs.conversions_space.locked_convs = prev_locked_convs
            self.state.progress_bar = prev_progress_bar
            self.state.set_obj_buffs(prev_obj_buffs)
        else:
            self.progress_bar.increment()

        return self.converted_code
