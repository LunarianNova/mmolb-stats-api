'''
Howdy Hey! I'm Nova. I wrote most (if not all) of this code! (depends on if someone wants to help)
Just wanted to say thanks to Danny for making MMOLB and making the API accessible
This project is an exploration of a lot of things that are new to me
And I have no formal instruction in python, so be nice please (:
'''
from fastapi import FastAPI
from sqlite_handler import *
from typing import List
import asyncio
import time

app = FastAPI()

@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}

@app.get("/teams", response_model=List[dict])
async def get_all_teams() -> List[dict]:
    teams = teamsDatabase.execute_fetchall('''SELECT * FROM teams''')
    return [Team(t).get_json() for t in teams]

@app.get("/team/{team_id}")
async def get_team_by_id(team_id: str, named_league:bool=False) -> dict:
    team = teamsDatabase.fetch_team_object(team_id)
    if named_league:
        team.league = leaguesDatabase.fetch_league_object(team.league)
        team.league = team.league.emoji + " " + team.league.name + " League"
    return team.get_json()

@app.get("/team/{team_id}/players", response_model=List[dict])
async def get_players_in_team(team_id: str) -> list[dict]:
    # Gets all players that were ever on the team in history
    players = playersDatabase.execute_fetchall('''SELECT DISTINCT id FROM players WHERE team_id = ?''', (team_id,))
    player_obj = []
    for i in players:
        p = playersDatabase.execute_fetchone('''SELECT * FROM players WHERE id = ? AND day = (SELECT MAX(day) FROM players WHERE id = ?)''', (i[0], i[0],))
        player_obj.append(Player(p))
    players = [p.get_json() for p in player_obj]   
    return players

@app.get("/team/{team_id}/games", response_model=List[dict])
async def get_games_by_team(team_id: str) -> list[dict]:
    games = gamesDatabase.execute_fetchall('''SELECT * FROM games WHERE home_team_id = ? OR away_team_id = ? ORDER BY day DESC''', (team_id, team_id,))
    return [Game(g).get_json() for g in games]

@app.get("/games", response_model=List[dict])
async def get_all_games() -> list[dict]:
    games = gamesDatabase.execute_fetchall('''SELECT * FROM games''')
    return [Game(g).get_json() for g in games]

async def update_teams_leagues_games():
    global start_time
    teamsDatabase.update_all()
    leaguesDatabase.update()
    gamesDatabase.update()
    print("Finished updating teams, leagues, games. Running for " + str((time.time() - start_time)/60) + " minutes")

async def update_players():
    global start_time
    playersDatabase.update(destructive=True)
    print("Finished updating players. Running for " + str((time.time() - start_time)/60) + " minutes")

async def run_update():
    while True:
        for _ in range(5):
            asyncio.create_task(update_teams_leagues_games())
            await asyncio.sleep(180)
        asyncio.create_task(update_players())

# Deprecated, but I'm too lazy to find the new method
@app.on_event('startup')
async def app_startup():
    global start_time
    start_time = time.time()
    asyncio.create_task(run_update())