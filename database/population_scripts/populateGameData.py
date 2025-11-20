"""
populate_games.py

Fetches all games for a specified NHL season and inserts:
- Game info
- Skater stats
- Goalie stats
- Goals and assists

Handles API errors with retries and commits data per game.
"""

import sqlite3
from nhlpy import NHLClient
from enum import IntEnum
import time
from datetime import date, timedelta
from game_data_helpers import safe_call, build_game_row, build_skaters_and_goalies, \
    process_play_by_play, process_goals_and_assists, SkaterStat, insert_game_data, SEASON

CUTOFF_DATE =  (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

# ---------------------------
# Main Function
# ---------------------------
def main():
    try:
        client = NHLClient()
        conn = sqlite3.connect("hockey.db")
        cursor = conn.cursor()

        game_ids = client.helpers.game_ids_by_season(SEASON, [2])

        for g in game_ids:
            print(f"Processing game {g}...")

            bs = safe_call(client.game_center.boxscore, g)
            pbp = safe_call(client.game_center.play_by_play, g)
            story = safe_call(client.game_center.game_story, g)

            if bs["gameDate"] >= CUTOFF_DATE:
                continue

            game_row = build_game_row(bs)
            skater_rows, goalie_rows, skater_dict = build_skaters_and_goalies(cursor, client, bs, pbp)
            process_play_by_play(pbp, skater_dict, skater_rows)
            goal_rows, assist_rows = process_goals_and_assists(story, g)

            insert_game_data(cursor, game_row, skater_rows, goalie_rows, goal_rows, assist_rows)
            conn.commit()

            print(f"Game {g} data inserted.")
            time.sleep(0.25)  # avoid hitting API too fast
        
        cursor.execute("""
            INSERT OR REPLACE INTO LastUpdate(update_type, last_date)
            VALUES (?, ?)
        """, ("game_update", CUTOFF_DATE))
        conn.commit()

        conn.close()

    except Exception as e:
        print(f"Error populating games: {e}")


if __name__ == "__main__":
    main()
