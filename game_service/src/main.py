from game_server import GameServer

if __name__ == "__main__":
    server = GameServer(port=10000, controller_port=11000)
    server.run()
