from pod_of_tokyo_client.view.view import PodOfTokyoView


class Controller:
    def __init__(self, model):
        self.model = model

    def set_view(self, view: PodOfTokyoView):
        self.view = view

    def handle_input(self, user_input):
        pass

    def update_model(self):
        pass

    def join_lobby(self, address: str):
        pass
