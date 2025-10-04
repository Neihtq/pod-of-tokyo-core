class Player:
    def __init__(self, player_id: str, player_name: str):
        self.player_id = player_id
        self.player_name = player_name

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return (
                self.player_id == other.player_id
                and self.player_name == other.player_name
            )
        return False
