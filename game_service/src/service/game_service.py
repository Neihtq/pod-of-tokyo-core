class GameService:
    def __init__(self):
        self.players = {}

    def add(self, sid):
        self.players[sid] = "placehold"
        print(f"[+] Added player {sid}")

    def remove(self, sid):
        if sid in self.players:
            del self.players[sid]
            print(f"[-] Removed player {sid}")

    def get(self, sid):
        return self.players.get(sid)

    def all(self):
        return list(self.players.keys())
