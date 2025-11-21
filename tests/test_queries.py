import database.queries as q
from nhlpy import NHLClient
from database.population_scripts.game_data_helpers import safe_call

conn = q.get_connection()

client = NHLClient()

test_players = ['8477492', '8478402', '8484801', '8484144', '8476460', '8477956', '8484153']

test_data = {
    id : safe_call(client.stats.player_career_stats, id) for id in test_players
}


def test_get_player_by_id(db):
    for test in test_data:
        player = q.get_player_by_id(db, '8477934')

        assert player == (test["firstName"], test["lastName"])


test_get_player_by_id(conn)
    
