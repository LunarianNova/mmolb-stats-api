import json

class Player:
    def __init__(self, data: dict | tuple):
        # From the csv
        if type(data) == dict:
            self.id = data.get("_id")
            self.first_name = data.get("FirstName")
            self.last_name = data.get("LastName")
            self.team_id = data.get("TeamID")
            self.likes = data.get("Likes")
            self.dislikes = data.get("Dislikes")
            self.bats = data.get("Bats")
            self.throws = data.get("Throws")
            self.number = data.get("Number")
            self.position = data.get("Position")
            self.augments = data.get("Augments")
            self.home = data.get("Home")
            self.stats = data.get("Stats", {})
        # From the database
        elif type(data) == tuple:
            self.id, self.season, self.day, self.first_name, self.last_name, self.team_id, self.likes, self.dislikes, self.bats, self.throws, self.number, self.position, self.augments, self.home, stats_json = data
            self.stats = json.loads(stats_json)
        else:
            raise ValueError("Player __init__ only processes tuple or (json) dictionaries")

    def get_batting_average(self):
        ab = self.stats.get("at_bats")
        hits = self.stats.get("singles") + self.stats.get("doubles") + self.stats.get("triples") + self.stats.get("home_runs")
        return hits / ab if ab != 0 else 0

    def get_on_base_percentage(self):
        walks = self.stats.get("walked")
        hbp = self.stats.get("hit_by_pitch")
        hits = self.stats.get("singles") + self.stats.get("doubles") + self.stats.get("triples") + self.stats.get("home_runs")
        pa = self.stats.get("plate_appearances")
        return (hits + walks + hbp) / pa if pa != 0 else 0

    def get_slugging_percentage(self):
        ab = self.stats.get("at_bats")
        total_bases = (self.stats.get("singles") + 2 * self.stats.get("doubles") + 3 * self.stats.get("triples") + 4 * self.stats.get("home_runs"))
        return total_bases / ab if ab != 0 else 0

    def get_on_base_plus_slugging(self):
        return self.get_on_base_percentage() + self.get_slugging_percentage()

    def get_innings_pitched(self):
        return self.stats.get("outs") / 3

    def get_earned_run_average(self):
        ip = self.get_innings_pitched()
        er = self.stats.get("earned_runs")
        return (er * 9) / ip if ip != 0 else 0

    def get_strikeouts_per_nine_innings(self):
        ip = self.get_innings_pitched()
        return (self.stats.get("strikeouts") * 9) / ip if ip != 0 else 0

    def get_walks_per_nine_innings(self):
        ip = self.get_innings_pitched()
        return (self.stats.get("walks") * 9) / ip if ip != 0 else 0

    def get_home_runs_per_nine_innings(self):
        ip = self.get_innings_pitched()
        return (self.stats.get("home_runs_allowed") * 9) / ip if ip != 0 else 0

    def get_walks_and_hits_per_inning_played(self):
        ip = self.get_innings_pitched()
        walks = self.stats.get("walks")
        hits = self.stats.get("hits_allowed")
        return (walks + hits) / ip if ip != 0 else 0

    def get_stolen_base_percentage(self):
        sb = self.stats.get("stolen_bases")
        cs = self.stats.get("caught_stealing")
        total = sb + cs
        return sb / total if total != 0 else 0

    def get_fielding_percentage(self):
        po = self.stats.get("putouts")
        a = self.stats.get("assists")
        e = self.stats.get("errors")
        return (po + a) / (po + a + e) if (po + a + e) != 0 else 0

    # Fuck you, truthy
    def get_json(self):
        # season = self.season if self.season else -1
        season = self.season if self.season is not None else -1
        day = self.day if self.day is not None else -1
        return {"id": self.id, "day": day, "season": season, "first_name": self.first_name, "last_name": self.last_name, "team_id": self.team_id, "likes": self.likes, "dislikes": self.dislikes, "bats": self.bats, "throws": self.throws, "number": self.number, "position": self.position, "augments": self.augments, "home": self.home, "stats": self.stats}