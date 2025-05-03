import ast

class League:
    __slots__ = [ 'id', 'color', 'emoji', 'league_type', 'name', 'teams']

    def __init__(self, data):
        if type(data) == tuple:
            for i in range(len(self.__slots__)):
                setattr(self, self.__slots__[i], data[i])
        elif type(data) == dict:
            self.color = data.get("Color", "ffffff")
            self.emoji = data.get("Emoji", "")
            self.league_type = data.get("LeagueType", "Not Found")
            self.name = data.get("Name", "Not Found")
            self.teams = [x for x in data.get("Teams", [])]
            self.id = data.get("_id", None)
    
    def get_json(self) -> dict:
        return {"id": self.id, "color": self.color, "emoji": self.emoji, "league_type": self.league_type, "name": self.name, "teams": ast.literal_eval(self.teams)}