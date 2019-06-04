__filename__ = "playerconnections.py"
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

maximum_players = 128

def runNewPlayerConnections(mud,id,players,playersDB,fights,Config):
    # go through any newly connected players
    for id in mud.get_new_players():
                if len(players) >= maximum_players:
                    mud.send_message(id, "Player limit reached\n\n")
                    mud._handle_disconnect(id)

                # add the new player to the dictionary, noting that they've not been
                # named yet.
                # The dictionary key is the player's id number. We set their room to
                # None initially until they have entered a name
                # Try adding more player stats - level, gold, inventory, etc
                players[id] = {
                        'name': None,
                        'prefix': None,
                        'room': None,
                        'lvl': None,
                        'exp': None,
                        'str': None,
                        'siz': None,
                        'wei': None,
                        'per': None,
                        'endu': None,
                        'cha': None,
                        'int': None,
                        'agi': None,
                        'luc': None,
                        'cred': None,
                        'inv': None,
                        'authenticated': None,
                        'clo_head': None,
                        'clo_neck': None,
                        'clo_larm': None,
                        'clo_rarm': None,
                        'clo_lhand': None,
                        'clo_rhand': None,
                        'clo_lwrist': None,
                        'clo_rwrist': None,
                        'clo_chest': None,
                        'clo_lleg': None,
                        'clo_rleg': None,
                        'clo_feet': None,
                        'imp_head': None,
                        'imp_larm': None,
                        'imp_rarm': None,
                        'imp_lhand': None,
                        'imp_rhand': None,
                        'imp_chest': None,
                        'imp_lleg': None,
                        'imp_rleg': None,
                        'imp_feet': None,
                        'hp': None,
                        'charge': None,
                        'isInCombat': None,
                        'lastCombatAction': None,
                        'isAttackable': None,
                        'lastRoom': None,
                        'corpseTTL': None,
                        'canSay': None,
                        'canGo': None,
                        'canLook': None,
                        'canAttack': None,
                        'canDirectMessage': None,
                        'inDescription': None,
                        'outDescription': None,
                        'lookDescription': None,
                        'idleStart': int(time.time()),
                        'channels': None,
                        'permissionLevel': None,
                        'defaultChannel': None,
                        'exAttribute0': None,
                        'exAttribute1': None,
                        'exAttribute2': None,
                        'ref': None,
                        'bodyType': None,
                        'race': None,
                        'characterClass': None
                }

                # Read in the MOTD file and send to the player
                motdFile = open(str(Config.get('System', 'Motd')) ,"r")
                motdLines = motdFile.readlines()
                motdFile.close()
                linesCount = len(motdLines)
                for l in motdLines:
                        mud.send_message(id, l[:-1])

                if not os.path.isfile(".disableRegistrations"):
                        mud.send_message(id, '<f15>You can create a new Character, or use the following guest account:')
                        mud.send_message(id, '<f15>Username: <r><f220>Guest<r><f15> Password: <r><f220>Password')
                        mud.send_message(id, "\nWhat is your username? (type <f255>new<r> for new character)\n\n")
                else:
                        mud.send_message(id, '<f0><b220> New account registrations are currently closed')

                        mud.send_message(id, "\nWhat is your username?\n\n")
                log("Client ID: " + str(id) + " has connected", "info")

def runPlayerDisconnections(mud,id,players,playersDB,fights,Config):
    # go through any recently disconnected players
    for id in mud.get_disconnected_players():

                # if for any reason the player isn't in the player map, skip them and
                # move on to the next one
                if id not in players:
                        continue

                log("Player ID: " + str(id) + " has disconnected (" + str(players[id]['name']) + ")", "info")

                # go through all the players in the game
                for (pid, pl) in list(players.items()):
                        # send each player a message to tell them about the diconnected
                        # player if they are in the same room
                        if players[pid]['authenticated'] is not None:
                                if players[pid]['authenticated'] is not None \
                                   and players[pid]['room'] == players[id]['room'] \
                                   and players[pid]['name'] != players[id]['name']:
                                        mud.send_message(pid,
                                                         "<f32><u>{}<r>'s body has vanished.".format(players[id]['name']) + "\n\n")

                # Code here to save player to the database after he's disconnected and before removing him from players dictionary
                if players[id]['authenticated'] is not None:
                        log("Player disconnected, saving state", "info")
                        saveState(players[id], playersDB, False)
                        playersDB = loadPlayersDB()

                # Create a deep copy of fights, iterate through it and remove fights disconnected player was taking part in
                fightsCopy = deepcopy(fights)
                for (fight, pl) in fightsCopy.items():
                        if fightsCopy[fight]['s1'] == players[id]['name'] or fightsCopy[fight]['s2'] == players[id]['name']:
                                del fights[fight]

                # remove the player's entry in the player dictionary
                del players[id]

def runPlayerConnections(mud,id,players,playersDB,fights,Config):
    runNewPlayerConnections(mud,id,players,playersDB,fights,Config)
    runPlayerDisconnections(mud,id,players,playersDB,fights,Config)

def disconnectIdlePlayers(mud,players,allowedPlayerIdle):
        # Evaluate player idle time and disconnect if required
        now = int(time.time())
        playersCopy = deepcopy(players)
        for p in playersCopy:
                if now - playersCopy[p]['idleStart'] > allowedPlayerIdle:
                        if players[p]['authenticated'] != None:
                                mud.send_message(p, "<f232><b11>Your body starts tingling. You instinctively hold your hand up to your face and notice you slowly begin to vanish. You are being disconnected due to inactivity...\n")
                        else:
                                mud.send_message(p, "<f232><b11>You are being disconnected due to inactivity. Bye!\n")
                        log("Character " + str(players[p]['name']) + " is being disconnected due to inactivity.", "warning")
                        log("Disconnecting client " + str(p), "warning")
                        del players[p]
                        mud._handle_disconnect(p)
