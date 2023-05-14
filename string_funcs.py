#!/usr/bin/env python3

"""Class containing basic string functions"""


from errors import BlockNotFoundError
from data_capsules.lines import Lines
from data_capsules.word import Word


class StringFuncs:

    brackets = {"(": ")", "[": "]", "{": "}"}
    basic_types = {"str", "float", "int", "bool", "None"}
    word_sep = "<>?:\"{}|~!@#$%^&*()+,/;'[]\\-=` \n\t\v"
    operators = None
    assignment_ops = None
    comparison_ops = None
    misc_ops = None
    ref_ops = None

    unary_ops = None
    binary_ops = None
    custom_ops = None

    matchable = None
    long_symbols = None

    eqn_ops = None
    eqn_terminators = None

    ALNUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._"
    stmt_end = {"stmt_term", "blk_start", "blk_end"}

    def __init__(self, state, convs_space):
        """Initiation function of StringFuncs class"""

        self.state = state
        self.tok_type = state.database.from_["from"]["tok_type"]
        self.get_type_funcs_from = convs_space.get_type_from
        self.setup_symbols()

    def change_word(self, word, new_str):
        """Change word to new_value"""

        new_word = self.state.new_capsule.word(new_str, type_=word.tok_type)
        new_word.index = word.index
        self.state.words[word.index] = new_word
        self.state.conversions.skim(word.index, word.index+1,
                                    level=word.tags["stmt"].level)

    def setup_symbols(self):
        """Get symbols use able in from language source code"""

        symbol_sets = self.state.execute(self.tok_type, {}, func="get_symbols")
        self.matchable, self.assignment_ops, self.misc_ops = symbol_sets[:3]
        self.comparison_ops, self.unary_ops, self.binary_ops = symbol_sets[3:6]
        self.ref_ops, self.custom_ops, self.eqn_terminators = symbol_sets[6:9]

        self.eqn_ops = self.comparison_ops.union(set(self.unary_ops)).union(
                        set(self.binary_ops)).union(set(self.ref_ops))

        self.operators = {s for symbol_set in symbol_sets for s in symbol_set}
        self.long_symbols = {}
        for long_symbol in {ls for ls in self.operators if len(ls) > 1}:
            branch = self.build_tree(long_symbol, self.long_symbols)
            branch["symbol"] = long_symbol

    @staticmethod
    def build_tree(path, tree):
        """Build tree"""

        branch = tree
        for choice in path:
            if choice not in branch:
                branch[choice] = {}
            branch = branch[choice]
        return branch

    @staticmethod
    def navigate_tree(i, string, tree):
        """Navigate tree"""

        branch, len_str = tree, len(string)
        while i < len_str and string[i] in branch:
            branch = branch[string[i]]
            i += 1
        return branch

    def tokenize(self, string):
        """Tokenize string into tokens"""

        i, word_buff, skip_till, skip_type, escaped = 0, "", "", None, False
        len_str = len(string)
        while i < len_str:
            char = string[i]
            if not(char.isalnum() or char == "_" or
                   (char == "." and word_buff and word_buff.isnumeric())):
                if word_buff:
                    yield Word(word_buff, type_=skip_type)
                    word_buff = ""

                skip_till, skip_type = self.state.execute(
                    self.tok_type,
                    {"string": string, "i": i}, func="check_skip")
                if skip_till == "":
                    symbol = Word(self.match_long_symbols(i, string))
                    i += len(symbol) - 1
                    yield symbol
                else:
                    end = self.find_sub_str(i+1, skip_till, string,
                                            escape=skip_type == "str")
                    yield Word(string[i:end], type_=skip_type)
                    i, skip_type = end - 1, None
            else:
                word_buff += char
            i += 1

        # Yield remaining buffer
        if word_buff:
            yield Word(word_buff)

        # Yield ending word
        yield Word("FILE END", type_="FILE END")

    @staticmethod
    def find_sub_str(i, sub_str, string, escape):
        """Search for char starting from index i"""

        len_sub_str = len(sub_str)
        len_str, escaped = len(string), False
        while i < len_str:
            escaped = False if escaped or i == 0 else string[i-1] == "\\"
            if string[i:i+len_sub_str] == sub_str and not(escape and escaped):
                return i+len_sub_str
            i += 1
        return len_str

    def match_long_symbols(self, i, string):
        """Match long symbols starting from char at index i"""

        branch = self.navigate_tree(i, string, self.long_symbols)
        return branch["symbol"] if "symbol" in branch else string[i]

    def handle_brackets(self, word, brackets_stack):
        """Handle brackets"""

        # Check if a new bracket is found
        if isinstance(word, str) and word in self.brackets:
            
            # If it is found, then save the closing bracket expected
            brackets_stack.append(self.brackets[word])

        # Check if a bracket is closed
        elif brackets_stack and word == brackets_stack[-1]:
            
            # If it is closed, then update brackets stack
            brackets_stack.pop(-1)

    def get_lns(self, array, lns=None):
        """Get Lines instances in array"""

        if lns is None:
            lns = []
        for ln in array:
            if isinstance(ln, Lines):
                lns.append(ln)
                self.get_lns(ln, lns)
        return lns

    def get_collection_queue(self, words, i=0, end=-1, ignore=False):

        brackets_stack = []
        queue = []
        base = i
        start = i
        ignored = False
        end = len(words) if end == -1 else end
        for j, word in enumerate(words[i:end]):

            # Check if word is a comma symbol, all brackets must be matched
            if word == "," and not brackets_stack:
                
                # If so, save start and end of queue item
                queue.append((start, base + j))
                start = base + j + 1

            # Handle brackets
            else:
                if not ignore:
                    self.handle_brackets(word, brackets_stack)
                else:
                    ignored = True

        # Add ending value to queue
        if (start, end) not in queue:
            queue.append((start, end))

        # If collection brackets are ignored, then remove closing bracket
        if ignored:
            queue[-1] = (queue[-1][0], queue[-1][1])
        
        # Return queue
        return queue

    @staticmethod
    def condense(indexes):
        """Condense indexes into ranges"""

        start = -1
        prev = -2
        ranges = []
        i = 0
        for i in indexes:
            new_rng = True
            if not isinstance(i, tuple) and i == prev + 1:
                prev += 1
                new_rng = False
            if new_rng:
                if start != -1:
                    ranges.append((start, prev+1))
                if isinstance(i, tuple):
                    ranges.append(i)
                    start = prev = -1
                else:
                    prev = start = i
        if start != -1:
            ranges.append((start, i+1))
        return ranges

    @staticmethod
    def find_in_list(list_, elem, start):
        for i in range(start, len(list_)):
            if list_[i] == elem:
                return i
        return -1

    @classmethod
    def contains(cls, super_list_a, list_b):
        """Returns if list_b is a sub_set of super_list_a(in the same order)"""

        start_pt = list_b[0]
        start = 0
        found_index = cls.find_in_list(super_list_a, start_pt, start)
        while found_index != -1:
            for i, el in enumerate(list_b):
                if super_list_a[found_index + i] != el:
                    break
            else:
                return True
            start = found_index + 1
            found_index = cls.find_in_list(super_list_a, start_pt, start)
        return False

    def get_words(self, lns):
        """Return next word in lines"""

        blocking_type = self.state.database.from_meta["blocking_type"]
        lns = lns if isinstance(lns, str) else "".join(lns)
        words = []
        token_gen = self.tokenize(lns)
        token = next(token_gen)
        comment_prefix = self.stmt_end

        self.state.progress_bar.increment()

        while token.tok_type != "FILE END":

            # Check for block starts
            if token == "\n" and blocking_type == "indent":

                # Store new line
                words.append(Word(token, type_="stmt_term"))

                # Count spaces or tabs
                indentation = 0
                token = next(token_gen)
                while token.tok_type == "comment":
                    token = next(token_gen)
                while token in [" ", "\t"]:
                    indentation += 1
                    token = next(token_gen)
                    if token.tok_type == "comment":
                        indentation = 0
                        token = next(token_gen)

                # Check if indentation level has increased
                if self.state.indents[-1] < indentation:
                    
                    # Store indent token
                    words.append(Word("INDENT", type_="blk_start"))
                    self.state.indents.append(indentation)

                # Check if Indentation level has decreased
                elif self.state.indents[-1] > indentation:
                    
                    # Store dedent token(s)
                    indent_loc = self.state.indents.index(indentation)
                    for _ in range(int(len(self.state.indents)-indent_loc-1)):
                        words.append(Word("DEDENT", type_="blk_end"))
                        self.state.indents.pop(-1)

            # Don't store lone spaces, comments and docs
            if not(token == " " or token == "\t" or token.tok_type == "comment"
                   or token.tok_type == "FILE END"):
                words.append(token)

            if (token.tok_type == "comment" and
                    words[-1].tok_type not in comment_prefix):
                words.append(Word(self.state.from_meta["stmt_term"],
                                  type_="stmt_term"))

            if token.tok_type != "FILE END":
                token = next(token_gen)

        self.state.progress_bar.increment()

        for i, word in enumerate(words):
            if word.tok_type is None:
                detected_type = self.state.execute(
                    self.tok_type, {"token": word, "index": i, "words": words},
                    func="detect")

                if detected_type:
                    words[i].tok_type = detected_type
        return words

    def get_block(self, start):
        """Get one block from the words list starting from 'start'"""

        # Initialize required variables
        words = self.state.words
        len_words = len(words)
        i = start
        prefix_i = 0
        while i < len_words:

            # Check if 'i' is block_start
            if words[i].tok_type == "blk_start":
                i = prefix_i = i+1
                break

            # Increment i
            i += 1

        # If start of block not found raise error
        if not prefix_i:

            err_msg = "Block start not found, start={}"
            raise BlockNotFoundError(err_msg.format(start))

        block_stack = 1
        while i < len_words:

            # Check if block_stack is empty
            if not block_stack:

                # Then return i as end of block
                return words[start:prefix_i], words[prefix_i:i], i

            # Add to block stack if word is a block start token
            if words[i].tok_type == "blk_start":
                block_stack += 1

            # Decrease from block stack if word is a block end token
            elif words[i].tok_type == "blk_end":
                block_stack -= 1

            # Increment Counter
            i += 1

    @staticmethod
    def is_whitespace(i, words):
        """Check if word is a whitespace"""

        return not words[i].strip() or words[i] in ["INDENT", "DEDENT"]

    def find_prev_word(self, i):
        """Find previous non whitespace word"""
        
        # While word is whitespace, decrement counter
        while not(i and self.state.words[i]
                  and not self.is_whitespace(i, self.state.words)):
            i -= 1
        return i

    def get_identifier_name(self, i):
        """Finds index of identifier name(get attribute name requested)"""
        
        # Jump to next word while word is followed by '.'
        while self.state.words[i+1] == ".":
            i += 2
        return i

    def pair_char(self, words, index):
        """Pair matching characters"""

        # Check if character is matchable
        if not (words[index] in self.matchable
                or words[index] in self.matchable.values()):
            raise ValueError("{} is not matchable".format(words[index]))

        # Initiate required variables
        matchable = self.matchable
        start = words[index]
        step = -1
        if start in matchable:
            end, step = matchable[start], 1
        else:
            end = list(matchable)[list(matchable.values()).index(start)]
        stack = 1
        final_words = []

        # While matching character is not found, keep on searching for it
        while stack:

            # If end character is found, then decrease stack
            index += step
            if words[index] == end:
                stack -= 1
            # If start character is found, then increase stack
            elif words[index] == start:
                stack += 1

            # Save current word
            if stack:
                final_words.append(words[index])

        return final_words, index
    
    @staticmethod
    def find_next(words, start, end_str_list, reverse=False):
        """Return index of first occurrence of any word in end_str_list"""
        
        # Convert end_str_list to a list
        if not isinstance(end_str_list, list):
            end_str_list = [end_str_list]

        # Iterate over words
        word_list = words[start::-1] if reverse else words[start:]
        for i, word in enumerate(word_list):
            
            for end_str in end_str_list:

                # If word is found, return its index
                if end_str == word:
                    return start - i if reverse else start + i
        
        # Return -1 in case match was not found
        return -1

    @staticmethod
    def find_seg(words, seg, start=0):
        """Find segment in list"""

        if not seg:
            return -1

        j = start_i = 0
        len_seg = len(seg)
        for i, word in words.items():

            # Wait till i is greater than start
            if i < start:
                continue

            # Check match
            if word == seg[j]:

                # Reset start_i
                if j == 0:
                    start_i = i
                j += 1

                # Find out letters left to match
                diff = i-start_i+1
                if diff >= len_seg:

                    # Check if all characters are matched
                    if diff == len_seg == j:
                        return start_i

                    # If not consider it as a match due to jump and reset j
                    j = 0
        return -1
    
    def find_start(self, index, words=None, detectors=None):
        """Get start of statement(point to first word of statement)"""

        words = words if words else self.state.words
        detectors = detectors if detectors else ["\n", ";"]
        i = self.find_next(words, index, detectors, reverse=True)
        if i == -1:
            raise ValueError("Start of statement not found")
        end = len(words)
        while i < end:
            
            if not self.is_whitespace(i+1, words):
                return i
            i += 1

    def find_end(self, i, words=None, detectors=None):
        """Find end of statement"""
        
        words = words if words else self.state.words
        detectors = detectors if detectors else ["\n", ";"]
        end = len(words)
        brackets_stack = []
        while i < end:
            if words[i] in detectors and not brackets_stack:
                return i
            self.handle_brackets(words[i], brackets_stack)
            i += 1

    @staticmethod
    def match_indent(words, index):
        """Get lines with lower indent levels"""

        # Get initial indent
        while words[index][0] != 7:
            index += 1
        indent_stack = 1

        # Till indent stack is zero, keep adding words to final_words
        final_words = []
        while indent_stack:
            index += 1
            final_words.append(words[index])
            if words[index][0] == 7:
                indent_stack += 1
            elif words[index][0] == 8:
                indent_stack -= 1

        return final_words

    def get_element(self, words=None, i=0, end=-1, base=0):
        """Get element(single array, number, string,...) starting from i"""

        words = self.state.words if words is None else words
        end = len(words) if end == -1 else end

        word_buff = []
        skip_till = -1
        while i < end:
            if i < skip_till:
                i += 1
                continue
            if words[i] == ",":
                word_val = self.state.new_capsule.variable_value(
                    word_buff, self.state,
                    base + i - len(word_buff), base + i)
                yield word_val
                word_buff.clear()
            else:
                word_buff.append(words[i])
                if hasattr(words[i], "tags") and "pair" in words[i].tags:
                    for _ in range(words[i].tags["pair"] - words[i].index):
                        i += 1
                        word_buff.append(words[i])
            i += 1
        if word_buff:
            word_val = self.state.new_capsule.variable_value(
                word_buff, self.state,
                base + i - len(word_buff), base + i)
            yield word_val

    def solve_type(self, val):
        """Return operations and operands in order dictated by BODMAS"""

        # TODO: Needs debugging and refining
        func_ops = {"."}

        # Use from language basic operations for result consistency
        all_types = self.state.all_types_from
        get_type_funcs = self.get_type_funcs_from

        # Solve brackets
        for i, tok in enumerate(val):
            if tok in self.matchable:
                _, j = self.pair_char(val, i)

                type_ = self.solve_type(val[i+1:j])
                group_opr = tok + self.matchable[tok]
                if tok == "(" and tok.tok_type == "pair_start_symbol":
                    set_start, set_end, copy_opr_capsule = i, j+1, False
                else:
                    set_start, set_end, copy_opr_capsule = i+1, j, True
                val.set_type_solve_list(set_start, set_end, type_, group_opr,
                                        all_types, copy_opr_capsule)

        # Run custom operators on value
        for op, op_attrs in self.custom_ops.items():

            # Initiate counter
            i = 1
            step = op_attrs["associativity"]

            # Loop over value tokens
            while True:
                try:
                    # Check if token is in current operators
                    if val[i*step] == op:

                        # Replace values with operators
                        val[i].tags["operator_type"] = "custom"
                        val_copy = val.list_copy()
                        self.state.execute(
                            get_type_funcs,
                            {"state": self.state, "val": val, "i": i,
                             "all_types": all_types}, "custom_ops",
                            add_default_args=False)
                        if val == val_copy:
                            i += 1
                        # get_type_funcs.custom_ops(self.state, val, i, all_types)
                    else:
                        i += 1
                except IndexError:
                    break

        # Solve unary operators
        for opr in self.unary_ops:
            step = self.unary_ops[opr]["associativity"]
            doo = self.unary_ops[opr]["doo"]
            i = 0 if step == 1 else len(val) - 1
            end = -1 if step == -1 else len(val)
            while i != end:
                if (isinstance(val[i], str) and val[i] == opr
                        and (i == 0 or isinstance(val[i-1], str))
                        and i < len(val)-1 and not isinstance(val[i+1], str)):
                    res = val[i+doo].get_opr_res(val[i])
                    val[i].tags["operator_type"] = "unary"
                    if res:
                        start, stop = i, i+2
                        val.solve_operator(start, stop, all_types[res])
                        if step == 1:
                            end = len(val)
                i += step

        # Run function operators on value
        for op in func_ops:
            for i, eq_part in enumerate(val):
                if eq_part == op:
                    val[i].tags["operator_type"] = "ref"
                    self.state.execute(
                        get_type_funcs,
                        {"op": op, "i": i, "val": val, "all_types": all_types},
                        "run_func_ops")
                    # get_type_funcs.run_func_ops(op, i, val)

        for i, tok in enumerate(val):
            if (hasattr(val[i], "tok_type") and val[i].tok_type == "operator"
                    and tok not in [")", "]"]):
                if not val[i].tags["lhs"].type_solved:
                    val[i].tags["lhs"].type_from = val[i-1]
                if not val[i].tags["rhs"].type_solved:
                    val[i].tags["rhs"].type_from = val[i+1]

        # Run other operators on value
        for op, op_attrs in self.binary_ops.items():

            # Initiate counter
            i = 1
            step = op_attrs["associativity"]

            # Loop over value tokens
            while True:
                try:
                    # Check if token is in current operators
                    if val[i*step] == op:

                        # If it's a comparison operator, then replace with bool
                        j = i if step == 1 else len(val) - i
                        val[j].tags["operator_type"] = "binary"
                        if val[j] in self.comparison_ops:
                            res = all_types["bool"]
                        else:
                            if not hasattr(val[j-1], "type_"):
                                raise self.state.errors.TypeSolveFailureError(
                                    f"Invalid Value Pattern {val}\n"
                                    + "Types Must be separated by operators")
                            # Replace values with operators
                            res = val[j-1].get_opr_res(val[j], val[j+1])

                        # Handle Failure Case
                        if res == val[j-1:j+1] + [val[j+1].type_]:
                            i += 1
                        else:
                            # val[i-1:i+2] = [all_types[res]]
                            type_ = (all_types[res]
                                     if isinstance(res, str) else res)
                            val.solve_operator(j-1, j+2, type_)
                    else:
                        i += 1
                except IndexError:
                    break
        return val
