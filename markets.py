__filename__ = "markets.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = ""


def _getMarketType(roomName: str, markets: {}) -> str:
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


def assignMarkets(markets: {}, rooms: {}, itemsDB: {}) -> int:
    """Assigns market types to rooms
    """
    noOfMarkets = 0
    for roomID, rm in rooms.items():
        rooms[roomID]['marketInventory'] = None
        roomName = rm['name'].lower()
        marketType = _getMarketType(roomName, markets)
        if not marketType:
            continue
        rooms[roomID]['marketInventory'] = {}
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
        if not marketSells:
            continue
        inventoryCtr = 0
        for itemID, item in itemsDB.items():
            for itemType in marketSells:
                itemName = item['name'].lower()
                if itemType not in itemName:
                    continue
                itemCost = item['cost']
                # TODO cost and stock level could vary with
                # region, coords, season, etc
                # which could then lead to merchanting
                rooms[roomID]['marketInventory'][itemID] = {
                    "stock": 1,
                    "cost": itemCost
                }
                inventoryCtr += 1
                break
        if inventoryCtr > 0:
            noOfMarkets += 1
    return noOfMarkets


def buyItem(players: {}, id, itemID, itemsDB: {}, cost: str) -> bool:
    """Returns true if the given item was bought
    """
    if cost == '0':
        cost = '0gp'

    denomination = 'gp'
    if cost.endswith('sp'):
        denomination = 'sp'
    elif cost.endswith('cp'):
        denomination = 'cp'
    elif cost.endswith('ep'):
        denomination = 'ep'
    elif cost.endswith('pp'):
        denomination = 'pp'

    qty = int(cost.replace(denomination, ''))
    if denomination not in players[id]:
        return False
    if int(players[id][denomination]) >= qty:
        players[id][denomination] = int(players[id][denomination]) - qty
        return True
    return False
