__filename__ = "familiar.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from functions import log
from functions import moveNPCs
from random import randint
from copy import deepcopy

import time

# Movement modes for familiars
familiarModes = ("follow","scout")

def getFamiliarModes():
    return familiarModes

def familiarRecall(mud, players, id, npcs, npcsDB):
    """Move any familiar to the player's location
    """
    # remove any existing familiars
    removals = []
    for (index, details) in npcs.items():
        if details['familiarOf'] == players[id]['name']:
            removals.append(index)

    for index in removals:
        del npcs[index]

    # By default player has no familiar
    players[id]['familiar'] = -1

    # Find familiar and set its room to that of the player
    for (index, details) in npcsDB.items():
        if details['familiarOf'] == players[id]['name']:
            players[id]['familiar'] = int(index)
            details['room'] = players[id]['room']
            if not npcs.get(str(index)):
                npcs[str(index)] = deepcopy(npcsDB[index])
            npcs[str(index)]['room'] = players[id]['room']
            mud.send_message(id, "Your familiar is recalled.\n\n")
            break
