__filename__ = "playerconnections.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Core"

import os
import time
from functions import log
from functions import save_state
from functions import load_players_db
from functions import deepcopy

MAXIMUM_PLAYERS = 128


def _run_new_player_connections(mud, players, players_db, fights, Config):
    # go through any newly connected players
    for id in mud.get_new_players():
        if len(players) >= MAXIMUM_PLAYERS:
            mud.send_message(id, "Player limit reached\n\n")
            mud.handle_disconnect(id)

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
            'magicShield': 0,
            'magicShieldDuration': 0,
            'magicShieldStart': 0,
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
        with open(str(Config.get('System', 'Motd')), "r") as motd_file:
            motd_lines = motd_file.readlines()

        for file_line in motd_lines:
            line_str = file_line[:-1]
            if line_str.strip().startswith('images/'):
                motd_image_file = line_str.strip()
                if os.path.isfile(motd_image_file):
                    with open(motd_image_file, 'r') as fp_img:
                        mud.send_image(id, '\n' + fp_img.read(), True)
            else:
                mud.send_message(id, line_str)

        if not os.path.isfile(".disableRegistrations"):
            mud.send_message_wrap(
                id, '<f220>',
                'You can create a new Character, or use the guest account, ' +
                'username: <f32>Guest<r>, password: <f32>Password<r>')
            mud.send_message(
                id, "What is your username? " +
                "(type <f32>new<r> for new character)\n")
        else:
            mud.send_message(
                id,
                '<f0><b220> New account registrations are currently closed')

            mud.send_message(id, "\nWhat is your username?\n\n")
        id_str = str(id)
        log("Player ID " + id_str + " has connected", "info")


def _run_player_disconnections(mud, players, players_db, fights,
                               Config, terminalMode: {}):
    # go through any recently disconnected players
    for id in mud.get_disconnected_players():

        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in players:
            continue

        id_str = str(id)
        terminalMode[id_str] = False
        name_str = str(players[id]['name'])
        log("Player ID " + id_str + " has disconnected [" +
            name_str + "]", "info")

        # go through all the players in the game
        for pid, _ in list(players.items()):
            # send each player a message to tell them about the diconnected
            # player if they are in the same room
            if players[pid]['authenticated'] is not None:
                if players[pid]['authenticated'] is not None \
                   and players[pid]['room'] == players[id]['room'] \
                   and players[pid]['name'] != players[id]['name']:
                    mud.send_message(
                        pid, "<f32><u>{}<r>".format(players[id]['name']) +
                        "'s body has vanished.\n\n")

        # Code here to save player to the database after he's disconnected and
        # before removing him from players dictionary
        if players[id]['authenticated'] is not None:
            log("Player disconnected, saving state", "info")
            save_state(players[id], players_db, False)
            players_db = load_players_db()

        # Create a deep copy of fights, iterate through it and remove fights
        # disconnected player was taking part in
        fights_copy = deepcopy(fights)
        for fight, _ in fights_copy.items():
            if fights_copy[fight]['s1'] == players[id]['name'] or \
               fights_copy[fight]['s2'] == players[id]['name']:
                del fights[fight]

        # remove the player's entry in the player dictionary
        del players[id]


def run_player_connections(mud, id, players, players_db, fights,
                           Config, terminalMode: {}):
    _run_new_player_connections(mud, players, players_db, fights, Config)
    _run_player_disconnections(mud, players, players_db, fights,
                               Config, terminalMode)


def disconnect_idle_players(mud, players: {}, allowed_player_idle: int,
                            players_db: {}) -> bool:
    # Evaluate player idle time and disconnect if required
    authenticated_players_disconnected = False
    now = int(time.time())
    players_copy = deepcopy(players)
    for plyr in players_copy:
        if now - players_copy[plyr]['idleStart'] > allowed_player_idle:
            if players[plyr]['authenticated'] is not None:
                mud.send_message_wrap(
                    plyr, "<f232><b11>",
                    "<f232><b11>Your body starts tingling. " +
                    "You instinctively hold your hand up to " +
                    "your face and notice you slowly begin to " +
                    "vanish. You are being disconnected due " +
                    "to inactivity...****DISCONNECT****\n")
                save_state(players[plyr], players_db, False)
                authenticated_players_disconnected = True
            else:
                mud.send_message(
                    plyr, "<f232><b11>You are being disconnected " +
                    "due to inactivity. Bye!****DISCONNECT****\n")
            name_str = str(players[plyr]['name'])
            log("Character " + name_str +
                " is being disconnected due to inactivity.", "warning")
            p_str = str(plyr)
            log("Disconnecting client " + p_str, "warning")
            del players[plyr]
            mud.handle_disconnect(plyr)
    return authenticated_players_disconnected


def player_in_game(id, username: str, players: {}) -> bool:
    """ is the given player already logged in?
    """
    for plyr in players:
        if username is not None and \
           players[plyr]['name'] is not None and \
           username == players[plyr]['name'] and \
           plyr != id:
            return True
    return False


def initial_setup_after_login(mud, id, players: {}, loadedJson: {}) -> None:
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

    id_str = str(id)
    log("Player ID " + id_str +
        " has successfully authenticated user " +
        players[id]['name'], "info")

    # print(players[id])
    # go through all the players in the game
    for pid, _ in list(players.items()):
        # send each player a message to tell them about the new
        # player
        if players[pid]['authenticated'] is not None \
           and players[pid]['room'] == players[id]['room'] \
           and players[pid]['name'] != players[id]['name']:
            mud.send_message(
                pid, '{} '.format(players[id]['name']) +
                'has materialised out of thin air nearby.\n\n')

    # send the new player a welcome message
    mud.send_message_wrap(id, '<f255>',
                          '****CLEAR****<f220>Welcome to AberMUSH!, ' +
                          '{}. '.format(players[id]['name']))
    mud.send_message_wrap(id, '<f255>',
                          '<f255>Hello there traveller! ' +
                          'You have connected to the ' +
                          'server. You can move around the ' +
                          'rooms along with other players, ' +
                          'attack each other (including NPCs), ' +
                          'pick up and drop items and chat. ' +
                          'Make sure to visit the repo for ' +
                          'further info. Thanks for your ' +
                          'interest in AberMUSH.')
    mud.send_message_wrap(id, '<f255>',
                          "<f255>Type '<r><f220>help<r><f255>' " +
                          "for a list of all currently implemented " +
                          "commands.")
    mud.send_message_wrap(id, '<f255>',
                          "<f255>Type '<r><f220>look<r><f255>' " +
                          "to see what's around you.\n\n")
