CREATE TABLE Teams (
    team_id INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL,
    team_abbreviation TEXT NOT NULL UNIQUE,
    conference TEXT,      -- e.g., "Eastern", "Western"
    division TEXT,        -- e.g., "Atlantic", "Central"
    logo_url TEXT         -- store a link or local path
);

CREATE TABLE Players (
    player_id        INTEGER PRIMARY KEY,
    position_code    TEXT,          -- e.g., C, LW, RW, D, G
    first_name TEXT NOT NULL,
    last_name  TEXT NOT NULL,
    shoots_catches    TEXT,         -- "L", "R", or "C" (goalies)
    current_team_id   INTEGER,      -- FK to Teams
    birthdate         TEXT,         -- store as ISO "YYYY-MM-DD"
    started           INTEGER,      -- season started or debut year
    height_inches     INTEGER,      -- total inches
    weight_lbs        INTEGER,
    sweater_number    INTEGER,
    birth_country     TEXT,         -- "CAN", "USA", "SWE", etc.
    headshot_url      TEXT,         -- URL to headshot image

    FOREIGN KEY (current_team_id) REFERENCES Teams(team_id)
);

CREATE TABLE Games (
    game_id INTEGER PRIMARY KEY,
    game_date TEXT NOT NULL,          -- store as "YYYY-MM-DD"
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    ot BOOLEAN,
    shootout BOOLEAN,
    FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES Teams(team_id)
);

CREATE TABLE Goals (
    goal_id TEXT PRIMARY KEY,
    game_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    period INTEGER,
    time_in_period TEXT,              -- e.g., "12:34"
    goal_type TEXT,                   -- "even strength", "powerplay", etc.
    goalie_id INTEGER,
    video_link TEXT,
    FOREIGN KEY (game_id) REFERENCES Games(game_id),
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    FOREIGN KEY (goalie_id) REFERENCES Players(player_id)
);

CREATE TABLE Assists (
    player_id INTEGER NOT NULL,
    goal_id TEXT NOT NULL,
    assist_type TEXT,  -- "primary" or "secondary"
    PRIMARY KEY (player_id, goal_id),
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    FOREIGN KEY (goal_id) REFERENCES Goals(goal_id)
);

CREATE TABLE SkaterGameStats (
    player_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    toi INTEGER,                     -- time on ice in seconds
    faceoff_wins INTEGER,
    faceoff_losses INTEGER,
    hits INTEGER,
    blocks INTEGER,
    penalty_minutes INTEGER,
    shots INTEGER,
    plus_minus INTEGER,
    PRIMARY KEY (player_id, game_id),
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    FOREIGN KEY (game_id) REFERENCES Games(game_id)
);

CREATE TABLE GoalieGameStats (
    player_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    started BOOLEAN,
    saves INTEGER,
    goals_allowed INTEGER,
    shots_against INTEGER,
    PRIMARY KEY (player_id, game_id),
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    FOREIGN KEY (game_id) REFERENCES Games(game_id)
);

CREATE TABLE LastUpdate (
    update_type TEXT PRIMARY KEY,
    last_date TEXT
);
