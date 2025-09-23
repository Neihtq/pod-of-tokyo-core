from textual.containers import Vertical


class GreenBorderVertical(Vertical):
    def __init__(self, model, controller, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "Menu"
        self.model = model
        self.controller = controller
        self.focus_element = self
