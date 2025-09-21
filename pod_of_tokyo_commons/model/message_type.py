from enum import Enum, auto


class MessageType(Enum):
    ROLL = auto()
    REROLL_AND_RESOLVE = auto()
    YIELD = auto()
    EVENT = auto()
    UPDATE = auto()
    DEATH = auto()
    LOBBY = auto()
