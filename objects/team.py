class Team:
    __slots__ = ['id', 'color', 'emoji', 'full_location', 'league', 'location', 'name', 'record', 'elo', 'rank']

    def __init__(self, data):
        if type(data) == tuple:
            for i in range(len(self.__slots__)):
                setattr(self, self.__slots__[i], data[i])
        elif type(data) == dict:
            self.id = data.get("_id", None)
            self.color = data.get("Color", "ffffff")
            if self.color == '0':
                self.color = "000000"
            self.emoji = data.get("Emoji", "")
            self.full_location = data.get("FullLocation", "Not Found")
            self.league = data.get("League", "Not Found")
            self.location = data.get("Location", "Not Found")
            self.name = data.get("Name", "Not Found")
            self.record = data.get("Record", "")
            self.elo = {0: 1000}
            self.rank = -1
    
    def get_json(self) -> dict:
        return {"id": self.id, "color": self.color, "emoji": self.emoji, "full_location": self.full_location, "league": self.league, "location": self.location, "name": self.name, "record": self.record, "elo": self.elo, "rank": self.rank}