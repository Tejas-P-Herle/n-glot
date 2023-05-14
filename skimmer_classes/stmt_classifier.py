from data_capsules.new_capsule import NewCapsule


class StmtClassifier:
    @classmethod
    def classify(cls, stmts):
        """Classify Statements into Function, Variable and Misc Usages"""

        classified_stmts = {
            "func_defs": [], "func_calls": [], "var_sets": [], "var_gets": [],
            "structs": [], "stmts": {}, "all": stmts, "all_mod": {},
            "misc": [], "words": {}
        }

        skip_till = -1
        for i, stmt in stmts.items():

            classified_stmts["stmts"][stmt.tags["stmt"]] = i

            if i < skip_till:
                continue

            if "func_usage" in stmt.tags:
                skip_till = cls.classify_funcs(classified_stmts, stmt)
            elif "var_usage" in stmt.tags:
                skip_till = cls.classify_vars(classified_stmts, stmt)
            else:
                classified_stmts["misc"].append(stmt)
                classified_stmts["all_mod"][i] = stmt

        return classified_stmts

    @staticmethod
    def stmts_linked_list(stmts):
        """Creates new StatementLinkedList instance"""

        return NewCapsule.statement_linked_list(stmts)

    @staticmethod
    def classify_funcs(classified_stmts, stmt):
        func_usage = stmt.tags["func_usage"]
        func_class = ("func_defs" if func_usage.usage_type == "def"
                      else "func_calls")
        classified_stmts[func_class].append(func_usage)
        classified_stmts["all_mod"][func_usage.start] = func_usage
        return func_usage.end

    @staticmethod
    def classify_vars(classified_stmts, stmt):
        var_usage = stmt.tags["var_usage"]
        var_stmt = stmt.tags["stmt"].words[var_usage.start].tags["var_stmt"]
        for var_usage in var_stmt.var_usages:
            if var_usage.usage_type == "set":
                var_class = "var_sets"
            elif var_usage.usage_type == "get":
                var_class = "var_gets"
            else:
                var_class = "structs"
            classified_stmts[var_class].append(var_usage)
            classified_stmts["all_mod"][var_usage.start] = var_usage
        return var_stmt.end
