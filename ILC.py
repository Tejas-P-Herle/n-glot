#!/usr/bin/env python3

"""
Inter Language Converter(ILC)
Converts Source Code from language A to B
"""

from debug_modules.logger import Logger
from validate import *
from code_processor import CodeProcessor
from progress_bar import ProgressBar
from database import DataBase
from ILC_GUI.ILC_app import ILCApp
import sys


# Initialize ilc_logger
ilc_logger = Logger("ILC")
code_processor = None


def run_ILC_CLI():
    """Main ILC application"""

    global code_processor

    # Create user input string template
    input_msg = "{} or 'q' to abort: "

    # Create input messages
    input_file_path_msg = input_msg.format("Path to Program File")
    input_language_msg = input_msg.format("To Language")
    input_file_name_msg = input_msg.format("Output File Path")
    
    # Initiate required classes
    database = DataBase()
    validate = Validate(database.languages)

    #
    # Get User Input
    #

    validate_methods = [
        (validate.validate_file_path, "file_path", input_file_path_msg),
        (validate.validate_language, "lang_to", input_language_msg),
        (validate.validate_file_name, "outfile_path", input_file_name_msg),
    ]

    # Validate user input
    for func, var_name, input_str in validate_methods:

        # Get input from user
        user_input_val, error = get_user_input(func, var_name, input_str)

        # Check if input is currently at to language 
        # and input language is same as output language
        if (var_name == "lang_to"
                and user_input_val.lower() == validate.lang_from):
            error = "Language of file is same as to conversion language"

        # If error encountered, print error and exit
        while error:

            # Parse the error
            print(error, file=sys.stderr)

            # Get input from user
            user_input_val, error = get_user_input(func, var_name, input_str)

            # Check if input is currently at to language 
            # and input language is same as output language
            if (var_name == "lang_to"
                    and user_input_val.lower() == validate.lang_from):
                error = "Language of file is same as to conversion language"
    #
    # Start Conversion
    #

    print(validate.lang_from, "->", validate.lang_to)

    # Create code processor instance
    progress_bar = ProgressBar("cli")
    code_processor = CodeProcessor(validate.in_file, validate.out_file,
                                   validate.lang_from, validate.lang_to,
                                   database, progress_bar)
                                   
    # Run convert method of code processor
    converted_code = code_processor.convert()

    print(converted_code)

    # # Write converted file to disk
    # error = code_processor.write_file_to_disk()

    # # Check if error occurred
    # if error:
    #     if error == 5:
    #         Error.parse(5, quit_ = True)
    #     Error.parse(error, user_input=False)
    return 0


def get_user_input(func, var_name, input_str):
    """Gets input from user and runs standard protocols"""

    # Get user input
    var = str(input(input_str))

    # Log debug message
    ilc_logger.log("VAR[NAME]", var_name, var)

    # Check if user requests abort
    if var == "q":
        print("User Abort")
        sys.exit()

    # Run validation
    return var, func(var)


def run_ILC_GUI():
    """Main ILC application"""

    global code_processor

    # Initiate required classes
    database = DataBase()
    app = ILCApp(Validate(database.languages))
    # inputs = app.get_inputs()
    dir_ = "/home/tejaspherle/Programming/ILC/beginner_programs/py_java_ct"
    inputs = [f"{dir_}/XL_program.py", f"{dir_}/XL_Program.java",
              "python", "java"]

    # print("SHOWING WINDOW") # progress_window.show() # timer = QTimer()
    # timer.start(5000) # timer.timeout.connect(progress_window.quit_app)

    #
    # Start Conversion
    #

    # Create code processor instance
    if inputs is not None:
        status_window = app.main_window.build_status_window()
        progress_bar = ProgressBar("gui", status_window)
        code_processor = CodeProcessor(*inputs, database, progress_bar)

        # Run convert method of code processor
        converted_code = app.main_window.show_progress(
            code_processor.convert, status_window)
        print(converted_code)

    app.main_window.show_complete_window()

    return 0


# def implement_corrections():
#     """Implement the corrections learnt from the user"""
#
#     global code_processor
#
#     # Read new conversions from data base
#     code_processor.read_conv_db()
#
#     # Run the new conversions
#     code_processor.run_regex_conversion()
#
#     # Write the output file to disk
#     code_processor.write_file_to_disk(ask_overwrite=1)


def main():
    """Function run on file open"""

    # Run ILC CLI Version
    run_ILC_CLI()

    # Run ILC GUI Version
    # run_ILC_GUI()

    # Request corrections for unknown conversion
    # corrections.get()

    # Learn corrections
    # corrections.digest(user_input["lang_from"], user_input["lang_to"])

    # Implement corrections
    # implement_corrections()


if __name__ == "__main__":
    main()
