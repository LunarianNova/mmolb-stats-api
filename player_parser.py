import requests
import shutil
import csv
import ast

URL = "https://freecashe.ws/api/allplayers/csv?fields=_id,FirstName,LastName,TeamID,Likes,Dislikes,Bats,Throws,Number,Position,PositionType,Augments,Bats,Home,Stats"
FILENAME = "databases/players.csv"

def download_csv():
    # Overwrite existing file with new, updated file
    with requests.get(URL, stream=True) as r:
        with open(FILENAME, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

def get_updated_players() -> list[dict]:
    download_csv()
    return get_players()


def get_players() -> iter:
    with open(FILENAME, encoding='UTF-8', errors='replace') as f:
        r = csv.reader(f)
        # Get headers from first row
        headers = next(r)
        for row in r:
            # Stats are the last object and are a dictionary represented as a string
            stats = row[-1]
            # Turn str to dict
            stats = ast.literal_eval(stats)
            # Get the stats for the player id if there are any
            stats = stats[list(stats.keys())[0]] if len(stats) > 0 else {}

            everything_else = row[:-1]

            p = {headers[i]: everything_else[i] for i in range(len(everything_else))}

            p["Stats"] = stats
            yield p