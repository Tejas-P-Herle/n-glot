from obj_classes.object_usage import Object, ObjectUsage, ObjectCallPath
from obj_classes.var_classes.variable import Variable, VariableValue
from obj_classes.var_classes.variable_usage import VariableUsage
from data_capsules.word import Word
from data_capsules.statement import Statement
from data_capsules.statement_linked_list import StatementLinkedList
from data_capsules.type_solve_list import TypeSolveList


class NewCapsule:
    @staticmethod
    def object(*args, **kwargs):
        """Creates new Object class instance"""

        return Object(*args, **kwargs)

    @staticmethod
    def object_usage(*args, **kwargs):
        """Creates new ObjectUsage class instance"""

        return ObjectUsage(*args, **kwargs)

    @staticmethod
    def type_solve_list(*args, **kwargs):
        """Creates new TypeSolveList class instance"""

        return TypeSolveList(*args, **kwargs)

    @staticmethod
    def object_call_path(*args, **kwargs):
        """Creates new ObjectCallPath class instance"""

        return ObjectCallPath(*args, **kwargs)

    @staticmethod
    def variable(*args, **kwargs):
        """Creates new Variable class instance"""

        return Variable(*args, **kwargs)

    @staticmethod
    def variable_usage(*args, **kwargs):
        """Creates new Variable class instance"""

        return VariableUsage(*args, **kwargs)

    @staticmethod
    def variable_value(*args, **kwargs):
        """Create new VariableValue class instance"""

        return VariableValue(*args, **kwargs)

    @staticmethod
    def statement(*args, **kwargs):
        """Creates new Statement class instance"""

        return Statement(*args, **kwargs)

    @staticmethod
    def statement_linked_list(*args, **kwargs):
        """Creates new StatementStructure class instance"""

        return StatementLinkedList(*args, **kwargs)

    @staticmethod
    def word(*args, **kwargs):
        """Creates new Word class instance"""

        return Word(*args, **kwargs)
