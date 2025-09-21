from pod_of_tokyo_client.controller.controller import Controller
from pod_of_tokyo_client.model.model import Model
from pod_of_tokyo_client.view.view import PodOfTokyoView

model = Model()
controller = Controller(model=model)
app = PodOfTokyoView(model=model, controller=controller)
controller.set_view(view=app)
model.set_view(view=app)


if __name__ == "__main__":
    app.run()
