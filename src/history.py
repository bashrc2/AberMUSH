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


def _get_sword_name(description: str, sword_names: []) -> str:
    """Returns a sword name based on its description
    """
    randgen = random.Random(description)
    index = randgen.randint(0, len(sword_names) - 1)
    return sword_names[index]


def assign_item_history(key: int, item: {}, item_history: {}) -> bool:
    """Assigns history to a single item
    """
    assigned = False
    item['itemName'] = ''
    item_name_lower = item['name'].lower()
    key_str = str(key)

    for _, hist in item_history.items():
        if not hist.get('match'):
            continue
        match_str = hist['match']
        if match_str not in item_name_lower:
            continue
        item['itemName'] = \
            _get_sword_name(key_str + item['long_description'],
                            hist['names'])
        assigned = True
    return assigned


def assign_items_history(items_db: {}, item_history: {}) -> int:
    """Assign names and history to items
    """
    ctr = 0
    for key, value in items_db.items():
        if assign_item_history(key, value, item_history):
            ctr += 1
    return ctr
