__filename__ = "markets.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = ""

from environment import getRoomCulture


exchangeRate = {
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


def moneyPurchase(id, players: {}, cost: str) -> bool:
    """Does the player have enough money to buy something at the given cost?
    """
    costDenom = None
    costValue = 0
    for denom, ex in exchangeRate.items():
        if not cost.endswith(denom):
            continue
        costStr = cost.replace(denom, '')
        if not costStr.isdigit():
            return False
        costValue = int(costStr)
        costDenom = denom

    if not costDenom:
        return False

    for denom, qty in exchangeRate[costDenom].items():
        minQty = int((1.0 / qty) * costValue)
        if players[id][denom] >= minQty:
            players[id][denom] -= minQty
            return True
    return False


def getMarketType(roomName: str, markets: {}) -> str:
    """Returns the market type for the room name
    """
    for marketType, item in markets.items():
        if '|' not in marketType:
            if marketType.lower() in roomName:
                return marketType
        else:
            marketTypeList = marketType.lower().split('|')
            for marketType2 in marketTypeList:
                if marketType2 in roomName:
                    return marketType
    return None


def _marketSellsItemTypes(marketType: str, markets: {}) -> []:
    """Returns a list of item types which a market sells
    """
    marketSells = []
    if markets[marketType].get('trades'):
        marketSells = markets[marketType]['trades']
    if markets[marketType].get('sells'):
        if not marketSells:
            marketSells = markets[marketType]['sells']
        else:
            for itemType in markets[marketType]['sells']:
                if itemType not in marketSells:
                    marketSells.append(itemType)
    return marketSells


def marketBuysItemTypes(marketType: str, markets: {}) -> []:
    """Returns a list of item types which a market buys
    """
    marketBuys = []
    if markets[marketType].get('buys'):
        marketBuys = markets[marketType]['buys']
    if markets[marketType].get('trades'):
        if not marketBuys:
            marketBuys = markets[marketType]['trades']
        else:
            for itemType in markets[marketType]['trades']:
                if itemType not in marketBuys:
                    marketBuys.append(itemType)
    return marketBuys


def assign_markets(markets: {}, rooms: {}, items_db: {},
                   cultures_db: {}) -> int:
    """Assigns market types to rooms
    """
    noOfMarkets = 0
    for room_id, rm in rooms.items():
        # whether or not there is a market here depends on the room name
        rooms[room_id]['marketInventory'] = None
        roomName = rm['name'].lower()
        marketType = getMarketType(roomName, markets)
        if not marketType:
            continue

        # get the types of items sold
        rooms[room_id]['marketInventory'] = {}
        marketSells = _marketSellsItemTypes(marketType, markets)
        if not marketSells:
            continue

        # the market can have a culture, which then
        # determines the types of items within it
        roomCulture = getRoomCulture(cultures_db, rooms, room_id)

        inventoryCtr = 0
        itemNamesList = []
        for itemID, item in items_db.items():
            for itemType in marketSells:
                itemName = item['name'].lower()
                if itemType not in itemName:
                    continue
                if itemName in itemNamesList:
                    continue
                if item['weight'] <= 0:
                    continue
                if roomCulture:
                    if item.get('culture'):
                        if item['culture'] != roomCulture:
                            continue
                itemNamesList.append(itemName)
                itemCost = item['cost']
                # TODO cost and stock level could vary with
                # region, coords, season, etc
                # which could then lead to merchanting
                rooms[room_id]['marketInventory'][itemID] = {
                    "stock": 1,
                    "cost": itemCost
                }
                inventoryCtr += 1
                break
        if inventoryCtr > 0:
            noOfMarkets += 1
    return noOfMarkets


def buyItem(players: {}, id, itemID, items_db: {}, cost: str) -> bool:
    """Returns true if the given item was bought
    """
    if cost == '0':
        cost = '0gp'

    if moneyPurchase(id, players, cost):
        return True
    return False
