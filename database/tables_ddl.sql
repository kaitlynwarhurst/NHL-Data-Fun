CREATE TABLE Teams (
    team_abbrev TEXT PRIMARY KEY,
    team_name TEXT NOT NULL,
    conference TEXT,
    division TEXT,
    logo_url TEXT
);

CREATE TABLE Players (
    player_id INTEGER PRIMARY KEY,
    position_code TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    shoots_catches TEXT,
    current_team_abbrev TEXT,  
    birthdate TEXT,
    height_inches INTEGER,
    weight_lbs INTEGER,
    sweater_number INTEGER,
    birth_country TEXT,
    headshot_url TEXT,
    FOREIGN KEY (current_team_abbrev) REFERENCES Teams(team_abbrev)
);

CREATE TABLE Games (
    game_id INTEGER PRIMARY KEY,
    game_date TEXT NOT NULL,            -- store as "YYYY-MM-DD"
    home_team_abbrev TEXT NOT NULL,
    away_team_abbrev TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    ot BOOLEAN,
    shootout BOOLEAN,
    FOREIGN KEY (home_team_abbrev) REFERENCES Teams(team_abbrev),
    FOREIGN KEY (away_team_abbrev) REFERENCES Teams(team_abbrev)
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
    plus_minus INTEGER, team_abbrev TEXT,
    PRIMARY KEY (player_id, game_id),
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    FOREIGN KEY (game_id) REFERENCES Games(game_id),
    FOREIGN KEY (team_abbrev) REFERENCES Teams(team_abbrev)
);

CREATE TABLE GoalieGameStats (
    player_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    started BOOLEAN,
    saves INTEGER,
    goals_allowed INTEGER,
    shots_against INTEGER,
    PRIMARY KEY (player_id, game_id), team_abbrev TEXT,
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    FOREIGN KEY (game_id) REFERENCES Games(game_id),
    FOREIGN KEY (team_abbrev) REFERENCES Teams(team_abbrev)
);

CREATE TABLE LastUpdate (
    update_type TEXT PRIMARY KEY,
    last_date TEXT
);
