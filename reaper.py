__filename__ = "reaper.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

#                   ...
#                 ;::::;
#               ;::::; :;
#             ;:::::'   :;
#            ;:::::;     ;.
#           ,:::::'       ;           OOO\
#           ::::::;       ;          OOOOO\
#           ;:::::;       ;         OOOOOOOO
#          ,;::::::;     ;'         / OOOOOOO
#        ;:::::::::`. ,,,;.        /  / DOOOOOO
#      .';:::::::::::::::::;,     /  /     DOOOO
#     ,::::::;::::::;;;;::::;,   /  /        DOOO
#    ;`::::::`'::::::;;;::::: ,#/  /          DOOO
#    :`:::::::`;::::::;;::: ;::#  /            DOOO
#    ::`:::::::`;:::::::: ;::::# /              DOO
#    `:`:::::::`;:::::: ;::::::#/               DOO
#     :::`:::::::`;; ;:::::::::##                OO
#     ::::`:::::::`;::::::::;:::#                OO
#     `:::::`::::::::::::;'`:;::#                O
#      `:::::`::::::::;' /  / `:#
#       ::::::`:::::;'  /  /   `#

import os
from functions import log
from functions import addToScheduler
from npcs import moveNPCs
from npcs import corpseExists
from random import randint
from copy import deepcopy

import time


def removeCorpses(corpses: {}):
    # Iterate through corpses and remove ones older than their TTL
    corpsesCopy = deepcopy(corpses)
    for (c, pl) in corpsesCopy.items():
        if int(time.time()) >= corpsesCopy[c]['died'] + corpsesCopy[c]['TTL']:
            del corpses[c]


def runDeaths(mud, players, corpses, fights, eventSchedule, scriptedEventsDB):
    # Handle Player Deaths
    for (pid, pl) in list(players.items()):
        if players[pid]['authenticated']:
            if players[pid]['hp'] <= 0:
                corpseName=str(players[pid]['name'] + "'s corpse")
                if not corpseExists(corpses,players[pid]['room'],corpseName):
                    # Create player's corpse in the room
                    corpses[len(corpses)] = {'room': players[pid]['room'],
                                             'name': corpseName,
                                             'inv': players[pid]['inv'],
                                             'died': int(time.time()),
                                             'TTL': players[pid]['corpseTTL'],
                                             'owner': 1}
                # Clear player's inventory, it stays on the corpse
                # This is bugged, causing errors when picking up things after death
                # players[pid]['inv'] = ''
                players[pid]['isInCombat'] = 0
                players[pid]['lastRoom'] = players[pid]['room']
                players[pid]['room'] = '$rid=1262$'
                fightsCopy = deepcopy(fights)
                for (fight, pl) in fightsCopy.items():
                    if fightsCopy[fight]['s1id'] == pid or fightsCopy[fight]['s2id'] == pid:
                        del fights[fight]
                for (pid2, pl) in list(players.items()):
                    if players[pid2]['authenticated'] is not None \
                       and players[pid2]['room'] == players[pid]['lastRoom'] \
                       and players[pid2]['name'] != players[pid]['name']:
                        mud.send_message(
                            pid2, '<u><f32>{}<r> <f124>has been killed.'.format(
                                players[pid]['name']) + "\n")
                        players[pid]['lastRoom'] = None
                        mud.send_message(
                            pid, '<b88><f158>Oh dear! You have died!\n')

                # Add Player Death event (ID:666) to eventSchedule
                addToScheduler(666, pid, eventSchedule, scriptedEventsDB)

                players[pid]['hp'] = 4
