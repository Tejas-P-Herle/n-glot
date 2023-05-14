class Learner:
    def __init__(self, state, learner_form=None):
        """Initiate new Learner"""

        self.state = state
        self.learner_form = learner_form

    def get_input(self, i):
        """Get Input from User"""

        if self.learner_form is None:
            return self.get_input_cli(i)
        return self.learner_form.get_input(i)

    def get_input_cli(self, i):
        """Get Input from Command Line Interface"""
        
        raise ValueError("Conv Not Found Properly")
        word = self.state.words[i]
        stmt = word.tags['stmt']
        stmt_str = " ".join(w for w in stmt.to_list())
        print(f"\rConv Data: '{stmt_str}'")

        rng_type = "word" or input("Range Type: ")
        if rng_type not in ["word", "stmt"]:
            raise ValueError("Invalid Range Type")
        if rng_type == "word":
            hook = "text" or input("Word Hook: ")
            if hook not in ["text", "type", "tag"]:
                raise ValueError("Invalid Word Hook")
            hook_val = ""
            if hook == "text":
                hook_val = word
            elif hook == "type":
                hook_val = word.type_
            elif hook == "tag":
                hook_val = input("Tag: ")
                if "tag" not in word.tags:
                    raise ValueError("Missing Tag")

            matcher = (False and input("Matcher: ")) or ""
            rep_regex = "throw" or input("Replacement Regex: ")

            if matcher == "":
                value = rep_regex
            else:
                value = {"matcher": matcher, "conversion": rep_regex}
            conv_space = self.state.conversions.conversions_space
            # self.state.database.update_json(
            #     conv_space.word_map_path, [hook, hook_val], value, append=True)
            ptr = conv_space.word_map[hook]
            if isinstance(ptr, list):
                ptr[hook_val].append(value)
            else:
                ptr[hook_val] = value
        return True

