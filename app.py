'''
Howdy Hey! I'm Nova. I wrote most (if not all) of this code! (depends on if someone wants to help)
Just wanted to say thanks to Danny for making MMOLB and making the API accessible
This project is an exploration of a lot of things that are new to me
And I have no formal instruction in python, so be nice please (:
'''
from fastapi import FastAPI
from sqlite_handler import *

app = FastAPI()

@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}

@app.get("/team/{team_id}")
async def get_team_by_id(team_id: str) -> dict:
    print(team_id)
    team = teamsDatabase.fetch_team_object(team_id)
    return team.get_json()