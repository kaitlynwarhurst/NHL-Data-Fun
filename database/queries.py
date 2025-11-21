import sqlite3

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



