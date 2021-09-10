__filename__ = "history.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski", "Mark Frimston"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Environment Simulation"

import random


def _getSwordName(description: str, swordNames: []) -> str:
    """Returns a sword name based on its description
    """
    randgen = random.Random(description)
    index = randgen.randint(0, len(swordNames) - 1)
    return swordNames[index]


def assignItemHistory(key: int, item: {}, itemHistory: {}) -> bool:
    """Assigns history to a single item
    """
    assigned = False
    item['itemName'] = ''
    itemNameLower = item['name'].lower()
    keyStr = str(key)

    for name, hist in itemHistory.items():
        if not hist.get('match'):
            continue
        matchStr = hist['match']
        if matchStr in itemNameLower:
            item['itemName'] = \
                _getSwordName(keyStr + item['long_description'], hist['names'])
            assigned = True
    return assigned


def assignItemsHistory(itemsDB: {}, itemHistory: {}) -> int:
    """Assign names and history to items
    """
    ctr = 0
    for key, value in itemsDB.items():
        if assignItemHistory(key, value, itemHistory):
            ctr += 1
    return ctr
