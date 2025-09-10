from game_server import GameServer

if __name__ == "__main__":
    server = GameServer(port=7000, controller_port=8000)
    server.run()
