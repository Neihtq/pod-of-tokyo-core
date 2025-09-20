from enum import Enum, auto


class MessageType(Enum):
    ROLL_AND_RESOLVE = auto()
    YIELD = auto()
    EVENT = auto()
