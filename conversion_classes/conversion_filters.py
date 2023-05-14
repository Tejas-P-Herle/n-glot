"""Includes Conversion Filters for different Conversion Settings"""


class ConversionFilters:
    LARGEST_SIZE = 1
    FUNC_CALL_CONV = 2

    SAFE = 0

    default_settings = None

    @staticmethod
    def largest_size(convs):
        """Gets Conversion with Largest size"""

        return max(convs, key=lambda c: c.size)

    @classmethod
    def func_call_convs(cls, convs):
        return filter(lambda c: c.func_call_conv, convs)

    @classmethod
    def filter_convs(cls, convs, settings):
        """Filter Conversions based on settings"""

        if settings & cls.FUNC_CALL_CONV:
            convs = cls.func_call_convs(convs)
        if settings & cls.LARGEST_SIZE:
            convs = [cls.largest_size(convs)]

        return list(convs)
