from server import ControllerServer

if __name__ == "__main__":
    server = ControllerServer()
    server.app.run(host="0.0.0.0", port=8000, debug=True)
