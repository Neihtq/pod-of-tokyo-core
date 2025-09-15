import os

from state_server import StateServer

if __name__ == "__main__":
    server = StateServer()
    service_port = os.environ["SERVICE_PORT"]
    server.app.run(host="0.0.0.0", port=int(service_port), debug=True)
