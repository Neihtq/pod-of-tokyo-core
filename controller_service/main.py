import os
import subprocess

from controller_service.controller_server import ControllerServer

if __name__ == "__main__":
    print("Initializing controller service with following DB parameters")
    DB_NAME = os.environ["DB_NAME"]
    DB_NAME = os.environ["DB_USER"]
    DB_NAME = os.environ["DB_PASSWORD"]

    server = ControllerServer()
    try:
        server.app.run(host="0.0.0.0", port=11000, debug=True, use_reloader=False)
    finally:
        subprocess.run(["minikube", "delete"], check=True)
