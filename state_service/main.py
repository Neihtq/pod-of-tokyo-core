from state_server import StateServer

if __name__ == "__main__":
    server = StateServer()
    server.app.run(host="0.0.0.0", port=12000, debug=True)
