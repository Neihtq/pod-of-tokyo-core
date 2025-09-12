from controller_server import ControllerServer

if __name__ == "__main__":
    server = ControllerServer()
    server.app.run(host="0.0.0.0", port=11000, debug=True)
