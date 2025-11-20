import sqlite3
from nhlpy import NHLClient
from enum import IntEnum
import time
import random
from datetime import date, timedelta
from game_data_helpers import safe_call, build_game_row, build_skaters_and_goalies, \
    process_play_by_play, process_goals_and_assists, SkaterStat, ensure_player, insert_game_data

def main():
    try:
        client = NHLClient()

        conn = sqlite3.connect("hockey.db")
        cursor = conn.cursor()

        # Get all regular season games
        def process_game_for_date(sched_date):
            sched = client.schedule.daily_schedule(sched_date)
            game_ids = sched["games"]

            for game in game_ids:
                g = game["id"]
                print(g)

                pbp = safe_call(client.game_center.play_by_play, g)
                bs = safe_call(client.game_center.boxscore, g)
                story = safe_call(client.game_center.game_story, g)

                game_row = build_game_row(bs)
                skater_rows, goalie_rows, skater_dict = build_skaters_and_goalies(cursor, client, bs, pbp)
                process_play_by_play(pbp, skater_dict, skater_rows)
                goal_rows, assist_rows = process_goals_and_assists(story, g)

                insert_game_data(cursor, game_row, skater_rows, goalie_rows, goal_rows, assist_rows)
                conn.commit()

            cursor.execute("SELECT last_date FROM LastRun WHERE script_name='daily_refresh'")


        row = cursor.fetchone()
        last_date = date.fromisoformat(row[0])
        current_date = last_date + timedelta(days=1)
        yesterday_date = date.today() - timedelta(days=1)

        while current_date <= yesterday_date:
            process_game_for_date(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)

        cursor.execute("""
            INSERT OR REPLACE INTO LastUpdate(update_type, last_date)
            VALUES (?, ?)
        """, ("game_update", yesterday_date.strftime("%Y-%m-%d")))
        conn.commit()
        

        conn.close()


    except Exception as e:
        print(f"Error updating games: {e}")

if __name__ == "__main__":
    main()