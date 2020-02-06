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


def runNewPlayerConnections(mud, id, players, playersDB, fights, Config):
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
            'cool': None,
            'cred': None,
            'inv': None,
            'authenticated': None,
            'speakLanguage': None,
            'language': None,
            'clo_head': None,
            'clo_neck': None,
            'clo_larm': None,
            'clo_rarm': None,
            'clo_lhand': None,
            'clo_rhand': None,
            'clo_lfinger': None,
            'clo_rfinger': None,
            'clo_lwrist': None,
            'clo_rwrist': None,
            'clo_chest': None,
            'clo_back': None,
            'clo_lleg': None,
            'clo_rleg': None,
            'clo_feet': None,
            'imp_head': None,
            'imp_larm': None,
            'imp_rarm': None,
            'imp_lhand': None,
            'imp_rhand': None,
            'imp_lfinger': None,
            'imp_rfinger': None,
            'imp_chest': None,
            'imp_back': None,
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
            'characterClass': None,
            'proficiencies': None,
            'fightingStyle': None,
            'restRequired': None,
            'enemy': None,
            'tempCharm': None,
            'tempCharmTarget': None,
            'tempCharmDuration': None,
            'tempCharmStart': None,
            'guild': None,
            'guildRole': None,
            'archetype': None,
            'preparedSpells': None,
            'spellSlots': None,
            'tempHitPoints': 0,
            'tempHitPointsStart': 0,
            'tempHitPointsDuration': 0,
            'prepareSpell': None,
            'prepareSpellProgress': None,
            'prepareSpellTime': None,
            'frozenDescription': None,
            'frozenStart': 0,
            'frozenDuration': 0,
            'affinity': None,
            'familiar': None
        }

        # Read in the MOTD file and send to the player
        motdFile = open(str(Config.get('System', 'Motd')), "r")
        motdLines = motdFile.readlines()
        motdFile.close()
        linesCount = len(motdLines)
        for l in motdLines:
            mud.send_message(id, l[:-1])

        if not os.path.isfile(".disableRegistrations"):
            mud.send_message_wrap(
                id, '<f220>', \
                '<f15>You can create a new Character, or use the following guest account:')
            mud.send_message(
                id, '<f15>Username: <r><f220>Guest<r><f15> Password: <r><f220>Password')
            mud.send_message(
                id, "\nWhat is your username? (type <f255>new<r> for new character)\n\n")
        else:
            mud.send_message(
                id, '<f0><b220> New account registrations are currently closed')

            mud.send_message(id, "\nWhat is your username?\n\n")
        log("Client ID: " + str(id) + " has connected", "info")


def runPlayerDisconnections(mud, id, players, playersDB, fights, Config,terminalMode: {}):
    # go through any recently disconnected players
    for id in mud.get_disconnected_players():

        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in players:
            continue

        terminalMode[str(id)]=False
        log("Player ID: " + str(id) + " has disconnected (" +
            str(players[id]['name']) + ")", "info")

        # go through all the players in the game
        for (pid, pl) in list(players.items()):
            # send each player a message to tell them about the diconnected
            # player if they are in the same room
            if players[pid]['authenticated'] is not None:
                if players[pid]['authenticated'] is not None \
                   and players[pid]['room'] == players[id]['room'] \
                   and players[pid]['name'] != players[id]['name']:
                    mud.send_message(
                        pid, "<f32><u>{}<r>'s body has vanished.".format(
                            players[id]['name']) + "\n\n")

        # Code here to save player to the database after he's disconnected and
        # before removing him from players dictionary
        if players[id]['authenticated'] is not None:
            log("Player disconnected, saving state", "info")
            saveState(players[id], playersDB, False)
            playersDB = loadPlayersDB()

        # Create a deep copy of fights, iterate through it and remove fights
        # disconnected player was taking part in
        fightsCopy = deepcopy(fights)
        for (fight, pl) in fightsCopy.items():
            if fightsCopy[fight]['s1'] == players[id]['name'] or fightsCopy[fight]['s2'] == players[id]['name']:
                del fights[fight]

        # remove the player's entry in the player dictionary
        del players[id]


def runPlayerConnections(mud,id,players,playersDB,fights,Config,terminalMode: {}):
    runNewPlayerConnections(mud,id,players,playersDB,fights,Config)
    runPlayerDisconnections(mud,id,players,playersDB,fights,Config,terminalMode)


def disconnectIdlePlayers(mud, players, allowedPlayerIdle):
    # Evaluate player idle time and disconnect if required
    now = int(time.time())
    playersCopy = deepcopy(players)
    for p in playersCopy:
        if now - playersCopy[p]['idleStart'] > allowedPlayerIdle:
            if players[p]['authenticated'] is not None:
                mud.send_message(
                    p,
                    "<f232><b11>Your body starts tingling. You instinctively hold your hand up to your face and notice you slowly begin to vanish. You are being disconnected due to inactivity...\n")
            else:
                mud.send_message(
                    p, "<f232><b11>You are being disconnected due to inactivity. Bye!\n")
            log("Character " +
                str(players[p]['name']) +
                " is being disconnected due to inactivity.", "warning")
            log("Disconnecting client " + str(p), "warning")
            del players[p]
            mud._handle_disconnect(p)

def playerInGame(id,username: str,players: {}) -> bool:
    """ is the given player already logged in?
    """
    for pl in players:
        if username is not None and \
           players[pl]['name'] is not None and \
           username == players[pl]['name'] and \
           pl != id:
            return True
    return False

def initialSetupAfterLogin(mud,id,players: {},dbResponse: []):
    """Sets up a player after login
    """
    players[id]['authenticated'] = True
    players[id]['prefix'] = "None"
    players[id]['room'] = dbResponse[1]
    players[id]['lvl'] = dbResponse[2]
    players[id]['exp'] = dbResponse[3]
    players[id]['str'] = dbResponse[4]
    players[id]['siz'] = dbResponse[5]
    players[id]['wei'] = dbResponse[6]
    players[id]['per'] = dbResponse[7]
    players[id]['endu'] = dbResponse[8]
    players[id]['cha'] = dbResponse[9]
    players[id]['int'] = dbResponse[10]
    players[id]['agi'] = dbResponse[11]
    players[id]['luc'] = dbResponse[12]
    players[id]['cool'] = dbResponse[13]
    players[id]['cred'] = dbResponse[14]
    players[id]['inv'] = dbResponse[15]  # .split(',')
    players[id]['speakLanguage'] = dbResponse[16]
    players[id]['language'] = dbResponse[17]
    players[id]['convstate'] = dbResponse[18]  # .split(',')
    # Example: item_list = [e for e in item_list if e not in ('item', 5)]
    #players[id]['inv'] = [e for e in players[id]['inv'] if e not in ('', ' ')]
    players[id]['clo_head'] = dbResponse[20]
    players[id]['clo_neck'] = dbResponse[21]
    players[id]['clo_larm'] = dbResponse[22]
    players[id]['clo_rarm'] = dbResponse[23]
    players[id]['clo_lhand'] = dbResponse[24]
    players[id]['clo_rhand'] = dbResponse[25]
    players[id]['clo_lfinger'] = dbResponse[26]
    players[id]['clo_rfinger'] = dbResponse[27]
    players[id]['clo_lwrist'] = dbResponse[28]
    players[id]['clo_rwrist'] = dbResponse[29]
    players[id]['clo_chest'] = dbResponse[30]
    players[id]['clo_back'] = dbResponse[31]
    players[id]['clo_lleg'] = dbResponse[32]
    players[id]['clo_rleg'] = dbResponse[33]
    players[id]['clo_feet'] = dbResponse[34]
    players[id]['imp_head'] = dbResponse[35]
    players[id]['imp_larm'] = dbResponse[36]
    players[id]['imp_rarm'] = dbResponse[37]
    players[id]['imp_lhand'] = dbResponse[38]
    players[id]['imp_rhand'] = dbResponse[39]
    players[id]['imp_lfinger'] = dbResponse[40]
    players[id]['imp_rfinger'] = dbResponse[41]
    players[id]['imp_chest'] = dbResponse[42]
    players[id]['imp_back'] = dbResponse[43]
    players[id]['imp_lleg'] = dbResponse[44]
    players[id]['imp_rleg'] = dbResponse[45]
    players[id]['imp_feet'] = dbResponse[46]
    players[id]['hpMax'] = dbResponse[47]
    players[id]['hp'] = dbResponse[48]
    players[id]['charge'] = dbResponse[49]
    players[id]['inDescription'] = dbResponse[50]
    players[id]['outDescription'] = dbResponse[51]
    players[id]['lookDescription'] = dbResponse[52]
    players[id]['isInCombat'] = 0
    players[id]['lastCombatAction'] = int(time.time())
    players[id]['isAttackable'] = 1
    players[id]['corpseTTL'] = 60
    players[id]['idleStart'] = int(time.time())
    players[id]['channels'] = dbResponse[53]
    players[id]['permissionLevel'] = dbResponse[54]
    players[id]['exAttribute0'] = dbResponse[55]
    players[id]['exAttribute1'] = dbResponse[56]
    players[id]['exAttribute2'] = dbResponse[57]
    players[id]['canGo'] = dbResponse[58]
    players[id]['canLook'] = dbResponse[59]
    players[id]['canSay'] = dbResponse[60]
    players[id]['canAttack'] = dbResponse[61]
    players[id]['canDirectMessage'] = dbResponse[62]
    players[id]['ref'] = dbResponse[63]
    players[id]['bodyType'] = dbResponse[64]
    players[id]['race'] = dbResponse[65]
    players[id]['characterClass'] = dbResponse[66]
    players[id]['proficiencies'] = dbResponse[67]
    players[id]['fightingStyle'] = dbResponse[68]
    players[id]['restRequired'] = dbResponse[69]
    players[id]['enemy'] = dbResponse[70]
    players[id]['tempCharm'] = dbResponse[71]
    players[id]['tempCharmTarget'] = dbResponse[72]
    players[id]['tempCharmDuration'] = dbResponse[73]
    players[id]['tempCharmStart'] = dbResponse[74]
    players[id]['guild'] = dbResponse[75]
    players[id]['guildRole'] = dbResponse[76]
    players[id]['archetype'] = dbResponse[77]
    players[id]['preparedSpells'] = dbResponse[78]
    players[id]['spellSlots'] = dbResponse[79]
    players[id]['tempHitPoints'] = dbResponse[80]
    players[id]['tempHitPointsStart'] = dbResponse[81]
    players[id]['tempHitPointsDuration'] = dbResponse[82]
    players[id]['prepareSpell'] = dbResponse[83]
    players[id]['prepareSpellProgress'] = dbResponse[84]
    players[id]['prepareSpellTime'] = dbResponse[85]
    players[id]['frozenDescription'] = dbResponse[86]
    players[id]['frozenStart'] = dbResponse[87]
    players[id]['frozenDuration'] = dbResponse[88]
    players[id]['affinity'] = dbResponse[89]
    players[id]['familiar'] = dbResponse[90]
    if players[id].get('visibleWhenWearing'):
        players[id]['visibleWhenWearing'] = dbResponse[91]

    log("Client ID: " +
        str(id) +
        " has successfully authenticated user " +
        players[id]['name'], "info")

    # print(players[id])
    # go through all the players in the game
    for (pid, pl) in list(players.items()):
        # send each player a message to tell them about the new
        # player
        if players[pid]['authenticated'] is not None \
           and players[pid]['room'] == players[id]['room'] \
           and players[pid]['name'] != players[id]['name']:
            mud.send_message(
                pid, '{} has materialised out of thin air nearby.'.format(
                    players[id]['name']) + "\n\n")

    # send the new player a welcome message
    mud.send_message_wrap(id, '<f255>', \
                          '<f220>Welcome to AberMUSH!, {}. '.format(players[id]['name']))
    mud.send_message_wrap(id, '<f255>', \
                          '<f255>Hello there traveller! You have connected to an AberMUSH server. You can move around the rooms along with other players (if you are lucky to meet any), attack each other (including NPCs), pick up and drop items and chat. Make sure to visit the repo for further info. Thanks for your interest in AberMUSH.')
    mud.send_message_wrap(id, '<f255>', \
                          "<f255>Type '<r><f220>help<r><f255>' for a list of all currently implemented commands/functions.")
    mud.send_message_wrap(id, '<f255>', \
                          "<f255>Type '<r><f220>look<r><f255>' to see what's around you.\n\n")

