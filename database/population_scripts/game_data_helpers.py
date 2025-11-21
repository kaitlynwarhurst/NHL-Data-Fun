"""
game_data_helpers.py

Shared helper functions for populating/updating NHL game data.
"""

import sqlite3
from nhlpy import NHLClient
from enum import IntEnum
import time
import random
from typing import List, Dict, Tuple

# ---------------------------
# Config
# ---------------------------
SEASON = "20252026"

# ---------------------------
# Utility
# ---------------------------
def safe_call(fn, *args, retries: int = 5, delay: float = 1):
    """
    Executes an NHL API function with retry logic and jitter.

    Args:
        fn (callable): API function to call.
        *args: Arguments to pass to fn.
        retries (int): Number of retries before failing.
        delay (float): Base delay between retries (seconds).

    Returns:
        Any: The return value of the API call.

    Raises:
        RuntimeError: If the API call fails after max retries.
    """
    for attempt in range(retries):
        try:
            return fn(*args)
        except Exception as e:
            print(f"Error: {e} — retrying ({attempt+1}/{retries})")
            time.sleep(delay + random.random())
    raise RuntimeError("Max retries exceeded")

# ---------------------------
# SkaterStat Enum
# ---------------------------
class SkaterStat(IntEnum):
    """Column indices for skater stats row."""
    PLAYER_ID = 0
    GAME_ID = 1
    TOI = 2
    FACEOFF_WINS = 3
    FACEOFF_LOSSES = 4
    HITS = 5
    BLOCKS = 6
    PENALTY_MINUTES = 7
    SHOTS = 8
    PLUS_MINUS = 9
    TEAM_ID = 10

# ---------------------------
# Player Utilities
# ---------------------------
def ensure_player(cursor: sqlite3.Cursor, client: NHLClient, player_id: int):
    """
    Ensures a player exists in the database. Inserts if missing, updates if changed.

    Args:
        cursor (sqlite3.Cursor): Database cursor.
        client (NHLClient): NHL API client.
        player_id (int): NHL player ID.

    Returns:
        None
    """
    cursor.execute("SELECT current_team_id FROM Players WHERE player_id = ?", (player_id,))
    row = cursor.fetchone()

    info = safe_call(client.stats.player_career_stats, player_id)

    pos = info.get("position")
    first = info["firstName"].get("default")
    last = info["lastName"].get("default")
    shoots = info.get("shootsCatches")
    birthdate = info.get("birthDate")
    height = info.get("heightInInches")
    weight = info.get("weightInPounds")
    sweater = info.get("sweaterNumber")
    birth_country = info.get("birthCountry")
    headshot = info.get("headshot")
    new_team = info.get("currentTeamId")

    # Insert if missing
    if row is None:
        cursor.execute(
            """
            INSERT INTO Players (
                player_id, position_code, first_name, last_name,
                shoots_catches, current_team_id, birthdate,
                height_inches, weight_lbs, sweater_number, birth_country, headshot_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (player_id, pos, first, last, shoots, new_team,
             birthdate, height, weight, sweater, birth_country, headshot)
        )
        return

    # Update if exists
    cursor.execute(
        """
        UPDATE Players SET
            position_code=?, first_name=?, last_name=?,
            shoots_catches=?, current_team_id=?, birthdate=?, height_inches=?,
            weight_lbs=?, sweater_number=?, birth_country=?, headshot_url=?
        WHERE player_id=?
        """,
        (pos, first, last, shoots, new_team, birthdate, height, weight,
         sweater, birth_country, headshot, player_id)
    )

# ---------------------------
# Game Processing
# ---------------------------
def build_game_row(bs: dict) -> List:
    """
    Builds a database row for the Games table.

    Args:
        bs (dict): NHL API boxscore data for a game.

    Returns:
        List: [game_id, game_date, home_team_id, away_team_id, ot (0/1), shootout (0/1)]
    """
    return [
        bs['id'],
        bs["gameDate"],
        bs["homeTeam"]["id"],
        bs["awayTeam"]["id"],
        0 if bs["gameOutcome"]["lastPeriodType"] == "REG" else 1,
        1 if bs["gameOutcome"]["lastPeriodType"] == "SHO" else 0,
    ]

def build_skaters_and_goalies(
    cursor: sqlite3.Cursor, client: NHLClient, bs: dict, pbp: dict
) -> Tuple[List[List], List[List], Dict[int,int]]:
    """
    Builds skater and goalie rows and a mapping of skater_id -> row index.

    Args:
        cursor (sqlite3.Cursor): Database cursor.
        client (NHLClient): NHL API client.
        bs (dict): Boxscore data.
        pbp (dict): Play-by-play data with roster information.

    Returns:
        Tuple:
            skater_rows (List[List]): Skater stat rows ready for DB insertion.
            goalie_rows (List[List]): Goalie stat rows ready for DB insertion.
            skater_dict (Dict[int,int]): Mapping player_id -> skater_rows index.
    """
    skater_rows = []
    goalie_rows = []
    skater_dict = {}

    roster = pbp["rosterSpots"]
    skater_rows_tmp = [[0 for _ in range(11)] for _ in range(len(roster))]
    idx = 0

    for side in ["awayTeam", "homeTeam"]:
        # Goalies
        for gk in bs["playerByGameStats"][side].get("goalies", []):
            ensure_player(cursor, client, gk["playerId"])
            goalie_rows.append([
                gk["playerId"],
                bs["id"],
                1 if gk.get("starter") else 0,
                gk.get("saves", 0),
                gk.get("goalsAgainst", 0),
                gk.get("shotsAgainst", 0),
                bs[side]["id"]
            ])

        # Skaters
        for pos in ["forwards", "defense"]:
            for sk in bs["playerByGameStats"][side].get(pos, []):
                pid = sk["playerId"]
                ensure_player(cursor, client, pid)
                skater_dict[pid] = idx
                skater_rows_tmp[idx][SkaterStat.PLAYER_ID] = pid
                skater_rows_tmp[idx][SkaterStat.GAME_ID] = bs["id"]
                skater_rows_tmp[idx][SkaterStat.TOI] = sk.get("toi", 0)
                skater_rows_tmp[idx][SkaterStat.PLUS_MINUS] = sk.get("plusMinus", 0)
                skater_rows_tmp[idx][SkaterStat.TEAM_ID] = bs[side]["id"]
                idx += 1

    skater_rows.extend(skater_rows_tmp)
    return skater_rows, goalie_rows, skater_dict

def process_play_by_play(pbp: dict, skater_dict: Dict[int,int], skater_rows: List[List]):
    """
    Updates skater_rows based on play-by-play events (faceoffs, hits, penalties, etc).

    Args:
        pbp (dict): Play-by-play data from NHL API.
        skater_dict (Dict[int,int]): Mapping player_id -> skater_rows index.
        skater_rows (List[List]): Skater rows to update in-place.

    Returns:
        None
    """
    for play in pbp.get("plays", []):
        details = play.get("details", {})
        t = play.get("typeDescKey")

        if t == "faceoff":
            w = details.get("winningPlayerId")
            l = details.get("losingPlayerId")
            if w in skater_dict:
                skater_rows[skater_dict[w]][SkaterStat.FACEOFF_WINS] += 1
            if l in skater_dict:
                skater_rows[skater_dict[l]][SkaterStat.FACEOFF_LOSSES] += 1

        elif t == "hit":
            h = details.get("hittingPlayerId")
            if h in skater_dict:
                skater_rows[skater_dict[h]][SkaterStat.HITS] += 1

        elif t == "blocked-shot":
            b = details.get("blockingPlayerId")
            if b in skater_dict:
                skater_rows[skater_dict[b]][SkaterStat.BLOCKS] += 1

        elif t == "penalty":
            c = details.get("committedByPlayerId")
            dur = details.get("duration", 0)
            if c in skater_dict:
                skater_rows[skater_dict[c]][SkaterStat.PENALTY_MINUTES] += dur

        elif t == "shot-on-goal":
            s = details.get("shootingPlayerId")
            if s in skater_dict:
                skater_rows[skater_dict[s]][SkaterStat.SHOTS] += 1

def process_goals_and_assists(story: dict, game_id: int) -> Tuple[List[List], List[List]]:
    """
    Processes scoring summary and builds goal and assist rows.

    Args:
        story (dict): Game story/summary from NHL API.
        game_id (int): NHL game ID.

    Returns:
        Tuple:
            goal_rows (List[List]): List of goal rows for DB insertion.
            assist_rows (List[List]): List of assist rows for DB insertion.
    """
    goal_rows = []
    assist_rows = []

    for period_block in story.get("summary", {}).get("scoring", []):
        period = period_block["periodDescriptor"]["number"]
        for goal in period_block.get("goals", []):
            gid = f"{game_id}_{goal['eventId']}"
            scorer = goal["playerId"]

            goal_rows.append([
                gid,
                game_id,
                scorer,
                period,
                goal.get("timeInPeriod"),
                goal.get("strength", "").lower(),
                None,
                goal.get("highlightClipSharingUrl")
            ])

            for i, ast in enumerate(goal.get("assists", [])):
                assist_rows.append([
                    ast["playerId"],
                    "primary" if i == 0 else "secondary",
                    gid
                ])

    return goal_rows, assist_rows

def insert_game_data(
    cursor: sqlite3.Cursor,
    game_row: List,
    skater_rows: List[List],
    goalie_rows: List[List],
    goal_rows: List[List],
    assist_rows: List[List]
):
    """
    Inserts all data for a single game into the database.

    Args:
        cursor (sqlite3.Cursor): Database cursor.
        game_row (List): Single row for Games table.
        skater_rows (List[List]): Skater stat rows.
        goalie_rows (List[List]): Goalie stat rows.
        goal_rows (List[List]): Goal rows.
        assist_rows (List[List]): Assist rows.

    Returns:
        None
    """
    cursor.execute(
        """
        INSERT OR REPLACE INTO Games (
            game_id, game_date, home_team_id, away_team_id,
            ot, shootout
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        game_row
    )

    cursor.executemany(
        """
        INSERT OR REPLACE INTO Goals (
            goal_id, game_id, player_id,
            period, time_in_period, goal_type,
            goalie_id, video_link
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        goal_rows
    )

    cursor.executemany(
        """
        INSERT OR REPLACE INTO Assists (
            player_id, assist_type, goal_id
        ) VALUES (?, ?, ?)
        """,
        assist_rows
    )

    cursor.executemany(
        """
        INSERT OR REPLACE INTO SkaterGameStats (
            player_id, game_id, toi, faceoff_wins,
            faceoff_losses, hits, blocks,
            penalty_minutes, shots, plus_minus, team_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        skater_rows
    )

    cursor.executemany(
        """
        INSERT OR REPLACE INTO GoalieGameStats (
            player_id, game_id, started,
            saves, goals_allowed, shots_against, team_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        goalie_rows
    )
