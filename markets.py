__filename__ = "markets.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = ""

from environment import get_room_culture


EXCHANGE_RATE = {
    "cp": {
        "cp": 1,
        "sp": 10,
        "ep": 50,
        "gp": 100,
        "pp": 1000
    },
    "sp": {
        "cp": 0.1,
        "sp": 1,
        "ep": 5,
        "gp": 10,
        "pp": 100
    },
    "ep": {
        "cp": 0.02,
        "sp": 0.2,
        "ep": 1,
        "gp": 2,
        "pp": 20
    },
    "gp": {
        "cp": 0.01,
        "sp": 0.1,
        "ep": 0.5,
        "gp": 1,
        "pp": 10
    },
    "pp": {
        "cp": 0.001,
        "sp": 0.01,
        "ep": 0.05,
        "gp": 0.1,
        "pp": 1
    }
}


def money_purchase(id, players: {}, cost: str) -> bool:
    """Does the player have enough money to buy something at the given cost?
    """
    cost_denom = None
    cost_value = 0
    for denom, _ in EXCHANGE_RATE.items():
        if not cost.endswith(denom):
            continue
        cost_str = cost.replace(denom, '')
        if not cost_str.isdigit():
            return False
        cost_value = int(cost_str)
        cost_denom = denom

    if not cost_denom:
        return False

    for denom, qty in EXCHANGE_RATE[cost_denom].items():
        min_qty = int((1.0 / qty) * cost_value)
        if players[id][denom] >= min_qty:
            players[id][denom] -= min_qty
            return True
    return False


def get_market_type(room_name: str, markets: {}) -> str:
    """Returns the market type for the room name
    """
    for market_type, _ in markets.items():
        if '|' not in market_type:
            if market_type.lower() in room_name:
                return market_type
        else:
            market_type_list = market_type.lower().split('|')
            for market_type2 in market_type_list:
                if market_type2 in room_name:
                    return market_type
    return None


def _market_sells_item_types(market_type: str, markets: {}) -> []:
    """Returns a list of item types which a market sells
    """
    market_sells = []
    if markets[market_type].get('trades'):
        market_sells = markets[market_type]['trades']
    if markets[market_type].get('sells'):
        if not market_sells:
            market_sells = markets[market_type]['sells']
        else:
            for item_type in markets[market_type]['sells']:
                if item_type not in market_sells:
                    market_sells.append(item_type)
    return market_sells


def market_buys_item_types(market_type: str, markets: {}) -> []:
    """Returns a list of item types which a market buys
    """
    market_buys = []
    if markets[market_type].get('buys'):
        market_buys = markets[market_type]['buys']
    if markets[market_type].get('trades'):
        if not market_buys:
            market_buys = markets[market_type]['trades']
        else:
            for item_type in markets[market_type]['trades']:
                if item_type not in market_buys:
                    market_buys.append(item_type)
    return market_buys


def assign_markets(markets: {}, rooms: {}, items_db: {},
                   cultures_db: {}) -> int:
    """Assigns market types to rooms
    """
    no_of_markets = 0
    for room_id, rm in rooms.items():
        # whether or not there is a market here depends on the room name
        rooms[room_id]['marketInventory'] = None
        room_name = rm['name'].lower()
        market_type = get_market_type(room_name, markets)
        if not market_type:
            continue

        # get the types of items sold
        rooms[room_id]['marketInventory'] = {}
        market_sells = _market_sells_item_types(market_type, markets)
        if not market_sells:
            continue

        # the market can have a culture, which then
        # determines the types of items within it
        room_culture = get_room_culture(cultures_db, rooms, room_id)

        inventory_ctr = 0
        item_names_list = []
        for item_id, item in items_db.items():
            for item_type in market_sells:
                item_name = item['name'].lower()
                if item_type not in item_name:
                    continue
                if item_name in item_names_list:
                    continue
                if item['weight'] <= 0:
                    continue
                if room_culture:
                    if item.get('culture'):
                        if item['culture'] != room_culture:
                            continue
                item_names_list.append(item_name)
                item_cost = item['cost']
                # TODO cost and stock level could vary with
                # region, coords, season, etc
                # which could then lead to merchanting
                rooms[room_id]['marketInventory'][item_id] = {
                    "stock": 1,
                    "cost": item_cost
                }
                inventory_ctr += 1
                break
        if inventory_ctr > 0:
            no_of_markets += 1
    return no_of_markets


def buy_item(players: {}, id, item_id: int, items_db: {},
             cost: str) -> bool:
    """Returns true if the given item was bought
    """
    if cost == '0':
        cost = '0gp'

    if money_purchase(id, players, cost):
        return True
    return False
