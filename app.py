'''
Howdy Hey! I'm Nova. I wrote most (if not all) of this code! (depends on if someone wants to help)
Just wanted to say thanks to Danny for making MMOLB and making the API accessible
This project is an exploration of a lot of things that are new to me
And I have no formal instruction in python, so be nice please (:
'''
from fastapi import FastAPI
from sqlite_handler import *
from typing import List

app = FastAPI()

@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}

@app.get("/team/{team_id}")
async def get_team_by_id(team_id: str) -> dict:
    team = teamsDatabase.fetch_team_object(team_id)
    return team.get_json()

@app.get("/team/{team_id}/players", response_model=List[dict])
async def get_players_in_team(team_id: str) -> dict:
    max_day = playersDatabase.execute_fetchone('''SELECT MAX(day) FROM players''')[0]
    players = playersDatabase.execute_fetchall('''SELECT * FROM players WHERE team_id = ? AND day = ?''', (team_id, max_day,))
    players = [Player(p).get_json() for p in players]
    offset = 0
    while players == []:
        offset += 1
        players = playersDatabase.execute_fetchall(f'''SELECT * FROM players WHERE team_id = ? AND day = ?''', (team_id, max_day-offset,))
        players = [Player(p).get_json() for p in players]
    return players