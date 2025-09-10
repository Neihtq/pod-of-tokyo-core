from game_server import GameServer

if __name__ == "__main__":
    server = GameServer(port=5000, controller_port=6000)
    server.run()
