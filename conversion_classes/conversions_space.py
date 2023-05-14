"""Creates Space to Store all Conversions for all words"""


from conversion_classes.conversion import Conversion
from conversion_classes.conversion_filters import ConversionFilters
from errors import ConversionFailed


class ConversionsSpace(dict):
    def __init__(self, state):
        """Initiate ConversionsSpace Object"""

        self.state = state
        self.conversion_filters = ConversionFilters
        all_convs = self.state.database.to["to"]
        self.func_call_convs = {}
        self.obj_mod_convs = {}
        self.word_replacement_map = {}
        self.applied_convs = {}
        self.locked_convs = set()
        self.convs = self.state.database.to["to"]["convs"]
        self.obj_mod_convs = self.state.database.to["to"]["obj_mod_convs"]
        self.eq_types = self.state.database.to["to"]["eq_types"]
        self.func_call_convs = self.state.database.to["to"]["func_call_convs"]
        self.lib_convs = self.state.database.to["to"]["lib_convs"]
        self.main_stmts = all_convs["main_stmts"]
        self.import_lib_func = all_convs["import_lib"]
        self.boilerplate_to = all_convs["boilerplate"]
        self.conv_func = all_convs["func_convert"]
        self.conv_var = all_convs["var_convert"]
        self.add_nglot_funcs = all_convs["add_nglot_funcs"]
        self.get_coll_type = all_convs["get_coll_type"]

        self.check_attrs_conv = all_convs["check_attrs"]
        self.word_map = all_convs["word_map"]
        self.word_map_applier = self.state.database.get_word_map_applier()

        self.get_type_from = self.state.database.from_["get_type"]

        super().__init__()

    def get_conv(self, i, setting, start, end, conv_set="conversions",
                 all_=False):
        """Get Conversion according to Setting"""

        if i in self:
            convs = self[i][conv_set]

            valid_convs = []
            for conv in convs:
                if conv.start >= start and conv.end <= end:
                    if conv not in self.locked_convs:
                        valid_convs.append(conv)

            if not valid_convs:
                if conv_set == "conversions":
                    raise ConversionFailed(
                        f"Unable to Convert word '{self.state.words[i]}'")
            if all_:
                return valid_convs

            if valid_convs:
                convs = ConversionFilters.filter_convs(valid_convs, setting)
                prioritized_convs = sorted(
                    convs, key=lambda c: (c.conv["priority"]
                                          if "priority" in c.conv
                                          else 0))
                for conv in prioritized_convs:
                    if i == conv.trigger:
                        return conv
        if all_:
            return []

    def add_conv(self, conv, conv_set="conversions"):
        """Add conversion to list of conversions for word"""

        for j in conv.aoe:
            j = self.state.words.new_index(j)
            if j not in self:
                self[j] = {"conversions": [], "func_call": [], "obj_mod": [],
                           "lib_conv": []}

            self[j][conv_set].append(conv)

    def check(self, learner):
        """
        Check if all words have conversions and
        remove conversions based on setting
        """

        len_words = len(self.state.words)
        for i in self.state.words.iterate_range(0, len_words):
            if i not in self:
                if learner.get_input(i):
                    self.state.conversions.find_conversions(i, i+1)
                    continue

                raise ConversionFailed(
                    f"Unable to Convert '{self.state.words[i]}'")

    def blank_conv(self, i, rng):
        """Return Blank Conversion for given range"""

        return Conversion(self.state, i, rng, rng, {"code": ""}, {})

    def run_matcher(self, conv_dat, i):
        """Run Matcher with given conv_dat with index i"""

        return self.run_matcher_params(conv_dat, {"index": i})

    def run_matcher_params(self, conv_dat, params):
        """Run matcher with given parameters"""

        convs = []
        match_res = self.state.execute(conv_dat, params, func="match")
        if match_res:
            if not isinstance(match_res, list):
                match_res = [match_res]

            for (trigger, rng, params) in match_res:
                if isinstance(rng, tuple):
                    rng, aoe = rng
                else:
                    aoe = rng
                convs.append(Conversion(
                    self.state, trigger, rng, aoe, conv_dat, params))
        return convs

    def find_convs(self, i):
        """Find All Conversions for given index"""
        
        other_convs = []
        for conv_name, conv_dat in self.convs.items():
            for conv in self.run_matcher(conv_dat, i):
                other_convs.append(conv)
        return other_convs

    def apply_conv(self, conv):
        """Apply conversion"""

        if conv.trigger not in self.applied_convs:
            self.applied_convs[conv.trigger] = set()
        self.applied_convs[conv.trigger].add(conv)
        self.locked_convs.add(conv)

        converted_str = str(conv)
        self.locked_convs.remove(conv)
        return converted_str
