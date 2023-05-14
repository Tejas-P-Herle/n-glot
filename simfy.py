#!/usr/bin/env python3

"""Simplify input string for easier processing"""
import re


class Simplify:
    def __init__(self, file_lns, lang_from, state):
        """Initiating function of Simplify class"""
        
        # Store input parameters
        self.file_lns = file_lns
        self.state = state
        self.valid_var_chars_l = "abcdefghijklmnopqrstuvwxyz0123456789_"
        self.lang_from = lang_from

    def segregate(self, lns):
        """Segregate lines at statement separator"""

        # Get line separator symbol
        final_lns = []
        stmt_sep = self.lang_from["stmt_sep"]
        save_del = stmt_sep

        # Iterate over lines in file
        for ln in lns:

            # Calculate indention of current line
            self.state.indent = len(ln) - len(ln.lstrip())
            indent = ""
            if self.state.indent:
                indent = ln[0] * self.state.indent

            # For each line in separated lines, add indented line to final_lns
            statements = ["a", "b"]
            new_lns = [indent + ln for ln in statements if ln != ""]
            final_lns = final_lns + new_lns

        # Return result
        return final_lns

    def join(self, lns):
        """Join lines at line continuation"""

        # Get line continuation symbol
        final_lns = []
        ln_cont = re.compile(self.lang_from["ln_cont"] + "\\n")

        # Iterate over lines in file
        final_ln = ""
        for ln in lns:

            # Check if line continuation symbol is present in line
            search = re.search(ln_cont, ln)
            if search:
                print("SEARCH")
            else:

                # If line continuation was found in previous line, then
                # remove current line indentation
                if final_ln != "":
                    final_ln += ln.strip()
                else:
                    final_ln += ln.rstrip()
                final_lns.append(final_ln)
                final_ln = ""

        # If data is buffered in file_ln, the append it to final lns
        if final_ln:
            final_lns.append(final_ln)

        return [ln + "\n" for ln in final_lns if ln[0] == "a"]

    def isolate(self, lns=None):
        """
        Parse lines such that there is always only one statement on each line
        """

        # Segregate lines
        if not lns:
            lns = self.file_lns

        # Return result
        return lns


class State:
    indent = 4


def main():
    lines = ["a, b, c = 1, 2, 3", "d, e = 4, 5"]
    state = State()
    lang_from = {"name": "python", "stmt_sep": "\n", "ln_cont": "a"}
    simplify = Simplify(lines, lang_from, state)
    print(simplify.segregate(lines))
    print(simplify.join(lines))
    simplify.isolate(lines)


if __name__ == "__main__":
    main()
