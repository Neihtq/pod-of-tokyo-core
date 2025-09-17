from textual.containers import Vertical


class GreenBorderVertical(Vertical):
    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.styles.border = ("solid", "green")
        self.border_title = "Menu"
        self.styles.width = "1fr"
        self.styles.height = "1fr"
        self.controller = controller
