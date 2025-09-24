import os
import subprocess

from controller_service import controller

if __name__ == "__main__":
    print("Initializing controller service with following DB parameters")
    print(os.environ["DB_NAME"])
    print(os.environ["DB_USER"])
    print(os.environ["DB_PASSWORD"])

    try:
        controller.serve()
    finally:
        subprocess.run(["minikube", "delete"], check=True)
