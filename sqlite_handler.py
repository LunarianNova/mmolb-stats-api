import sqlite3
import urllib3
import requests
import ast
import atexit
import player_parser
import statistics
import numpy as np
import json
from objects.game import Game
from objects.league import League
from objects.player import Player
from objects.team import Team

STATS = ['allowed_stolen_bases', 'allowed_stolen_bases_risp', 'assists', 'assists_risp', 'at_bats', 'at_bats_risp', 'caught_stealing', 'caught_stealing_risp', 'double_plays', 'double_plays_risp', 'doubles', 'doubles_risp', 'field_out', 'field_out_risp', 'fielders_choice', 'flyouts', 'flyouts_risp', 'force_outs', 'force_outs_risp', 'grounded_into_double_play', 'groundout', 'groundout_risp', 'home_runs', 'home_runs_risp', 'left_on_base', 'left_on_base_risp', 'lineouts', 'lineouts_risp', 'plate_appearances', 'plate_appearances_risp', 'popouts', 'popouts_risp', 'putouts', 'putouts_risp', 'reached_on_error', 'runners_caught_stealing', 'runners_caught_stealing_risp', 'runs', 'runs_batted_in', 'runs_batted_in_risp', 'runs_risp', 'sac_flies', 'sac_flies_risp', 'singles', 'singles_risp', 'stolen_bases', 'stolen_bases_risp', 'struck_out', 'struck_out_risp', 'walked', 'walked_risp', 'fielders_choice_risp', 'grounded_into_double_play_risp', 'hit_by_pitch', 'reached_on_error_risp', 'triples', 'triples_risp', 'appearances', 'batters_faced', 'batters_faced_risp', 'earned_runs', 'earned_runs_risp', 'errors', 'errors_risp', 'games_finished', 'hits_allowed', 'hits_allowed_risp', 'losses', 'outs', 'pitches_thrown', 'pitches_thrown_risp', 'strikeouts', 'strikeouts_risp', 'walks', 'caught_double_play', 'caught_double_play_risp', 'hit_by_pitch_risp', 'sacrifice_double_plays', 'sacrifice_double_plays_risp', 'hit_batters', 'home_runs_allowed', 'home_runs_allowed_risp', 'mound_visits', 'quality_starts', 'starts', 'unearned_runs', 'unearned_runs_risp', 'walks_risp', 'wins', 'inherited_runners', 'inherited_runners_risp', 'hit_batters_risp', 'inherited_runs_allowed', 'inherited_runs_allowed_risp', 'complete_games', 'shutouts', 'blown_saves', 'saves', 'no_hitters', 'perfect_games']    

def get_json(url: str) -> dict:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # Remove verify because freecashews errors otherwise
    data = requests.get(url, verify=False).json()
    return data

def store_json(data: dict) -> str:
    return json.dumps(data, separators=(',', ':'), ensure_ascii=False)

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

class GamesDatabase(Database):
    def __init__(self):
        super().__init__('games.db') 

    def create_table(self) -> None:
        super().execute_commit('''CREATE TABLE IF NOT EXISTS games(id STRING UNIQUE, season INTEGER, day INTEGER, home_team_id STRING, away_team_id STRING, home_score INTEGER, away_score INTEGER, state STRING)''')
    
    def fetch_game_object(self, id : str) -> Game:
        data = super().execute_fetchone('''SELECT * FROM games WHERE id = ?''', (id,))
        return Game(data)
    
    def update(self) -> None:
        games = get_json(f"https://freecashe.ws/api/games")
        buffer = []
        chunk_size = 1024
        for game in games:
            buffer.append(Game(game))
            if len(buffer) >= chunk_size:
                for g in buffer:
                    self.upsert_game(g)
                super().commit()
                buffer.clear()
        for g in buffer:
            self.upsert_game(g)
        super().commit()

    def upsert_game(self, game: Game, commit:bool=False) -> None:
        # Insert a new game if the game isn't in the db
        super().execute('''INSERT OR IGNORE INTO games (id, season, day, home_team_id, away_team_id, home_score, away_score, state) VALUES (:id, :season, :day, :home_team_id, :away_team_id, :home_score, :away_score, :state)''', game.get_json())
        # Otherwise update the game entry if it isn't already processed
        super().execute('''UPDATE games SET id=:id, day=:day, home_team_id=:home_team_id, away_team_id=:away_team_id, home_score=:home_score, away_score=:away_score, state=:state WHERE state != "Processed"''', game.get_json())
        if commit:
            super().commit()

# so help me god
class PlayersDatabase(Database):
    def __init__(self):
        super().__init__('players.db')

    def create_table(self, day: int) -> None:
        super().execute_commit(f'''CREATE TABLE IF NOT EXISTS day{day}(id STRING UNIQUE, first_name STRING, last_name STRING, team_id STRING, likes STRING, dislikes STRING, bats STRING, throws STRING, number STRING, position STRING, augments INTEGER, home STRING, stats STRING)''')

    def upsert_player(self, player: Player, commit:bool=False) -> None:
        super().execute('''INSERT OR REPLACE INTO players (id, first_name, last_name, team_id, likes, dislikes, bats, throws, number, position, augments, home, stats) VALUES (:id, :first_name, :last_name, :team_id, :likes, :dislikes, :bats, :throws, :number, :position, :augments, :home, :stats)''', player,get_json())
        if commit: super().commit()

    def fetch_player_object(self, id: str, day: int) -> Player:
        data = super().execute_fetchone(f'''SELECT * FROM players{day} WHERE id = ?''', (id,))
        return Player(data)
    
    # Chunk this?
    def calculate_median(self, day: int) -> None:
        # Get all players
        players = [Player(p) for p in super().execute_fetchall(f'''SELECT * FROM players{day}''')]
        median_player = {"id": "median", "first_name": "Median Player", "last_name": "(All Leagues)", "Stats": {}}

        # Loop through stats
        for stat in STATS:
            # get any non-zero stat
            values = []
            for player in players:
                v = player.stats.get(stat, 0)
                if v != 0: values.append(v)
            if values:
                median_player["Stats"][stat] = statistics.median(values)
        
        median_player = Player(median_player)
        self.upsert_player(median_player, commit=True)

    # Also chunk this?
    # Also not tested. Like everything else I've written thus far
    def calculate_bins(self, day: int) -> None:
        super().execute('''DROP TABLE IF EXISTS bins''')
        super().execute_commit('''CREATE TABLE bins(day, INTEGER, number INTEGER, data STRING)''')

        players = [Player(p) for p in super().execute_fetchall(f'''SELECT * FROM players{day}''')]
        # Calculated stats
        stats = ['strikeouts_per_nine_innings', 'walks_per_nine_innings', 'home_runs_per_nine_innings', 'walks_and_hits_per_inning_played', 'earned_run_average', 'innings_pitched', 'stolen_base_percentage', 'slugging_percentage', 'on_base_plus_slugging', 'on_base_percentage', 'batting_average']
        binned_players = [{} for _ in range(9)]

        for stat in stats:
            data = []
            for player in players:
                try:
                    # Has to calculate the stat, so it needs to be player object
                    v = getattr(player, 'get_' + stat)()
                    if v != 0:
                        data.append(v)
                except ZeroDivisionError:
                    pass
            if data:
                percentiles = np.percentile(data, [10 * i for i in range(1, 10)])
                for i, value in enumerate(percentiles):
                    binned_players[i][stat] = value
            
        rows = [(day, i, store_json(binned_players[i])) for i in range(9)]
        super().execute_many('INSERT INTO bins(day, number, data) VALUES(?, ?)', rows)
        super().commit()

    def update(self, destructive:bool=False) -> None:
        chunk_size = 1024
        buffer = []
        # Iterable now (:
        # Also this is the line I had mistyped that made the old system break (get_players vs get_updated_players)
        data = player_parser.get_players() if not destructive else player_parser.get_updated_players()
        for player_data in player_parser.get_updated_players():
            buffer.append(Player(player_data))

            # Commit the buffer
            if len(buffer) >= chunk_size:
                for p in buffer:
                    self.upsert_player(p)
                super().commit()
                buffer.clear()

        # Process remaining folk (left from the last chunk)
        if buffer:
            for p in buffer:
                self.upsert_player(p)
            super().commit()

        self.calculate_median()
        self.calculate_bins()

def create_tables():
    TeamsDatabase().create_table()
    LeaguesDatabase().create_table()
    GamesDatabase().create_table()

def close_databases():
    TeamsDatabase().close()
    LeaguesDatabase().close()
    GamesDatabase().close()

atexit.register(close_databases)