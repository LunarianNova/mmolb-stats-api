'''
I hate tests :/
Also yes, these aren't proper tests. Come at me
'''
import time
from sqlite_handler import *

def timed(name: str, func, *args, **kwargs) -> None:
    start_time = time.perf_counter()
    func(*args, **kwargs)
    end_time = time.perf_counter()
    print(f"{name} successful. Took {end_time - start_time:.3f} seconds.")

def main() -> None:
    timed("Updating Players", playersDatabase.update, destructive=False)
    timed("Creating Tables", create_tables)
    timed("Updating Games", gamesDatabase.update)
    timed("Updating Leagues", leaguesDatabase.update)
    timed("Updating Teams", teamsDatabase.update)
    timed("Updating Elo", teamsDatabase.update_elo)


if __name__ == "__main__":
    main()