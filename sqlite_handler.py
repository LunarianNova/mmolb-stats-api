import sqlite3
import urllib3
import requests
import ast
from objects.game import Game
from objects.league import League
from objects.player import Player
from objects.team import Team

def get_json(url: str) -> dict:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # Remove verify because freecashews errors otherwise
    data = requests.get(url, verify=False).json()
    return data

class SingletonBase:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[cls] = instance
        return cls._instances[cls]

# This just has some basic functions I like to use
class Database(SingletonBase):
    __slots__ = ["__database", "__cursor", "__filename"]

    def __init__(self, filename : str):
        self.__filename = filename
        self.__database = sqlite3.connect("databases/" + filename)
        self.__cursor = self.__database.cursor()

    def commit(self) -> None:
        self.__database.commit()

    def close(self) -> None:
        self.__database.close()

    def execute(self, sql : str, values : tuple[any, ...] = ()) -> None:
        self.__cursor.execute(sql, values)

    def execute_many(self, sql : str, values : tuple=()) -> None:
        self.__cursor.executemany(sql, values)

    def fetchone(self) -> None:
        return self.__cursor.fetchone()
    
    def fetchall(self) -> None:
        return self.__cursor.fetchall()
    
    def execute_fetchone(self, sql : str, values : tuple=()) -> tuple:
        self.execute(sql, values)
        return self.fetchone()
    
    def execute_fetchall(self, sql : str, values : tuple=()) -> tuple:
        self.execute(sql, values)
        return self.fetchall()
    
    def execute_commit(self, sql : str, values : tuple=()) -> None:
        self.execute(sql, values)
        self.commit()
    
    def get_filename(self) -> str:
        return self.__filename
    
    def get_cursor(self) -> sqlite3.Cursor:
        return self.__cursor
    
    def get_database(self) -> sqlite3.Connection:
        return self.__database

class TeamsDatabase(Database):
    def __init__(self):
        super().__init__('teams.db') 

    def create_table(self) -> None:
        super().execute_commit('''CREATE TABLE IF NOT EXISTS teams(id STRING UNIQUE, color STRING, emoji STRING, full_location STRING, league STRING, location STRING, name STRING, record STRING, elo INTEGER, rank INTEGER)''')

    def fetch_team_object(self, id : str) -> Team:
        team = super().execute_fetchone('''SELECT * FROM teams WHERE id = ?''', (id,))
        return Team(team)
    
    def update_all(self) -> None:
        self.update()
        self.update_elo()

    def update(self) -> None:
        # Returns a dict
        teams = get_json(f"https://freecashe.ws/api/allteams")
        for team in teams:
            team = teams[team]    # Get key's value
            team = Team(team)
            # Elo isn't from cashews, so make sure to keep it up to date
            elo_list = super().execute_fetchone('''SELECT elo FROM teams WHERE id = ?''', (team.id,))
            team.elo = ast.literal_eval(elo_list[0]) if elo_list else {0: 1000}
            self.upsert_team(team)
        super().commit()

    def update_elo(self) -> None:
        gamesDatabase = GamesDatabase()
        day = 1
        teams_to_update = {}

        # Load all games ordered by day
        count = 0
        for game_data in gamesDatabase.execute_fetchall('''SELECT * FROM games WHERE state = "Complete" ORDER BY day ASC'''):
            count += 1
            game = Game(game_data)

            # If the day changes, commit all pending team updates
            if game.day != day:
                for team in teams_to_update.values():
                    self.upsert_team(team)
                super().commit()
                teams_to_update.clear()
                day = game.day

            home_team = self.fetch_team_object(game.home_team_id)
            away_team = self.fetch_team_object(game.away_team_id)

            home_elos = ast.literal_eval(home_team.elo)
            away_elos = ast.literal_eval(away_team.elo)

            # If already calculated for this day, skip
            if game.day in home_elos:
                gamesDatabase.execute('''UPDATE games SET state = "Processed" WHERE id = ?''', (game.id,))
                continue

            # Safely find the latest available ELO for or before the current day
            home_elo_day = max((d for d in home_elos.keys() if d <= game.day), default=min(home_elos.keys()))
            away_elo_day = max((d for d in away_elos.keys() if d <= game.day), default=min(away_elos.keys()))

            home_elo = home_elos[home_elo_day]
            away_elo = away_elos[away_elo_day]

            new_home_elo, new_away_elo = self.calculate_elo(
                (game.home_score, game.away_score), (home_elo, away_elo)
            )

            # Update ELOs for the current day
            home_elos[game.day] = new_home_elo
            away_elos[game.day] = new_away_elo

            home_team.elo = home_elos
            away_team.elo = away_elos

            teams_to_update[home_team.id] = home_team
            teams_to_update[away_team.id] = away_team

            gamesDatabase.execute('''UPDATE games SET state = "Processed" WHERE id = ?''', (game.id,))


        # Final commit for any leftovers
        gamesDatabase.commit()
        for team in teams_to_update.values():
            self.upsert_team(team)
        super().commit()
    
    def calculate_elo(self, scores: tuple[int, int], elos: tuple[int, int]) -> tuple[int, int]:
        k = 50
        prob_0 = 1 / (1 + 10 ** ((elos[1] - elos[0]) / 400))  # expect player 0 to win
        if scores[0] > scores[1]:  # player 0 wins
            score_0, score_1 = 1, 0
        else:  # player 1 wins
            score_0, score_1 = 0, 1
        new_elo_0 = int(elos[0] + k * (score_0 - prob_0))
        new_elo_1 = int(elos[1] + k * (score_1 - (1 - prob_0)))
        return (new_elo_0, new_elo_1)
    
    def upsert_team(self, team: Team, commit=False) -> None:
        super().execute('''INSERT OR REPLACE INTO teams(id, color, emoji, full_location, league, location, name, record, elo, rank) VALUES (:id, :color, :emoji, :full_location, :league, :location, :name, :record, :elo, :rank)''', team.get_json())
        if commit: super().commit()

class LeaguesDatabase(Database):
    def __init__(self):
        super().__init__('leagues.db') 

    def create_table(self) -> None:
        super().execute_commit('''CREATE TABLE IF NOT EXISTS leagues(id STRING UNIQUE, color STRING, emoji STRING, league_type STRING, name STRING, teams STRING)''')

    def fetch_league_object(self, id : str) -> League:
        data = super().execute_fetchone('''SELECT * FROM leagues WHERE id = ?''', (id,))
        return League(data)
    
    def update(self) -> None:
        teamsDatabase = TeamsDatabase()
        league_ids = teamsDatabase.execute_fetchall('''SELECT DISTINCT league FROM teams''')
        for id in league_ids:
            league = get_json(f"https://mmolb.com/api/league/{id[0]}")
            self.upsert_league(League(league))
        super().commit()

    def upsert_league(self, league: League, commit:bool=False) -> None:
        super().execute('''INSERT OR REPLACE INTO leagues(id, color, emoji, league_type, name, teams) VALUES (:id, :color, :emoji, :league_type, :name, :teams)''', league.get_json())
        if commit: super().commit()