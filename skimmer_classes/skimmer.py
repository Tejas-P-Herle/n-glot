"""Skim over tokens in file and tag them with appropriate tags"""
import json
from bisect import bisect_left
from obj_classes.func_classes.function_stmt import FunctionStmt
from obj_classes.var_classes.variable_stmt import VariableStmt
from skimmer_classes.inspector import Inspector
from skimmer_classes.stmt_classifier import StmtClassifier
from obj_classes.var_classes.variable_value import VariableValue


class Skimmer:
    inspector = None
    stmts = None
    body_objs = None

    def __init__(self, state):
        """Initiation function for Skim Module"""

        self.state = state
        self.words = state.conversions.to_words()

        self.reserved_kw = state.database.from_reserved_kw
        self.return_kw = state.from_meta["return"]
        self.value_tags = ["str", "float", "int", "None", "bool", "name"]
        self.operators = {"operator", "comparison_op"}

        self.stmt_structs = state.conversions.stmt_structs

        self.null_val = VariableValue([], self.state, 0, 0)

    def inspect(self, start, end, level):
        """Inspect tokens and define object borders"""

        self.inspector = Inspector(self.state)
        self.inspector.inspect(start, end, level)

        if start == 0 and end == -1:
            self.stmts = self.inspector.stmts.copy()
            self.body_objs = self.inspector.body_objs.copy()

    def classify_stmts(self):

        self.stmts = StmtClassifier.classify(self.stmts)
        all_stmts = self.stmts["stmts"]
        for body_obj in self.body_objs:
            body_obj.stmts = StmtClassifier.classify(body_obj.stmts)
            all_stmts.update(body_obj.stmts["stmts"])
        all_stmts = sorted(all_stmts, key=lambda s: all_stmts[s])
        self.state.stmts = StmtClassifier.stmts_linked_list(all_stmts)
        self.state.execute(self.stmt_structs, {"stmts": self.state.stmts},
                           func="find_structs")

    def set_globals(self):
        """Get is_global attribute for objs in state.global_stmts"""

        for obj_type in ["var_sets", "func_defs"]:
            for obj_usage in self.state.global_stmts[obj_type]:
                obj_usage.obj.is_global = True

    def tag_tokens(self, obj=None):
        """Tag tokens with appropriate tags"""

        if obj is not None:
            if obj.implemented:
                return
            obj.implemented = True
        else:
            for struct in self.inspector.struct_objs:
                struct.implement()

        self.tag_tokens_stmts(self.stmts if obj is None else obj.stmts, obj)

    def tag_unused_tokens(self):
        """Tag unused body objects"""

        while self.inspector.body_objs:
            self.tag_tokens(self.inspector.body_objs.pop(0))

    def tag_tokens_stmts(self, stmts, upper=None, force=False):
        """Tag tokens for given statements"""

        for i, word in stmts.items():
            self.state.cursor = i
            if word in self.state.str_funcs.operators:
                self.handle_operator(word)
            if word.tok_type == "name" and word not in self.reserved_kw:
                word.tags["value"] = self.get_term(
                    self.state, i, self.state.words, 1)

        skip_till = -1
        stmts_end = next(iter(reversed(stmts)))
        for i, word in stmts.items():
            self.state.cursor = i
            if (not force and i in self.inspector.visited) or i < skip_till:
                continue
            if word == self.return_kw:
                self.handle_return_stmt(i, upper)
            elif word.tok_type == "name" and word not in self.reserved_kw:
                self.state.recently_added_objs.clear()
                skip_till = self.detect_identifier(i, stmts_end)
            word.tags["stmt"].scope_copy = self.state.stmt_scope

            corrections = self.state.corrections.copy()
            self.state.corrections.clear()
            for rng, correction in corrections:
                len_diff = int(len(correction) - (rng[1] - rng[0]))
                indexes = self.state.words.indexes

                old_rng = [int(val) for val in rng]
                rng_obj = range(rng[1], len(self.state.words))
                if len_diff != 0:
                    rng_iter = reversed(rng_obj) if len_diff > 0 else rng_obj
                    for index in rng_iter:
                        indexes.pop((rng[0].word_space, index)).shift(len_diff)
                        if index in self.inspector.visited:
                            self.inspector.visited.remove(index)
                            self.inspector.visited.add(index+len_diff)

                for obj in self.state.recently_added_objs:
                    self.state.obj_map.delete_obj(obj)
                    self.state.scope.remove_from_scope(obj)
                self.state.recently_added_objs.clear()
                correction_words = self.state.str_funcs.get_words(correction)
                level = self.state.words[old_rng[0]].tags["stmt"].level
                self.state.words[old_rng[0]: old_rng[1]] = correction_words
                self.inspector.inspect(*rng, level)
                self.tag_tokens_range(*rng)

    def tag_tokens_range(self, start, end, upper=None):
        """Tag tokens for statements in range, start -> end"""

        stmts = {i: self.words[i]
                 for i in self.state.words.iterate_range(start, end)}
        self.tag_tokens_stmts(stmts, upper, force=True)

    def handle_return_stmt(self, index, upper):
        """Handle return Statement"""

        if "kw_follower_value" in self.words[index].tags:
            ret_val = self.words[index].tags["kw_follower_value"]
            upper.types_from.append(ret_val)
            upper.values.append(ret_val)

    def detect_identifier(self, index, end):
        """Detect type of identifier at given index"""

        stmt_end = None
        obj_stmt = FunctionStmt(self.state)
        tag_prefix, obj_usages = "func", obj_stmt.check_obj_no_body(index, end)

        if not obj_usages:
            obj_stmt = VariableStmt(self.state)

            tag_prefix, obj_usages = "var", obj_stmt.check_obj_no_body(
                index, end)

            if obj_stmt.usage_type == "set":
                stmt_end = obj_stmt.equals + 1

        if obj_usages:
            self.words[obj_stmt.start].tags[tag_prefix + "_stmt"] = obj_stmt
            for obj_usage in obj_usages:
                obj_usage.obj_stmt = obj_stmt
                usage_tag_name = tag_prefix + "_usage"
                if tag_prefix == "var" and not hasattr(obj_usage, "var"):
                    usage_tag_name = "obj_usage"
                self.words[obj_usage.index].tags[usage_tag_name] = obj_usage
                if obj_usage.usage_type in ["call", "get"]:
                    tags = self.words[obj_usage.end-1].tags
                    tags["obj_usage_end"] = obj_usage
            if stmt_end is None:
                return obj_stmt.end
            return stmt_end
        return obj_stmt.end

    def handle_operator(self, word):
        """Handle Operators"""

        lhs = self.get_lhs(word.index)
        if lhs:
            word.tags["lhs"] = lhs
        rhs = self.get_rhs(word.index)
        if rhs:
            word.tags["rhs"] = rhs

        eqn = self.get_equation(word)
        if eqn is not None:
            self.state.equations.append(eqn)
            range_i = bisect_left(self.state.eq_ranges, eqn.start)
            self.state.eq_ranges.insert(range_i, eqn.start)
            self.state.sorted_eq.insert(range_i, eqn)

    def get_equation(self, opr):
        """Get equation containing the given operator"""

        if opr not in self.state.str_funcs.eqn_ops:
            return

        opr_stmt_type = opr.tags["stmt"].stmt_type
        if opr_stmt_type == "func_def_stmt":
            return

        if opr.tok_type == "assignment_op":
            return

        eqn = self.has_defined_eqn(opr)
        if eqn:
            return

        i = opr.tags["lhs"].start if "lhs" in opr.tags else opr.index
        if opr in self.state.str_funcs.unary_ops:
            i = opr.index-1

        if (opr not in self.state.str_funcs.binary_ops
                and opr.tok_type != "ref_op"):
            i += 1
        start, end = i, -1
        len_words = len(self.state.words)
        while i < len_words:
            word = self.state.words[i]
            if word.tok_type in ["stmt_term", "stmt_sep"]:
                end = i
                break
            elif word in self.state.str_funcs.eqn_terminators:
                end = i
                break
            elif "pair" in word.tags:
                pair_i = word.tags["pair"]
                if pair_i > i:
                    i = pair_i
                else:
                    end = i
                    break
            i += 1
        if end != -1 and end - start > 1:
            return self.state.new_capsule.variable_value(
                self.state.words[start:end], self.state, start, end)

    def has_defined_eqn(self, opr):
        i = bisect_left(self.state.eq_ranges, opr.index)
        if i > 0:
            eqn = self.state.sorted_eq[i-1]
            if eqn.start <= opr.index < eqn.end:
                return eqn

    def get_lhs(self, i):
        """Get LHS of term at index i"""

        return (self.get_term(self.state, i-1, self.words, -1)
                if i else self.null_val)

    def get_rhs(self, i):
        """Get RHS of term at index i"""

        return (self.get_term(self.state, i+1, self.words, 1)
                if i != len(self.words) else self.null_val)

    @classmethod
    def get_term(cls, state, i, words, dir_):
        """Get Term at word"""

        start = i
        name_word = False
        while ((not name_word and words[i].tok_type == "name")
               or words[i].tok_type == "ref_op"
               or cls.is_forward_pair(words, i, dir_)
               or "const" in words[i].tags):
            if cls.is_forward_pair(words, i, dir_):
                i = words[i].tags["pair"] + dir_
            else:
                name_word = (words[i].tok_type == "name"
                             or "const" in words[i].tags)
                i += dir_
        if dir_ == -1:
            end = start + 1
            start = i - dir_
        else:
            end = i - dir_ + 1
        if end > start:
            return VariableValue(words[start:end], state, start, end)
        return

    @staticmethod
    def is_forward_pair(words, i, dir_):
        """Check if word at given index is start of a forward pair"""

        if "pair" not in words[i].tags:
            return False
        return (1 if (words[i].tags["pair"] - i) > 0 else -1) == dir_
