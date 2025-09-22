from enum import Enum


class MessageType(Enum):
    ROLL = "ROLL"
    REROLL_AND_RESOLVE = "REROLL_AND_RESOLVE"
    YIELD = "YIELD"
    EVENT = "EVENT"
    UPDATE = "UPDATE"
    DEATH = "DEATH"
    LOBBY = "LOBBY"
    START_GAME = "START_GAME"
    END_TURN = "END_TURN"
