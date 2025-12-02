import sqlite3
import os
import pandas as pd

def get_connection(db_path="hockey.db"):
    """Return a connection to the SQLite database."""
    return sqlite3.connect(db_path)

def get_player_by_id(conn, player_id):
    """Return first_name, last_name for a given player_id.
    Args: conn = that database connection
    """
    query = """
        SELECT first_name, last_name
        FROM Players
        WHERE player_id = ?;
    """
    return conn.execute(query, (player_id,)).fetchone()

def get_all_player_summary_stats(conn):
    """
    Return first_name, last_name, team_name, position, weight, height, games_played, goals, assists, power play goals, power play assists, short handed goals, short handed assists, penalty minutes, face off wins, face off losses, hattricks, shots on goal, hits, blocks
    
    """

    query = """
        SELECT
        p.first_name,
        p.last_name,
        t.team_name,
        p.position_code AS position,
        p.weight_lbs AS weight,
        p.height_inches AS height,
        COUNT(DISTINCT s.game_id) AS games_played,
        
        -- Goals breakdown
        COUNT(DISTINCT g.goal_id) AS goals,
        SUM(CASE WHEN a.goal_id IS NOT NULL THEN 1 ELSE 0 END) AS assists,
        
        SUM(CASE WHEN g.goal_type = 'powerplay' THEN 1 ELSE 0 END) AS power_play_goals,
        SUM(CASE WHEN g.goal_type = 'short handed' THEN 1 ELSE 0 END) AS short_handed_goals,
        
        SUM(CASE WHEN g.goal_id IN (
            SELECT goal_id
            FROM Assists
        ) AND g.goal_type = 'powerplay' THEN 1 ELSE 0 END) AS power_play_assists,
        
        SUM(CASE WHEN g.goal_id IN (
            SELECT goal_id
            FROM Assists
        ) AND g.goal_type = 'short handed' THEN 1 ELSE 0 END) AS short_handed_assists,
        
        SUM(s.penalty_minutes) AS penalty_minutes,
        SUM(s.faceoff_wins) AS faceoff_wins,
        SUM(s.faceoff_losses) AS faceoff_losses,
        
        -- Hattricks: 3+ goals in a game
        SUM(CASE WHEN g_count.goals_in_game >= 3 THEN 1 ELSE 0 END) AS hattricks,
        
        SUM(s.shots) AS shots_on_goal,
        SUM(s.hits) AS hits,
        SUM(s.blocks) AS blocks

        FROM Players p
        LEFT JOIN Teams t ON p.current_team_id = t.team_id
        LEFT JOIN SkaterGameStats s ON p.player_id = s.player_id
        LEFT JOIN Goals g ON p.player_id = g.player_id
        LEFT JOIN (
            SELECT g.player_id, g.game_id, COUNT(*) AS goals_in_game
            FROM Goals g
            GROUP BY g.player_id, g.game_id
        ) g_count ON p.player_id = g_count.player_id

        LEFT JOIN Assists a ON g.goal_id = a.goal_id AND a.player_id = p.player_id

        WHERE position != 'G'

        GROUP BY p.player_id
        ORDER BY goals DESC, p.last_name, p.first_name;

    """
    cursor = conn.cursor()
    return cursor.execute(query, ()).fetchall()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "hockey.db")
conn = get_connection(DB_PATH)


tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

print(tables)

players = (get_all_player_summary_stats(conn))
df = pd.DataFrame(players)
df.to_csv("players.csv")

conn.close()