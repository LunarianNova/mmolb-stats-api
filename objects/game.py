K = 50

class Game:
    __slots__ = ['id', 'season', 'day', 'home_team_id', 'away_team_id', 'home_score', 'away_score', 'state']

    def __init__(self, data):
        if type(data) == tuple:
            for i in range(len(self.__slots__)):
                setattr(self, self.__slots__[i], data[i])
        elif type(data) == dict:
            self.id = data.get("game_id", "")
            self.season = int(data.get("season", 0))
            self.day = int(data.get("day", 0))
            self.home_team_id = data.get("home_team_id", "")
            self.away_team_id = data.get("away_team_id", "")
            self.home_score = int(data.get("home_score", 0))
            self.away_score = int(data.get("away_score", 0))
            self.state = data.get("state", "")
    
    def get_json(self) -> dict:
        return {"id": self.id, "season": self.season, "day": self.day, "home_team_id": self.home_team_id, "away_team_id": self.away_team_id, "home_score": self.home_score, "away_score": self.away_score, "state": self.state}