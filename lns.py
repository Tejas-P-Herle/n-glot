"""Class to manage converted file lines"""


class Lines(list):

    converted = False

    def __init__(self, state):
        """Initiation Function for Lines class"""

        # Initiate list class
        super().__init__()

        # Setup CnvFileLines
        self.state = state

    def __str__(self):
        """Convert file lines to string"""

        if self.converted:
            return

        # Convert all segments in list to string
        conv_str = ""
        prev_word = ""
        for seg in self:
            word = str(seg)
            if (word and word[0] in self.state.str_funcs.ALNUM and prev_word
                    and prev_word[-1] in self.state.str_funcs.ALNUM):

                conv_str += " "
            conv_str += word
            prev_word = word
        return conv_str


class StrFuncs:
    def __init__(self):
        self.ALNUM = "a"


class State:
    def __init__(self):
        self.str_funcs = StrFuncs()


if __name__ == "__main__":
    state = State()
    lns = Lines(state)
