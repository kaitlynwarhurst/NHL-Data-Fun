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
