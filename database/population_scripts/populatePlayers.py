"""
populate_players.py

Fetches all NHL players from nhlpy for each team and inserts them into the Players table.
Uses SQLite and replaces existing entries if the player already exists.
"""

import sqlite3
from nhlpy import NHLClient
import os

# Function to flatten roster
def flatten_roster(roster, team_id):
    """
    Converts a team's roster data from nhlpy into a list of tuples suitable for inserting into the Players table.

    Args:
        roster (dict): The roster dictionary from nhlpy for a single team.
        team_id (int): The franchise_id of the team, used as current_team_id in the database.

    Returns:
        List[Tuple]: Each tuple corresponds to a row for the Players table.
    """
    players = []
    for category in ["forwards","defensemen", "goalies"]:
        for p in roster.get(category, []):
            players.append((
                p["id"],                        # player_id
                p["positionCode"],               # position_code
                p["firstName"]["default"],       # first_name
                p["lastName"]["default"],        # last_name
                p.get("shootsCatches"),          # shoots_catches
                team_id,                         # current_team_id
                p.get("birthDate"),              # birthdate
                p.get("heightInInches"),         # height_inches
                p.get("weightInPounds"),         # weight_lbs
                p.get("sweaterNumber"),          # sweater_number
                p.get("birthCountry"),           # birth_country
                p.get("headshot")                # headshot_url
            ))
    return players

def main():
    try:
        
        client = NHLClient()
        
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        DB_PATH = os.path.join(BASE_DIR, "database", "hockey.db")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        teams = client.teams.teams()
        players = []

        for t in teams:
            roster = client.players.players_by_team(t["abbr"], "20252026")
            
            player_rows = flatten_roster(roster, t["franchise_id"])
            
            cursor.executemany("""
                INSERT OR REPLACE INTO Players (
                    player_id,
                    position_code,
                    first_name,
                    last_name,
                    shoots_catches,
                    current_team_id,
                    birthdate,
                    height_inches,
                    weight_lbs,
                    sweater_number,
                    birth_country,
                    headshot_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, player_rows)
            
            # Commit per team
            conn.commit()
            print(f"Inserted {len(player_rows)} players for team {t['name']}")

        # Close connection
        conn.close()

    except Exception as e:
        print(f"Error populating players: {e}")

if __name__ == "__main__":
    main()