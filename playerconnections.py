__filename__ = "playerconnections.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"
__module_group__ = "Core"

import os
from functions import log
from functions import saveState
from functions import loadPlayersDB
from functions import deepcopy
# from copy import deepcopy

import time

maximum_players = 128


def _runNewPlayerConnections(mud, id, players, playersDB, fights, Config):
    # go through any newly connected players
    for id in mud.get_new_players():
        if len(players) >= maximum_players:
            mud.sendMessage(id, "Player limit reached\n\n")
            mud.handleDisconnect(id)

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
            'pp': None,
            'ep': None,
            'cp': None,
            'sp': None,
            'gp': None,
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
            'clo_gloves': None,
            'clo_lfinger': None,
            'clo_rfinger': None,
            'clo_waist': None,
            'clo_lear': None,
            'clo_rear': None,
            'clo_lwrist': None,
            'clo_rwrist': None,
            'clo_chest': None,
            'clo_back': None,
            'clo_lleg': None,
            'clo_rleg': None,
            'clo_feet': None,
            'imp_head': None,
            'imp_neck': None,
            'imp_larm': None,
            'imp_rarm': None,
            'imp_lhand': None,
            'imp_rhand': None,
            'imp_gloves': None,
            'imp_lfinger': None,
            'imp_rfinger': None,
            'imp_waist': None,
            'imp_lear': None,
            'imp_rear': None,
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
        for fileLine in motdLines:
            lineStr = fileLine[:-1]
            if lineStr.strip().startswith('images/'):
                motdImageFile = lineStr.strip()
                if os.path.isfile(motdImageFile):
                    with open(motdImageFile, 'r') as imgFile:
                        mud.sendImage(id, '\n' + imgFile.read(), True)
            else:
                mud.sendMessage(id, lineStr)

        if not os.path.isfile(".disableRegistrations"):
            mud.sendMessageWrap(
                id, '<f220>',
                'You can create a new Character, or use the guest account, ' +
                'username: <f32>Guest<r>, password: <f32>Password<r>')
            mud.sendMessage(
                id, "What is your username? " +
                "(type <f32>new<r> for new character)\n")
        else:
            mud.sendMessage(
                id,
                '<f0><b220> New account registrations are currently closed')

            mud.sendMessage(id, "\nWhat is your username?\n\n")
        idStr = str(id)
        log("Player ID " + idStr + " has connected", "info")


def _runPlayerDisconnections(mud, id, players, playersDB, fights,
                             Config, terminalMode: {}):
    # go through any recently disconnected players
    for id in mud.get_disconnected_players():

        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in players:
            continue

        idStr = str(id)
        terminalMode[idStr] = False
        nameStr = str(players[id]['name'])
        log("Player ID " + idStr + " has disconnected [" +
            nameStr + "]", "info")

        # go through all the players in the game
        for (pid, pl) in list(players.items()):
            # send each player a message to tell them about the diconnected
            # player if they are in the same room
            if players[pid]['authenticated'] is not None:
                if players[pid]['authenticated'] is not None \
                   and players[pid]['room'] == players[id]['room'] \
                   and players[pid]['name'] != players[id]['name']:
                    mud.sendMessage(
                        pid, "<f32><u>{}<r>".format(players[id]['name']) +
                        "'s body has vanished.\n\n")

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
            if fightsCopy[fight]['s1'] == players[id]['name'] or \
               fightsCopy[fight]['s2'] == players[id]['name']:
                del fights[fight]

        # remove the player's entry in the player dictionary
        del players[id]


def runPlayerConnections(mud, id, players, playersDB, fights,
                         Config, terminalMode: {}):
    _runNewPlayerConnections(mud, id, players, playersDB, fights, Config)
    _runPlayerDisconnections(mud, id, players, playersDB, fights,
                             Config, terminalMode)


def disconnectIdlePlayers(mud, players: {}, allowedPlayerIdle: int,
                          playersDB: {}) -> bool:
    # Evaluate player idle time and disconnect if required
    authenticatedPlayersDisconnected = False
    now = int(time.time())
    playersCopy = deepcopy(players)
    for p in playersCopy:
        if now - playersCopy[p]['idleStart'] > allowedPlayerIdle:
            if players[p]['authenticated'] is not None:
                mud.sendMessageWrap(
                    p, "<f232><b11>",
                    "<f232><b11>Your body starts tingling. " +
                    "You instinctively hold your hand up to " +
                    "your face and notice you slowly begin to " +
                    "vanish. You are being disconnected due " +
                    "to inactivity...****DISCONNECT****\n")
                saveState(players[p], playersDB, False)
                authenticatedPlayersDisconnected = True
            else:
                mud.sendMessage(
                    p, "<f232><b11>You are being disconnected " +
                    "due to inactivity. Bye!****DISCONNECT****\n")
            nameStr = str(players[p]['name'])
            log("Character " + nameStr +
                " is being disconnected due to inactivity.", "warning")
            pStr = str(p)
            log("Disconnecting client " + pStr, "warning")
            del players[p]
            mud.handleDisconnect(p)
    return authenticatedPlayersDisconnected


def playerInGame(id, username: str, players: {}) -> bool:
    """ is the given player already logged in?
    """
    for pl in players:
        if username is not None and \
           players[pl]['name'] is not None and \
           username == players[pl]['name'] and \
           pl != id:
            return True
    return False


def initialSetupAfterLogin(mud, id, players: {}, loadedJson: {}) -> None:
    """Sets up a player after login
    """
    players[id] = loadedJson.copy()
    players[id]['authenticated'] = True
    players[id]['prefix'] = "None"
    players[id]['isInCombat'] = 0
    players[id]['lastCombatAction'] = int(time.time())
    players[id]['isAttackable'] = 1
    players[id]['corpseTTL'] = 60
    players[id]['idleStart'] = int(time.time())

    idStr = str(id)
    log("Player ID " + idStr +
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
            mud.sendMessage(
                pid, '{} '.format(players[id]['name']) +
                'has materialised out of thin air nearby.\n\n')

    # send the new player a welcome message
    mud.sendMessageWrap(id, '<f255>',
                        '****CLEAR****<f220>Welcome to AberMUSH!, ' +
                        '{}. '.format(players[id]['name']))
    mud.sendMessageWrap(id, '<f255>',
                        '<f255>Hello there traveller! ' +
                        'You have connected to the ' +
                        'server. You can move around the ' +
                        'rooms along with other players, ' +
                        'attack each other (including NPCs), ' +
                        'pick up and drop items and chat. ' +
                        'Make sure to visit the repo for ' +
                        'further info. Thanks for your ' +
                        'interest in AberMUSH.')
    mud.sendMessageWrap(id, '<f255>',
                        "<f255>Type '<r><f220>help<r><f255>' " +
                        "for a list of all currently implemented " +
                        "commands.")
    mud.sendMessageWrap(id, '<f255>',
                        "<f255>Type '<r><f220>look<r><f255>' " +
                        "to see what's around you.\n\n")
