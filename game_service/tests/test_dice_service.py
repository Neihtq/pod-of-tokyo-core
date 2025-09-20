from unittest.mock import patch

from pod_of_tokyo_commons.entities import DiceSymbols

from game_service.service.dice_service import SYMBOLS, roll_dices


def test_roll_dices_number_of_rolls():
    """
    Tests that roll_dices returns the correct number of dice.
    """
    num_rolls = 6
    result = roll_dices(num_rolls)
    assert len(result) == num_rolls


def test_roll_dices_symbol_types():
    """
    Tests that roll_dices returns valid dice symbols.
    """
    num_rolls = 10
    result = roll_dices(num_rolls)
    valid_symbols = set([s.value for s in SYMBOLS])
    for symbol in result:
        assert symbol in valid_symbols


@patch("random.choice")
def test_roll_dices_with_mock_random(mock_choice):
    """
    Tests the roll_dices function with a mocked random.choice to ensure predictable output.
    """
    mock_choice.side_effect = [
        DiceSymbols.ONE,
        DiceSymbols.TWO,
        DiceSymbols.THREE,
        DiceSymbols.FIST,
        DiceSymbols.HEART,
        DiceSymbols.THUNDER,
    ]
    num_rolls = 6
    expected = [
        DiceSymbols.ONE.value,
        DiceSymbols.TWO.value,
        DiceSymbols.THREE.value,
        DiceSymbols.FIST.value,
        DiceSymbols.HEART.value,
        DiceSymbols.THUNDER.value,
    ]
    result = roll_dices(num_rolls)
    assert result == expected
