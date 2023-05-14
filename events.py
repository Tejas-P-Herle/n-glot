from enum import Enum


class EventEnum(Enum):

    @classmethod
    def get_events(cls):
        """Get events"""

        return list(cls)

    @classmethod
    def get_events_count(cls) -> int:
        """Get count of events"""

        return len(cls.get_events())


class SpecialEvents(EventEnum):
    START = 0
    COMPLETE = 1


class TokenizeEvents(EventEnum):
    TOKENIZE_WORD = 0
    BASIC_TAG_WORD = 1


class StandardizeEvents(EventEnum):
    STANDARDIZE = 0


class SkimEvents(EventEnum):
    INSPECT = 0
    TAG_TOKENS = 1
    TAG_UNUSED_TOKENS = 2
    CLASSIFY_STMTS = 3


class SetupConversionEvents(EventEnum):
    BOILERPLATE_MATCH = 0
    LINKING_PATHWAYS = 1


class FindConversionsEvents(EventEnum):
    FINDING_CONVERSIONS = 0


class CheckConversionsEvents(EventEnum):
    CHECKING_CONVERSIONS = 0


class RunModConversionsEvents(EventEnum):
    RUNNING_MOD_CONVERSIONS = 0


class SolveTypesEvents(EventEnum):
    SOLVING_VARIABLE_TYPES = 0
    SOLVING_FUNCTION_TYPES = 1


class FindTypeConversionsEvents(EventEnum):
    FINDING_TYPE_CONVERSIONS = 0


class ConvertBaseEvents(EventEnum):
    CONVERTING_MAIN = 0
    CONVERTING_GLOBAL_FUNCS = 1
    CONVERTING_GLOBAL_STRUCTS = 2


class CombiningResultsEvents(EventEnum):
    ADDING_PREFIX_LINES = 0
    ADDING_SUFFIX_LINES = 1
    MAKING_FINAL_STRING = 2


class EventClasses(EventEnum):
    SPECIAL_EVENTS = SpecialEvents
    TOKENIZE = TokenizeEvents
    STANDARDIZE = StandardizeEvents
    SKIM = SkimEvents
    SETUP_CONVERSION = SetupConversionEvents
    FIND_CONVERSIONS = FindConversionsEvents
    CHECK_CONVERSIONS = CheckConversionsEvents
    RUN_MOD_CONVERSIONS = RunModConversionsEvents
    SOLVE_TYPES = SolveTypesEvents
    FIND_TYPE_CONVERSIONS = FindTypeConversionsEvents
    CONVERT_BASE = ConvertBaseEvents
    COMBINING_RESULTS = CombiningResultsEvents


class EventCounter:
    event_id: int = 0
    sub_progress: int = 0
    total_events: int = 0
    is_complete: bool = False

    def __init__(self):
        """Initiate new Events"""

        self.event_class = EventClasses.SPECIAL_EVENTS
        self.event = self.event_class.value.START
        self.event_classes = iter(EventClasses.get_events())
        next(self.event_classes)
        self.events = iter([])
        for event_class in EventClasses.get_events():
            if event_class == EventClasses.SPECIAL_EVENTS:
                continue
            self.total_events += event_class.value.get_events_count()

    def get_progress(self):
        """Return progress as a percentage"""

        per_event_percent = 1 / self.total_events * 100
        return ((self.event_id-1) + self.sub_progress) * per_event_percent

    def increment(self):
        """Store next Event"""

        if self.event != EventClasses.SPECIAL_EVENTS.value.COMPLETE:
            self.event_id += 1

        try:
            self.event = next(self.events)
        except StopIteration:
            self.increment_event_class()

        self.sub_progress = 0

    def set_sub_progress(self, progress):
        """Store value of sub task progress"""

        self.sub_progress = progress

    def increment_event_class(self):
        """Store next Event Class"""

        try:
            self.event_class = next(self.event_classes)
            self.events = iter(self.event_class.value.get_events())
            self.event = next(self.events)
        except StopIteration:
            self.event_class = EventClasses.SPECIAL_EVENTS
            self.event = self.event_class.value.COMPLETE
            self.is_complete = True
