"""Struct Class"""


from dataclasses import dataclass
from obj_classes.var_classes.variable import Variable


@dataclass
class Struct(Variable):
    body_end: int = -1
