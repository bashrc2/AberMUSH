__filename__ = "npcs.py"
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
from functions import saveState
from functions import loadPlayersDB
from random import randint
from copy import deepcopy

import time

def npcRespawns(npcs):
        for (nid, pl) in list(npcs.items()):
                # print(npcs[nid])
                if npcs[nid]['whenDied'] is not None and int(time.time()) >= npcs[nid]['whenDied'] + npcs[nid]['respawn']:
                        #print("IN")
                        npcs[nid]['whenDied'] = None
                        #npcs[nid]['room'] = npcsTemplate[nid]['room']
                        npcs[nid]['room'] = npcs[nid]['lastRoom']
                        # print("respawning " + npcs[nid]['name'])
                        # print(npcs[nid]['hp'])
