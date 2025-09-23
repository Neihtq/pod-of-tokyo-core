from pod_of_tokyo_commons.model.update_event import UpdateEvent


class Message:
    def __init__(self, data):
        self.members = data.get("members", None)
        self.message = data.get("message", None)
        self.dices = data.get("dices")

        update = data.get("update", None)
        if update:
            self.player_update = UpdateEvent(updates=update)

        self.game_state = data.get("gameState", None)
