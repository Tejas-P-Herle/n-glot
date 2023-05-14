"""Defines all Custom Errors Throwable by Program"""


class UnknownOperationError(Exception):
    """Raised when no resulting type is defined for given Operation"""
    pass


class BlockNotFoundError(Exception):
    """Raised when block is not found in given range"""
    pass


class NoMatchingPrototypeError(Exception):
    """
    Raised when no matching function prototype is found for given arguments
    """
    pass


class NameNotInScopeError(Exception):
    """Raised when requested name is not found in current scope"""
    pass


class MissingAttributeError(Exception):
    """Raised when given variable doesn't have requested attribute"""
    pass


class NameCollisionError(Exception):
    """Raised when a given name already exists in scope"""
    pass


class ObjDelWithoutDecError(Exception):
    """Raised when an object is Deleted Without being declared first"""
    pass


class MultipleObjDecError(Exception):
    """Raised when an object is Deleted Without being declared first"""
    pass


class MissingFunctionError(Exception):
    """Raised when a function is expected but is not defined"""
    pass


class TypeCastFailureError(Exception):
    """Raised when type cannot be casted to required type"""
    pass


class ConversionFailed(Exception):
    """Raised when conversion fails"""
    pass


class TypeSolveFailureError(Exception):
    """Raised when value of type is not successfully determined"""
    pass


class SkimOverIndexError(Exception):
    """Raised when expected skim tags are missing"""
    pass


class TypeAdditionError(Exception):
    """Raised when two incompatible types are added"""
