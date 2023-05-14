"""Store and Help Assemble Conversions"""


from dataclasses import dataclass


@dataclass
class Conversion:
    state: None
    trigger: int
    rng: range
    aoe: list or range
    conv: dict
    params: dict
    func_call_conv: bool = False
    size: int = -1

    def __post_init__(self):
        """Initiate Conversion Object"""

        # Calculate size
        # if isinstance(self.rng, list):
        #     self.size = len(self.rng)
        #     self.start = min(self.rng)
        #     self.end = max(self.rng)
        # else:
        #     self.size = self.rng.stop - self.rng.start
        #     self.start = self.rng.start
        #     self.end = self.rng.stop

        self.size = self.rng.stop - self.rng.start
        self.start = self.rng.start
        self.end = self.rng.stop

    def __str__(self):

        # Convert to string
        if self.conv["code"]:
            return self.state.execute(self.conv, self.params, func="to_str")
        return ""

    def __repr__(self):

        return (f"<Conversion trigger={self.trigger} rng={self.rng}"
                + f"params={self.params}>")

    def __hash__(self):
        """Return Hash of conversion"""

        return id(self)
