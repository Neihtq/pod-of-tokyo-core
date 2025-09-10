import random

from model import DiceSymbols

SYMBOLS = [
    DiceSymbols.ONE,
    DiceSymbols.TWO,
    DiceSymbols.THREE,
    DiceSymbols.FIST,
    DiceSymbols.HEART,
    DiceSymbols.THUNDER,
]


def roll_dices(num_rolls):
    return [random.choice(SYMBOLS).value for _ in range(num_rolls)]
