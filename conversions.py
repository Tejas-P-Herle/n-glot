#!/usr/bin/env python3

"""Handle conversions"""

import os
import re
from string_funcs import StringFuncs
from obj_classes.func_classes.function_stmt import FunctionStmt
from obj_classes.var_classes.variable_stmt import VariableStmt, Variable
from debug_modules.logger import Logger
from conversion_classes.conversion import Conversion
from conversion_classes.conversions_space import ConversionsSpace
from data_capsules.lines import Lines
from bisect import bisect_right
from type_classes.solve_types import SolveTypes
from skimmer_classes.skimmer import Skimmer, Inspector
from learner import Learner


class Conversions:
    def __init__(self, code_processor):
        """Initiation function for Conversions class"""

        # Save input parameters
        self.code_processor = code_processor

        # Define class attributes
        self.state = state = code_processor.state
        self.database = code_processor.database
        self.file_name = self.state.out_file_path.rsplit(
            "/", 1)[-1].split(".")[0]
        self.stmt_end = ["stmt_term", "stmt_sep"]
        self.logger = Logger("Conversions", tee=False)

        self.conversions_space = convs_space = ConversionsSpace(state)
        self.learner = Learner(state)

        self.conv_filters = convs_space.conversion_filters
        self.func_call_convs = convs_space.func_call_convs

        # Setup state object
        self.str_funcs = StringFuncs(state, convs_space)
        state.str_funcs = self.str_funcs
        state.get_lib_obj = Inspector.get_lib_obj

        # Setup links to used database functions
        self.get_type_from = convs_space.get_type_from
        self.import_lib_func = convs_space.import_lib_func

        from_funcs = self.state.database.from_["from"]

        self.default_vars = from_funcs["defaults"]

        self.stmt_classifier = from_funcs["stmt_classifier"]
        self.stmt_structs = from_funcs["stmt_structs"]

        from_lang_convs = self.database.to["to"]
        self.conv_func = convs_space.conv_func
        self.conv_var = convs_space.conv_var
        self.boilerplate_to = convs_space.boilerplate_to
        self.add_nglot_funcs = convs_space.add_nglot_funcs
        self.check_attrs = convs_space.check_attrs_conv["code"]
        self.get_coll_type = convs_space.get_coll_type
        self.from_lang_convs = from_lang_convs

        # Store statement parser
        self.func_stmt = FunctionStmt(state)
        self.var_stmt = VariableStmt(state)
        self.skimmer = None

        # Store from and to boilerplate handlers
        self.main_stmts = convs_space.main_stmts

        # Store preprocessor and standardizer modules
        self.preprocessor = from_funcs["preprocessor"]
        self.standardizer = from_funcs["standardize"]

        # Store pathways
        self.pathways = {}

        # Store core components
        self.core_comps = {}

        # Store converted Lines in buffer
        self.conv_lns_buff = []

    def to_words(self, string=None):
        """Convert string(or file lines if string is None) to list of words"""

        # If string is not provided, then use file string as default
        if isinstance(string, type(None)):
            # Return state words
            return self.state.words
        elif isinstance(string, str):
            # Convert to words and return it
            return self.str_funcs.get_words(string)
        else:

            # If input is already a list of words, don't reprocess it
            return string

    def preprocess(self, file_lns):
        """Preprocess file string for splitting it into words"""

        # Run standardizer and save result
        return self.state.execute(self.preprocessor,
                                  {"re": re, "file_lns": file_lns},
                                  func="preprocess")

    def standardize(self):
        """Standardize file for easier conversion logic"""

        # Run standardizer and save result
        self.state.progress_bar.increment()
        self.state.words = self.state.execute(self.standardizer,
                                              func="standardize")

        # Add default variables to scope
        self.state.execute(self.default_vars, {"Variable": Variable})

    def skim(self, i=0, skim_end=-1, level=0):
        """Skim over file lines and create pointers to
        Variables and Function"""

        is_main_skim = i == 0 and skim_end == -1

        # Create new Skimmer
        if is_main_skim:
            self.state.progress_bar.increment()
        skimmer = Skimmer(self.state)
        self.skimmer = skimmer

        skimmer.inspect(i, skim_end, level)

        if is_main_skim:
            self.state.progress_bar.increment()
            skimmer.tag_tokens()
        else:
            tag_start = self.state.words[i].tags["stmt"].start
            tag_end = self.state.words[skim_end].tags["stmt"].end
            upper = self.state.get_upper(tag_start)
            skimmer.tag_tokens_range(tag_start, tag_end, upper)
            return

        self.state.progress_bar.increment()
        skimmer.tag_unused_tokens()

        # Remove padding words
        skimmer.stmts.pop(next(iter(skimmer.stmts.keys())))
        skimmer.stmts.pop(next(iter(reversed(skimmer.stmts.keys()))))

        self.state.progress_bar.increment()
        skimmer.classify_stmts()
        if i == 0 and skim_end == -1:
            self.state.global_stmts = skimmer.stmts

        skimmer.set_globals()

    def solve_types(self, main_solve=False):
        """Solve types for all functions and variables"""

        solve_types = SolveTypes(self.state)
        solve_types.solve(main_solve=main_solve)

    def match_conv(self, conv_link, match_params, conv_set="conversions"):
        """Match Conversions"""

        convs = self.conversions_space.run_matcher_params(
            conv_link, match_params)
        for conv in convs:
            self.conversions_space.add_conv(conv, conv_set=conv_set)
        return convs

    def find_conversions(self, start=0, end=-1):
        """Find Conversions for all words"""

        conv_space = self.conversions_space
        kw_convs = {}
        word_map = conv_space.word_map

        words = self.state.words
        len_words = len(words)

        if end == -1:
            end = len_words

        # Iterate over words
        self.state.progress_bar.increment()
        i = start
        while i < end:

            word = words[i]
            if word.tags["stmt"].stmt_type == "import":
                stmt = self.state.words[i].tags["stmt"]
                conv_space.add_conv(conv_space.blank_conv(
                    i, range(stmt.start, stmt.end)))
                i += 1
                continue

            self.state.progress_bar.set_sub_progress(i/len_words)
            is_func_stmt = "func_stmt" in word.tags
            is_var_stmt = "var_stmt" in word.tags

            # Add Standard Function Statement Conversion Path
            if is_func_stmt:
                self.find_func_convs(word)

            # Convert Variable Statements
            elif is_var_stmt:
                self.find_var_convs(word)

            self.find_word_map_convs(word, word_map)

            # Store Keyword triggered Conversions
            self.find_keyword_convs(word, kw_convs)

            # Find all Conversions
            convs = conv_space.find_convs(word.index)
            for conv in convs:
                conv_space.add_conv(conv)
            i += 1
        
        self.logger.log("\n".join(
            str((k[0], [cs_name
                        for cs_name, cs in k[1].items()
                        for c in cs])) for k in conv_space.items()))

    def find_func_convs(self, word):
        """Find Function conversions"""

        func_stmt = word.tags["func_stmt"]

        log_msg = "Found Function Statement({0.start}->{0.end})"
        self.logger.log(log_msg.format(func_stmt))

        convs = self.conversions_space.run_matcher(self.conv_func, word.index)
        for conv in convs:
            self.conversions_space.add_conv(conv)

        if word.tags["func_stmt"].usage_type == "call":

            for func in self.func_call_convs.values():
                for func_usage in func_stmt.func_usages:
                    convs = self.match_conv(
                        func, {"func_usage": func_usage}, "func_call")
                    for conv in convs:
                        conv.func_call_conv = True

    def find_var_convs(self, word):
        """Find Variable conversions"""

        log_msg = "Found Variable Statement({0.start}->{0.end})"
        var_stmt = word.tags["var_stmt"]
        self.logger.log(log_msg.format(var_stmt))
        convs = self.conversions_space.run_matcher(self.conv_var, word.index)
        for conv in convs:
            self.conversions_space.add_conv(conv)

    def find_mod_convs(self, start=0, end=-1):
        """Find Object Modifier Conversions"""

        end = len(self.state.words) if end == -1 else end
        for word in self.state.words[start:end]:
            found_tag = ""
            for tag_name in ["func_stmt", "var_stmt", "const_obj"]:
                if tag_name in word.tags:
                    found_tag = tag_name
                    break
            if found_tag:
                self.find_obj_convs(word, found_tag)

    def find_obj_convs(self, word, tag_name):
        """Find Object Conversions"""

        obj_stmt = word.tags[tag_name]
        for obj_usage in obj_stmt.obj_usages:
            params = {"obj_usage": obj_usage}
            for obj_func in self.conversions_space.obj_mod_convs.values():
                self.match_conv(obj_func, params, "obj_mod")

            if obj_usage.obj.is_func:
                func = obj_usage.func
                if (func.is_lib and
                        self.state.func_in_module(func.lib_conv, "modify")):
                    self.state.execute(
                        func.lib_conv, {"obj_usage": obj_usage}, "modify",
                        add_default_args=True)

    def find_lib_convs(self, obj_usage):

        root = obj_usage.obj.get_root()

        lib_paths = []

        if obj_usage.obj.is_lib:
            lib_paths.append(obj_usage.obj.lib_path)
        else:
            if root.is_lib:
                lib_path = root.lib_path
                for part in list(obj_usage.obj.ref_loc.get_path_parts())[1:]:
                    lib_path += [".", part]
                lib_paths.append(lib_path)
            if root.type_from.lib:
                lib_path = [str(root.type_from)]
                lib_path += [p for p in
                             obj_usage.obj.ref_loc.get_path_parts()][1:]
                lib_paths.append(lib_path)
            if obj_usage.obj.is_func and len(obj_usage.obj.ref_loc) > 1:
                prev_elem = obj_usage.obj.ref_loc[-2]
                if prev_elem.is_func:
                    prev_from_type = str(prev_elem.get_type_from())
                else:
                    prev_from_type = str(prev_elem.type_from)
                default_path = ([prev_from_type,
                                 obj_usage.obj.ref_loc[-1].abs_name])
                lib_paths.append(default_path)
        for lib_path in lib_paths:
            conv_link = self.state.database.get_lib_obj(lib_path)
            if not conv_link:
                continue
                # raise ValueError(f"Missing Library {'.'.join(lib_path)}")
            if self.state.func_in_module(conv_link, "match"):
                match_res = self.state.execute(
                    conv_link, {"obj_usage": obj_usage}, func="match")
            else:
                match_res = (
                    obj_usage.start,
                    range(obj_usage.start, obj_usage.end),
                    {"obj_usage": obj_usage}
                )
            if match_res:
                obj_usage.has_lib_conv = True
                trigger, rng, params = match_res
                if isinstance(rng, tuple):
                    rng, aoe = rng
                else:
                    aoe = rng
                conv = Conversion(
                    self.state, trigger, rng, aoe, conv_link, params)
                self.conversions_space.add_conv(conv, conv_set="lib_conv")
                return

    def find_word_map_convs(self, word, word_map):
        """Find word_map conversions"""

        # Check word map conversions
        word_map_match, i = None, word.index
        if word in word_map["text"]:
            word_map_match = ("text", word)
        elif word.tok_type in word_map["type"]:
            word_map_match = ("type", word.tok_type)
        else:
            for tag in word.tags:
                if tag in word_map["tag"]:
                    word_map_match = ("tag", tag)

        if word_map_match:
            self.conversions_space.add_conv(Conversion(
                self.state, i, range(i, i+1), [i],
                {"code": self.conversions_space.word_map_applier,
                 "path": "word_map_applier",
                 "priority": -1},
                params={"re": re, "match": word_map_match, "word": word}))

    def find_keyword_convs(self, word, kw_convs):
        """Find keyword triggered conversions"""

        if word.tok_type == "name" and word in self.database.from_reserved_kw:
            if word not in kw_convs:
                conv_link = self.database.get_kw_conv(word)
                if not conv_link:
                    conv_link = None
                kw_convs[word] = conv_link
            conv_link = kw_convs[word]
            if conv_link:
                self.match_conv(conv_link, {"word": word})

    def find_type_convs(self):
        """Find type based Conversions"""

        self.state.progress_bar.increment()
        len_words = len(self.state.words)
        for i, word in enumerate(self.state.words):
            self.state.progress_bar.set_sub_progress(i/len_words)
            # self.find_opr_convs(word)
            obj_usage = None
            if "func_usage" in word.tags:
                obj_usage = word.tags["func_usage"]
            elif "var_usage" in word.tags:
                obj_usage = word.tags["var_usage"]
            if obj_usage is not None:
                self.find_lib_convs(obj_usage)
            if word.index in self.state.type_solved_values:
                self.find_value_type_convs(word)

    def find_value_type_convs(self, word):
        """Find conversions based on value type"""

        type_info = self.state.type_solved_values[word.index]
        type_ = type_info[0].type_
        if self.state.func_in_module(type_.module_code, "to_str"):
            start, end = word.index, type_info[0].end
            trigger, rng = word.index, range(start, end)
            params = {"value": type_info[0]}
            conv = Conversion(
                self.state, trigger, rng, rng,
                type_.module_code, params)
            self.conversions_space.add_conv(conv)

    def setup_conversion(self):
        """Get boilerplate and core components for conversion"""

        # Run boilerplate matcher
        self.state.progress_bar.increment()
        main_stmts = self.state.execute(self.main_stmts, func="extract")

        core_comps = {"global_structs": self.state.global_stmts["structs"],
                      "global_funcs": self.state.global_stmts["func_defs"],
                      "main": main_stmts}

        # Save core components
        self.core_comps = core_comps

        # Create lines and pathways with boilerplate
        boilerplate = self.state.execute(self.boilerplate_to, func="template")

        # Link pathways according to boilerplate
        self.state.progress_bar.increment()
        start = i = 0
        while i != -1:
            i = boilerplate.find("@@", i)
            if i == -1:
                self.state.cnv_file_lns.append(boilerplate[start:])
                break
            if i != 0 and boilerplate[i - 1] == "\\":
                self.state.cnv_file_lns.append(boilerplate[start:i - 1])
                start = i
                i += 2
                continue
            end = boilerplate.find("@@", i + 2)
            if end == -1:
                raise ValueError("Boilerplate Format is Incorrect")

            self.state.cnv_file_lns.append(boilerplate[start:i])
            start = end + 2

            path_name = boilerplate[i + 2:end]

            if path_name == "filename":
                filename = os.path.splitext(os.path.split(
                    self.state.out_file_path)[-1])[0]
                self.state.cnv_file_lns.append(filename)
            else:
                pathway = Lines(self.state)
                self.state.cnv_file_lns.append(pathway)
                self.pathways[path_name] = pathway

            i = end + 2

    def check_conversions(self):
        """
        Check if all words have conversions and
        remove conversions based on setting
        """

        self.state.progress_bar.increment()
        self.conversions_space.check(self.learner)

    def convert_base(self, settings=None):
        """Convert the whole program"""

        # Convert main function
        self.state.progress_bar.increment()
        for rng in self.str_funcs.condense(self.core_comps["main"]):
            self.convert(*rng, settings=settings, lns=self.pathways["main"])

        # Convert global functions
        self.state.progress_bar.increment()
        for global_func_usage in self.core_comps["global_funcs"]:
            if global_func_usage.usage_type == "def":
                start = global_func_usage.start
                end = global_func_usage.func.body_end
                self.convert(start, end, settings=settings,
                             lns=self.pathways["global_funcs"])

        # Convert structs
        self.state.progress_bar.increment()
        for var_usage in self.core_comps["global_structs"]:
            struct = var_usage.var
            self.convert(struct.start, struct.body_end, settings=settings,
                         lns=self.pathways["global_structs"])

    def run_lib_conv(self, obj_usage):
        """Run Lib Conversion with given object"""

        start, end = obj_usage.start, obj_usage.end

        settings = self.conv_filters.default_settings
        conv = self.conversions_space.get_conv(start, settings, start, end,
                                               conv_set="lib_conv")

        if conv:
            if self.state.func_in_module(conv.conv, "to_str"):
                return str(self.state.execute(conv.conv,
                                              conv.params, func="to_str"))
            elif self.state.func_in_module(conv.conv, "func_conv"):
                return self.state.execute(conv.conv,
                                          conv.params, func="func_conv")

            raise ValueError("No conversion functions found")

    def run_mod_conv(self, start=0, end=-1, settings=None):
        """Run modifier conversions within given range and settings"""

        end = len(self.state.words) if end == -1 else end
        settings = settings if settings else self.conv_filters.default_settings

        convs_space = self.conversions_space
        called_convs = set()

        range_len = end - start
        self.state.progress_bar.increment()

        for j, i in enumerate(self.state.words.iterate_range(start, end)):
            self.state.progress_bar.set_sub_progress(j/range_len)

            for conv in convs_space.get_conv(
                    i, settings, start, end, conv_set="obj_mod", all_=True):

                if conv in called_convs:
                    continue

                # RUN CONVERSION
                self.state.execute(conv.conv, conv.params, func="modify")
                called_convs.add(conv)

    def get_conv_dat(self, start, end, settings):
        """Get conversion supplements in given range and settings"""

        if settings == "func_call_conv":
            c_filters = self.conv_filters
            settings = c_filters.FUNC_CALL_CONV | c_filters.LARGEST_SIZE
        conv = self.conversions_space.get_conv(
            start, settings, start, end, conv_set="func_call")

        if conv:
            return self.state.execute(conv.conv, conv.params, func="get_dat")

    def convert_obj(self, obj, buffer_adds=True):
        """Convert Object"""

        converted = self.convert(obj.start, obj.end)
        return converted

    def convert(self, start, end, at_index=-1,
                settings=None, lns=None):
        """Convert words in range with given settings"""

        if settings is None:
            settings = self.conv_filters.default_settings
        convs_space = self.conversions_space

        if lns is None:
            lns = Lines(self.state)

        end = end if end != -1 else len(self.state.words)
        rng_start = start

        conv_lns_buff = self.conv_lns_buff
        old_suffix_lns = old_prefix_lns = None
        if at_index != -1:
            rng_start = at_index
        visited = set()

        for i in self.state.words.iterate_range(rng_start, end):

            if i in visited:
                continue

            self.state.cursor = i
            conv = convs_space.get_conv(i, settings, start, end)

            # RUN CONVERSION
            if conv:
                visited = visited.union(
                    self.state.words.iterate_range(conv.rng.start,
                                                   conv.rng.stop))
                converted_lns = Lines(self.state)
                converted_lns.append(convs_space.apply_conv(conv))
                lns.append(converted_lns)
                conv_lns_buff.append((i, converted_lns))
            if at_index != -1:
                break
        return str(lns)

    @staticmethod
    def get_conv_word(conversions, word):
        """Get conversion word"""

        if (isinstance(conversions, str)
                or isinstance(conversions, tuple)):
            conversions = [conversions]

        matcher = f"({word})"
        for conversion in conversions:
            if isinstance(conversion, tuple):
                matcher = re.sub(matcher, conversion[0], word)
                if not re.match(matcher, word):
                    continue
                conversion = conversion[1]
            return re.sub(matcher, conversion, word)

    def import_lib(self, lib):
        """Add import statement for given library if not already imported"""

        import_stmt = self.state.execute(
            self.import_lib_func, {"lib": lib}, func="to_str"
        )
        if import_stmt not in self.state.imported_libs:
            self.state.imported_libs.add(import_stmt)
            self.pathways["imports"].append(import_stmt)

    def get_result(self, cnv_file_lns=None, conv_lns_buff=None,
                   main_str_build=False):
        """Condense converted lines into string"""

        conv_lns_buff = conv_lns_buff if conv_lns_buff else self.conv_lns_buff
        if cnv_file_lns is None:
            cnv_file_lns = self.state.cnv_file_lns
        lns_list = self.str_funcs.get_lns(cnv_file_lns)
        filtered_lns_buff = [ln for ln in conv_lns_buff if ln[1] in lns_list]
        sorted_lns_buff = sorted(filtered_lns_buff, key=lambda x: x[0])
        low_rng = [rng for rng, conv in sorted_lns_buff]
        len_lns = len(sorted_lns_buff)

        if main_str_build and self.state.progress_bar.widget is not None:
            self.state.progress_bar.increment()
        len_prefix_lns = len(self.state.prefix_lns)
        for i, (k, lns) in enumerate(self.state.prefix_lns):

            self.state.progress_bar.set_sub_progress(i/len_prefix_lns)

            # Add to converted lines only if the word space is the same
            if (not isinstance(k, int) and
                    k.word_space != self.state.words.chosen_word_space):
                continue

            # bisect_left gives index, one less then key if key isn't in list
            pos = bisect_right(low_rng, k)

            # Add line to start of current buffer
            if pos == len_lns:
                raise ValueError("Can't Add lines after max of words range")

            if pos == 0 and low_rng[0] >= k:
                continue
            elif low_rng[pos-1] >= k:
                sorted_lns_buff[pos-1][1].insert(0, lns)
            else:
                sorted_lns_buff[pos-1][1].append(lns)

        if main_str_build and self.state.progress_bar.widget is not None:
            self.state.progress_bar.increment()
        len_suffix_lns = len(self.state.suffix_lns)
        for i, (k, lns) in enumerate(self.state.suffix_lns):
            self.state.progress_bar.set_sub_progress(i / len_suffix_lns)

            # Add to converted lines only if the word space is the same
            if (not isinstance(k, int) and
                    k.word_space != self.state.words.chosen_word_space):
                continue

            # bisect_left gives index, one less then key if key isn't in list
            pos = bisect_right(low_rng, k)

            # Add line to end of previous buffer
            if pos == 0:
                raise ValueError("Can't Add lines before 0 index")

            if low_rng[pos-1] <= k:
                sorted_lns_buff[pos-1][1].append(lns)
            else:
                sorted_lns_buff[pos-1][1].insert(0, lns)

        if main_str_build and self.state.progress_bar.widget is not None:
            self.state.progress_bar.increment()

        chosen_word_space = self.state.words.chosen_word_space
        paste_bottom_code = (
            "" if chosen_word_space not in self.state.paste_bottom_code
            else self.state.paste_bottom_code[chosen_word_space])
        return str(cnv_file_lns) + paste_bottom_code

    def convert_snippet(self, code, index):
        """Convert Snippet"""

        return self.code_processor.convert(code, index)
