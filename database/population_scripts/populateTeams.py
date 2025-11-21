"""
populate_teams.py

Fetches all NHL teams via nhlpy and inserts them into the Teams table.
Uses SQLite and updates existing entries if the team already exists.
"""

import sqlite3
from nhlpy import NHLClient
import os

def main():
    try:
        client = NHLClient()

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        DB_PATH = os.path.join(BASE_DIR, "database", "hockey.db")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        teams = client.teams.teams()

        team_rows = [
            (
                t["franchise_id"],
                t["name"],
                t["abbr"],
                t["conference"]["name"],
                t["division"]["name"],
                t["logo"]
            )
            for t in teams
        ]

        cursor.execute("BEGIN TRANSACTION")  # major speed boost

        cursor.executemany("""
            INSERT INTO Teams (
                team_id,
                team_name,
                team_abbreviation,
                conference,
                division,
                logo_url
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(team_id) DO UPDATE SET
            team_name=excluded.team_name,
            team_abbreviation=excluded.team_abbreviation,
            conference=excluded.conference,
            division=excluded.division,
            logo_url=excluded.logo_url;
        """, team_rows)

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error populating teams: {e}")

if __name__ == "__main__":
    main()