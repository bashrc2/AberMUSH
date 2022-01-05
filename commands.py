__filename__ = "commands.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Command Interface"

from functions import parse_cost
from functions import player_is_prone
from functions import set_player_prone
from functions import wear_location
from functions import is_wearing
from functions import player_is_visible
from functions import message_to_room_players
from functions import time_string_to_sec
from functions import add_to_scheduler
from functions import get_free_key
from functions import get_free_room_key
from functions import hash_password
from functions import log
from functions import save_state
from functions import player_inventory_weight
from functions import save_blocklist
from functions import save_universe
from functions import update_player_attributes
from functions import size_from_description
from functions import stow_hands
from functions import random_desc
from functions import increase_affinity_between_players
from functions import decrease_affinity_between_players
from functions import get_sentiment
from functions import get_guild_sentiment
from environment import moon_phase
from environment import moon_illumination
from environment import holding_fly_fishing_rod
from environment import holding_fishing_rod
from environment import is_fishing_site
from environment import get_room_culture
from environment import run_tide
from environment import get_rain_at_coords
from history import assign_item_history
from traps import player_is_trapped
from traps import describe_trapped_player
from traps import trap_activation
from traps import teleport_from_trap
from traps import escape_from_trap
from combat import remove_prepared_spell
from combat import health_of_player
from combat import is_attacking
from combat import stop_attack
from combat import get_attacking_target
from combat import player_begins_attack
from combat import is_player_fighting
from chess import show_chess_board
from chess import initial_chess_board
from chess import move_chess_piece
from cards import deal_to_players
from cards import hand_of_cards_show
from cards import swap_card
from cards import shuffle_cards
from cards import call_cards
from morris import show_morris_board
from morris import morris_move
from morris import reset_morris_board
from morris import take_morris_counter
from morris import get_morris_board_name

from proficiencies import thieves_cant

from npcs import npc_conversation
from npcs import get_solar

from markets import buy_item
from markets import market_buys_item_types
from markets import get_market_type
from markets import money_purchase

from familiar import get_familiar_name

import os
import re
import sys
# from copy import deepcopy
from functions import deepcopy
import time
import datetime
import os.path
import random
from random import randint


def _get_max_weight(id, players: {}) -> int:
    """Returns the maximum weight which can be carried
    """
    strength = int(players[id]['str'])
    return strength * 15


def _pose_prone(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '\n\n')
        return

    if player_is_trapped(id, players, rooms):
        describe_trapped_player(mud, id, players, rooms)
        return

    if 'isFishing' in players[id]:
        del players[id]['isFishing']

    if not player_is_prone(id, players):
        msgStr = 'You lie down<r>\n\n'
        mud.send_message(id, random_desc(msgStr))
        set_player_prone(id, players, True)
    else:
        msgStr = 'You are already lying down<r>\n\n'
        mud.send_message(id, random_desc(msgStr))


def _stand(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {},
           env_db: {}, env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '\n\n')
        return

    if player_is_trapped(id, players, rooms):
        describe_trapped_player(mud, id, players, rooms)
        return

    if player_is_prone(id, players):
        msgStr = 'You stand up<r>\n\n'
        mud.send_message(id, random_desc(msgStr))
        set_player_prone(id, players, True)
    else:
        msgStr = 'You are already standing up<r>\n\n'
        mud.send_message(id, random_desc(msgStr))


def _shove(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {},
           env_db: {}, env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '\n\n')
        return

    if player_is_trapped(id, players, rooms):
        describe_trapped_player(mud, id, players, rooms)
        return

    if player_is_prone(id, players):
        mud.send_message(id, random_desc('You stand up<r>\n\n'))
        set_player_prone(id, players, False)
        return

    if not is_player_fighting(id, players, fights):
        mud.send_message(
            id,
            random_desc('You try to shove, but to your surprise ' +
                        'discover that you are not in combat ' +
                        'with anyone.') +
            '\n\n')
        return

    if players[id]['canGo'] != 1:
        mud.send_message(
            id, random_desc(
                "You try to shove, but don't seem to be able to move") +
            '\n\n')
        return

    mud.send_message(
        id, random_desc(
            "You get ready to shove...") +
        '\n')
    players[id]['shove'] = 1


def _dodge(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {},
           env_db: {}, env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '\n\n')
        return

    if player_is_trapped(id, players, rooms):
        describe_trapped_player(mud, id, players, rooms)
        return

    if player_is_prone(id, players):
        mud.send_message(id, random_desc('You stand up<r>\n\n'))
        set_player_prone(id, players, False)
        return

    if not is_player_fighting(id, players, fights):
        mud.send_message(
            id, random_desc(
                "You try dodging, but then realize that you're not actually " +
                "fighting|You practice dodging an imaginary attacker") +
            '\n\n')
        return

    if players[id]['canGo'] != 1:
        mud.send_message(
            id, random_desc(
                "You try to dodge, but don't seem to be able to move") +
            '\n\n')
        return

    mud.send_message(
        id, random_desc(
            "Ok|Ok, here goes...") +
        '\n\n')
    players[id]['dodge'] = 1


def _remove_item_from_clothing(players: {}, pid: int, itemID: int) -> None:
    """If worn an item is removed
    """
    for cstr in wear_location:
        if int(players[pid]['clo_' + cstr]) == itemID:
            players[pid]['clo_' + cstr] = 0


def _send_command_error(params, mud, playersDB: {}, players: {}, rooms: {},
                        npcs_db: {}, npcs: {}, items_db: {}, items: {},
                        env_db: {}, env, eventDB: {}, event_schedule, id: int,
                        fights: {}, corpses, blocklist, map_area: [],
                        character_class_db: {}, spells_db: {},
                        sentiment_db: {}, guilds_db: {}, clouds: {},
                        races_db: {}, item_history: {}, markets: {},
                        cultures_db: {}) -> None:
    mud.send_message(id, "Unknown command " + str(params) + "!\n")


def _is_witch(id: int, players: {}) -> bool:
    """Have we found a witch?
    """
    name = players[id]['name']

    if not os.path.isfile("witches"):
        return False

    witchesfile = open("witches", "r")

    for line in witchesfile:
        witchName = line.strip()
        if witchName == name:
            return True

    witchesfile.close()
    return False


def _disable_registrations(mud, id: int, players: {}) -> None:
    """Turns off new registrations
    """
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return
    if os.path.isfile(".disableRegistrations"):
        mud.send_message(id, "New registrations are already closed.\n\n")
        return
    with open(".disableRegistrations", 'w') as fp:
        fp.write('')
    mud.send_message(id, "New player registrations are now closed.\n\n")


def _enable_registrations(mud, id: int, players: {}) -> None:
    """Turns on new registrations
    """
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return
    if not os.path.isfile(".disableRegistrations"):
        mud.send_message(id, "New registrations are already allowed.\n\n")
        return
    os.remove(".disableRegistrations")
    mud.send_message(id, "New player registrations are now permitted.\n\n")


def _teleport(params, mud, playersDB: {}, players: {}, rooms: {}, npcs_db: {},
              npcs: {}, items_db: {}, items: {}, env_db: {}, env, eventDB: {},
              event_schedule, id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}) -> None:

    if players[id]['permissionLevel'] != 0:
        mud.send_message(id, "You don't have enough powers for that.\n\n")
        return

    if _is_witch(id, players):
        if player_is_trapped(id, players, rooms):
            teleport_from_trap(mud, id, players, rooms)

        targetLocation = params[0:].strip().lower().replace('to ', '', 1)
        if len(targetLocation) != 0:
            currRoom = players[id]['room']
            if rooms[currRoom]['name'].strip().lower() == targetLocation:
                mud.send_message(
                    id, "You are already in " +
                    rooms[currRoom]['name'] +
                    "\n\n")
                return
            for rm in rooms:
                if rooms[rm]['name'].strip().lower() == targetLocation:
                    if is_attacking(players, id, fights):
                        stop_attack(players, id, npcs, fights)
                    mud.send_message(
                        id, "You teleport to " + rooms[rm]['name'] + "\n\n")
                    pName = players[id]['name']
                    desc = '<f32>{}<r> suddenly vanishes.'.format(pName)
                    message_to_room_players(mud, players, id, desc + "\n\n")
                    players[id]['room'] = rm
                    desc = '<f32>{}<r> suddenly appears.'.format(pName)

                    message_to_room_players(mud, players, id, desc + "\n\n")
                    _look('', mud, playersDB, players, rooms, npcs_db, npcs,
                          items_db, items, env_db, env, eventDB,
                          event_schedule,
                          id, fights, corpses, blocklist, map_area,
                          character_class_db, spells_db, sentiment_db,
                          guilds_db, clouds, races_db, item_history, markets,
                          cultures_db)
                    return

            # try adding or removing "the"
            if targetLocation.startswith('the '):
                targetLocation = targetLocation.replace('the ', '')
            else:
                targetLocation = 'the ' + targetLocation

            pName = players[id]['name']
            desc1 = '<f32>{}<r> suddenly vanishes.'.format(pName)
            desc2 = '<f32>{}<r> suddenly appears.'.format(pName)
            for rm in rooms:
                if rooms[rm]['name'].strip().lower() == targetLocation:
                    mud.send_message(
                        id, "You teleport to " + rooms[rm]['name'] + "\n\n")
                    message_to_room_players(mud, players, id,
                                            desc1 + "\n\n")
                    players[id]['room'] = rm
                    message_to_room_players(mud, players, id,
                                            desc2 + "\n\n")
                    _look('', mud, playersDB, players, rooms, npcs_db, npcs,
                          items_db, items, env_db, env, eventDB,
                          event_schedule,
                          id, fights, corpses, blocklist, map_area,
                          character_class_db, spells_db, sentiment_db,
                          guilds_db, clouds, races_db, item_history, markets,
                          cultures_db)
                    return

            mud.send_message(
                id, targetLocation +
                " isn't a place you can teleport to.\n\n")
        else:
            mud.send_message(id, "That's not a place.\n\n")
    else:
        mud.send_message(id, "You don't have enough powers to teleport.\n\n")


def _summon(params, mud, playersDB: {}, players: {}, rooms: {}, npcs_db: {},
            npcs: {}, items_db: {}, items: {}, env_db: {}, env, eventDB: {},
            event_schedule, id: int, fights: {}, corpses: {}, blocklist,
            map_area: [], character_class_db: {}, spells_db: {},
            sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}) -> None:
    if players[id]['permissionLevel'] == 0:
        if _is_witch(id, players):
            targetPlayer = params[0:].strip().lower()
            if len(targetPlayer) != 0:
                for p in players:
                    if players[p]['name'].strip().lower() == targetPlayer:
                        if players[p]['room'] != players[id]['room']:
                            pNam = players[p]['name']
                            desc = '<f32>{}<r> suddenly vanishes.'.format(pNam)
                            message_to_room_players(mud, players, p,
                                                    desc + "\n")
                            players[p]['room'] = players[id]['room']
                            rm = players[p]['room']
                            mud.send_message(id, "You summon " +
                                             players[p]['name'] + "\n\n")
                            mud.send_message(p,
                                             "A mist surrounds you. When it " +
                                             "clears you find that you " +
                                             "are now in " +
                                             rooms[rm]['name'] + "\n\n")
                        else:
                            mud.send_message(
                                id, players[p]['name'] +
                                " is already here.\n\n")
                        return
        else:
            mud.send_message(id, "You don't have enough powers for that.\n\n")


def _mute(params, mud, playersDB: {}, players: {}, rooms: {}, npcs_db: {},
          npcs: {}, items_db: {}, items: {}, env_db: {}, env, eventDB: {},
          event_schedule, id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}) -> None:
    if players[id]['permissionLevel'] != 0:
        mud.send_message(
            id, "You aren't capable of doing that.\n\n")
        return
    if not _is_witch(id, players):
        mud.send_message(
            id, "You aren't capable of doing that.\n\n")
        return
    target = params.partition(' ')[0]
    if len(target) != 0:
        for p in players:
            if players[p]['name'] == target:
                if not _is_witch(p, players):
                    players[p]['canSay'] = 0
                    players[p]['canAttack'] = 0
                    players[p]['canDirectMessage'] = 0
                    mud.send_message(
                        id, "You have muted " + target + "\n\n")
                else:
                    mud.send_message(
                        id, "You try to mute " + target +
                        " but their power is too strong.\n\n")
                return


def _unmute(params, mud, playersDB: {}, players: {}, rooms: {}, npcs_db: {},
            npcs: {}, items_db: {}, items: {}, env_db: {}, env, eventDB: {},
            event_schedule, id: int, fights: {}, corpses: {}, blocklist,
            map_area: [], character_class_db: {}, spells_db: {},
            sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}) -> None:
    if players[id]['permissionLevel'] != 0:
        mud.send_message(
            id, "You aren't capable of doing that.\n\n")
        return
    if not _is_witch(id, players):
        mud.send_message(
            id, "You aren't capable of doing that.\n\n")
        return
    target = params.partition(' ')[0]
    if len(target) != 0:
        if target.lower() != 'guest':
            for p in players:
                if players[p]['name'] == target:
                    if not _is_witch(p, players):
                        players[p]['canSay'] = 1
                        players[p]['canAttack'] = 1
                        players[p]['canDirectMessage'] = 1
                        mud.send_message(
                            id, "You have unmuted " + target + "\n\n")
                    return


def _freeze(params, mud, playersDB: {}, players: {}, rooms: {}, npcs_db: {},
            npcs: {}, items_db: {}, items: {}, env_db: {}, env, eventDB: {},
            event_schedule, id: int, fights: {}, corpses: {}, blocklist,
            map_area: [], character_class_db: {}, spells_db: {},
            sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['permissionLevel'] == 0:
        if _is_witch(id, players):
            target = params.partition(' ')[0]
            if len(target) != 0:
                # freeze players
                for p in players:
                    if players[p]['whenDied']:
                        mud.send_message(
                            id,
                            "Freezing a player while dead is pointless\n\n")
                        continue
                    if players[p]['frozenStart'] > 0:
                        mud.send_message(
                            id, "They are already frozen\n\n")
                        continue
                    if target in players[p]['name']:
                        if not _is_witch(p, players):
                            # remove from any fights
                            for (fight, pl) in fights.items():
                                if fights[fight]['s1id'] == p or \
                                   fights[fight]['s2id'] == p:
                                    del fights[fight]
                                    players[p]['isInCombat'] = 0
                            players[p]['canGo'] = 0
                            players[p]['canAttack'] = 0
                            mud.send_message(
                                id, "You have frozen " + target + "\n\n")
                        else:
                            mud.send_message(
                                id, "You try to freeze " + target +
                                " but their power is too strong.\n\n")
                        return
                # freeze npcs
                for p in npcs:
                    if npcs[p]['whenDied']:
                        mud.send_message(
                            id, "Freezing while dead is pointless\n\n")
                        continue
                    if npcs[p]['frozenStart'] > 0:
                        mud.send_message(
                            id, "They are already frozen\n\n")
                        continue
                    if target in npcs[p]['name']:
                        if not _is_witch(p, npcs):
                            # remove from any fights
                            for (fight, pl) in fights.items():
                                if fights[fight]['s1id'] == p or \
                                   fights[fight]['s2id'] == p:
                                    del fights[fight]
                                    npcs[p]['isInCombat'] = 0

                            npcs[p]['canGo'] = 0
                            npcs[p]['canAttack'] = 0
                            mud.send_message(
                                id, "You have frozen " + target + "\n\n")
                        else:
                            mud.send_message(
                                id, "You try to freeze " + target +
                                " but their power is too strong.\n\n")
                        return


def _unfreeze(params, mud, playersDB: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {},
              env_db: {}, env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['permissionLevel'] == 0:
        if _is_witch(id, players):
            target = params.partition(' ')[0]
            if len(target) != 0:
                if target.lower() != 'guest':
                    # unfreeze players
                    for p in players:
                        if target in players[p]['name']:
                            if not _is_witch(p, players):
                                players[p]['canGo'] = 1
                                players[p]['canAttack'] = 1
                                players[p]['frozenStart'] = 0
                                mud.send_message(
                                    id, "You have unfrozen " + target + "\n\n")
                            return
                    # unfreeze npcs
                    for p in npcs:
                        if target in npcs[p]['name']:
                            if not _is_witch(p, npcs):
                                npcs[p]['canGo'] = 1
                                npcs[p]['canAttack'] = 1
                                npcs[p]['frozenStart'] = 0
                                mud.send_message(
                                    id, "You have unfrozen " + target + "\n\n")
                            return


def _show_blocklist(params, mud, playersDB: {}, players: {}, rooms: {},
                    npcs_db: {}, npcs: {}, items_db: {}, items: {},
                    env_db: {}, env: {}, eventDB: {}, event_schedule,
                    id: int, fights: {}, corpses: {}, blocklist,
                    map_area: [], character_class_db: {}, spells_db: {},
                    sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                    item_history: {}, markets: {}, cultures_db: {}):
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have sufficient powers to do that.\n")
        return

    blocklist.sort()

    blockStr = ''
    for blockedstr in blocklist:
        blockStr = blockStr + blockedstr + '\n'

    mud.send_message(id, "Blocked strings are:\n\n" + blockStr + '\n')


def _block(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
           env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have sufficient powers to do that.\n")
        return

    if len(params) == 0:
        _show_blocklist(params, mud, playersDB, players, rooms, npcs_db, npcs,
                        items_db, items, env_db, env, eventDB, event_schedule,
                        id, fights, corpses, blocklist, map_area,
                        character_class_db, spells_db, sentiment_db, guilds_db,
                        clouds, races_db, item_history, markets, cultures_db)
        return

    blockedstr = params.lower().strip().replace('"', '')

    if blockedstr.startswith('the word '):
        blockedstr = blockedstr.replace('the word ', '')
    if blockedstr.startswith('word '):
        blockedstr = blockedstr.replace('word ', '')
    if blockedstr.startswith('the phrase '):
        blockedstr = blockedstr.replace('the phrase ', '')
    if blockedstr.startswith('phrase '):
        blockedstr = blockedstr.replace('phrase ', '')

    if blockedstr not in blocklist:
        blocklist.append(blockedstr)
        save_blocklist("blocked.txt", blocklist)
        mud.send_message(id, "Blocklist updated.\n\n")
    else:
        mud.send_message(id, "That's already in the blocklist.\n")


def _unblock(params, mud, playersDB: {}, players: {}, rooms: {}, npcs_db: {},
             npcs: {}, items_db: {}, items: {}, env_db: {}, env: {},
             eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have sufficient powers to do that.\n")
        return

    if len(params) == 0:
        _show_blocklist(params, mud, playersDB, players, rooms, npcs_db,
                        npcs, items_db, items, env_db, env, eventDB,
                        event_schedule,
                        id, fights, corpses, blocklist, map_area,
                        character_class_db, spells_db, sentiment_db, guilds_db,
                        clouds, races_db, item_history, markets, cultures_db)
        return

    unblockedstr = params.lower().strip().replace('"', '')

    if unblockedstr.startswith('the word '):
        unblockedstr = unblockedstr.replace('the word ', '')
    if unblockedstr.startswith('word '):
        unblockedstr = unblockedstr.replace('word ', '')
    if unblockedstr.startswith('the phrase '):
        unblockedstr = unblockedstr.replace('the phrase ', '')
    if unblockedstr.startswith('phrase '):
        unblockedstr = unblockedstr.replace('phrase ', '')

    if unblockedstr in blocklist:
        blocklist.remove(unblockedstr)
        save_blocklist("blocked.txt", blocklist)
        mud.send_message(id, "Blocklist updated.\n\n")
    else:
        mud.send_message(id, "That's not in the blocklist.\n")


def _kick(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return

    playerName = params

    if len(playerName) == 0:
        mud.send_message(id, "Who?\n\n")
        return

    for (pid, pl) in list(players.items()):
        if players[pid]['name'] == playerName:
            mud.send_message(id, "Removing player " + playerName + "\n\n")
            mud.handle_disconnect(pid)
            return

    mud.send_message(id, "There are no players with that name.\n\n")


def _shutdown(params, mud, playersDB: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {},
              env_db: {}, env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have enough power to do that.\n\n")
        return

    mud.send_message(id, "\n\nShutdown commenced.\n\n")
    save_universe(rooms, npcs_db, npcs, items_db, items,
                  env_db, env, guilds_db)
    mud.send_message(id, "\n\nUniverse saved.\n\n")
    log("Universe saved", "info")
    for (pid, pl) in list(players.items()):
        mud.send_message(pid, "Game server shutting down...\n\n")
        mud.handle_disconnect(pid)
    log("Shutting down", "info")
    sys.exit()


def _resetUniverse(params, mud, playersDB: {}, players: {}, rooms: {},
                   npcs_db: {}, npcs: {}, items_db: {}, items: {},
                   env_db: {}, env: {}, eventDB: {}, event_schedule,
                   id: int, fights: {}, corpses: {}, blocklist,
                   map_area: [], character_class_db: {}, spells_db,
                   sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                   item_history: {}, markets: {}, cultures_db: {}):
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have enough power to do that.\n\n")
        return
    os.system('rm universe*.json')
    log('Universe reset', 'info')
    for (pid, pl) in list(players.items()):
        mud.send_message(pid, "Game server shutting down...\n\n")
        mud.handle_disconnect(pid)
    log("Shutting down", "info")
    sys.exit()


def _quit(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    mud.handle_disconnect(id)


def _who(params, mud, playersDB: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {},
         env_db: {}, env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db,
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    counter = 1
    if players[id]['permissionLevel'] == 0:
        is_witch = _is_witch(id, players)
        for p in players:
            if players[p]['name'] is None:
                continue

            if not is_witch:
                name = players[p]['name']
            else:
                if not _is_witch(p, players):
                    if players[p]['canSay'] == 1:
                        name = players[p]['name']
                    else:
                        name = players[p]['name'] + " (muted)"
                else:
                    name = "<f32>" + players[p]['name'] + "<r>"

            if players[p]['room'] is None:
                room = "None"
            else:
                rm = rooms[players[p]['room']]
                room = "<f230>" + rm['name']

            mud.send_message(id, str(counter) + ". " + name + " is in " + room)
            counter += 1
        mud.send_message(id, "\n")
    else:
        mud.send_message(id, "You do not have permission to do this.\n")


def _tell(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    told = False
    target = params.partition(' ')[0]

    # replace "familiar" with their NPC name
    # as in: "ask familiar to follow"
    if target.lower() == 'familiar':
        newTarget = get_familiar_name(players, id, npcs)
        if len(newTarget) > 0:
            target = newTarget

    message = params.replace(target, "")[1:]
    if len(target) != 0 and len(message) != 0:
        cantStr = thieves_cant(message)
        for p in players:
            if players[p]['authenticated'] is not None and \
               players[p]['name'].lower() == target.lower():
                # print("sending a tell")
                if players[id]['name'].lower() == target.lower():
                    mud.send_message(
                        id, "It'd be pointless to send a tell " +
                        "message to yourself\n")
                    told = True
                    break
                else:
                    # don't tell if the string contains a blocked string
                    selfOnly = False
                    msglower = message.lower()
                    for blockedstr in blocklist:
                        if blockedstr in msglower:
                            selfOnly = True
                            break

                    if not selfOnly:
                        langList = players[p]['language']
                        if players[id]['speakLanguage'] in langList:
                            add_to_scheduler(
                                "0|msg|<f90>From " +
                                players[id]['name'] +
                                ": " + message +
                                '\n', p, event_schedule,
                                eventDB)
                            sentimentScore = \
                                get_sentiment(message, sentiment_db) + \
                                get_guild_sentiment(players, id, players,
                                                    p, guilds_db)
                            if sentimentScore >= 0:
                                increase_affinity_between_players(
                                    players, id, players, p, guilds_db)
                            else:
                                decrease_affinity_between_players(
                                    players, id, players, p, guilds_db)
                        else:
                            if players[id]['speakLanguage'] != 'cant':
                                add_to_scheduler(
                                    "0|msg|<f90>From " +
                                    players[id]['name'] +
                                    ": something in " +
                                    players[id]['speakLanguage'] +
                                    '\n', p, event_schedule,
                                    eventDB)
                            else:
                                add_to_scheduler(
                                    "0|msg|<f90>From " +
                                    players[id]['name'] +
                                    ": " + cantStr +
                                    '\n', p, event_schedule,
                                    eventDB)
                    mud.send_message(
                        id, "<f90>To " +
                        players[p]['name'] +
                        ": " + message +
                        "\n\n")
                    told = True
                    break
        if not told:
            for (nid, pl) in list(npcs.items()):
                if (npcs[nid]['room'] == players[id]['room']) or \
                   npcs[nid]['familiarOf'] == players[id]['name']:
                    if target.lower() in npcs[nid]['name'].lower():
                        messageLower = message.lower()
                        npc_conversation(mud, npcs, npcs_db, players,
                                         items, items_db, rooms, id,
                                         nid, messageLower,
                                         character_class_db,
                                         sentiment_db, guilds_db,
                                         clouds, races_db, item_history,
                                         cultures_db)
                        told = True
                        break

        if not told:
            mud.send_message(
                id, "<f32>" + target +
                "<r> does not appear to be reachable at this moment.\n\n")
    else:
        mud.send_message(id, "Huh?\n\n")


def _whisper(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {},
             env_db: {}, env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    target = params.partition(' ')[0]
    message = params.replace(target, "")

    # if message[0] == " ":
    # message.replace(message[0], "")
    messageSent = False
    # print(message)
    # print(str(len(message)))
    if len(target) > 0:
        if len(message) > 0:
            cantStr = thieves_cant(message)
            for p in players:
                if players[p]['name'] is not None and \
                   players[p]['name'].lower() == target.lower():
                    if players[p]['room'] == players[id]['room']:
                        if players[p]['name'].lower() != \
                           players[id]['name'].lower():

                            # don't whisper if the string contains a blocked
                            # string
                            selfOnly = False
                            msglower = message[1:].lower()
                            for blockedstr in blocklist:
                                if blockedstr in msglower:
                                    selfOnly = True
                                    break

                            sentimentScore = \
                                get_sentiment(message[1:], sentiment_db) + \
                                get_guild_sentiment(players, id, players,
                                                    p, guilds_db)
                            if sentimentScore >= 0:
                                increase_affinity_between_players(
                                    players, id, players, p, guilds_db)
                            else:
                                decrease_affinity_between_players(
                                    players, id, players, p, guilds_db)

                            mud.send_message(
                                id, "You whisper to <f32>" +
                                players[p]['name'] + "<r>: " +
                                message[1:] + '\n')
                            if not selfOnly:
                                langList = players[p]['language']
                                if players[id]['speakLanguage'] in langList:
                                    mud.send_message(
                                        p, "<f162>" + players[id]['name'] +
                                        " whispers: " + message[1:] + '\n')
                                else:
                                    if players[id]['speakLanguage'] != 'cant':
                                        mud.send_message(
                                            p, "<f162>" +
                                            players[id]['name'] +
                                            " whispers something in " +
                                            players[id]['speakLanguage'] +
                                            '\n')
                                    else:
                                        mud.send_message(
                                            p, "<f162>" + players[id]['name'] +
                                            " whispers:  " + cantStr + '\n')
                            messageSent = True
                            break
                        else:
                            mud.send_message(
                                id, "You would probably look rather silly " +
                                "whispering to yourself.\n")
                            messageSent = True
                            break
            if not messageSent:
                mud.send_message(
                    id, "<f32>" + target + "<r> is not here with you.\n")
        else:
            mud.send_message(id, "What would you like to whisper?\n")
    else:
        mud.send_message(id, "Who would you like to whisper to??\n")


def _help(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db,
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    if params.lower().startswith('card'):
        _help_cards(params, mud, playersDB, players,
                    rooms, npcs_db, npcs, items_db,
                    items, env_db, env, eventDB, event_schedule,
                    id, fights, corpses,
                    blocklist, map_area, character_class_db,
                    spells_db, sentiment_db, guilds_db, clouds, races_db,
                    item_history, markets, cultures_db)
        return
    if params.lower().startswith('chess'):
        _help_chess(params, mud, playersDB, players,
                    rooms, npcs_db, npcs, items_db,
                    items, env_db, env, eventDB,
                    event_schedule, id, fights, corpses,
                    blocklist, map_area, character_class_db,
                    spells_db, sentiment_db, guilds_db, clouds, races_db,
                    item_history, markets, cultures_db)
        return
    if params.lower().startswith('morris'):
        _help_morris(params, mud, playersDB, players,
                     rooms, npcs_db, npcs, items_db,
                     items, env_db, env, eventDB,
                     event_schedule, id, fights, corpses,
                     blocklist, map_area, character_class_db,
                     spells_db, sentiment_db,
                     guilds_db, clouds, races_db, item_history, markets,
                     cultures_db)
        return
    if params.lower().startswith('witch'):
        _help_witch(params, mud, playersDB, players,
                    rooms, npcs_db, npcs, items_db,
                    items, env_db, env, eventDB,
                    event_schedule, id, fights, corpses,
                    blocklist, map_area, character_class_db,
                    spells_db, sentiment_db, guilds_db, clouds, races_db,
                    item_history, markets, cultures_db)
        return
    if params.lower().startswith('spell'):
        _help_spell(params, mud, playersDB, players,
                    rooms, npcs_db, npcs, items_db,
                    items, env_db, env, eventDB, event_schedule,
                    id, fights, corpses,
                    blocklist, map_area, character_class_db,
                    spells_db, sentiment_db, guilds_db, clouds, races_db,
                    item_history, markets, cultures_db)
        return
    if params.lower().startswith('emot'):
        _help_emote(params, mud, playersDB, players,
                    rooms, npcs_db, npcs, items_db,
                    items, env_db, env, eventDB, event_schedule,
                    id, fights, corpses,
                    blocklist, map_area, character_class_db,
                    spells_db, sentiment_db, guilds_db, clouds, races_db,
                    item_history, markets, cultures_db)
        return

    mud.send_message(id, '****CLEAR****\n')
    mud.send_message(id, 'Commands:')
    mud.send_message(id,
                     '  <f220>help witch|spell|emote|' +
                     'cards|chess|morris<f255>' +
                     '     - Show help')
    mud.send_message(id,
                     '  <f220>bio [description]<f255>' +
                     '                       - ' +
                     'Set a description of yourself')
    mud.send_message(id,
                     '  <f220>graphics [on|off]<f255>' +
                     '                       - ' +
                     'Turn graphic content on or off')
    mud.send_message(id,
                     '  <f220>change password [newpassword]<f255>' +
                     '           - ' +
                     'Change your password')
    mud.send_message(id,
                     '  <f220>who<f255>' +
                     '                                     - ' +
                     'List players and where they are')
    mud.send_message(id,
                     '  <f220>quit/exit<f255>' +
                     '                               - ' +
                     'Leave the game')
    mud.send_message(id,
                     '  <f220>eat/drink [item]<f255>' +
                     '                        - ' +
                     'Eat or drink a consumable')
    mud.send_message(id,
                     '  <f220>speak [language]<f255>' +
                     '                        - ' +
                     'Switch to speaking a different language')
    mud.send_message(id,
                     '  <f220>say [message]<f255>' +
                     '                           - ' +
                     'Says something out loud, ' +
                     "e.g. 'say Hello'")
    mud.send_message(id,
                     '  <f220>look/examine<f255>' +
                     '                            - ' +
                     'Examines the surroundings,\n' +
                     '                ' +
                     '                            ' +
                     "items in the room, NPCs or other " +
                     "players\n" +
                     '                ' +
                     '                            ' +
                     "e.g. 'examine inn-keeper'")
    mud.send_message(id,
                     '  <f220>go [exit]<f255>' +
                     '                               - ' +
                     'Moves through the exit ' +
                     "specified, e.g. 'go outside'")
    mud.send_message(id,
                     '  <f220>climb though/up [exit]<f255>' +
                     '                  - ' +
                     'Try to climb through/up an exit')
    mud.send_message(id,
                     '  <f220>move/roll/heave [target]<f255>' +
                     '                - ' +
                     'Try to move or roll a heavy object')
    mud.send_message(id,
                     '  <f220>jump to [exit]<f255>' +
                     '                          - ' +
                     'Try to jump onto something')
    mud.send_message(id,
                     '  <f220>attack [target]<f255>' +
                     '                         - ' +
                     'Attack target ' +
                     "specified, e.g. 'attack knight'")
    mud.send_message(id,
                     '  <f220>shove<f255>' +
                     '                                   - ' +
                     'Try to knock a target over ' +
                     'during an attack')
    mud.send_message(id,
                     '  <f220>prone<f255>' +
                     '                                   - ' +
                     'Lie down')
    mud.send_message(id,
                     '  <f220>stand<f255>' +
                     '                                   - ' +
                     'Stand up')
    mud.send_message(id,
                     '  <f220>check inventory<f255>' +
                     '                         - ' +
                     'Check the contents of ' +
                     "your inventory")
    mud.send_message(id,
                     '  <f220>take/get [item]<f255>' +
                     '                         - ' +
                     'Pick up an item lying ' +
                     "on the floor")
    mud.send_message(id,
                     '  <f220>put [item] in/on [item]<f255>' +
                     '                 - ' +
                     'Put an item into or onto another one')
    mud.send_message(id,
                     '  <f220>drop [item]<f255>' +
                     '                             - ' +
                     'Drop an item from your inventory ' +
                     "on the floor")
    mud.send_message(id,
                     '  <f220>use/hold/pick/wield [item] ' +
                     '[left|right]<f255> - ' +
                     'Transfer an item to your hands')
    mud.send_message(id,
                     '  <f220>stow<f255>' +
                     '                                    - ' +
                     'Free your hands of items')
    mud.send_message(id,
                     '  <f220>wear [item]<f255>' +
                     '                             - ' +
                     'Wear an item')
    mud.send_message(id,
                     '  <f220>remove/unwear [item]<f255>' +
                     '                    - ' +
                     'Remove a worn item')
    mud.send_message(id,
                     '  <f220>whisper [target] [message]<f255>' +
                     '              - ' +
                     'Whisper to a player in the same room')
    mud.send_message(id,
                     '  <f220>tell/ask [target] [message]<f255>' +
                     '             - ' +
                     'Send a tell message to another player or NPC')
    mud.send_message(id,
                     '  <f220>open [item]<f255>' +
                     '                             - ' +
                     'Open an item or door')
    mud.send_message(id,
                     '  <f220>close [item]<f255>' +
                     '                            - ' +
                     'Close an item or door')
    mud.send_message(id,
                     '  <f220>push [item]<f255>' +
                     '                             - ' +
                     'Pushes a lever')
    mud.send_message(id,
                     '  <f220>pull [item]<f255>' +
                     '                             - ' +
                     'Pulls a lever')
    mud.send_message(id,
                     '  <f220>wind [item]<f255>' +
                     '                             - ' +
                     'Winds a lever')
    mud.send_message(id,
                     '  <f220>affinity [player name]<f255>' +
                     '                  - ' +
                     'Shows your affinity level with another player')
    mud.send_message(id,
                     '  <f220>cut/escape<f255>' +
                     '                              - ' +
                     'Attempt to escape from a trap')
    mud.send_message(id,
                     '  <f220>step over tripwire [exit]<f255>' +
                     '               - ' +
                     'Step over a tripwire in the given direction')
    mud.send_message(id,
                     '  <f220>dodge<f255>' +
                     '                                   - ' +
                     'Dodge an attacker on the next combat round')
    mud.send_message(id, '\n\n')


def _help_spell(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    mud.send_message(id, '\n')
    mud.send_message(id,
                     '<f220>prepare spells<f255>' +
                     '                          - ' +
                     'List spells which can be prepared')
    mud.send_message(id,
                     '<f220>prepare [spell name]<f255>' +
                     '                    - ' +
                     'Prepares a spell')
    mud.send_message(id,
                     '<f220>spells<f255>' +
                     '                                  - ' +
                     'Lists your prepared spells')
    mud.send_message(id,
                     '<f220>clear spells<f255>' +
                     '                            - ' +
                     'Clears your prepared spells list')
    mud.send_message(id,
                     '<f220>cast find familiar<f255>' +
                     '                      - ' +
                     'Summons a familiar with random form')
    mud.send_message(id,
                     '<f220>dismiss familiar<f255>' +
                     '                        - ' +
                     'Dismisses a familiar')
    mud.send_message(id,
                     '<f220>cast [spell name] on [target]<f255>' +
                     '           - ' +
                     'Cast a spell on a player or NPC')

    mud.send_message(id, '\n\n')


def _help_emote(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    mud.send_message(id, '\n')
    mud.send_message(id, '<f220>applaud<f255>')
    mud.send_message(id, '<f220>astonished<f255>')
    mud.send_message(id, '<f220>bow<f255>')
    mud.send_message(id, '<f220>confused<f255>')
    mud.send_message(id, '<f220>calm<f255>')
    mud.send_message(id, '<f220>cheer<f255>')
    mud.send_message(id, '<f220>curious<f255>')
    mud.send_message(id, '<f220>curtsey<f255>')
    mud.send_message(id, '<f220>eyebrow<f255>')
    mud.send_message(id, '<f220>frown<f255>')
    mud.send_message(id, '<f220>giggle<f255>')
    mud.send_message(id, '<f220>grin<f255>')
    mud.send_message(id, '<f220>laugh<f255>')
    mud.send_message(id, '<f220>relieved<f255>')
    mud.send_message(id, '<f220>smug<f255>')
    mud.send_message(id, '<f220>think<f255>')
    mud.send_message(id, '<f220>wave<f255>')
    mud.send_message(id, '<f220>yawn<f255>')
    mud.send_message(id, '\n\n')


def _help_witch(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    mud.send_message(id, '\n')
    if not _is_witch(id, players):
        mud.send_message(id, "You're not a witch.\n\n")
        return
    mud.send_message(id,
                     '<f220>close registrations<f255>' +
                     '                     - ' +
                     'Closes registrations of new players')
    mud.send_message(id,
                     '<f220>open registrations<f255>' +
                     '                      - ' +
                     'Allows registrations of new players')
    mud.send_message(id,
                     '<f220>mute/silence [target]<f255>' +
                     '                   - ' +
                     'Mutes a player and prevents them from attacking')
    mud.send_message(id,
                     '<f220>unmute/unsilence [target]<f255>' +
                     '               - ' +
                     'Unmutes a player')
    mud.send_message(id,
                     '<f220>freeze [target]<f255>' +
                     '                         - ' +
                     'Prevents a player from moving or attacking')
    mud.send_message(id,
                     '<f220>unfreeze [target]<f255>' +
                     '                       - ' +
                     'Allows a player to move or attack')
    mud.send_message(id,
                     '<f220>teleport [room]<f255>' +
                     '                         - ' +
                     'Teleport to a room')
    mud.send_message(id,
                     '<f220>summon [target]<f255>' +
                     '                         - ' +
                     'Summons a player to your location')
    mud.send_message(id,
                     '<f220>kick/remove [target]<f255>' +
                     '                    - ' +
                     'Remove a player from the game')
    mud.send_message(id,
                     '<f220>blocklist<f255>' +
                     '                               - ' +
                     'Show the current blocklist')
    mud.send_message(id,
                     '<f220>block [word or phrase]<f255>' +
                     '                  - ' +
                     'Adds a word or phrase to the blocklist')
    mud.send_message(id,
                     '<f220>unblock [word or phrase]<f255>' +
                     '                - ' +
                     'Removes a word or phrase to the blocklist')
    mud.send_message(id,
                     '<f220>describe "room" "room name"<f255>' +
                     '             - ' +
                     'Changes the name of the current room')
    mud.send_message(id,
                     '<f220>describe "room description"<f255>' +
                     '             - ' +
                     'Changes the current room description')
    mud.send_message(id,
                     '<f220>describe "tide" "room description"<f255>' +
                     '      - ' +
                     'Changes the room description when tide is out')
    mud.send_message(id,
                     '<f220>describe "item" "item description"<f255>' +
                     '      - ' +
                     'Changes the description of an item in the room')
    mud.send_message(id,
                     '<f220>describe "NPC" "NPC description"<f255>' +
                     '        - ' +
                     'Changes the description of an NPC in the room')
    mud.send_message(id,
                     '<f220>conjure room [direction]<f255>' +
                     '                - ' +
                     'Creates a new room in the given direction')
    mud.send_message(id,
                     '<f220>conjure npc [target]<f255>' +
                     '                    - ' +
                     'Creates a named NPC in the room')
    mud.send_message(id,
                     '<f220>conjure [item]<f255>' +
                     '                          - ' +
                     'Creates a new item in the room')
    mud.send_message(id,
                     '<f220>destroy room [direction]<f255>' +
                     '                - ' +
                     'Removes the room in the given direction')
    mud.send_message(id,
                     '<f220>destroy npc [target]<f255>' +
                     '                    - ' +
                     'Removes a named NPC from the room')
    mud.send_message(id,
                     '<f220>destroy [item]<f255>' +
                     '                          - ' +
                     'Removes an item from the room')
    mud.send_message(id,
                     '<f220>resetuniverse<f255>' +
                     '                           - ' +
                     'Resets the universe, losing any changes from defaults')
    mud.send_message(id,
                     '<f220>shutdown<f255>' +
                     '                                - ' +
                     'Shuts down the game server')
    mud.send_message(id, '\n\n')


def _help_morris(params, mud, playersDB: {}, players: {}, rooms,
                 npcs_db: {}, npcs: {}, items_db: {}, items: {},
                 env_db: {}, env: {}, eventDB: {}, event_schedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 map_area: [], character_class_db: {}, spells_db: {},
                 sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                 item_history: {}, markets: {}, cultures_db: {}):
    mud.send_message(id, '\n')
    mud.send_message(id,
                     '<f220>morris<f255>' +
                     '                                  - ' +
                     'Show the board')
    mud.send_message(id,
                     '<f220>morris put [coordinate]<f255>' +
                     '                 - ' +
                     'Place a counter')
    mud.send_message(id,
                     '<f220>morris move [from coord] [to coord]<f255>' +
                     '     - ' +
                     'Move a counter')
    mud.send_message(id,
                     '<f220>morris take [coordinate]<f255>' +
                     '                - ' +
                     'Remove a counter after mill')
    mud.send_message(id,
                     '<f220>morris reset<f255>' +
                     '                            - ' +
                     'Resets the board')
    mud.send_message(id, '\n\n')


def _help_chess(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    mud.send_message(id, '\n')
    mud.send_message(id,
                     '<f220>chess<f255>' +
                     '                                   - ' +
                     'Shows the board')
    mud.send_message(id,
                     '<f220>chess reset<f255>' +
                     '                             - ' +
                     'Rests the game')
    mud.send_message(id,
                     '<f220>chess move [coords]<f255>' +
                     '                     - ' +
                     'eg. chess move e2e3')
    mud.send_message(id,
                     '<f220>chess undo<f255>' +
                     '                              - ' +
                     'undoes the last move')
    mud.send_message(id, '\n\n')


def _help_cards(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    mud.send_message(id, '\n')
    mud.send_message(id,
                     '<f220>shuffle<f255>' +
                     '                                 - ' +
                     'Shuffles the deck')
    mud.send_message(id,
                     '<f220>deal to [player names]<f255>' +
                     '                  - ' +
                     'Deals cards')
    mud.send_message(id,
                     '<f220>hand<f255>' +
                     '                                    - ' +
                     'View your hand of cards')
    mud.send_message(id,
                     '<f220>swap [card description]<f255>' +
                     '                 - ' +
                     'Swaps a card')
    mud.send_message(id,
                     '<f220>stick<f255>' +
                     '                 - ' +
                     "Don't swap any cards")
    mud.send_message(id,
                     '<f220>call<f255>' +
                     '                                    - ' +
                     'Players show their hands')
    mud.send_message(id, 'Possible suits are: <f32>leashes, collars, ' +
                     'swords, horns, coins, clubs, cups, hearts, ' +
                     'diamonds and spades.<r>')
    mud.send_message(id, 'In some packs the <f32>Queen<r> is replaced ' +
                     'by a <f32>Knight<r>.')
    mud.send_message(id, '\n\n')


def _cast_spell_on_player(mud, spellName: str, players: {}, id, npcs: {},
                          p, spellDetails):
    if npcs[p]['room'] != players[id]['room']:
        mud.send_message(id, "They're not here.\n\n")
        return

    if spellDetails['action'].startswith('protect'):
        npcs[p]['tempHitPoints'] = spellDetails['hp']
        npcs[p]['tempHitPointsDuration'] = \
            time_string_to_sec(spellDetails['duration'])
        npcs[p]['tempHitPointsStart'] = int(time.time())

    if spellDetails['action'].startswith('cure'):
        if npcs[p]['hp'] < npcs[p]['hpMax']:
            npcs[p]['hp'] += randint(1, spellDetails['hp'])
            if npcs[p]['hp'] > npcs[p]['hpMax']:
                npcs[p]['hp'] = npcs[p]['hpMax']

    if spellDetails['action'].startswith('charm'):
        charmTarget = players[id]['name']
        charmValue = int(npcs[p]['cha'] + players[id]['cha'])
        npcs[p]['tempCharm'] = charmValue
        npcs[p]['tempCharmTarget'] = charmTarget
        npcs[p]['tempCharmDuration'] = \
            time_string_to_sec(spellDetails['duration'])
        npcs[p]['tempCharmStart'] = int(time.time())
        if npcs[p]['affinity'].get(charmTarget):
            npcs[p]['affinity'][charmTarget] += charmValue
        else:
            npcs[p]['affinity'][charmTarget] = charmValue

    if spellDetails['action'].startswith('friend'):
        if players[id]['cha'] < npcs[p]['cha']:
            remove_prepared_spell(players, id, spellName)
            mud.send_message(id, "You don't have enough charisma.\n\n")
            return
        playerName = players[id]['name']
        if npcs[p]['affinity'].get(playerName):
            npcs[p]['affinity'][playerName] += 1
        else:
            npcs[p]['affinity'][playerName] = 1

    if spellDetails['action'].startswith('attack'):
        if len(spellDetails['damageType']
               ) == 0 or spellDetails['damageType'] == 'str':
            npcs[p]['hp'] = npcs[p]['hp'] - randint(1, spellDetails['damage'])
        else:
            damageType = spellDetails['damageType']
            if npcs[p].get(damageType):
                npcs[p][damageType] = npcs[p][damageType] - \
                    randint(1, spellDetails['damage'])
                if npcs[p][damageType] < 0:
                    npcs[p][damageType] = 0

    if spellDetails['action'].startswith('frozen'):
        npcs[p]['frozenDescription'] = spellDetails['actionDescription']
        npcs[p]['frozenDuration'] = \
            time_string_to_sec(spellDetails['duration'])
        npcs[p]['frozenStart'] = int(time.time())

    _show_spell_image(mud, id, spellName.replace(' ', '_'), players)

    mud.send_message(
        id,
        random_desc(spellDetails['description']).format('<f32>' +
                                                        npcs[p]['name'] +
                                                        '<r>') + '\n\n')

    secondDesc = random_desc(spellDetails['description_second'])
    if npcs == players and len(secondDesc) > 0:
        mud.send_message(
            p,
            secondDesc.format(players[id]['name'],
                              'you') + '\n\n')

    remove_prepared_spell(players, id, spellName)


def _cast_spell_undirected(params, mud, playersDB: {}, players: {}, rooms: {},
                           npcs_db: {}, npcs: {}, items_db: {}, items: {},
                           env_db: {}, env: {}, eventDB: {}, event_schedule,
                           id: int, fights: {}, corpses: {}, blocklist,
                           map_area: [], character_class_db: {}, spells_db: {},
                           sentiment_db: {}, spellName: {}, spellDetails: {},
                           clouds: {}, races_db: {}, guilds_db: {},
                           item_history: {}, markets: {}, cultures_db: {}):
    spellAction = spellDetails['action']
    if spellAction.startswith('familiar'):
        _show_spell_image(mud, id, spellName.replace(' ', '_'), players)
        _conjure_npc(spellDetails['action'], mud, playersDB, players,
                     rooms, npcs_db, npcs, items_db, items, env_db, env,
                     eventDB, event_schedule, id, fights, corpses,
                     blocklist, map_area, character_class_db, spells_db,
                     sentiment_db, guilds_db, clouds, races_db,
                     item_history, markets, cultures_db)
        return
    elif spellAction.startswith('defen'):
        # defense spells
        if spellName.endswith('shield') and spellDetails.get('armor'):
            _show_spell_image(mud, id, "magic_shield", players)
            if not players[id]["magicShield"]:
                remove_prepared_spell(players, id, spellName)
                players[id]['magicShield'] = spellDetails['armor']
                players[id]['magicShieldStart'] = int(time.time())
                players[id]["magicShieldDuration"] = \
                    time_string_to_sec(spellDetails['duration'])
                mud.send_message(id, "Magic shield active.\n\n")

                # inform other players in the room
                for pid in players:
                    if pid == id:
                        continue
                    if players[pid]['room'] == players[id]['room']:
                        _show_spell_image(mud, pid, "magic_shield", players)
                        msgStr = \
                            '<f32>' + players[id]['name'] + \
                            '<r> activates a magic shield'
                        mud.send_message(pid, msgStr + ".\n\n")
            else:
                mud.send_message(id, "Magic shield is already active.\n\n")
            return
    mud.send_message(id, "Nothing happens.\n\n")


def _cast_spell(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    # cast fishing rod
    if 'fishing' in params or params == 'rod' or params == 'fish':
        _fish(params, mud, playersDB, players, rooms,
              npcs_db, npcs, items_db, items,
              env_db, env, eventDB, event_schedule,
              id, fights, corpses, blocklist,
              map_area, character_class_db, spells_db,
              sentiment_db, guilds_db, clouds, races_db,
              item_history, markets, cultures_db)
        return

    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '\n\n')
        return

    if len(params.strip()) == 0:
        mud.send_message(id, 'You try to cast a spell but fail horribly.\n\n')
        return

    castStr = params.lower().strip()
    if castStr.startswith('the spell '):
        castStr = castStr.replace('the spell ', '', 1)
    if castStr.startswith('a '):
        castStr = castStr.replace('a ', '', 1)
    if castStr.startswith('the '):
        castStr = castStr.replace('the ', '', 1)
    if castStr.startswith('spell '):
        castStr = castStr.replace('spell ', '', 1)
    castAt = ''
    spellName = ''
    if ' at ' in castStr:
        spellName = castStr.split(' at ')[0].strip()
        castAt = castStr.split(' at ')[1].strip()
    else:
        if ' on ' in castStr:
            spellName = castStr.split(' on ')[0].strip()
            castAt = castStr.split(' on ')[1].strip()
        else:
            spellName = castStr.strip()

    if not players[id]['preparedSpells'].get(spellName):
        mud.send_message(id, "That's not a prepared spell.\n\n")
        return

    spellDetails = None
    if spells_db.get('cantrip'):
        if spells_db['cantrip'].get(spellName):
            spellDetails = spells_db['cantrip'][spellName]
    if spellDetails is None:
        maxSpellLevel = _get_player_max_spell_level(players, id)
        for level in range(1, maxSpellLevel + 1):
            if spells_db[str(level)].get(spellName):
                spellDetails = spells_db[str(level)][spellName]
                break
    if spellDetails is None:
        mud.send_message(id, "You have no knowledge of that spell.\n\n")
        return

    if len(castAt) > 0:
        for p in players:
            if castAt not in players[p]['name'].lower():
                continue
            if p == id:
                mud.send_message(id, "This is not a hypnosis spell.\n\n")
                return
            _cast_spell_on_player(
                mud, spellName, players, id, players, p, spellDetails)
            return

        for p in npcs:
            if castAt not in npcs[p]['name'].lower():
                continue

            if npcs[p]['familiarOf'] == players[id]['name']:
                mud.send_message(
                    id, "You can't cast a spell on your own familiar!\n\n")
                return

            _cast_spell_on_player(mud, spellName, players, id, npcs,
                                  p, spellDetails)
            return
    else:
        _cast_spell_undirected(params, mud, playersDB, players, rooms,
                               npcs_db, npcs, items_db, items, env_db,
                               env, eventDB, event_schedule, id, fights,
                               corpses, blocklist, map_area,
                               character_class_db, spells_db, sentiment_db,
                               spellName, spellDetails,
                               clouds, races_db, guilds_db,
                               item_history, markets, cultures_db)


def _affinity(params, mud, playersDB: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {},
              env_db: {}, env: {}, eventDB: {}, event_schedule: {},
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    otherPlayer = params.lower().strip()
    if len(otherPlayer) == 0:
        mud.send_message(id, 'With which player?\n\n')
        return
    if players[id]['affinity'].get(otherPlayer):
        affinity = players[id]['affinity'][otherPlayer]
        if affinity >= 0:
            mud.send_message(
                id, 'Your affinity with <f32><u>' +
                otherPlayer + '<r> is <f15><b2>+' +
                str(affinity) + '<r>\n\n')
        else:
            mud.send_message(
                id, 'Your affinity with <f32><u>' +
                otherPlayer + '<r> is <f15><b88>' +
                str(affinity) + '<r>\n\n')
        return
    mud.send_message(id, "You don't have any affinity with them.\n\n")


def _clear_spells(params, mud, playersDB: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                  item_history: {}, markets: {}, cultures_db: {}):
    if len(players[id]['preparedSpells']) > 0:
        players[id]['preparedSpells'].clear()
        players[id]['spellSlots'].clear()
        mud.send_message(id, 'Your prepared spells list has been cleared.\n\n')
        return

    mud.send_message(id, "Your don't have any spells prepared.\n\n")


def _spells(params, mud, playersDB: {}, players: {}, rooms: {},
            npcs_db: {}, npcs: {}, items_db: {}, items: {},
            env_db: {}, env: {}, eventDB: {}, event_schedule,
            id: int, fights: {}, corpses: {}, blocklist,
            map_area: [], character_class_db: {}, spells_db: {},
            sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}):
    if len(players[id]['preparedSpells']) > 0:
        mud.send_message(id, 'Your prepared spells:\n')
        for name, details in players[id]['preparedSpells'].items():
            mud.send_message(id, '  <b234>' + name + '<r>')
        mud.send_message(id, '\n')
    else:
        mud.send_message(id, 'You have no spells prepared.\n\n')


def _prepare_spell_at_level(params, mud, playersDB: {}, players: {}, rooms: {},
                            npcs_db: {}, npcs: {}, items_db: {}, items: {},
                            env_db: {}, env: {}, eventDB: {}, event_schedule,
                            id: int, fights: {}, corpses: {}, blocklist,
                            map_area: [], character_class_db: {},
                            spells_db: {}, spellName: {}, level: {}):
    for name, details in spells_db[level].items():
        if name.lower() == spellName:
            if name.lower() not in players[id]['preparedSpells']:
                if len(spells_db[level][name]['items']) == 0:
                    players[id]['preparedSpells'][name] = 1
                else:
                    for required in spells_db[level][name]['items']:
                        requiredItemFound = False
                        for i in list(players[id]['inv']):
                            if int(i) == required:
                                requiredItemFound = True
                                break
                        if not requiredItemFound:
                            mud.send_message(
                                id, 'You need <b234>' +
                                items_db[required]['article'] +
                                ' ' + items_db[required]['name'] +
                                '<r>\n\n')
                            return True
                players[id]['prepareSpell'] = spellName
                players[id]['prepareSpellProgress'] = 0
                players[id]['prepareSpellTime'] = time_string_to_sec(
                    details['prepareTime'])
                if len(details['prepareTime']) > 0:
                    mud.send_message(
                        id,
                        'You begin preparing the spell <b234>' +
                        spellName + '<r>. It will take ' +
                        details['prepareTime'] + '.\n\n')
                else:
                    mud.send_message(
                        id,
                        'You begin preparing the spell <b234>' +
                        spellName + '<r>.\n\n')
                return True
    return False


def _player_max_cantrips(players: {}, id) -> int:
    """Returns the maximum number of cantrips which the player can prepare
    """
    maxCantrips = 0
    for prof in players[id]['proficiencies']:
        if isinstance(prof, list):
            continue
        if prof.lower().startswith('cantrip'):
            if '(' in prof and ')' in prof:
                cantrips = int(prof.split('(')[1].replace(')', ''))
                if cantrips > maxCantrips:
                    maxCantrips = cantrips
    return maxCantrips


def _get_player_max_spell_level(players: {}, id) -> int:
    """Returns the maximum spell level of the player
    """
    for prof in players[id]['proficiencies']:
        if isinstance(prof, list):
            spellList = list(prof)
            if len(spellList) > 0:
                if spellList[0].lower() == 'spell':
                    return len(spellList) - 1
    return -1


def _get_player_spell_slots_at_spell_level(players: {}, id, spellLevel) -> int:
    """Returns the maximum spell slots at the given spell level
    """
    for prof in players[id]['proficiencies']:
        if isinstance(prof, list):
            spellList = list(prof)
            if len(spellList) > 0:
                if spellList[0].lower() == 'spell':
                    return spellList[spellLevel]
    return 0


def _get_player_used_slots_at_spell_level(players: {}, id, spellLevel,
                                          spells_db: {}):
    """Returns the used spell slots at the given spell level
    """
    if not spells_db.get(str(spellLevel)):
        return 0

    usedCounter = 0
    for spellName, details in spells_db[str(spellLevel)].items():
        if spellName in players[id]['preparedSpells']:
            usedCounter += 1
    return usedCounter


def _player_prepared_cantrips(players, id, spells_db: {}) -> int:
    """Returns the number of cantrips which the player has prepared
    """
    preparedCounter = 0
    for spellName in players[id]['preparedSpells']:
        for cantripName, details in spells_db['cantrip'].items():
            if cantripName == spellName:
                preparedCounter += 1
                break
    return preparedCounter


def _prepare_spell(params, mud, playersDB: {}, players: {}, rooms: {},
                   npcs_db: {}, npcs: {}, items_db: {}, items: {},
                   env_db: {}, env: {}, eventDB: {}, event_schedule,
                   id: int, fights: {}, corpses: {}, blocklist,
                   map_area: [], character_class_db: {}, spells_db: {},
                   sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                   item_history: {}, markets: {}, cultures_db: {}):
    spellName = params.lower().strip()

    # "learn spells" or "prepare spells" shows list of spells
    if spellName == 'spell' or spellName == 'spells':
        spellName = ''

    maxCantrips = _player_max_cantrips(players, id)
    maxSpellLevel = _get_player_max_spell_level(players, id)

    if maxSpellLevel < 0 and maxCantrips == 0:
        mud.send_message(id, "You can't prepare spells.\n\n")
        return

    if len(spellName) == 0:
        # list spells which can be prepared
        mud.send_message(id, 'Spells you can prepare are:\n')

        if maxCantrips > 0 and spells_db.get('cantrip'):
            for name, details in spells_db['cantrip'].items():
                if name.lower() not in players[id]['preparedSpells']:
                    spellClasses = spells_db['cantrip'][name]['classes']
                    if players[id]['characterClass'] in spellClasses or \
                       len(spellClasses) == 0:
                        mud.send_message(id, '  <f220>-' + name + '<r>')

        if maxSpellLevel > 0:
            for level in range(1, maxSpellLevel + 1):
                if not spells_db.get(str(level)):
                    continue
                for name, details in spells_db[str(level)].items():
                    if name.lower() not in players[id]['preparedSpells']:
                        spellClasses = spells_db[str(level)][name]['classes']
                        if players[id]['characterClass'] in spellClasses or \
                           len(spellClasses) == 0:
                            mud.send_message(id, '  <b234>' + name + '<r>')
        mud.send_message(id, '\n')
    else:
        if spellName.startswith('the spell '):
            spellName = spellName.replace('the spell ', '')
        if spellName.startswith('spell '):
            spellName = spellName.replace('spell ', '')
        if spellName == players[id]['prepareSpell']:
            mud.send_message(id, 'You are already preparing that.\n\n')
            return

        if maxCantrips > 0 and spells_db.get('cantrip'):
            if _player_prepared_cantrips(players, id, spells_db) < maxCantrips:
                if _prepare_spell_at_level(params, mud, playersDB, players,
                                           rooms, npcs_db, npcs, items_db,
                                           items, env_db, env, eventDB,
                                           event_schedule, id, fights,
                                           corpses, blocklist, map_area,
                                           character_class_db, spells_db,
                                           spellName, 'cantrip'):
                    return
            else:
                mud.send_message(
                    id, "You can't prepare any more cantrips.\n\n")
                return

        if maxSpellLevel > 0:
            for level in range(1, maxSpellLevel + 1):
                if not spells_db.get(str(level)):
                    continue
                maxSlots = \
                    _get_player_spell_slots_at_spell_level(players, id, level)
                usedSlots = \
                    _get_player_used_slots_at_spell_level(players, id,
                                                          level, spells_db)
                if usedSlots < maxSlots:
                    if _prepare_spell_at_level(params, mud, playersDB,
                                               players, rooms, npcs_db, npcs,
                                               items_db, items, env_db, env,
                                               eventDB, event_schedule, id,
                                               fights, corpses, blocklist,
                                               map_area,
                                               character_class_db,
                                               spells_db, spellName,
                                               str(level)):
                        return
                else:
                    mud.send_message(
                        id,
                        "You have prepared the maximum level" +
                        str(level) + " spells.\n\n")
                    return

        mud.send_message(id, "That's not a spell.\n\n")


def _speak(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
           env: {}, eventDB: {}, event_schedule: {}, id: int,
           fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    lang = params.lower().strip()
    if lang not in players[id]['language']:
        mud.send_message(id, "You don't know how to speak that language\n\n")
        return
    players[id]['speakLanguage'] = lang
    mud.send_message(id, "You switch to speaking in " + lang + "\n\n")


def _taunt(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
           env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    if not params:
        mud.send_message_wrap(id, '<f230>', "Who shall be your victim?\n")
        return

    if players[id]['canSay'] == 1:
        if params.startswith('at '):
            params = params.replace('at ', '', 1)
        target = params
        if not target:
            mud.send_message_wrap(id, '<f230>', "Who shall be your victim?\n")
            return

        # replace "familiar" with their NPC name
        # as in: "taunt familiar"
        if target.lower() == 'familiar':
            newTarget = get_familiar_name(players, id, npcs)
            if len(newTarget) > 0:
                target = newTarget

        fullTarget = target
        if target.startswith('the '):
            target = target.replace('the ', '', 1)

        tauntTypeFirstPerson = \
            random_desc('taunt|insult|besmirch|' +
                        'gibe|ridicule')
        if tauntTypeFirstPerson != 'besmirch':
            tauntTypeSecondPerson = tauntTypeFirstPerson + 's'
        else:
            tauntTypeSecondPerson = tauntTypeFirstPerson + 'es'

        isDone = False
        for p in players:
            if players[p]['authenticated'] is not None and \
               target.lower() in players[p]['name'].lower() and \
               players[p]['room'] == players[id]['room']:
                if target.lower() in players[id]['name'].lower():
                    mud.send_message_wrap(
                        id, '<f230>', "It'd be pointless to taunt yourself!\n")
                else:
                    langList = players[p]['language']
                    if players[id]['speakLanguage'] in langList:
                        mud.send_message_wrap(
                            p, '<f230>',
                            players[id]['name'] + " " +
                            tauntTypeSecondPerson + " you\n")
                        decrease_affinity_between_players(
                            players, p, players, id, guilds_db)
                    else:
                        mud.send_message_wrap(
                            p, '<f230>',
                            players[id]['name'] + " says something in " +
                            players[id]['speakLanguage'] + '\n')
                    decrease_affinity_between_players(
                        players, id, players, p, guilds_db)
                isDone = True
                break
        if not isDone:
            for p in npcs:
                if target.lower() in npcs[p]['name'].lower() and \
                   npcs[p]['room'] == players[id]['room']:
                    if target.lower() in players[id]['name'].lower():
                        mud.send_message_wrap(
                            id, '<f230>',
                            "It'd be pointless to " + tauntTypeFirstPerson +
                            " yourself!\n")
                    else:
                        langList = npcs[p]['language']
                        if players[id]['speakLanguage'] in langList:
                            decrease_affinity_between_players(
                                npcs, p, players, id, guilds_db)
                    decrease_affinity_between_players(
                        players, id, npcs, p, guilds_db)
                    isDone = True
                    break

        if isDone:
            tauntTypeFirstPerson
            for p in players:
                if p == id:
                    tauntSeverity = \
                        random_desc('mercilessly|severely|harshly|' +
                                    'loudly|blatantly|coarsely|' +
                                    'crudely|unremittingly|' +
                                    'witheringly|pitilessly')
                    descr = "You " + tauntSeverity + ' ' + \
                        tauntTypeFirstPerson + ' ' + fullTarget
                    mud.send_message_wrap(id, '<f230>', descr + ".\n")
                    continue
                if players[p]['room'] == players[id]['room']:
                    mud.send_message_wrap(
                        id, '<f230>',
                        players[id]['name'] + ' ' + tauntTypeSecondPerson +
                        ' ' + fullTarget + "\n")
        else:
            mud.send_message_wrap(
                id, '<f230>', target + ' is not here.\n')
    else:
        mud.send_message_wrap(
            id, '<f230>',
            'To find yourself unable to taunt at this time.\n')


def _say(params, mud, playersDB: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
         env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['canSay'] == 1:

        # don't say if the string contains a blocked string
        selfOnly = False
        params2 = params.lower()
        for blockedstr in blocklist:
            if blockedstr in params2:
                selfOnly = True
                break

        # go through every player in the game
        cantStr = thieves_cant(params)
        for (pid, pl) in list(players.items()):
            # if they're in the same room as the player
            if players[pid]['room'] == players[id]['room']:
                # can the other player see this player?
                if not player_is_visible(mud, pid, players, id, players):
                    continue
                if selfOnly is False or pid == id:
                    langList = players[pid]['language']
                    if players[id]['speakLanguage'] in langList:
                        sentimentScore = \
                            get_sentiment(params, sentiment_db) + \
                            get_guild_sentiment(players, id, players,
                                                pid, guilds_db)

                        if sentimentScore >= 0:
                            increase_affinity_between_players(
                                players, id, players, pid, guilds_db)
                            increase_affinity_between_players(
                                players, pid, players, id, guilds_db)
                        else:
                            decrease_affinity_between_players(
                                players, id, players, pid, guilds_db)
                            decrease_affinity_between_players(
                                players, pid, players, id, guilds_db)

                        # send them a message telling them what the player said
                        pName = players[id]['name']
                        desc = \
                            '<f220>{}<r> says: <f159>{}'.format(pName, params)
                        mud.send_message_wrap(
                            pid, '<f230>', desc + "\n\n")
                    else:
                        pName = players[id]['name']
                        if players[id]['speakLanguage'] != 'cant':
                            pLang = players[id]['speakLanguage']
                            desc = \
                                '<f220>{}<r> says '.format(pName) + \
                                'something in <f159>{}<r>'.format(pLang)
                            mud.send_message_wrap(
                                pid, '<f230>', desc + "\n\n")
                        else:
                            mud.send_message_wrap(
                                pid, '<f230>',
                                '<f220>{}<r> says: '.format(pName) +
                                '<f159>{}'.format(cantStr) + "\n\n")
    else:
        mud.send_message_wrap(
            id, '<f230>',
            'To your horror, you realise you somehow cannot force ' +
            'yourself to utter a single word!\n')


def _emote(params, mud, playersDB: {}, players: {}, rooms: {},
           id: int, emoteDescription: str):
    if players[id]['canSay'] == 1:
        # go through every player in the game
        for (pid, pl) in list(players.items()):
            # if they're in the same room as the player
            if players[pid]['room'] == players[id]['room']:
                # can the other player see this player?
                if not player_is_visible(mud, pid, players, id, players):
                    continue

                # send them a message telling them what the player did
                pName = players[id]['name']
                desc = \
                    '<f220>{}<r> {}<f159>'.format(pName, emoteDescription)
                mud.send_message_wrap(
                    pid, '<f230>', desc + "\n\n")
    else:
        mud.send_message_wrap(
            id, '<f230>',
            'To your horror, you realise you somehow cannot force ' +
            'yourself to make any expression!\n')


def _laugh(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
           env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'laughs')


def _thinking(params, mud, playersDB: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
              env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'is thinking')


def _grimace(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'grimaces')


def _applaud(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'applauds')


def _nod(params, mud, playersDB: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
         env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'nods')


def _wave(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
          env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'waves')


def _astonished(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
                env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'is astonished')


def _confused(params, mud, playersDB: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
              env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'looks confused')


def _bow(params, mud, playersDB: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
         env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'takes a bow')


def _calm(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
          env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'looks calm')


def _cheer(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
           env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'cheers heartily')


def _curious(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'looks curious')


def _curtsey(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'curtseys')


def _frown(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
           env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'frowns')


def _eyebrow(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'raises an eyebrow')


def _giggle(params, mud, playersDB: {}, players: {}, rooms: {},
            npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
            env: {}, eventDB: {}, event_schedule,
            id: int, fights: {}, corpses: {}, blocklist,
            map_area: [], character_class_db: {}, spells_db: {},
            sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'giggles')


def _grin(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
          env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'grins')


def _yawn(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
          env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'yawns')


def _smug(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
          env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'looks smug')


def _relieved(params, mud, playersDB: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
              env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'looks relieved')


def _stick(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
           env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    _say('stick', mud, playersDB, players, rooms,
         npcs_db, npcs, items_db, items, env_db,
         env, eventDB, event_schedule,
         id, fights, corpses, blocklist,
         map_area, character_class_db, spells_db,
         sentiment_db, guilds_db, clouds, races_db, item_history, markets,
         cultures_db)


def _holding_light_source(players: {}, id, items: {}, items_db: {}) -> bool:
    """Is the given player holding a light source?
    """
    itemID = int(players[id]['clo_lhand'])
    if itemID > 0:
        if items_db[itemID]['lightSource'] != 0:
            return True
    itemID = int(players[id]['clo_rhand'])
    if itemID > 0:
        if items_db[int(itemID)]['lightSource'] != 0:
            return True

    # are there any other players in the same room holding a light source?
    for p in players:
        if p == id:
            continue
        if players[p]['room'] != players[id]['room']:
            continue
        itemID = int(players[p]['clo_lhand'])
        if itemID > 0:
            if items_db[itemID]['lightSource'] != 0:
                return True
        itemID = int(players[p]['clo_rhand'])
        if itemID > 0:
            if items_db[int(itemID)]['lightSource'] != 0:
                return True

    # is there a light source in the room?
    return _light_source_in_room(players, id, items, items_db)


def _conditional_logic(condType: str, cond: str, description: str, id,
                       players: {}, items: {},
                       items_db: {}, clouds: {}, map_area: [],
                       rooms: {}, lookModifier: str) -> bool:
    if lookModifier:
        # look under/above/behind
        if condType == lookModifier:
            return True

    if condType == 'sunrise' or \
       condType == 'dawn':
        currTime = datetime.datetime.today()
        currHour = currTime.hour
        sun = get_solar()
        sunRiseTime = sun.get_local_sunrise_time(currTime).hour
        if 'true' in cond.lower() or \
           'y' in cond.lower():
            if currHour >= sunRiseTime - 1 and currHour <= sunRiseTime:
                return True
        else:
            if currHour < sunRiseTime - 1 or currHour > sunRiseTime:
                return True

    if condType == 'sunset' or \
       condType == 'dusk':
        currTime = datetime.datetime.today()
        currHour = currTime.hour
        sun = get_solar()
        sunSetTime = sun.get_local_sunset_time(currTime).hour
        if 'true' in cond.lower() or \
           'y' in cond.lower():
            if currHour >= sunSetTime and currHour <= sunSetTime+1:
                return True
        else:
            if currHour < sunSetTime or currHour > sunSetTime+1:
                return True

    if condType.startswith('rain'):
        rm = players[id]['room']
        coords = rooms[rm]['coords']
        if 'true' in cond.lower() or \
           'y' in cond.lower():
            if get_rain_at_coords(coords, map_area, clouds):
                return True
        else:
            if not get_rain_at_coords(coords, map_area, clouds):
                return True

    if condType == 'morning':
        currHour = datetime.datetime.today().hour
        if currHour < 12:
            if 'true' in cond.lower() or \
               'y' in cond.lower():
                return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True
    if condType == 'noon':
        currHour = datetime.datetime.today().hour
        if currHour == 12:
            if 'true' in cond.lower() or \
               'y' in cond.lower():
                return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True
    if condType == 'afternoon':
        currHour = datetime.datetime.today().hour
        if currHour >= 12 and currHour < 17:
            if 'true' in cond.lower() or \
               'y' in cond.lower():
                return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True
    if condType == 'evening':
        currHour = datetime.datetime.today().hour
        if currHour >= 17:
            if 'true' in cond.lower() or \
               'y' in cond.lower():
                return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True
    if condType == 'night':
        currHour = datetime.datetime.today().hour
        if currHour >= 22 or currHour < 6:
            if 'true' in cond.lower() or \
               'y' in cond.lower():
                return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True

    if condType.endswith('moon'):
        currTime = datetime.datetime.today()
        currHour = currTime.hour
        phase = moon_phase(currTime)
        if currHour >= 22 or currHour < 6:
            moon_phaseNames = {
                0: "newmoon",
                1: "waxingcrescentmoon",
                2: "firstquartermoon",
                3: "waxinggibbousmoon",
                4: "fullmoon",
                5: "waninggibbousmoon",
                6: "lastquartermoon",
                7: "waningcrescentmoon"
            }
            for moonIndex, phaseName in moon_phaseNames.items():
                if condType == phaseName and phase == moonIndex:
                    if 'true' in cond.lower() or \
                       'y' in cond.lower():
                        return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True

    if condType == 'hour':
        currHour = datetime.datetime.today().hour
        condHour = \
            cond.replace('>', '').replace('<', '').replace('=', '').strip()
        if '>' in cond:
            if currHour > int(condHour):
                return True
        if '<' in cond:
            if currHour < int(condHour):
                return True
        if '=' in cond:
            if currHour == int(condHour):
                return True

    if condType == 'skill':
        if '<=' in cond:
            skillType = cond.split('<=')[0].strip()
            if players[id].get(skillType):
                skillValue = int(cond.split('<=')[1].split())
                if players[id][skillType] <= skillValue:
                    return True
        if '>=' in cond:
            skillType = cond.split('>=')[0].strip()
            if players[id].get(skillType):
                skillValue = int(cond.split('>=')[1].split())
                if players[id][skillType] >= skillValue:
                    return True
        if '>' in cond:
            skillType = cond.split('>')[0].strip()
            if players[id].get(skillType):
                skillValue = int(cond.split('>')[1].split())
                if players[id][skillType] > skillValue:
                    return True
        if '<' in cond:
            skillType = cond.split('<')[0].strip()
            if players[id].get(skillType):
                skillValue = int(cond.split('<')[1].split())
                if players[id][skillType] < skillValue:
                    return True
        if '=' in cond:
            cond = cond.replace('==', '=')
            skillType = cond.split('=')[0].strip()
            if players[id].get(skillType):
                skillValue = int(cond.split('=')[1].split())
                if players[id][skillType] == skillValue:
                    return True

    if condType == 'date' or condType == 'dayofmonth':
        dayNumber = int(cond.split('/')[0])
        if dayNumber == \
           int(datetime.datetime.today().strftime("%d")):
            monthNumber = int(cond.split('/')[1])
            if monthNumber == \
               int(datetime.datetime.today().strftime("%m")):
                return True

    if condType == 'month':
        if '|' in cond:
            months = cond.split('|')
            for m in months:
                if int(m) == int(datetime.datetime.today().strftime("%m")):
                    return True
        else:
            currMonthNumber = \
                int(datetime.datetime.today().strftime("%m"))
            monthNumber = int(cond)
            if monthNumber == currMonthNumber:
                return True

    if condType == 'season':
        currMonthNumber = int(datetime.datetime.today().strftime("%m"))
        if cond == 'spring':
            if currMonthNumber > 1 and currMonthNumber <= 4:
                return True
        elif cond == 'summer':
            if currMonthNumber > 4 and currMonthNumber <= 9:
                return True
        elif cond == 'autumn':
            if currMonthNumber > 9 and currMonthNumber <= 10:
                return True
        elif cond == 'winter':
            if currMonthNumber > 10 or currMonthNumber <= 1:
                return True

    if condType == 'day' or \
       condType == 'dayofweek' or condType == 'dow' or \
       condType == 'weekday':
        dayOfWeek = int(cond)
        if dayOfWeek == datetime.datetime.today().weekday():
            return True

    if condType == 'held' or condType.startswith('hold'):
        if not cond.isdigit():
            if cond.lower() == 'lightsource':
                return _holding_light_source(players, id, items, items_db)
        elif (players[id]['clo_lhand'] == int(cond) or
              players[id]['clo_rhand'] == int(cond)):
            return True

    if condType.startswith('wear'):
        for c in wear_location:
            if players[id]['clo_' + c] == int(cond):
                return True

    return False


def _conditional_room_desc(description: str, tideOutDescription: str,
                           conditional: [], id, players: {}, items: {},
                           items_db: {}, clouds: {}, map_area: [],
                           rooms: {}):
    """Returns a room description which can vary depending on conditions
    """
    roomDescription = description
    if len(tideOutDescription) > 0:
        if run_tide() < 0.0:
            roomDescription = tideOutDescription

    # Alternative descriptions triggered by conditions
    for possibleDescription in conditional:
        if len(possibleDescription) >= 3:
            condType = possibleDescription[0]
            cond = possibleDescription[1]
            alternativeDescription = possibleDescription[2]
            if _conditional_logic(condType, cond,
                                  alternativeDescription,
                                  id, players, items, items_db,
                                  clouds, map_area, rooms, None):
                roomDescription = alternativeDescription
                break

    return roomDescription


def _conditional_item_desc(itemId, conditional: [],
                           id, players: {}, items: {},
                           items_db: {}, clouds: {}, map_area: [],
                           rooms: {}, lookModifier: str):
    """Returns an item description which can vary depending on conditions
    """
    itemDescription = items_db[itemId]['long_description']

    # Alternative descriptions triggered by conditions
    for possibleDescription in conditional:
        if len(possibleDescription) >= 2:
            condType = possibleDescription[0]
            cond = None
            if condType.startswith('wear') or condType.startswith('hold'):
                cond = str(itemId)
                alternativeDescription = possibleDescription[1]
            elif len(possibleDescription) >= 3:
                cond = possibleDescription[1]
                alternativeDescription = possibleDescription[2]
            if cond:
                if _conditional_logic(condType, cond,
                                      alternativeDescription,
                                      id, players, items, items_db,
                                      clouds, map_area, rooms,
                                      lookModifier):
                    itemDescription = alternativeDescription
                    break

    return itemDescription


def _conditional_room_image(conditional: [], id, players: {}, items: {},
                            items_db: {}, clouds: {}, map_area: [],
                            rooms: {}) -> str:
    """If there is an image associated with a conditional
    room description then return its name
    """
    for possibleDescription in conditional:
        if len(possibleDescription) < 4:
            continue
        condType = possibleDescription[0]
        cond = possibleDescription[1]
        alternativeDescription = possibleDescription[2]
        if _conditional_logic(condType, cond,
                              alternativeDescription,
                              id, players, items, items_db, clouds,
                              map_area, rooms, None):
            roomImageFilename = \
                'images/rooms/' + possibleDescription[3]
            if os.path.isfile(roomImageFilename):
                return possibleDescription[3]
            break
    return None


def _conditional_item_image(itemId,
                            conditional: [], id, players: {}, items: {},
                            items_db: {}, clouds: {}, map_area: [],
                            rooms: {}, lookModifier: str) -> str:
    """If there is an image associated with a conditional
    item description then return its name
    """
    # Alternative descriptions triggered by conditions
    for possibleDescription in conditional:
        if len(possibleDescription) < 3:
            continue
        condType = possibleDescription[0]
        cond = None
        itemIdStr = None
        if condType.startswith('wear') or condType.startswith('hold'):
            cond = str(itemId)
            alternativeDescription = possibleDescription[1]
            itemIdStr = possibleDescription[2]
        elif len(possibleDescription) >= 4:
            cond = possibleDescription[1]
            alternativeDescription = possibleDescription[2]
            itemIdStr = possibleDescription[3]
        if cond and itemIdStr:
            if _conditional_logic(condType, cond,
                                  alternativeDescription,
                                  id, players, items, items_db,
                                  clouds, map_area, rooms,
                                  lookModifier):
                return str(itemIdStr)
    return str(itemId)


def _players_in_room(targetRoom, players, npcs):
    """Returns the number of players in the given room.
       This includes NPCs.
    """
    playersCtr = 0
    for (pid, pl) in list(players.items()):
        # if they're in the same room as the player
        if players[pid]['room'] == targetRoom:
            playersCtr += 1

    for (nid, pl) in list(npcs.items()):
        if npcs[nid]['room'] == targetRoom:
            playersCtr += 1

    return playersCtr


def _room_requires_light_source(players: {}, id, rooms: {}) -> bool:
    """Returns true if the room requires a light source
    """
    rid = players[id]['room']
    if not rooms[rid]['conditional']:
        return False
    for cond in rooms[rid]['conditional']:
        if len(cond) > 2:
            if cond[0].lower() == 'hold' and \
               cond[1].lower() == 'lightsource':
                return True
    return False


def _light_source_in_room(players: {}, id, items: {}, items_db: {}) -> bool:
    """Returns true if there is a light source in the room
    """
    for i in items:
        if items[i]['room'].lower() != players[id]['room']:
            continue
        if items_db[items[i]['id']]['lightSource'] != 0:
            return True
    return False


def _item_is_visible(observerId: int, players: {},
                     itemId: int, items_db: {}) -> bool:
    """Is the item visible to the observer?
    """
    itemId = int(itemId)
    if not items_db[itemId].get('visibleWhenWearing'):
        return True
    if is_wearing(observerId, players,
                  items_db[itemId]['visibleWhenWearing']):
        return True
    return False


def _item_is_climbable(climberId: int, players: {},
                       itemId: int, items_db: {}) -> bool:
    """Is the item climbable by the player?
    """
    itemId = int(itemId)
    if not items_db[itemId].get('climbWhenWearing'):
        return True
    if is_wearing(climberId, players,
                  items_db[itemId]['climbWhenWearing']):
        return True
    return False


def _room_illumination(roomImage, outdoors: bool):
    """Alters the brightness and contrast of the image to simulate
    evening and night conditions
    """
    if not outdoors:
        return roomImage
    currTime = datetime.datetime.today()
    currHour = currTime.hour
    sun = get_solar()
    sunRiseTime = sun.get_local_sunrise_time(currTime).hour
    sunSetTime = sun.get_local_sunset_time(currTime).hour
    if currHour > sunRiseTime+1 and currHour < sunSetTime-1:
        return roomImage
    brightness = 60
    colorVariance = 80
    if currHour < sunRiseTime or currHour > sunSetTime:
        brightness = 30
    # extra dark
    if currHour < (sunRiseTime-2) or currHour > (sunSetTime+2):
        colorVariance = 50

    brightness += moon_illumination(currTime)
    pixels = roomImage.split('[')

    averageIntensity = 0
    averageIntensityCtr = 0
    for p in pixels:
        values = p.split(';')
        if len(values) != 5:
            continue
        values[4] = values[4].split('m')[0]
        ctr = 0
        for v in values:
            if ctr > 1:
                averageIntensity += int(v)
                averageIntensityCtr += 1
            ctr += 1
    averageIntensity /= averageIntensityCtr
    newAverageIntensity = int(averageIntensity * brightness / 100)
    # minimum average illumination
    if newAverageIntensity < 20:
        newAverageIntensity = 20

    newRoomImage = ''
    trailing = None
    firstValue = True
    for p in pixels:
        if firstValue:
            newRoomImage += p + '['
            firstValue = False
            continue
        values = p.split(';')
        if len(values) != 5:
            newRoomImage += p + '['
            continue
        trailing = values[4].split('m')[1]
        values[4] = values[4].split('m')[0]
        ctr = 0
        for v in values:
            if ctr > 1:
                # difference from average illumination
                diff = int(int(v) - averageIntensity)
                # reduce color variance
                variance = colorVariance
                # reduce blue by more than other channels
                if ctr == 2:
                    variance = int(colorVariance / 4)
                v = int(newAverageIntensity + (diff * variance / 100))
                if v < 0:
                    v = 0
                elif v > 255:
                    v = 255
            values[ctr] = int(v)
            ctr += 1
        darkStr = trailing + '['
        darkStr = ''
        ctr = 0
        for v in values:
            if ctr < 4:
                darkStr += str(v) + ';'
            else:
                darkStr += str(v) + 'm'
            ctr += 1
        newRoomImage += darkStr+trailing + '['
    return newRoomImage[:len(newRoomImage) - 1]


def _show_room_image(mud, id, roomId, rooms: {}, players: {},
                     items: {}, items_db: {},
                     clouds: {}, map_area: []) -> None:
    """Shows an image for the room if it exists
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    conditionalImage = \
        _conditional_room_image(rooms[roomId]['conditional'],
                                id, players, items,
                                items_db, clouds,
                                map_area, rooms)
    outdoors = False
    if rooms[roomId]['weather'] == 1:
        outdoors = True
    if not conditionalImage:
        roomIdStr = str(roomId).replace('rid=', '').replace('$', '')
    else:
        roomIdStr = conditionalImage
    roomImageFilename = 'images/rooms/' + roomIdStr
    if os.path.isfile(roomImageFilename + '_night'):
        currTime = datetime.datetime.today()
        sun = get_solar()
        sunRiseTime = sun.get_local_sunrise_time(currTime).hour
        sunSetTime = sun.get_local_sunset_time(currTime).hour
        if currTime.hour < sunRiseTime or \
           currTime.hour > sunSetTime:
            roomImageFilename = roomImageFilename + '_night'
            outdoors = False
    if not os.path.isfile(roomImageFilename):
        return
    with open(roomImageFilename, 'r') as roomFile:
        roomImageStr = roomFile.read()
        mud.send_image(id, '\n' + _room_illumination(roomImageStr, outdoors))


def _show_spell_image(mud, id, spellId, players: {}) -> None:
    """Shows an image for a spell
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    spellImageFilename = 'images/spells/' + spellId
    if not os.path.isfile(spellImageFilename):
        return
    with open(spellImageFilename, 'r') as spellFile:
        mud.send_image(id, '\n' + spellFile.read())


def _show_item_image(mud, id, itemId, roomId, rooms: {}, players: {},
                     items: {}, items_db: {},
                     clouds: {}, map_area: [], lookModifier: str) -> None:
    """Shows an image for the item if it exists
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    itemIdStr = \
        _conditional_item_image(itemId,
                                items_db[itemId]['conditional'],
                                id, players, items,
                                items_db, clouds,
                                map_area, rooms, lookModifier)

    # fixed items can have their illumination changed if they are outdoors
    outdoors = False
    if items_db[itemId]['weight'] == 0:
        if rooms[roomId]['weather'] == 1:
            outdoors = True

    itemImageFilename = 'images/items/' + itemIdStr
    if os.path.isfile(itemImageFilename + '_night'):
        currTime = datetime.datetime.today()
        sun = get_solar()
        sunRiseTime = sun.get_local_sunrise_time(currTime).hour
        sunSetTime = sun.get_local_sunset_time(currTime).hour
        if currTime.hour < sunRiseTime or \
           currTime.hour > sunSetTime:
            itemImageFilename = itemImageFilename + '_night'
            outdoors = False
    if not os.path.isfile(itemImageFilename):
        return
    with open(itemImageFilename, 'r') as itemFile:
        itemImageStr = itemFile.read()
        mud.send_image(id, '\n' + _room_illumination(itemImageStr, outdoors))


def _show_npc_image(mud, id, npcName, players: {}) -> None:
    """Shows an image for a NPC
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    npcImageFilename = 'images/npcs/' + npcName.replace(' ', '_')
    if not os.path.isfile(npcImageFilename):
        return
    with open(npcImageFilename, 'r') as npcFile:
        mud.send_image(id, '\n' + npcFile.read())


def _get_room_exits(mud, rooms: {}, players: {}, id) -> {}:
    """Returns a dictionary of exits for the given player
    """
    rm = rooms[players[id]['room']]
    exits = rm['exits']

    if rm.get('tideOutExits'):
        if run_tide() < 0.0:
            for direction, room_id in rm['tideOutExits'].items():
                exits[direction] = room_id
        else:
            for direction, room_id in rm['tideOutExits'].items():
                if exits.get(direction):
                    del rm['exits'][direction]

    if rm.get('exitsWhenWearing'):
        directionsAdded = []
        for ex in rm['exitsWhenWearing']:
            if len(ex) < 3:
                continue
            direction = ex[0]
            itemID = ex[1]
            if is_wearing(id, players, [itemID]):
                room_id = ex[2]
                exits[direction] = room_id
                # keep track of directions added via wearing items
                if direction not in directionsAdded:
                    directionsAdded.append(direction)
            else:
                if exits.get(direction):
                    # only remove if the direction was not previously added
                    # via another item
                    if direction not in directionsAdded:
                        del rm['exits'][direction]
    return exits


def _item_in_player_room(players: {}, id, items: {}, itemId: int) -> bool:
    """Returns true if the given item is in the given room
    """
    return items[itemId]['room'].lower() == players[id]['room']


def _look(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['canLook'] == 1:
        if len(params) < 1:
            # If no arguments are given, then look around and describe
            # surroundings

            # store the player's current room
            rm = rooms[players[id]['room']]

            # send the player back the description of their current room
            playerRoomId = players[id]['room']
            _show_room_image(mud, id, playerRoomId,
                             rooms, players, items,
                             items_db, clouds, map_area)
            roomDescription = \
                _conditional_room_desc(rm['description'],
                                       rm['tideOutDescription'],
                                       rm['conditional'],
                                       id, players, items, items_db,
                                       clouds, map_area, rooms)

            if rm['trap'].get('trap_activation') and \
               rm['trap'].get('trapPerception'):
                if randint(1, players[id]['per']) > \
                   rm['trap']['trapPerception']:
                    if rm['trap']['trapType'].startswith('dart') and \
                       randint(0, 1) == 1:
                        roomDescription += \
                            random_desc(" You notice some tiny " +
                                        "holes in the wall.| " +
                                        "There are some small " +
                                        "holes in the wall.|You " +
                                        "observe some tiny holes" +
                                        " in the wall.")
                    else:
                        if rm['trap']['trap_activation'] == 'tripwire':
                            roomDescription += \
                                random_desc(" A tripwire is " +
                                            "carefully set along " +
                                            "the floor.| You notice " +
                                            "a thin wire across " +
                                            "the floor.| An almost " +
                                            "invisible wire runs " +
                                            "along the floor.")
                        trap_act = rm['trap']['trap_activation']
                        if trap_act.startswith('pressure'):
                            roomDescription += \
                                random_desc(" The faint outline of " +
                                            "a pressure plate can be " +
                                            "seen on the floor.| The " +
                                            "outline of a pressure " +
                                            "plate is visible on " +
                                            "the floor.")

            mud.send_message_wrap(id, '<f230>',
                                  "****CLEAR****<f230>" +
                                  roomDescription.strip())
            playershere = []

            itemshere = []

            # go through every player in the game
            for (pid, pl) in list(players.items()):
                # if they're in the same room as the player
                if players[pid]['room'] == players[id]['room']:
                    # ... and they have a name to be shown
                    if players[pid]['name'] is not None and \
                       players[pid]['name'] is not players[id]['name']:
                        if player_is_visible(mud, id, players, pid, players):
                            # add their name to the list
                            if players[pid]['prefix'] == "None":
                                playershere.append(players[pid]['name'])
                            else:
                                playershere.append(
                                    "[" + players[pid]['prefix'] + "] " +
                                    players[pid]['name'])

            # Show corpses in the room
            for (corpse, pl) in list(corpses.items()):
                if corpses[corpse]['room'] == players[id]['room']:
                    playershere.append(corpses[corpse]['name'])

            # Show NPCs in the room
            for nid in npcs:
                if npcs[nid]['room'] == players[id]['room']:
                    # Don't show hidden familiars
                    if (npcs[nid]['familiarMode'] != 'hide' or
                        (len(npcs[nid]['familiarOf']) > 0 and
                         npcs[nid]['familiarOf'] == players[id]['name'])):
                        if player_is_visible(mud, id, players, nid, npcs):
                            playershere.append(npcs[nid]['name'])

            # Show items in the room
            for (item, pl) in list(items.items()):
                if _item_in_player_room(players, id, items, item):
                    if _item_is_visible(id, players, items[item]['id'],
                                        items_db):
                        if items_db[items[item]['id']]['hidden'] == 0:
                            itemshere.append(
                                items_db[items[item]['id']]['article'] + ' ' +
                                items_db[items[item]['id']]['name'])

            # send player a message containing the list of players in the room
            if len(playershere) > 0:
                mud.send_message(
                    id,
                    '<f230>You see: <f220>{}'.format(', '.join(playershere)))

            # send player a message containing the list of exits from this room
            roomExitsStr = _get_room_exits(mud, rooms, players, id)
            if roomExitsStr:
                desc = \
                    '<f230>Exits are: <f220>{}'.format(', '.join(roomExitsStr))
                mud.send_message(id, desc)

            # send player a message containing the list of items in the room
            if len(itemshere) > 0:
                needsLight = _room_requires_light_source(players, id, rooms)
                playersWithLight = False
                if needsLight:
                    playersWithLight = \
                        _holding_light_source(players, id, items, items_db)
                if needsLight is False or \
                   (needsLight is True and playersWithLight is True):
                    desc = '<f230>You notice: ' + \
                        '<f220>{}'.format(', '.join(itemshere))
                    mud.send_message_wrap(id, '<f220>', desc)

            mud.send_message(id, "<r>\n")
        else:
            # look at something or someone
            # If argument is given, then evaluate it
            param = params.lower()

            if param.startswith('my '):
                param = params.replace('my ', '', 1)

            # "look under the ..."
            lookModifier = None
            if param.startswith('under '):
                param = params.replace('under ', '', 1)
                lookModifier = 'under'
            elif param.startswith('below '):
                param = params.replace('below ', '', 1)
                lookModifier = 'under'
            elif param.startswith('behind '):
                param = params.replace('behind ', '', 1)
                lookModifier = 'behind'
            elif param.startswith('above '):
                param = params.replace('above ', '', 1)
                lookModifier = 'above'
            elif param.startswith('on top of '):
                param = params.replace('on top of ', '', 1)
                lookModifier = 'above'

            # replace "familiar" with the name of the familiar
            if param.startswith('familiar'):
                familiarName = get_familiar_name(players, id, npcs)
                if len(familiarName) > 0:
                    param = param.replace('familiar', familiarName, 1)

            if param.startswith('at the '):
                param = param.replace('at the ', '')
            if param.startswith('the '):
                param = param.replace('the ', '')
            if param.startswith('at '):
                param = param.replace('at ', '')
            if param.startswith('a '):
                param = param.replace('a ', '')
            messageSent = False

            # Go through all players in game
            for p in players:
                if players[p]['authenticated'] is not None:
                    if players[p]['name'].lower() == param and \
                       players[p]['room'] == players[id]['room']:
                        if player_is_visible(mud, players, id, p, players):
                            _bio_of_player(mud, id, p, players, items_db)
                            messageSent = True

            message = ""

            # Go through all NPCs in game
            for n in npcs:
                if param in npcs[n]['name'].lower() and \
                   npcs[n]['room'] == players[id]['room']:
                    if player_is_visible(mud, id, players, n, npcs):
                        if npcs[n]['familiarMode'] != 'hide':
                            nameLower = npcs[n]['name'].lower()
                            _show_npc_image(mud, id, nameLower, players)
                            _bio_of_player(mud, id, n, npcs, items_db)
                            messageSent = True
                        else:
                            if npcs[n]['familiarOf'] == players[id]['name']:
                                message = "They are hiding somewhere here."
                                messageSent = True

            if len(message) > 0:
                mud.send_message(id, "****CLEAR****" + message + "\n\n")
                messageSent = True

            message = ""

            # Go through all Items in game
            itemCounter = 0
            for i in items:
                if _item_in_player_room(players, id, items, i) and \
                   param in items_db[items[i]['id']]['name'].lower():
                    if _item_is_visible(id, players, items[i]['id'], items_db):
                        if itemCounter == 0:
                            itemLanguage = items_db[items[i]['id']]['language']
                            thisItemID = int(items[i]['id'])
                            idx = items[i]['id']
                            if items_db[idx].get('itemName'):
                                message += \
                                    'Name: ' + items_db[idx]['itemName'] + '\n'
                            condDesc = []
                            if items_db[idx].get('conditional'):
                                condDesc = items_db[idx]['conditional']
                            desc = \
                                _conditional_item_desc(idx, condDesc,
                                                       id, players,
                                                       items, items_db,
                                                       clouds, map_area,
                                                       rooms, lookModifier)
                            message += random_desc(desc)
                            message += \
                                _describe_container_contents(mud, id,
                                                             items_db,
                                                             items[i]['id'],
                                                             True)
                            if len(itemLanguage) == 0:
                                roomId = players[id]['room']
                                _show_item_image(mud, id, idx,
                                                 roomId, rooms, players,
                                                 items, items_db,
                                                 clouds, map_area,
                                                 lookModifier)
                            else:
                                if itemLanguage in players[id]['language']:
                                    roomId = players[id]['room']
                                    _show_item_image(mud, id, idx,
                                                     roomId, rooms, players,
                                                     items, items_db,
                                                     clouds, map_area,
                                                     lookModifier)
                                else:
                                    message += \
                                        "It's written in " + itemLanguage
                            itemName = \
                                items_db[items[i]['id']]['article'] + \
                                " " + items_db[items[i]['id']]['name']
                        itemCounter += 1

            # Examine items in inventory
            if len(message) == 0:
                playerinv = list(players[id]['inv'])
                if len(playerinv) > 0:
                    # check for exact match of item name
                    invItemFound = False
                    for i in playerinv:
                        thisItemID = int(i)
                        items_dbEntry = items_db[thisItemID]
                        if param == items_dbEntry['name'].lower():
                            itemLanguage = items_dbEntry['language']
                            roomId = players[id]['room']
                            _show_item_image(mud, id, thisItemID,
                                             roomId, rooms, players,
                                             items, items_db,
                                             clouds, map_area, None)
                            if len(itemLanguage) == 0:
                                condDesc = []
                                if items_dbEntry.get('conditional'):
                                    condDesc = items_dbEntry['conditional']
                                desc = \
                                    _conditional_item_desc(thisItemID,
                                                           condDesc,
                                                           id, players,
                                                           items, items_db,
                                                           clouds,
                                                           map_area,
                                                           rooms, None)
                                message += random_desc(desc)
                                message += \
                                    _describe_container_contents(
                                        mud, id, items_db, thisItemID, True)
                            else:
                                if itemLanguage in players[id]['language']:
                                    condDesc = []
                                    if items_dbEntry.get('conditional'):
                                        condDesc = items_dbEntry['conditional']
                                    desc = \
                                        _conditional_item_desc(thisItemID,
                                                               condDesc,
                                                               id,
                                                               players,
                                                               items,
                                                               items_db,
                                                               clouds,
                                                               map_area,
                                                               rooms, None)
                                    message += random_desc(desc)
                                    message += \
                                        _describe_container_contents(
                                            mud, id, items_db, thisItemID,
                                            True)
                                else:
                                    message += \
                                        "It's written in " + itemLanguage
                            itemName = \
                                items_dbEntry['article'] + " " + \
                                items_dbEntry['name']
                            invItemFound = True
                            break
                    if not invItemFound:
                        # check for partial match of item name
                        for i in playerinv:
                            thisItemID = int(i)
                            items_dbEntry = items_db[thisItemID]
                            if param in items_dbEntry['name'].lower():
                                itemLanguage = items_dbEntry['language']
                                roomId = players[id]['room']
                                _show_item_image(mud, id, thisItemID,
                                                 roomId, rooms, players,
                                                 items, items_db,
                                                 clouds, map_area, None)
                                if len(itemLanguage) == 0:
                                    condDesc = []
                                    if items_dbEntry.get('conditional'):
                                        condDesc = items_dbEntry['conditional']
                                    desc = \
                                        _conditional_item_desc(thisItemID,
                                                               condDesc,
                                                               id,
                                                               players,
                                                               items,
                                                               items_db,
                                                               clouds,
                                                               map_area,
                                                               rooms, None)
                                    message += random_desc(desc)
                                    message += \
                                        _describe_container_contents(
                                            mud, id, items_db, thisItemID,
                                            True)
                                else:
                                    if itemLanguage in players[id]['language']:
                                        condDesc = []
                                        if items_dbEntry.get('conditional'):
                                            condDesc = \
                                                items_dbEntry['conditional']
                                        desc = \
                                            _conditional_item_desc(thisItemID,
                                                                   condDesc,
                                                                   id,
                                                                   players,
                                                                   items,
                                                                   items_db,
                                                                   clouds,
                                                                   map_area,
                                                                   rooms, None)
                                        message += random_desc(desc)
                                        message += \
                                            _describe_container_contents(
                                                mud, id, items_db,
                                                thisItemID, True)
                                    else:
                                        message += \
                                            "It's written in " + itemLanguage

                                itemName = \
                                    items_dbEntry['article'] + " " + \
                                    items_dbEntry['name']
                                break

            if len(message) > 0:
                mud.send_message(id, "****CLEAR****It's " + itemName + ".")
                mud.send_message_wrap(id, '', message + "<r>\n\n")
                messageSent = True
                if itemCounter > 1:
                    mud.send_message(
                        id, "You can see " +
                        str(itemCounter) +
                        " of those in the vicinity.<r>\n\n")

            # If no message has been sent, it means no player/npc/item was
            # found
            if not messageSent:
                mud.send_message(id, "Look at what?<r>\n")
    else:
        mud.send_message(
            id,
            '****CLEAR****' +
            'You somehow cannot muster enough perceptive powers ' +
            'to perceive and describe your immediate surroundings...<r>\n')


def _escape_trap(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcs_db: {}, npcs: {}, items_db: {}, items: {},
                 env_db: {}, env: {}, eventDB: {}, event_schedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 map_area: [], character_class_db: {}, spells_db: {},
                 sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                 item_history: {}, markets: {}, cultures_db: {}):
    if not player_is_trapped(id, players, rooms):
        mud.send_message(
            id, random_desc(
                "You try to escape but find there's nothing to escape from") +
            '\n\n')

    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '\n\n')
        return

    if players[id]['canAttack'] == 1:
        escape_from_trap(mud, id, players, rooms, items_db)


def _begin_attack(params, mud, playersDB: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {},
                  races_db: {}, item_history: {}, markets: {},
                  cultures_db: {}):
    if players[id]['frozenStart'] != 0:
        desc = players[id]['frozenDescription']
        mud.send_message(
            id, random_desc(desc) + '\n\n')
        return

    if players[id]['canAttack'] == 1:
        if player_is_trapped(id, players, rooms):
            mud.send_message(
                id, random_desc(
                    "You're trapped") + '.\n\n')
            return

        if player_is_prone(id, players):
            mud.send_message(id, random_desc('You stand up<r>\n\n'))
            set_player_prone(id, players, False)
            return

        target = params  # .lower()
        if target.startswith('at '):
            target = params.replace('at ', '')
        if target.startswith('the '):
            target = params.replace('the ', '')

        if not is_attacking(players, id, fights):
            player_begins_attack(players, id, target,
                                 npcs, fights, mud, races_db, item_history)
        else:
            currentTarget = get_attacking_target(players, id, fights)
            if not isinstance(currentTarget, int):
                mud.send_message(
                    id, 'You are already attacking ' +
                    currentTarget + "\n")
            else:
                mud.send_message(
                    id, 'You are already attacking ' +
                    npcs[currentTarget]['name'] + "\n")

        # List fights for debugging purposes
        # for x in fights:
            # print (x)
            # for y in fights[x]:
                # print (y,':',fights[x][y])
    else:
        mud.send_message(
            id,
            'Right now, you do not feel like you can force ' +
            'yourself to attack anyone or anything.\n')


def _item_in_inventory(players: {}, id, itemName: str, items_db: {}):
    """Is the named item in the player inventory?
    """
    if len(list(players[id]['inv'])) > 0:
        itemNameLower = itemName.lower()
        for i in list(players[id]['inv']):
            if items_db[int(i)]['name'].lower() == itemNameLower:
                return True
    return False


def _describe(params, mud, playersDB: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {},
              env_db: {}, env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return

    if '"' not in params:
        mud.send_message(
            id, 'Descriptions need to be within double quotes.\n\n')
        return

    descriptionStrings = re.findall('"([^"]*)"', params)
    if len(descriptionStrings) == 0:
        mud.send_message(
            id, 'Descriptions need to be within double quotes.\n\n')
        return

    if len(descriptionStrings[0].strip()) < 3:
        mud.send_message(id, 'Description is too short.\n\n')
        return

    rm = players[id]['room']
    if len(descriptionStrings) == 1:
        rooms[rm]['description'] = descriptionStrings[0]
        mud.send_message(id, 'Room description set.\n\n')
        save_universe(rooms, npcs_db, npcs,
                      items_db, items, env_db,
                      env, guilds_db)
        return

    if len(descriptionStrings) == 2:
        thingDescribed = descriptionStrings[0].lower()
        thingDescription = descriptionStrings[1]

        if len(thingDescription) < 3:
            mud.send_message(
                id, 'Description of ' +
                descriptionStrings[0] +
                ' is too short.\n\n')
            return

        if thingDescribed == 'name':
            rooms[rm]['name'] = thingDescription
            mud.send_message(
                id, 'Room name changed to ' +
                thingDescription + '.\n\n')
            save_universe(rooms, npcs_db, npcs,
                          items_db, items, env_db,
                          env, guilds_db)
            return

        if thingDescribed == 'tide':
            rooms[rm]['tideOutDescription'] = thingDescription
            mud.send_message(id, 'Tide out description set.\n\n')
            save_universe(rooms, npcs_db, npcs,
                          items_db, items,
                          env_db, env, guilds_db)
            return

        # change the description of an item in the room
        for (item, pl) in list(items.items()):
            if items[item]['room'] == players[id]['room']:
                idx = items[item]['id']
                if thingDescribed in items_db[idx]['name'].lower():
                    items_db[idx]['long_description'] = thingDescription
                    mud.send_message(id, 'New description set for ' +
                                     items_db[idx]['article'] +
                                     ' ' + items_db[idx]['name'] +
                                     '.\n\n')
                    save_universe(
                        rooms, npcs_db, npcs, items_db,
                        items, env_db, env, guilds_db)
                    return

        # Change the description of an NPC in the room
        for (nid, pl) in list(npcs.items()):
            if npcs[nid]['room'] == players[id]['room']:
                if thingDescribed in npcs[nid]['name'].lower():
                    npcs[nid]['lookDescription'] = thingDescription
                    mud.send_message(
                        id, 'New description set for ' +
                        npcs[nid]['name'] + '.\n\n')
                    save_universe(
                        rooms, npcs_db, npcs, items_db,
                        items, env_db, env, guilds_db)
                    return

    if len(descriptionStrings) == 3:
        if descriptionStrings[0].lower() != 'name':
            mud.send_message(id, "I don't understand.\n\n")
            return
        thingDescribed = descriptionStrings[1].lower()
        thingName = descriptionStrings[2]
        if len(thingName) < 3:
            mud.send_message(
                id, 'Description of ' +
                descriptionStrings[1] +
                ' is too short.\n\n')
            return

        # change the name of an item in the room
        for (item, pl) in list(items.items()):
            if items[item]['room'] == players[id]['room']:
                idx = items[item]['id']
                if thingDescribed in items_db[idx]['name'].lower():
                    items_db[idx]['name'] = thingName
                    mud.send_message(id, 'New description set for ' +
                                     items_db[idx]['article'] +
                                     ' ' +
                                     items_db[idx]['name'] +
                                     '.\n\n')
                    save_universe(
                        rooms, npcs_db, npcs, items_db,
                        items, env_db, env, guilds_db)
                    return

        # Change the name of an NPC in the room
        for (nid, pl) in list(npcs.items()):
            if npcs[nid]['room'] == players[id]['room']:
                if thingDescribed in npcs[nid]['name'].lower():
                    npcs[nid]['name'] = thingName
                    mud.send_message(
                        id, 'New description set for ' +
                        npcs[nid]['name'] + '.\n\n')
                    save_universe(
                        rooms, npcs_db, npcs, items_db,
                        items, env_db, env, guilds_db)
                    return


def _check_inventory(params, mud, playersDB: {}, players: {}, rooms: {},
                     npcs_db: {}, npcs: {}, items_db: {}, items: {},
                     env_db: {}, env: {}, eventDB: {}, event_schedule,
                     id: int, fights: {}, corpses: {}, blocklist,
                     map_area: [], character_class_db: {}, spells_db: {},
                     sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                     item_history: {}, markets: {}, cultures_db: {}):
    mud.send_message(id, '****CLEAR****You check your inventory.')

    room_id = players[id]['room']
    _show_items_for_sale(mud, rooms, room_id, players, id, items_db)

    if len(list(players[id]['inv'])) == 0:
        mud.send_message(id, 'You haven`t got any items on you.<r>\n\n')
        return

    mud.send_message(id, 'You are currently in possession of:<r>\n')
    for i in list(players[id]['inv']):
        if int(players[id]['clo_lhand']) == int(i):
            mud.send_message(id, ' * ' +
                             items_db[int(i)]['article'] +
                             ' <b234>' +
                             items_db[int(i)]['name'] +
                             '<r> (left hand)')
            continue

        if int(players[id]['clo_lleg']) == int(i):
            mud.send_message(id, ' * ' +
                             items_db[int(i)]['article'] +
                             ' <b234>' +
                             items_db[int(i)]['name'] +
                             '<r> (left leg)')
            continue

        if int(players[id]['clo_rleg']) == int(i):
            mud.send_message(id, ' * ' +
                             items_db[int(i)]['article'] +
                             ' <b234>' +
                             items_db[int(i)]['name'] +
                             '<r> (right leg)')
            continue

        if players[id].get('clo_gloves'):
            if int(players[id]['clo_gloves']) == int(i):
                mud.send_message(id, ' * ' +
                                 items_db[int(i)]['article'] +
                                 ' <b234>' +
                                 items_db[int(i)]['name'] +
                                 '<r> (hands)')
                continue

        if int(players[id]['clo_rhand']) == int(i):
            mud.send_message(id, ' * ' +
                             items_db[int(i)]['article'] +
                             ' <b234>' +
                             items_db[int(i)]['name'] +
                             '<r> (right hand)')
            continue

        if int(players[id]['clo_lfinger']) == int(i):
            mud.send_message(id, ' * ' +
                             items_db[int(i)]['article'] +
                             ' <b234>' +
                             items_db[int(i)]['name'] +
                             '<r> (finger of left hand)')
            continue

        if int(players[id]['clo_rfinger']) == int(i):
            mud.send_message(id, ' * ' +
                             items_db[int(i)]['article'] +
                             ' <b234>' +
                             items_db[int(i)]['name'] +
                             '<r> (finger of right hand)')
            continue

        if int(players[id]['clo_waist']) == int(i):
            mud.send_message(id, ' * ' +
                             items_db[int(i)]['article'] +
                             ' <b234>' +
                             items_db[int(i)]['name'] +
                             '<r> (waist)')
            continue

        if int(players[id]['clo_lear']) == int(i):
            mud.send_message(id, ' * ' +
                             items_db[int(i)]['article'] +
                             ' <b234>' +
                             items_db[int(i)]['name'] +
                             '<r> (left ear)')
            continue

        if int(players[id]['clo_rear']) == int(i):
            mud.send_message(id, ' * ' +
                             items_db[int(i)]['article'] +
                             ' <b234>' +
                             items_db[int(i)]['name'] +
                             '<r> (right ear)')
            continue

        if int(players[id]['clo_head']) == int(i) or \
           int(players[id]['clo_lwrist']) == int(i) or \
           int(players[id]['clo_rwrist']) == int(i) or \
           int(players[id]['clo_larm']) == int(i) or \
           int(players[id]['clo_rarm']) == int(i) or \
           int(players[id]['clo_gloves']) == int(i) or \
           int(players[id]['clo_lfinger']) == int(i) or \
           int(players[id]['clo_rfinger']) == int(i) or \
           int(players[id]['clo_neck']) == int(i) or \
           int(players[id]['clo_chest']) == int(i) or \
           int(players[id]['clo_back']) == int(i) or \
           int(players[id]['clo_feet']) == int(i):
            mud.send_message(id, ' * ' +
                             items_db[int(i)]['article'] +
                             ' <b234>' +
                             items_db[int(i)]['name'] +
                             '<r> (worn)')
            continue

        mud.send_message(id, ' * ' +
                         items_db[int(i)]['article'] +
                         ' <b234>' +
                         items_db[int(i)]['name'])
    mud.send_message(id, '<r>\n\n')


def _change_setting(params, mud, playersDB: {}, players: {}, rooms: {},
                    npcs_db: {}, npcs: {}, items_db: {}, items: {},
                    env_db: {}, env: {}, eventDB: {}, event_schedule,
                    id: int, fights: {}, corpses: {}, blocklist,
                    map_area: [], character_class_db: {}, spells_db: {},
                    sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                    item_history: {}, markets: {}, cultures_db: {}):
    newPassword = ''
    if params.startswith('password '):
        newPassword = params.replace('password ', '')
    if params.startswith('pass '):
        newPassword = params.replace('pass ', '')
    if len(newPassword) > 0:
        if len(newPassword) < 6:
            mud.send_message(id, "That password is too short.\n\n")
            return
        players[id]['pwd'] = hash_password(newPassword)
        log("Player " + players[id]['name'] +
            " changed their password", "info")
        save_state(players[id], playersDB, True)
        mud.send_message(id, "Your password has been changed.\n\n")


def _write_on_item(params, mud, playersDB: {}, players: {}, rooms: {},
                   npcs_db: {}, npcs: {}, items_db: {}, items: {},
                   env_db: {}, env: {}, eventDB: {}, event_schedule,
                   id: int, fights: {}, corpses: {}, blocklist,
                   map_area: [], character_class_db: {}, spells_db: {},
                   sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                   item_history: {}, markets: {}, cultures_db: {}):
    if ' on ' not in params:
        if ' onto ' not in params:
            if ' in ' not in params:
                if ' using ' not in params:
                    if ' with ' not in params:
                        mud.send_message(id, 'What?\n\n')
                        return
    msg = ''
    if ' using ' not in params:
        msg = params.split(' using ')[0].remove('"')
    if ' with ' not in params:
        msg = params.split(' with ')[0].remove('"')

    if len(msg) == 0:
        return
    if len(msg) > 64:
        mud.send_message(id, 'That message is too long.\n\n')


def _check(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {},
           env_db: {}, env: {}, eventDB: {}, event_schedule,
           id: str, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    if params.lower() == 'inventory' or \
       params.lower() == 'inv':
        _check_inventory(params, mud, playersDB, players,
                         rooms, npcs_db, npcs, items_db, items,
                         env_db, env, eventDB, event_schedule,
                         id, fights, corpses, blocklist,
                         map_area, character_class_db, spells_db,
                         sentiment_db, guilds_db, clouds, races_db,
                         item_history, markets, cultures_db)
    elif params.lower() == 'stats':
        mud.send_message(id, 'You check your character sheet.\n')
    else:
        mud.send_message(id, 'Check what?\n')


def _wear(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '\n\n')
        return

    if len(params) < 1:
        mud.send_message(id, 'Specify an item from your inventory.\n\n')
        return

    if len(list(players[id]['inv'])) == 0:
        mud.send_message(id, 'You are not carrying that.\n\n')
        return

    itemName = params.lower()
    if itemName.startswith('the '):
        itemName = itemName.replace('the ', '')
    if itemName.startswith('my '):
        itemName = itemName.replace('my ', '')
    if itemName.startswith('your '):
        itemName = itemName.replace('your ', '')

    itemID = 0
    for i in list(players[id]['inv']):
        if items_db[int(i)]['name'].lower() == itemName:
            itemID = int(i)

    if itemID == 0:
        for i in list(players[id]['inv']):
            if itemName in items_db[int(i)]['name'].lower():
                itemID = int(i)

    if itemID == 0:
        mud.send_message(id, itemName + " is not in your inventory.\n\n")
        return

    for clothingType in wear_location:
        if _wear_clothing(itemID, players, id, clothingType, mud, items_db):
            return

    mud.send_message(id, "You can't wear that\n\n")


def _wield(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {},
           env_db: {}, env: {}, eventDB: {}, event_schedule: {},
           id: int, fights: {}, corpses: {}, blocklist: {},
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '\n\n')
        return

    if len(params) < 1:
        mud.send_message(id, 'Specify an item from your inventory.\n\n')
        return

    if len(list(players[id]['inv'])) == 0:
        mud.send_message(id, 'You are not carrying that.\n\n')
        return

    itemName = params.lower()
    itemHand = 1
    if itemName.startswith('the '):
        itemName = itemName.replace('the ', '')
    if itemName.startswith('my '):
        itemName = itemName.replace('my ', '')
    if itemName.startswith('your '):
        itemName = itemName.replace('your ', '')
    if itemName.endswith(' on left hand'):
        itemName = itemName.replace(' on left hand', '')
        itemHand = 0
    if itemName.endswith(' in left hand'):
        itemName = itemName.replace(' in left hand', '')
        itemHand = 0
    if itemName.endswith(' in my left hand'):
        itemName = itemName.replace(' in my left hand', '')
        itemHand = 0
    if itemName.endswith(' in your left hand'):
        itemName = itemName.replace(' in your left hand', '')
        itemHand = 0
    if itemName.endswith(' left'):
        itemName = itemName.replace(' left', '')
        itemHand = 0
    if itemName.endswith(' in left'):
        itemName = itemName.replace(' in left', '')
        itemHand = 0
    if itemName.endswith(' on left'):
        itemName = itemName.replace(' on left', '')
        itemHand = 0
    if itemName.endswith(' on right hand'):
        itemName = itemName.replace(' on right hand', '')
        itemHand = 1
    if itemName.endswith(' in right hand'):
        itemName = itemName.replace(' in right hand', '')
        itemHand = 1
    if itemName.endswith(' in my right hand'):
        itemName = itemName.replace(' in my right hand', '')
        itemHand = 1
    if itemName.endswith(' in your right hand'):
        itemName = itemName.replace(' in your right hand', '')
        itemHand = 1
    if itemName.endswith(' right'):
        itemName = itemName.replace(' right', '')
        itemHand = 1
    if itemName.endswith(' in right'):
        itemName = itemName.replace(' in right', '')
        itemHand = 1
    if itemName.endswith(' on right'):
        itemName = itemName.replace(' on right', '')
        itemHand = 1

    itemID = 0
    for i in list(players[id]['inv']):
        if items_db[int(i)]['name'].lower() == itemName:
            itemID = int(i)

    if itemID == 0:
        for i in list(players[id]['inv']):
            if itemName in items_db[int(i)]['name'].lower():
                itemID = int(i)

    if itemID == 0:
        mud.send_message(id, itemName + " is not in your inventory.\n\n")
        return

    if items_db[itemID]['clo_lhand'] == 0 and \
       items_db[itemID]['clo_rhand'] == 0:
        mud.send_message(id, "You can't hold that.\n\n")
        return

    # items stowed on legs
    if int(players[id]['clo_lleg']) == itemID:
        players[id]['clo_lleg'] = 0
    if int(players[id]['clo_rleg']) == itemID:
        players[id]['clo_rleg'] = 0

    if 'isFishing' in players[id]:
        del players[id]['isFishing']

    if itemHand == 0:
        if int(players[id]['clo_rhand']) == itemID:
            players[id]['clo_rhand'] = 0
        players[id]['clo_lhand'] = itemID
        mud.send_message(id, 'You hold <b234>' +
                         items_db[itemID]['article'] + ' ' +
                         items_db[itemID]['name'] +
                         '<r> in your left hand.\n\n')
    else:
        if int(players[id]['clo_lhand']) == itemID:
            players[id]['clo_lhand'] = 0
        players[id]['clo_rhand'] = itemID
        mud.send_message(id, 'You hold <b234>' +
                         items_db[itemID]['article'] + ' ' +
                         items_db[itemID]['name'] +
                         '<r> in your right hand.\n\n')


def _stow(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    if len(list(players[id]['inv'])) == 0:
        return

    stowFrom = ('clo_lhand', 'clo_rhand')
    for stowLocation in stowFrom:
        itemID = int(players[id][stowLocation])
        if itemID == 0:
            continue
        if int(items_db[itemID]['clo_rleg']) > 0:
            if int(players[id]['clo_rleg']) == 0:
                if int(players[id]['clo_lleg']) != itemID:
                    players[id]['clo_rleg'] = itemID
                    mud.send_message(id, 'You stow <b234>' +
                                     items_db[itemID]['article'] + ' ' +
                                     items_db[itemID]['name'] + '<r>\n\n')
                    players[id][stowLocation] = 0
                    continue

        if int(items_db[itemID]['clo_lleg']) > 0:
            if int(players[id]['clo_lleg']) == 0:
                if int(players[id]['clo_rleg']) != itemID:
                    players[id]['clo_lleg'] = itemID
                    mud.send_message(id, 'You stow <b234>' +
                                     items_db[itemID]['article'] + ' ' +
                                     items_db[itemID]['name'] + '<r>\n\n')
                    players[id][stowLocation] = 0

    stow_hands(id, players, items_db, mud)

    if 'isFishing' in players[id]:
        del players[id]['isFishing']


def _wear_clothing(itemID, players: {}, id, clothingType,
                   mud, items_db: {}) -> bool:
    clothingParam = 'clo_' + clothingType
    if items_db[itemID][clothingParam] > 0:
        players[id][clothingParam] = itemID

        # handle items which are pairs
        if items_db[itemID]['article'] == 'some':
            if clothingType == 'lleg' or clothingType == 'rleg':
                players[id]['clo_lleg'] = itemID
                players[id]['clo_rleg'] = itemID
            elif clothingType == 'lhand' or clothingType == 'rhand':
                players[id]['clo_lhand'] = itemID
                players[id]['clo_rhand'] = itemID

        clothingOpened = False
        if len(items_db[itemID]['open_description']) > 0:
            # there is a special description for wearing
            desc = \
                random_desc(items_db[itemID]['open_description'])
            if ' open' not in items_db[itemID]['open_description']:
                mud.send_message(id, desc + '\n\n')
                clothingOpened = True
        if not clothingOpened:
            # generic weating description
            mud.send_message(
                id,
                'You put on ' +
                items_db[itemID]['article'] +
                ' <b234>' +
                items_db[itemID]['name'] +
                '\n\n')
        return True
    return False


def _remove_clothing(players: {}, id, clothingType, mud, items_db: {}):
    if int(players[id]['clo_' + clothingType]) > 0:
        itemID = int(players[id]['clo_' + clothingType])
        clothingClosed = False
        if len(items_db[itemID]['close_description']) > 0:
            desc = items_db[itemID]['open_description']
            if ' close ' not in desc and \
               'closed' not in desc and \
               'closing' not in desc and \
               'shut' not in desc:
                desc = \
                    random_desc(items_db[itemID]['close_description'])
                mud.send_message(id, desc + '\n\n')
                clothingClosed = True
        if not clothingClosed:
            mud.send_message(id, 'You remove ' +
                             items_db[itemID]['article'] + ' <b234>' +
                             items_db[itemID]['name'] + '\n\n')

        # handle items which are pairs
        if items_db[itemID]['article'] == 'some':
            if clothingType == 'lleg' or clothingType == 'rleg':
                players[id]['clo_lleg'] = 0
                players[id]['clo_rleg'] = 0
            elif clothingType == 'lhand' or clothingType == 'rhand':
                players[id]['clo_lhand'] = 0
                players[id]['clo_rhand'] = 0

        players[id]['clo_' + clothingType] = 0


def _unwear(params, mud, playersDB: {}, players: {}, rooms: {},
            npcs_db: {}, npcs: {}, items_db: {}, items: {},
            env_db: {}, env: {}, eventDB: {}, event_schedule,
            id: int, fights: {}, corpses: {}, blocklist,
            map_area: [], character_class_db: {}, spells_db: {},
            sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}):
    if len(list(players[id]['inv'])) == 0:
        return

    for clothingType in wear_location:
        _remove_clothing(players, id, clothingType, mud, items_db)


def _players_move_together(id, rm, mud,
                           playersDB, players, rooms: {}, npcs_db: {}, npcs,
                           items_db: {}, items: {}, env_db: {},
                           env, eventDB: {}, event_schedule,
                           fights, corpses, blocklist, map_area,
                           character_class_db: {}, spells_db: {},
                           sentiment_db: {}, guilds_db: {}, clouds,
                           races_db: {},
                           item_history: {}, markets: {},
                           cultures_db: {}) -> None:
    """In boats when one player rows the rest move with them
    """
    # go through all the players in the game
    for (pid, pl) in list(players.items()):
        # if player is in the same room and isn't the player
        # sending the command
        if players[pid]['room'] == players[id]['room'] and \
           pid != id:
            players[pid]['room'] = rm

            desc = 'You row to <f106>{}'.format(rooms[rm]['name'])
            mud.send_message(pid, desc + "\n\n")

            _look('', mud, playersDB, players, rooms, npcs_db, npcs,
                  items_db, items, env_db, env, eventDB, event_schedule,
                  pid, fights, corpses, blocklist, map_area,
                  character_class_db, spells_db, sentiment_db, guilds_db,
                  clouds, races_db, item_history, markets, cultures_db)

            if rooms[rm]['eventOnEnter'] != "":
                evID = int(rooms[rm]['eventOnEnter'])
                add_to_scheduler(evID, pid, event_schedule, eventDB)


def _bio_of_player(mud, id, pid, players: {}, items_db: {}) -> None:
    thisPlayer = players[pid]
    if thisPlayer.get('race'):
        if len(thisPlayer['race']) > 0:
            mud.send_message(id, '****CLEAR****<f32>' +
                             thisPlayer['name'] + '<r> (' +
                             thisPlayer['race'] + ' ' +
                             thisPlayer['characterClass'] + ')\n')

    if thisPlayer.get('speakLanguage'):
        mud.send_message(
            id,
            '<f15>Speaks:<r> ' +
            thisPlayer['speakLanguage'] +
            '\n')
    if pid == id:
        if players[id].get('language'):
            if len(players[id]['language']) > 1:
                languagesStr = ''
                langCtr = 0
                for lang in players[id]['language']:
                    if langCtr > 0:
                        languagesStr = languagesStr + ', ' + lang
                    else:
                        languagesStr = languagesStr + lang
                    langCtr += 1
                mud.send_message(id, 'Languages:<r> ' + languagesStr + '\n')

    desc = \
        random_desc(thisPlayer['lookDescription'])
    mud.send_message_wrap(id, '', desc + '<r>\n')

    if thisPlayer.get('canGo'):
        if thisPlayer['canGo'] == 0:
            mud.send_message(id, 'They are frozen.<r>\n')

    # count items of clothing
    wearingCtr = 0
    for c in wear_location:
        if int(thisPlayer['clo_' + c]) > 0:
            wearingCtr += 1

    playerName = 'You'
    playerName2 = 'your'
    playerName3 = 'have'
    if id != pid:
        playerName = 'They'
        playerName2 = 'their'
        playerName3 = 'have'

    if int(thisPlayer['clo_rhand']) > 0:
        handItemID = thisPlayer['clo_rhand']
        itemName = items_db[handItemID]['name']
        if 'right hand ' in itemName:
            itemName = itemName.replace('right hand ', '')
        elif 'right handed ' in itemName:
            itemName = itemName.replace('right handed ', '')
        mud.send_message(id, playerName + ' ' + playerName3 + ' ' +
                         items_db[handItemID]['article'] +
                         ' ' + itemName +
                         ' in ' + playerName2 + ' right hand.<r>\n')
    if thisPlayer.get('clo_rfinger'):
        if int(thisPlayer['clo_rfinger']) > 0:
            mud.send_message(id, playerName + ' ' + playerName3 + ' ' +
                             items_db[thisPlayer['clo_rfinger']]['article'] +
                             ' ' +
                             items_db[thisPlayer['clo_rfinger']]['name'] +
                             ' on the finger of ' + playerName2 +
                             ' right hand.<r>\n')
    if thisPlayer.get('clo_waist'):
        if int(thisPlayer['clo_waist']) > 0:
            mud.send_message(id, playerName + ' ' + playerName3 + ' ' +
                             items_db[thisPlayer['clo_waist']]['article'] +
                             ' ' +
                             items_db[thisPlayer['clo_waist']]['name'] +
                             ' on waist of ' + playerName2 + '<r>\n')
    if int(thisPlayer['clo_lhand']) > 0:
        handItemID = thisPlayer['clo_lhand']
        itemName = items_db[handItemID]['name']
        if 'left hand ' in itemName:
            itemName = itemName.replace('left hand ', '')
        elif 'left handed ' in itemName:
            itemName = itemName.replace('left handed ', '')
        mud.send_message(id, playerName + ' ' + playerName3 + ' ' +
                         items_db[thisPlayer['clo_lhand']]['article'] +
                         ' ' + itemName +
                         ' in ' + playerName2 + ' left hand.<r>\n')
    if int(thisPlayer['clo_lear']) > 0:
        handItemID = thisPlayer['clo_lear']
        itemName = items_db[handItemID]['name']
        mud.send_message(id, playerName + ' ' + playerName3 + ' ' +
                         items_db[thisPlayer['clo_lear']]['article'] +
                         ' ' + itemName +
                         ' in ' + playerName2 + ' left ear.<r>\n')
    if int(thisPlayer['clo_rear']) > 0:
        handItemID = thisPlayer['clo_rear']
        itemName = items_db[handItemID]['name']
        mud.send_message(id, playerName + ' ' + playerName3 + ' ' +
                         items_db[thisPlayer['clo_rear']]['article'] +
                         ' ' + itemName +
                         ' in ' + playerName2 + ' right ear.<r>\n')
    if thisPlayer.get('clo_lfinger'):
        if int(thisPlayer['clo_lfinger']) > 0:
            mud.send_message(id, playerName + ' ' + playerName3 + ' ' +
                             items_db[thisPlayer['clo_lfinger']]['article'] +
                             ' ' +
                             items_db[thisPlayer['clo_lfinger']]['name'] +
                             ' on the finger of ' + playerName2 +
                             ' left hand.<r>\n')

    if wearingCtr > 0:
        wearingMsg = playerName + ' are wearing'
        wearingCtr2 = 0
        for cl in wear_location:
            if not thisPlayer.get('clo_' + cl):
                continue
            clothingItemID = thisPlayer['clo_' + cl]
            if int(clothingItemID) > 0:
                if wearingCtr2 > 0:
                    if wearingCtr2 == wearingCtr - 1:
                        wearingMsg = wearingMsg + ' and '
                    else:
                        wearingMsg = wearingMsg + ', '
                else:
                    wearingMsg = wearingMsg + ' '
                wearingMsg = wearingMsg + \
                    items_db[clothingItemID]['article'] + \
                    ' ' + items_db[clothingItemID]['name']
                if cl == 'neck':
                    wearingMsg = \
                        wearingMsg + ' around ' + playerName2 + ' neck'
                if cl == 'lwrist':
                    wearingMsg = \
                        wearingMsg + ' on ' + playerName2 + ' left wrist'
                if cl == 'rwrist':
                    wearingMsg = \
                        wearingMsg + ' on ' + playerName2 + ' right wrist'
                if cl == 'lleg':
                    wearingMsg = \
                        wearingMsg + ' on ' + playerName2 + ' left leg'
                if cl == 'rleg':
                    wearingMsg = \
                        wearingMsg + ' on ' + playerName2 + ' right leg'
                wearingCtr2 += 1
        mud.send_message(id, wearingMsg + '.<r>\n')

    mud.send_message(id, '<f15>Health status:<r> ' +
                     health_of_player(pid, players) + '.<r>\n')
    mud.send_message(id, '<r>\n')


def _health(params, mud, playersDB: {}, players: {}, rooms: {},
            npcs_db: {}, npcs: {}, items_db: {}, items: {},
            env_db: {}, env: {}, eventDB: {}, event_schedule,
            id: int, fights: {}, corpses: {}, blocklist,
            map_area: [], character_class_db: {}, spells_db: {},
            sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}):
    mud.send_message(id, '<r>\n')
    mud.send_message(id, '<f15>Health status:<r> ' +
                     health_of_player(id, players) + '.<r>\n')


def _bio(params, mud, playersDB: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {},
         env_db: {}, env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    if len(params) == 0:
        _bio_of_player(mud, id, id, players, items_db)
        return

    if params == players[id]['name']:
        _bio_of_player(mud, id, id, players, items_db)
        return

    # go through all the players in the game
    if players[id]['authenticated'] is not None:
        for (pid, pl) in list(players.items()):
            if players[pid]['name'] == params:
                _bio_of_player(mud, id, pid, players, items_db)
                return

    if players[id]['name'].lower() == 'guest':
        mud.send_message(id, "Guest players cannot set a bio.\n\n")
        return

    if players[id]['canSay'] == 0:
        mud.send_message(
            id, "You try to describe yourself, " +
            "but find you have nothing to say.\n\n")
        return

    if '"' in params:
        mud.send_message(id, "Your bio must not include double quotes.\n\n")
        return

    if params.startswith(':'):
        params = params.replace(':', '').strip()

    players[id]['lookDescription'] = params
    mud.send_message(id, "Your bio has been set.\n\n")


def _eat(params, mud, playersDB: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {},
         env_db: {}, env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    food = params.lower()
    foodItemID = 0
    if len(list(players[id]['inv'])) > 0:
        for i in list(players[id]['inv']):
            if food in items_db[int(i)]['name'].lower():
                if items_db[int(i)]['edible'] != 0:
                    foodItemID = int(i)
                    break
                else:
                    mud.send_message(id, "That's not consumable.\n\n")
                    return

    if foodItemID == 0:
        mud.send_message(id, "Your don't have " + params + ".\n\n")
        return

    edibility = items_db[foodItemID]['edible']

    foodStr = \
        items_db[foodItemID]['article'] + " " + items_db[foodItemID]['name']
    if edibility > 1:
        eatStr = "You consume " + foodStr
    else:
        eatStr = \
            random_desc(
                "With extreme reluctance, you eat " + foodStr + '|' +
                "You eat " + foodStr +
                ", but now you wish that you hadn't|" +
                "Revoltingly, you eat " + foodStr)
    mud.send_message(id, eatStr + ".\n\n")

    # Alter hp
    players[id]['hp'] = players[id]['hp'] + edibility
    if players[id]['hp'] > 100:
        players[id]['hp'] = 100

    # Consumed
    players[id]['inv'].remove(str(foodItemID))

    # decrement any attributes associated with the food
    update_player_attributes(id, players, items_db, foodItemID, -1)

    # Remove from hands
    if int(players[id]['clo_rhand']) == foodItemID:
        players[id]['clo_rhand'] = 0
    if int(players[id]['clo_lhand']) == foodItemID:
        players[id]['clo_lhand'] = 0


def _step_over(params, mud, playersDB: {}, players: {}, rooms: {},
               npcs_db: {}, npcs: {}, items_db: {}, items: {},
               env_db: {}, env: {}, eventDB: {}, event_schedule,
               id: int, fights: {}, corpses: {}, blocklist,
               map_area: [], character_class_db: {}, spells_db: {},
               sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
               item_history: {}, markets: {}, cultures_db: {}):
    room_id = players[id]['room']
    if not rooms[room_id]['trap'].get('trap_activation'):
        mud.send_message(
            id, random_desc("You don't notice a tripwire") +
            '.\n\n')
        return
    if rooms[room_id]['trap']['trap_activation'] != 'tripwire':
        mud.send_message(
            id, random_desc(
                "You don't notice a tripwire|You don't see a tripwire") +
            '.\n\n')
        return
    if 'over ' not in params:
        mud.send_message(
            id, random_desc(
                "Do what?|Eh?") + '.\n\n')
        return

    for direction, ex in rooms[room_id]['exits'].items():
        if direction in params:
            _go('######step######' + direction, mud, playersDB, players,
                rooms, npcs_db, npcs, items_db, items, env_db, env, eventDB,
                event_schedule, id, fights, corpses, blocklist, map_area,
                character_class_db, spells_db, sentiment_db, guilds_db,
                clouds, races_db, item_history, markets, cultures_db)
            break


def _climb_base(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                sit: bool, item_history: {}, markets: {}, cultures_db: {}):
    """Climbing through or into an item takes the player to a different room
    """
    if players[id]['canGo'] != 1:
        mud.send_message(id, "You try to move but find that you " +
                         "lack any ability to.\n\n")
        return

    if player_is_prone(id, players):
        mud.send_message(id, random_desc('You stand up<r>\n\n'))
        set_player_prone(id, players, False)
        return

    failMsg = None
    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            itemId = items[item]['id']

            # can the player see the item?
            if not _item_is_visible(id, players, itemId, items_db):
                continue

            # item fields needed for climbing
            if items_db[itemId].get('climbFail'):
                failMsg = items_db[itemId]['climbFail']
            if not items_db[itemId].get('climbThrough'):
                continue
            if not items_db[itemId].get('exit'):
                continue

            # if this is a door is it open?
            if items_db[itemId].get('state'):
                if 'open' not in items_db[itemId]['state']:
                    mud.send_message(id, items_db[itemId]['name'] +
                                     " is closed.\n\n")
                    continue

            # is the player too big?
            targetRoom = items_db[itemId]['exit']
            if rooms[targetRoom]['maxPlayerSize'] > -1:
                if players[id]['siz'] > rooms[targetRoom]['maxPlayerSize']:
                    mud.send_message(id, "You're too big.\n\n")
                    return

            # are there too many players in the room?
            if rooms[targetRoom]['maxPlayers'] > -1:
                if _players_in_room(targetRoom, players, npcs) >= \
                   rooms[targetRoom]['maxPlayers']:
                    if not sit:
                        mud.send_message(id, "It's too crowded.\n\n")
                    else:
                        mud.send_message(id,
                                         "It's already fully occupied.\n\n")
                    return

            if not _item_is_climbable(id, players, itemId, items_db):
                if failMsg:
                    mud.send_message_wrap(id, '<f220>',
                                          random_desc(failMsg) + ".\n\n")
                else:
                    if not sit:
                        failMsg = 'You try to climb, but totally fail'
                    else:
                        failMsg = 'You try to sit, but totally fail'
                    mud.send_message(id, random_desc(failMsg) + ".\n\n")
                return

            if 'isFishing' in players[id]:
                del players[id]['isFishing']

            desc = \
                random_desc(players[id]['outDescription'])
            message_to_room_players(mud, players, id, '<f32>' +
                                    players[id]['name'] + '<r> ' +
                                    desc + '\n')

            # Trigger old room eventOnLeave for the player
            if rooms[players[id]['room']]['eventOnLeave'] != "":
                evLeave = int(rooms[players[id]['room']]['eventOnLeave'])
                add_to_scheduler(evLeave, id, event_schedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = targetRoom
            # climbing message
            desc = \
                random_desc(items_db[itemId]['climbThrough'])
            mud.send_message_wrap(id, '<f230>', desc + "\n\n")
            time.sleep(3)
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] != "":
                evEnter = int(rooms[players[id]['room']]['eventOnEnter'])
                add_to_scheduler(evEnter, id, event_schedule, eventDB)
            # message to other players
            desc = random_desc(players[id]['inDescription'])
            message_to_room_players(mud, players, id, '<f32>' +
                                    players[id]['name'] + '<r> ' +
                                    desc + "\n\n")
            # look after climbing
            _look('', mud, playersDB, players, rooms,
                  npcs_db, npcs, items_db, items,
                  env_db, env, eventDB, event_schedule,
                  id, fights, corpses, blocklist,
                  map_area, character_class_db, spells_db,
                  sentiment_db, guilds_db, clouds, races_db,
                  item_history, markets, cultures_db)
            return
    if failMsg:
        failMsgStr = random_desc(failMsg)
        mud.send_message_wrap(id, '<f220>', failMsgStr + ".\n\n")
    else:
        mud.send_message(id, "Nothing happens.\n\n")


def _climb(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {},
           env_db: {}, env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    _climb_base(params, mud, playersDB, players, rooms,
                npcs_db, npcs, items_db, items,
                env_db, env, eventDB, event_schedule,
                id, fights, corpses, blocklist,
                map_area, character_class_db, spells_db,
                sentiment_db, guilds_db, clouds, races_db,
                False, item_history, markets, cultures_db)


def _sit(params, mud, playersDB: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {},
         env_db: {}, env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    _climb_base(params, mud, playersDB, players, rooms,
                npcs_db, npcs, items_db, items,
                env_db, env, eventDB, event_schedule,
                id, fights, corpses, blocklist,
                map_area, character_class_db, spells_db,
                sentiment_db, guilds_db, clouds, races_db,
                True, item_history, markets, cultures_db)


def _heave(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {},
           env_db: {}, env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    """Roll/heave an item takes the player to a different room
    """
    if players[id]['canGo'] != 1:
        mud.send_message(id, "You try to move but find that " +
                         "you lack any ability to.\n\n")
        return

    if player_is_prone(id, players):
        mud.send_message(id, random_desc('You stand up<r>\n\n'))
        set_player_prone(id, players, False)
        return

    target = params.lower()
    if target.startswith('the '):
        target = target.replace('the ', '')

    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            itemId = items[item]['id']
            if not _item_is_visible(id, players, itemId, items_db):
                continue
            if not items_db[itemId].get('heave'):
                continue
            if not items_db[itemId].get('exit'):
                continue
            if target not in items_db[itemId]['name']:
                continue
            if items_db[itemId].get('state'):
                if 'open' not in items_db[itemId]['state']:
                    mud.send_message(id, items_db[itemId]['name'] +
                                     " is closed.\n\n")
                    continue
            targetRoom = items_db[itemId]['exit']
            if rooms[targetRoom]['maxPlayerSize'] > -1:
                if players[id]['siz'] > rooms[targetRoom]['maxPlayerSize']:
                    mud.send_message(id, "You're too big.\n\n")
                    return
            if rooms[targetRoom]['maxPlayers'] > -1:
                if _players_in_room(targetRoom, players, npcs) >= \
                   rooms[targetRoom]['maxPlayers']:
                    mud.send_message(id, "It's too crowded.\n\n")
                    return
            desc = random_desc(players[id]['outDescription'])
            message_to_room_players(mud, players, id, '<f32>' +
                                    players[id]['name'] + '<r> ' +
                                    desc + '\n')
            # Trigger old room eventOnLeave for the player
            if rooms[players[id]['room']]['eventOnLeave'] != "":
                evLeave = int(rooms[players[id]['room']]['eventOnLeave'])
                add_to_scheduler(evLeave, id, event_schedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = targetRoom
            # heave message
            desc = random_desc(items_db[itemId]['heave'])
            mud.send_message_wrap(id, '<f220>', desc + "\n\n")
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] != "":
                evEnter = int(rooms[players[id]['room']]['eventOnEnter'])
                add_to_scheduler(evEnter, id, event_schedule, eventDB)
            # message to other players
            desc = random_desc(players[id]['inDescription'])
            message_to_room_players(mud, players, id, '<f32>' +
                                    players[id]['name'] + '<r> ' +
                                    desc + "\n\n")
            time.sleep(3)
            # look after climbing
            _look('', mud, playersDB, players, rooms,
                  npcs_db, npcs, items_db, items,
                  env_db, env, eventDB, event_schedule, id,
                  fights, corpses, blocklist,
                  map_area, character_class_db, spells_db,
                  sentiment_db, guilds_db, clouds, races_db,
                  item_history, markets, cultures_db)
            return
    mud.send_message(id, "Nothing happens.\n\n")


def _jump(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    """Jumping onto an item takes the player to a different room
    """
    if players[id]['canGo'] != 1:
        mud.send_message(id, "You try to move but find that you " +
                         "lack any ability to.\n\n")
        return

    if player_is_prone(id, players):
        mud.send_message(id, random_desc('You stand up<r>\n\n'))
        set_player_prone(id, players, False)
        return

    if not params:
        desc = (
            "You jump, expecting something to happen. But it doesn't.",
            "Jumping doesn't help.",
            "You jump. Nothing happens.",
            "In this situation jumping only adds to the confusion.",
            "You jump up and down on the spot.",
            "You jump, and then feel vaguely silly."
        )
        mud.send_message(id, random_desc(desc) + "\n\n")
        return
    words = params.lower().replace('.', '').split(' ')
    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            itemId = items[item]['id']
            if not _item_is_visible(id, players, itemId, items_db):
                continue
            if not items_db[itemId].get('jumpTo'):
                continue
            if not items_db[itemId].get('exit'):
                continue
            wordMatched = False
            for w in words:
                if w in items_db[itemId]['name'].lower():
                    wordMatched = True
                    break
            if not wordMatched:
                continue
            if items_db[itemId].get('state'):
                if 'open' not in items_db[itemId]['state']:
                    mud.send_message(id, items_db[itemId]['name'] +
                                     " is closed.\n\n")
                    continue
            targetRoom = items_db[itemId]['exit']
            if rooms[targetRoom]['maxPlayerSize'] > -1:
                if players[id]['siz'] > rooms[targetRoom]['maxPlayerSize']:
                    mud.send_message(id, "You're too big.\n\n")
                    return
            if rooms[targetRoom]['maxPlayers'] > -1:
                if _players_in_room(targetRoom, players, npcs) >= \
                   rooms[targetRoom]['maxPlayers']:
                    mud.send_message(id, "It's too crowded.\n\n")
                    return
            desc = \
                random_desc(players[id]['outDescription'])
            message_to_room_players(mud, players, id, '<f32>' +
                                    players[id]['name'] + '<r> ' +
                                    desc + '\n')
            # Trigger old room eventOnLeave for the player
            if rooms[players[id]['room']]['eventOnLeave'] != "":
                evLeave = int(rooms[players[id]['room']]['eventOnLeave'])
                add_to_scheduler(evLeave, id, event_schedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = targetRoom
            # climbing message
            desc = random_desc(items_db[itemId]['jumpTo'])
            mud.send_message_wrap(id, '<f230>', desc + "\n\n")
            time.sleep(3)
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] != "":
                evEnter = int(rooms[players[id]['room']]['eventOnEnter'])
                add_to_scheduler(evEnter, id, event_schedule, eventDB)
            # message to other players
            desc = random_desc(players[id]['inDescription'])
            message_to_room_players(mud, players, id, '<f32>' +
                                    players[id]['name'] + '<r> ' +
                                    desc + "\n\n")
            # look after climbing
            _look('', mud, playersDB, players,
                  rooms, npcs_db, npcs, items_db, items,
                  env_db, env, eventDB, event_schedule,
                  id, fights, corpses, blocklist,
                  map_area, character_class_db, spells_db,
                  sentiment_db, guilds_db, clouds, races_db,
                  item_history, markets, cultures_db)
            return
    desc = (
        "You jump, expecting something to happen. But it doesn't.",
        "Jumping doesn't help.",
        "You jump. Nothing happens.",
        "In this situation jumping only adds to the confusion.",
        "You jump up and down on the spot.",
        "You jump, and then feel vaguely silly."
    )
    mud.send_message(id, random_desc(desc) + "\n\n")


def _chess_board_in_room(players: {}, id, rooms: {}, items: {}, items_db: {}):
    """Returns the item ID if there is a chess board in the room
    """
    rid = players[id]['room']
    for i in items:
        if items[i]['room'] != rid:
            continue
        if 'chess' in items_db[items[i]['id']]['game'].lower():
            return i
    return None


def _chess_board_name(players: {}, id, rooms: {}, items: {}, items_db: {}):
    """Returns the name of the chess board if there is one in the room
    This then corresponds to the subdirectory within chessboards, where
    icons exist
    """
    rid = players[id]['room']
    for i in items:
        if items[i]['room'] != rid:
            continue
        if items_db[items[i]['id']].get('chessBoardName'):
            return items_db[items[i]['id']]['chessBoardName']
    return None


def _deal(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    """Deal cards to other players
    """
    paramsLower = params.lower()
    deal_to_players(players, id, paramsLower, mud, rooms, items, items_db)


def _hand_of_cards(params, mud, playersDB: {}, players: {}, rooms: {},
                   npcs_db: {}, npcs: {}, items_db: {}, items: {},
                   env_db: {}, env: {}, eventDB: {}, event_schedule,
                   id: int, fights: {}, corpses: {}, blocklist,
                   map_area: [], character_class_db: {}, spells_db: {},
                   sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                   item_history: {}, markets: {}, cultures_db: {}):
    """Show hand of cards
    """
    hand_of_cards_show(players, id, mud, rooms, items, items_db)


def _swap_a_card(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcs_db: {}, npcs: {}, items_db: {}, items: {},
                 env_db: {}, env: {}, eventDB: {}, event_schedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 map_area: [], character_class_db: {}, spells_db: {},
                 sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                 item_history: {}, markets: {}, cultures_db: {}):
    """Swap a playing card for another from the deck
    """
    swap_card(params, players, id, mud, rooms, items, items_db)


def _shuffle(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {},
             env_db: {}, env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    """Shuffle a deck of cards
    """
    shuffle_cards(players, id, mud, rooms, items, items_db)


def _call_card_game(params, mud, playersDB: {}, players: {}, rooms: {},
                    npcs_db: {}, npcs: {}, items_db: {}, items: {},
                    env_db: {}, env: {}, eventDB: {}, event_schedule,
                    id: int, fights: {}, corpses: {}, blocklist,
                    map_area: [], character_class_db: {}, spells_db: {},
                    sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                    item_history: {}, markets: {}, cultures_db: {}):
    """Players show their cards
    """
    call_cards(players, id, mud, rooms, items, items_db)


def _morris_game(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcs_db: {}, npcs: {}, items_db: {}, items: {},
                 env_db: {}, env: {}, eventDB: {}, event_schedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 map_area: [], character_class_db: {}, spells_db: {},
                 sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                 item_history: {}, markets: {}, cultures_db: {}):
    """Show the nine men's morris board
    """
    params = params.lower()
    if params.startswith('reset') or \
       params.startswith('clear'):
        reset_morris_board(players, id, mud, rooms, items, items_db)
        return

    if params.startswith('take') or \
       params.startswith('remove') or \
       params.startswith('capture'):
        take_morris_counter(params, players, id, mud, rooms, items, items_db)
        return

    if params.startswith('move ') or \
       params.startswith('play ') or \
       params.startswith('put ') or \
       params.startswith('counter ') or \
       params.startswith('place '):
        morris_move(params, players, id, mud, rooms,
                    items, items_db)
        return

    boardName = get_morris_board_name(players, id, rooms, items, items_db)
    show_morris_board(boardName, players, id, mud, rooms, items, items_db)


def _chess(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {},
           env_db: {}, env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    """Jumping onto an item takes the player to a different room
    """
    # check if board exists in room
    boardItemID = \
        _chess_board_in_room(players, id, rooms, items, items_db)
    if not boardItemID:
        mud.send_message(id, "\nThere isn't a chess board here.\n\n")
        return
    # create the game state
    if not items[boardItemID].get('gameState'):
        items[boardItemID]['gameState'] = {}
    if not items[boardItemID]['gameState'].get('state'):
        items[boardItemID]['gameState']['state'] = initial_chess_board()
        items[boardItemID]['gameState']['turn'] = 'white'
        items[boardItemID]['gameState']['history'] = []
    # get the game history
    game_state = items[boardItemID]['gameState']['state']
    gameBoardName = \
        _chess_board_name(players, id, rooms, items, items_db)
    if not params:
        show_chess_board(gameBoardName, game_state, id, mud,
                         items[boardItemID]['gameState']['turn'])
        return
    if players[id]['canGo'] != 1 or \
       players[id]['frozenStart'] > 0:
        desc = (
            "You try to make a chess move but find " +
            "that you lack any ability to",
            "You suddenly lose all enthusiasm for chess"
        )
        mud.send_message(id, '\n' + random_desc(desc) + ".\n\n")
        return
    params = params.lower().strip()
    if 'undo' in params:
        if len(items[boardItemID]['gameState']['history']) < 2:
            params = 'reset'
        else:
            mud.send_message(id, '\nUndoing last chess move.\n')
            items[boardItemID]['gameState']['history'].pop()
            game_state = items[boardItemID]['gameState']['history'][-1]
            items[boardItemID]['gameState']['state'] = game_state
            if items[boardItemID]['gameState']['turn'] == 'white':
                items[boardItemID]['gameState']['turn'] = 'black'
            else:
                items[boardItemID]['gameState']['turn'] = 'white'
            show_chess_board(gameBoardName, game_state, id, mud,
                             items[boardItemID]['gameState']['turn'])
            return
    # begin a new chess game
    if 'reset' in params or \
       'restart' in params or \
       'start again' in params or \
       'begin again' in params or \
       'new game' in params:
        mud.send_message(id, '\nStarting a new game.\n')
        items[boardItemID]['gameState']['state'] = initial_chess_board()
        items[boardItemID]['gameState']['turn'] = 'white'
        items[boardItemID]['gameState']['history'] = []
        game_state = items[boardItemID]['gameState']['state']
        show_chess_board(gameBoardName, game_state, id, mud,
                         items[boardItemID]['gameState']['turn'])
        return
    if 'move' in params:
        params = params.replace('move ', '').replace('to ', '')
        params = params.replace('from ', '').replace('.', '')
        params = params.replace('-', '').strip()
        chess_moves = params.split(' ')

        if len(chess_moves) == 1:
            if len(params) != 4:
                mud.send_message(id, "\nEnter a move such as g8f6.\n")
                return
            chess_moves = [params[:2], params[2:]]

        if len(chess_moves) != 2:
            mud.send_message(id, "\nThat's not a valid move.\n")
            return
        if len(chess_moves[0]) != 2 or \
           len(chess_moves[1]) != 2:
            mud.send_message(id, "\nEnter a move such as g8 f6.\n")
            return
        if move_chess_piece(chess_moves[0] + chess_moves[1],
                            items[boardItemID]['gameState']['state'],
                            items[boardItemID]['gameState']['turn'],
                            id, mud):
            mud.send_message(id, "\n" +
                             items[boardItemID]['gameState']['turn'] +
                             " moves from " + chess_moves[0] +
                             " to " + chess_moves[1] + ".\n")
            game_state = items[boardItemID]['gameState']['state']
            currTurn = items[boardItemID]['gameState']['turn']
            if currTurn == 'white':
                items[boardItemID]['gameState']['player1'] = \
                    players[id]['name']
                items[boardItemID]['gameState']['turn'] = 'black'
                # send a notification to the other player
                if items[boardItemID]['gameState'].get('player2'):
                    for p in players:
                        if p == id:
                            continue
                        if players[p]['name'] == \
                           items[boardItemID]['gameState']['player2']:
                            if players[p]['room'] == players[id]['room']:
                                turnStr = \
                                    items[boardItemID]['gameState']['turn']
                                show_chess_board(gameBoardName,
                                                 game_state, p, mud,
                                                 turnStr)
            else:
                items[boardItemID]['gameState']['player2'] = \
                    players[id]['name']
                items[boardItemID]['gameState']['turn'] = 'white'
                # send a notification to the other player
                if items[boardItemID]['gameState'].get('player1'):
                    for p in players:
                        if p == id:
                            continue
                        if players[p]['name'] == \
                           items[boardItemID]['gameState']['player1']:
                            if players[p]['room'] == players[id]['room']:
                                turnStr = \
                                    items[boardItemID]['gameState']['turn']
                                show_chess_board(gameBoardName, game_state,
                                                 p, mud, turnStr)
            gstate = game_state.copy()
            items[boardItemID]['gameState']['history'].append(gstate)
            show_chess_board(gameBoardName, game_state, id, mud, currTurn)
            return
        else:
            mud.send_message(id, "\nThat's not a valid move.\n")
            return
    show_chess_board(gameBoardName, game_state, id, mud,
                     items[boardItemID]['gameState']['turn'])


def _graphics(params, mud, playersDB: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {},
              env_db: {}, env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    """Turn graphical output on or off
    """
    graphicsState = params.lower().strip()
    if graphicsState == 'off' or \
       graphicsState == 'false' or \
       graphicsState == 'no':
        players[id]['graphics'] = 'off'
        mud.send_message(id, "Graphics have been turned off.\n\n")
    else:
        players[id]['graphics'] = 'on'
        mud.send_message(id, "Graphics have been activated.\n\n")


def _show_items_for_sale(mud, rooms: {}, room_id, players: {},
                         id, items_db: {}):
    """Shows items for sale within a market
    """
    if not rooms[room_id].get('marketInventory'):
        return
    mud.send_message(id, '\nFor Sale\n')
    ctr = 0
    for itemID, item in rooms[room_id]['marketInventory'].items():
        if item['stock'] < 1:
            continue
        itemLine = items_db[itemID]['name']
        while len(itemLine) < 30:
            itemLine += '.'
        itemCost = item['cost']
        if itemCost == '0':
            itemLine += 'Free'
        else:
            itemLine += itemCost
        mud.send_message(id, itemLine)
        ctr += 1
    mud.send_message(id, '\n')
    if ctr == 0:
        mud.send_message(id, 'Nothing\n\n')


def _buy(params, mud, playersDB: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {},
         env_db: {}, env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    """Buy from a market
    """
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '<r>\n\n')
        return

    if player_is_trapped(id, players, rooms):
        describe_trapped_player(mud, id, players, rooms)
        return

    if player_is_prone(id, players):
        mud.send_message(id, random_desc('You stand up<r>\n\n'))
        set_player_prone(id, players, False)
        return

    if players[id]['canGo'] != 1:
        mud.send_message(id,
                         'Somehow, your body refuses to move.<r>\n')
        return

    room_id = players[id]['room']
    if not rooms[room_id].get('marketInventory'):
        mud.send_message(id, 'There is nothing to buy here.<r>\n')
        return

    paramsLower = params.lower()
    if not paramsLower:
        _show_items_for_sale(mud, rooms, room_id, players, id, items_db)
    else:
        # buy some particular item
        for itemID, item in rooms[room_id]['marketInventory'].items():
            if item['stock'] < 1:
                continue
            itemName = items_db[itemID]['name'].lower()
            if itemName not in paramsLower:
                continue
            if _item_in_inventory(players, id,
                                  items_db[itemID]['name'], items_db):
                mud.send_message(id, 'You already have that\n\n')
                return
            itemCost = item['cost']
            if buy_item(players, id, itemID, items_db, itemCost):
                # is the item too heavy?
                players[id]['wei'] = \
                    player_inventory_weight(id, players, items_db)

                if players[id]['wei'] + items_db[itemID]['weight'] > \
                   _get_max_weight(id, players):
                    mud.send_message(id, "You can't carry any more.\n\n")
                    return
                # add the item to the player's inventory
                if str(itemID) not in players[id]['inv']:
                    players[id]['inv'].append(str(itemID))
                # update the weight of the player
                players[id]['wei'] = \
                    player_inventory_weight(id, players, items_db)
                update_player_attributes(id, players, items_db, itemID, 1)

                mud.send_message(id, 'You buy ' + items_db[itemID]['article'] +
                                 ' ' + items_db[itemID]['name'] + '\n\n')
            else:
                if itemCost.endswith('gp'):
                    mud.send_message(id,
                                     'You do not have enough gold pieces\n\n')
                elif itemCost.endswith('sp'):
                    mud.send_message(id,
                                     'You do not have enough ' +
                                     'silver pieces\n\n')
                elif itemCost.endswith('cp'):
                    mud.send_message(id,
                                     'You do not have enough ' +
                                     'copper pieces\n\n')
                elif itemCost.endswith('ep'):
                    mud.send_message(id,
                                     'You do not have enough ' +
                                     'electrum pieces\n\n')
                elif itemCost.endswith('pp'):
                    mud.send_message(id,
                                     'You do not have enough ' +
                                     'platinum pieces\n\n')
                else:
                    mud.send_message(id, 'You do not have enough money\n\n')
            return
        mud.send_message(id, "That's not sold here\n\n")


def _fish(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    """Go fishing
    """
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '<r>\n\n')
        return

    if player_is_trapped(id, players, rooms):
        describe_trapped_player(mud, id, players, rooms)
        return

    if not holding_fishing_rod(players, id, items_db):
        if 'isFishing' in players[id]:
            del players[id]['isFishing']
        descStr = 'You need to be holding a rod|' + \
            'You need to be holding something to fish with'
        mud.send_message(id, random_desc(descStr) + '<r>\n\n')
        return
    rid = players[id]['room']
    roomNameLower = rooms[rid]['name'].lower()
    if not is_fishing_site(rooms, rid):
        if 'isFishing' in players[id]:
            del players[id]['isFishing']
        descStr = "This isn't a fishing site|" + \
            "You can't fish here|" + \
            "This does not appear to be a fishing location"
        mud.send_message(id, random_desc(descStr) + '<r>\n\n')
        return
    if 'lava' in roomNameLower:
        if 'isFishing' in players[id]:
            del players[id]['isFishing']
        descStr = "You won't find any fish here"
        mud.send_message(id, random_desc(descStr) + '<r>\n\n')
        return
    if player_is_prone(id, players):
        if 'isFishing' in players[id]:
            del players[id]['isFishing']
        descStr = "You can't fish while lying down"
        mud.send_message(id, random_desc(descStr) + '<r>\n\n')
        return
    if 'isFishing' not in players[id]:
        players[id]['isFishing'] = True
        if holding_fly_fishing_rod(players, id, items_db):
            descStr = "You prepare the fly and then cast it out|" + \
                "You wave the rod back and forth and cast out the fly|" + \
                "Casting out the fly, you begin fishing"
        else:
            descStr = \
                "With a forwards flick of the rod you cast out the line|" + \
                "Casting out the line with a forward flick of the rod, " + \
                "you begin fishing"
    else:
        descStr = "You continue fishing"
    mud.send_message(id, random_desc(descStr) + '<r>\n\n')


def _sell(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    """Sell in a market
    """
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '<r>\n\n')
        return

    if player_is_trapped(id, players, rooms):
        describe_trapped_player(mud, id, players, rooms)
        return

    if player_is_prone(id, players):
        mud.send_message(id, random_desc('You stand up<r>\n\n'))
        set_player_prone(id, players, False)
        return

    if players[id]['canGo'] != 1:
        mud.send_message(id,
                         'Somehow, your body refuses to move.<r>\n')
        return

    room_id = players[id]['room']
    if not rooms[room_id].get('marketInventory'):
        mud.send_message(id, "You can't sell here.<r>\n")
        return

    paramsLower = params.lower()
    if not paramsLower:
        mud.send_message(id, 'What do you want to sell?\n')
    else:
        # does this market buy this type of item?
        marketType = get_market_type(rooms[room_id]['name'], markets)
        if not marketType:
            mud.send_message(id, "You can't sell here.<r>\n")
            return
        buysItemTypes = market_buys_item_types(marketType, markets)
        ableToSell = False
        for itemType in buysItemTypes:
            if itemType in paramsLower:
                ableToSell = True
                break
        if not ableToSell:
            mud.send_message(id, "You can't sell that here\n\n")
            return
        itemID = -1
        for (item, pl) in list(items.items()):
            if paramsLower in items_db[items[item]['id']]['name'].lower():
                itemID = items[item]['id']
                break
        if itemID == -1:
            mud.send_message(id, 'Error: item not found ' + params + ' \n\n')
            return
        # remove from item to the player's inventory
        if str(itemID) in players[id]['inv']:
            players[id]['inv'].remove(str(itemID))
        # update the weight of the player
        players[id]['wei'] = player_inventory_weight(id, players, items_db)
        update_player_attributes(id, players, items_db, itemID, 1)

        # Increase your money
        itemCost = items_db[itemID]['cost']
        # TODO the cost may vary depending upon room/region/time
        qty, denomination = parse_cost(itemCost)
        if denomination:
            if denomination in players[id]:
                qty = int(itemCost.replace(denomination, ''))
                players[id][denomination] += qty
        mud.send_message(id, 'You have sold ' + items_db[itemID]['article'] +
                         ' ' + items_db[itemID]['name'] + ' for ' +
                         itemCost + '\n\n')


def _go(params, mud, playersDB: {}, players: {}, rooms: {},
        npcs_db: {}, npcs: {}, items_db: {}, items: {},
        env_db: {}, env: {}, eventDB: {}, event_schedule,
        id: int, fights: {}, corpses: {}, blocklist,
        map_area: [], character_class_db: {}, spells_db: {},
        sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
        item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '<r>\n\n')
        return

    if player_is_trapped(id, players, rooms):
        describe_trapped_player(mud, id, players, rooms)
        return

    if player_is_prone(id, players):
        mud.send_message(id, random_desc('You stand up<r>\n\n'))
        set_player_prone(id, players, False)
        return

    if players[id]['canGo'] == 1:
        # store the exit name
        ex = params.lower()

        stepping = False
        if '######step######' in ex:
            if rooms[players[id]['room']]['trap'].get('trap_activation'):
                if rooms[players[id]['room']]['trap']['trap_activation'] == \
                   'tripwire':
                    ex = ex.replace('######step######', '')
                    stepping = True

        # store the player's current room
        rm = rooms[players[id]['room']]

        # if the specified exit is found in the room's exits list
        rmExits = _get_room_exits(mud, rooms, players, id)
        if ex in rmExits:
            # check if there is enough room
            targetRoom = None
            if ex in rm['exits']:
                targetRoom = rm['exits'][ex]
            elif rm.get('tideOutExits'):
                targetRoom = rm['tideOutExits'][ex]
            elif rm.get('exitsWhenWearing'):
                targetRoom = rm['exitsWhenWearing'][ex]
            if targetRoom:
                if rooms[targetRoom]['maxPlayers'] > -1:
                    if _players_in_room(targetRoom, players, npcs) >= \
                       rooms[targetRoom]['maxPlayers']:
                        mud.send_message(id, 'The room is full.<r>\n\n')
                        return

                # Check that the player is not too tall
                if rooms[targetRoom]['maxPlayerSize'] > -1:
                    if players[id]['siz'] > \
                       rooms[targetRoom]['maxPlayerSize']:
                        mud.send_message(id, "The entrance is too small " +
                                         "for you to enter.<r>\n\n")
                        return

                if not stepping:
                    if trap_activation(mud, id, players, rooms, ex):
                        return

                if rooms[players[id]['room']]['onWater'] == 0:
                    desc = \
                        random_desc(players[id]['outDescription'])
                    message_to_room_players(mud, players, id, '<f32>' +
                                            players[id]['name'] + '<r> ' +
                                            desc + " via exit " + ex + '\n')

                # stop any fights
                stop_attack(players, id, npcs, fights)

                # Trigger old room eventOnLeave for the player
                if rooms[players[id]['room']]['eventOnLeave'] != "":
                    idx = int(rooms[players[id]['room']]['eventOnLeave'])
                    add_to_scheduler(idx, id, event_schedule, eventDB)

                # Does the player have any follower NPCs or familiars?
                followersMsg = ""
                for (nid, pl) in list(npcs.items()):
                    if ((npcs[nid]['follow'] == players[id]['name'] or
                        npcs[nid]['familiarOf'] == players[id]['name']) and
                       npcs[nid]['familiarMode'] == 'follow'):
                        # is the npc in the same room as the player?
                        if npcs[nid]['room'] == players[id]['room']:
                            # is the player within the permitted npc path?
                            if rm['exits'][ex] in list(npcs[nid]['path']) or \
                               npcs[nid]['familiarOf'] == players[id]['name']:
                                follRoomID = rm['exits'][ex]
                                if rooms[follRoomID]['maxPlayerSize'] < 0 or \
                                   npcs[nid]['siz'] <= \
                                   rooms[follRoomID]['maxPlayerSize']:
                                    npcs[nid]['room'] = follRoomID
                                    np = npcs[nid]
                                    desc = \
                                        random_desc(np['inDescription'])
                                    followersMsg = \
                                        followersMsg + '<f32>' + \
                                        npcs[nid]['name'] + '<r> ' + \
                                        desc + '.\n\n'
                                    desc = \
                                        random_desc(np['outDescription'])
                                    message_to_room_players(mud, players,
                                                            id,
                                                            '<f32>' +
                                                            np['name'] +
                                                            '<r> ' +
                                                            desc +
                                                            " via exit " +
                                                            ex + '\n')
                                else:
                                    # The room height is too small
                                    # for the follower
                                    npcs[nid]['follow'] = ""
                            else:
                                # not within the npc path, stop following
                                # print(npcs[nid]['name'] +
                                # ' stops following (out of path)\n')
                                npcs[nid]['follow'] = ""
                        else:
                            # stop following
                            # print(npcs[nid]['name'] + ' stops following\n')
                            npcs[nid]['follow'] = ""

                # update the player's current room to the one the exit leads to
                if rooms[players[id]['room']]['onWater'] == 1:
                    _players_move_together(id, rm['exits'][ex], mud,
                                           playersDB, players, rooms,
                                           npcs_db, npcs,
                                           items_db, items, env_db, env,
                                           eventDB, event_schedule,
                                           fights, corpses, blocklist,
                                           map_area,
                                           character_class_db, spells_db,
                                           sentiment_db, guilds_db, clouds,
                                           races_db, item_history, markets,
                                           cultures_db)
                players[id]['room'] = rm['exits'][ex]
                rm = rooms[players[id]['room']]

                if 'isFishing' in players[id]:
                    del players[id]['isFishing']

                # trigger new room eventOnEnter for the player
                if rooms[players[id]['room']]['eventOnEnter'] != "":
                    idx = \
                        int(rooms[players[id]['room']]['eventOnEnter'])
                    add_to_scheduler(idx, id, event_schedule, eventDB)

                if rooms[players[id]['room']]['onWater'] == 0:
                    desc = random_desc(players[id]['inDescription'])
                    message_to_room_players(mud, players, id, '<f32>' +
                                            players[id]['name'] + '<r> ' +
                                            desc + "\n\n")
                    # send the player a message telling them where they are now
                    desc = \
                        '****TITLE****You arrive at ' + \
                        '<f106>{}'.format(rooms[players[id]['room']]['name'])
                    mud.send_message(id, desc + "<r>\n\n")
                else:
                    # send the player a message telling them where they are now
                    desc = \
                        '****TITLE****You row to ' + \
                        '<f106>{}'.format(rooms[players[id]['room']]['name'])
                    mud.send_message(id, desc + "<r>\n\n")

                _look('', mud, playersDB, players, rooms, npcs_db, npcs,
                      items_db, items, env_db, env, eventDB, event_schedule,
                      id, fights, corpses, blocklist, map_area,
                      character_class_db, spells_db, sentiment_db,
                      guilds_db, clouds, races_db, item_history, markets,
                      cultures_db)
                # report any followers
                if len(followersMsg) > 0:
                    message_to_room_players(mud, players, id, followersMsg)
                    mud.send_message(id, followersMsg)
        else:
            # the specified exit wasn't found in the current room
            # send back an 'unknown exit' message
            mud.send_message(id, "Unknown exit <f226>'{}'".format(ex) +
                             "<r>\n\n")
    else:
        mud.send_message(id,
                         'Somehow, your legs refuse to obey your will.<r>\n')


def _go_north(params, mud, playersDB, players, rooms,
              npcs_db: {}, npcs, items_db: {}, items: {}, env_db: {},
              env, eventDB: {}, event_schedule, id, fights,
              corpses, blocklist, map_area, character_class_db: {},
              spells_db: {}, sentiment_db: {},
              guilds_db: {}, clouds, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('north', mud, playersDB, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_south(params, mud, playersDB: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
              env, eventDB: {}, event_schedule, id, fights,
              corpses, blocklist, map_area, character_class_db: {},
              spells_db: {}, sentiment_db: {}, guilds_db: {},
              clouds, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('south', mud, playersDB, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_east(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
             env, eventDB: {}, event_schedule, id, fights,
             corpses, blocklist, map_area, character_class_db: {},
             spells_db: {}, sentiment_db: {},
             guilds_db: {}, clouds, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('east', mud, playersDB, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_west(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env, eventDB: {}, event_schedule, id, fights,
             corpses, blocklist, map_area, character_class_db: {},
             spells_db: {}, sentiment_db: {}, guilds_db: {},
             clouds, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('west', mud, playersDB, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_up(params, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
           env, eventDB: {}, event_schedule, id, fights,
           corpses, blocklist, map_area, character_class_db: {},
           spells_db: {}, sentiment_db: {}, guilds_db: {},
           clouds, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('up', mud, playersDB, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_down(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
             env, eventDB: {}, event_schedule, id, fights,
             corpses, blocklist, map_area, character_class_db: {},
             spells_db: {}, sentiment_db: {}, guilds_db: {}, clouds,
             races_db: {}, item_history: {}, markets: {},
             cultures_db: {}) -> None:
    _go('down', mud, playersDB, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_in(params: str, mud, playersDB: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
           env, eventDB: {}, event_schedule, id, fights: {},
           corpses, blocklist, map_area, character_class_db: {},
           spells_db: {}, sentiment_db: {}, guilds_db: {},
           clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('in', mud, playersDB, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_out(params: str, mud, playersDB: {}, players: {}, rooms: {},
            npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
            env, eventDB: {}, event_schedule, id, fights: {},
            corpses, blocklist, map_area, character_class_db: {},
            spells_db: {}, sentiment_db: {}, guilds_db: {},
            clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('out', mud, playersDB, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _conjure_room(params, mud, playersDB: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist: {},
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                  item_history: {}, markets: {}, cultures_db: {}):
    params = params.replace('room ', '')
    roomDirection = params.lower().strip()
    possibleDirections = ('north', 'south', 'east', 'west',
                          'up', 'down', 'in', 'out')
    oppositeDirection = {
        'north': 'south',
        'south': 'north',
        'east': 'west',
        'west': 'east',
        'up': 'down',
        'down': 'up',
        'in': 'out',
        'out': 'in'
    }
    if roomDirection not in possibleDirections:
        mud.send_message(id, 'Specify a room direction.\n\n')
        return False

    # Is there already a room in that direction?
    playerRoomID = players[id]['room']
    roomExits = _get_room_exits(mud, rooms, players, id)
    if roomExits.get(roomDirection):
        mud.send_message(id, 'A room already exists in that direction.\n\n')
        return False

    room_id = get_free_room_key(rooms)
    if len(room_id) == 0:
        room_id = '$rid=1$'

    desc = \
        "You are in an empty room. There is a triangular symbol carved " + \
        "into the wall depicting a peasant digging with a spade. " + \
        "Underneath it is an inscription which reads 'aedificium'."

    newrm = {
        'name': 'Empty room',
        'description': desc,
        'roomTeleport': "",
        'conditional': [],
        'trap': {},
        'eventOnEnter': "",
        'eventOnLeave': "",
        'maxPlayerSize': -1,
        'maxPlayers': -1,
        'weather': 0,
        'onWater': 0,
        'roomType': "",
        'virtualExits': {},
        'tideOutDescription': "",
        'region': "",
        'terrainDifficulty': 0,
        'coords': [],
        'exits': {
            oppositeDirection[roomDirection]: playerRoomID
        }
    }
    rooms[room_id] = newrm
    roomExits[roomDirection] = room_id

    # update the room coordinates
    for rm in rooms:
        rooms[rm]['coords'] = []

    log("New room: " + room_id, 'info')
    save_universe(rooms, npcs_db, npcs, items_db, items,
                  env_db, env, guilds_db)
    mud.send_message(id, 'Room created.\n\n')


def _conjure_item(params, mud, playersDB: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                  item_history: {}, markets: {}, cultures_db: {}):
    itemName = params.lower()
    if len(itemName) == 0:
        mud.send_message(id, "Specify the name of an item to conjure.\n\n")
        return False

    # Check if item is in player's inventory
    for item in players[id]['inv']:
        for (iid, pl) in list(items_db.items()):
            if str(iid) == item:
                if itemName in items_db[iid]['name'].lower():
                    mud.send_message(id, "You have " +
                                     items_db[iid]['article'] + " " +
                                     items_db[iid]['name'] +
                                     " in your inventory already.\n\n")
                    return False
    # Check if it is in the room
    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            if itemName in items_db[items[item]['id']]['name'].lower():
                mud.send_message(id, "It's already here.\n\n")
                return False

    itemID = -1
    for (item, pl) in list(items.items()):
        if itemName == items_db[items[item]['id']]['name'].lower():
            itemID = items[item]['id']
            break

    if itemID == -1:
        for (item, pl) in list(items.items()):
            if itemName in items_db[items[item]['id']]['name'].lower():
                itemID = items[item]['id']
                break

    if itemID != -1:
        # Generate item
        itemKey = get_free_key(items)
        items[itemKey] = {
            'id': itemID,
            'room': players[id]['room'],
            'whenDropped': int(time.time()),
            'lifespan': 900000000, 'owner': id
        }
        keyStr = str(itemKey)
        assign_item_history(keyStr, items, item_history)
        mud.send_message(id, items_db[itemID]['article'] + ' ' +
                         items_db[itemID]['name'] +
                         ' spontaneously materializes in front of you.\n\n')
        save_universe(rooms, npcs_db, npcs, items_db, items, env_db,
                      env, guilds_db)
        return True
    return False


def _random_familiar(npcs_db: {}):
    """Picks a familiar at random and returns its index
    """
    possibleFamiliars = []
    for index, details in npcs_db.items():
        if len(details['familiarType']) > 0:
            if len(details['familiarOf']) == 0:
                possibleFamiliars.append(int(index))
    if len(possibleFamiliars) > 0:
        randIndex = len(possibleFamiliars) - 1
        return possibleFamiliars[randint(0, randIndex)]
    return -1


def _conjure_npc(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcs_db: {}, npcs: {}, items_db: {}, items: {},
                 env_db: {}, env: {}, eventDB: {}, event_schedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 map_area: [], character_class_db: {}, spells_db: {},
                 sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                 item_history: {}, markets: {}, cultures_db: {}):
    if not params.startswith('npc '):
        if not params.startswith('familiar'):
            return False

    npcHitPoints = 100
    isFamiliar = False
    npcType = 'NPC'
    if params.startswith('familiar'):
        isFamiliar = True
        npcType = 'Familiar'
        npcIndex = _random_familiar(npcs_db)
        if npcIndex < 0:
            mud.send_message(id, "No familiars known.\n\n")
            return
        npcName = npcs_db[npcIndex]['name']
        npcHitPoints = 5
        npcSize = 0
        npcStrength = 5
        npcFamiliarOf = players[id]['name']
        npcAnimalType = npcs_db[npcIndex]['animalType']
        npcFamiliarType = npcs_db[npcIndex]['familiarType']
        npcFamiliarMode = "follow"
        npcConv = deepcopy(npcs_db[npcIndex]['conv'])
        npcVocabulary = deepcopy(npcs_db[npcIndex]['vocabulary'])
        npcTalkDelay = npcs_db[npcIndex]['talkDelay']
        npcRandomFactor = npcs_db[npcIndex]['randomFactor']
        npcLookDescription = npcs_db[npcIndex]['lookDescription']
        npcInDescription = npcs_db[npcIndex]['inDescription']
        npcOutDescription = npcs_db[npcIndex]['outDescription']
        npcMoveDelay = npcs_db[npcIndex]['moveDelay']
    else:
        npcName = params.replace('npc ', '', 1).strip().replace('"', '')
        npcSize = size_from_description(npcName)
        npcStrength = 80
        npcFamiliarOf = ""
        npcAnimalType = ""
        npcFamiliarType = ""
        npcFamiliarMode = ""
        npcConv = []
        npcVocabulary = [""]
        npcTalkDelay = 300
        npcRandomFactor = 100
        npcLookDescription = "A new NPC, not yet described"
        npcInDescription = "arrives"
        npcOutDescription = "goes"
        npcMoveDelay = 300

    if len(npcName) == 0:
        mud.send_message(id, "Specify the name of an NPC to conjure.\n\n")
        return False

    # Check if NPC is in the room
    for (nid, pl) in list(npcs.items()):
        if npcs[nid]['room'] == players[id]['room']:
            if npcName.lower() in npcs[nid]['name'].lower():
                mud.send_message(id, npcs[nid]['name'] +
                                 " is already here.\n\n")
                return False

    # NPC has the culture assigned to the room
    roomCulture = get_room_culture(cultures_db, rooms, players[id]['room'])
    if roomCulture is None:
        roomCulture = ''

    # default medium size
    newNPC = {
        "name": npcName,
        "whenDied": None,
        "isAggressive": 0,
        "inv": [],
        "speakLanguage": "common",
        "language": ["common"],
        "culture": roomCulture,
        "conv": npcConv,
        "room": players[id]['room'],
        "path": [],
        "bodyType": "",
        "moveDelay": npcMoveDelay,
        "moveType": "",
        "moveTimes": [],
        "vocabulary": npcVocabulary,
        "talkDelay": npcTalkDelay,
        "timeTalked": 0,
        "lastSaid": 0,
        "lastRoom": None,
        "lastMoved": 0,
        "randomizer": 0,
        "randomFactor": npcRandomFactor,
        "follow": "",
        "canWield": 0,
        "canWear": 0,
        "race": "",
        "characterClass": "",
        "archetype": "",
        "proficiencies": [],
        "fightingStyle": "",
        "restRequired": 0,
        "enemy": "",
        "tempCharmStart": 0,
        "tempCharmDuration": 0,
        "tempCharm": 0,
        "magicShieldStart": 0,
        "magicShieldDuration": 0,
        "magicShield": 0,
        "tempCharmTarget": "",
        "guild": "",
        "guildRole": "",
        "tempHitPointsDuration": 0,
        "tempHitPointsStart": 0,
        "tempHitPoints": 0,
        "spellSlots": {},
        "preparedSpells": {},
        "hpMax": npcHitPoints,
        "hp": npcHitPoints,
        "charge": 1233,
        "lvl": 5,
        "exp": 32,
        "str": npcStrength,
        "siz": npcSize,
        "wei": 100,
        "per": 3,
        "endu": 1,
        "cha": 4,
        "int": 2,
        "agi": 6,
        "luc": 1,
        "cool": 0,
        "ref": 1,
        "cred": 122,
        "pp": 0,
        "ep": 0,
        "cp": 0,
        "sp": 0,
        "gp": 0,
        "clo_head": 0,
        "clo_neck": 0,
        "clo_larm": 0,
        "clo_rarm": 0,
        "clo_lhand": 0,
        "clo_rhand": 0,
        "clo_gloves": 0,
        "clo_lfinger": 0,
        "clo_rfinger": 0,
        "clo_waist": 0,
        "clo_lear": 0,
        "clo_rear": 0,
        "clo_rwrist": 0,
        "clo_lwrist": 0,
        "clo_chest": 0,
        "clo_back": 0,
        "clo_lleg": 0,
        "clo_rleg": 0,
        "clo_feet": 0,
        "imp_head": 0,
        "imp_neck": 0,
        "imp_larm": 0,
        "imp_rarm": 0,
        "imp_lhand": 0,
        "imp_rhand": 0,
        "imp_gloves": 0,
        "imp_lfinger": 0,
        "imp_rfinger": 0,
        "imp_waist": 0,
        "imp_lear": 0,
        "imp_rear": 0,
        "imp_rwrist": 0,
        "imp_lwrist": 0,
        "imp_chest": 0,
        "imp_back": 0,
        "imp_lleg": 0,
        "imp_rleg": 0,
        "imp_feet": 0,
        "inDescription": npcInDescription,
        "outDescription": npcOutDescription,
        "lookDescription": npcLookDescription,
        "canGo": 0,
        "canLook": 1,
        "canWield": 0,
        "canWear": 0,
        "visibleWhenWearing": [],
        "climbWhenWearing": [],
        "frozenStart": 0,
        "frozenDuration": 0,
        "frozenDescription": "",
        "affinity": {},
        "familiar": -1,
        "familiarOf": npcFamiliarOf,
        "familiarTarget": "",
        "familiarType": npcFamiliarType,
        "familiarMode": npcFamiliarMode,
        "animalType": npcAnimalType
    }

    if isFamiliar:
        if players[id]['familiar'] != -1:
            npcsKey = players[id]['familiar']
        else:
            npcsKey = get_free_key(npcs)
            players[id]['familiar'] = npcsKey
    else:
        npcsKey = get_free_key(npcs)

    npcs[npcsKey] = newNPC
    npcs_db[npcsKey] = newNPC
    npcsKeyStr = str(npcsKey)
    log(npcType + ' ' + npcName + ' generated in ' +
        players[id]['room'] + ' with key ' + npcsKeyStr, 'info')
    if isFamiliar:
        mud.send_message(
            id,
            'Your familiar, ' +
            npcName +
            ', spontaneously appears.\n\n')
    else:
        mud.send_message(id, npcName + ' spontaneously appears.\n\n')
    save_universe(rooms, npcs_db, npcs, items_db, items,
                  env_db, env, guilds_db)
    return True


def _dismiss(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {},
             env_db: {}, env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    """Dismiss a familiar
    """
    if params.lower().startswith('familiar'):
        players[id]['familiar'] = -1
        familiarRemoved = False
        removals = []
        for (index, details) in npcs_db.items():
            if details['familiarOf'] == players[id]['name']:
                removals.append(index)
                familiarRemoved = True
        for index in removals:
            del npcs_db[index]

        removals.clear()
        for (index, details) in npcs.items():
            if details['familiarOf'] == players[id]['name']:
                removals.append(index)
        for index in removals:
            del npcs[index]

        if familiarRemoved:
            mud.send_message(id, "Your familiar vanishes.\n\n")
        else:
            mud.send_message(id, "\n\n")


def _conjure(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {},
             env_db: {}, env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return

    if params.startswith('familiar'):
        _conjure_npc(params, mud, playersDB, players, rooms,
                     npcs_db, npcs, items_db, items, env_db, env,
                     eventDB, event_schedule, id, fights, corpses,
                     blocklist, map_area, character_class_db,
                     spells_db, sentiment_db, guilds_db, clouds, races_db,
                     item_history, markets, cultures_db)
        return

    if params.startswith('room '):
        _conjure_room(params, mud, playersDB, players, rooms, npcs_db,
                      npcs, items_db, items, env_db, env, eventDB,
                      event_schedule, id, fights, corpses, blocklist,
                      map_area, character_class_db, spells_db,
                      sentiment_db, guilds_db, clouds, races_db,
                      item_history, markets, cultures_db)
        return

    if params.startswith('npc '):
        _conjure_npc(params, mud, playersDB, players, rooms,
                     npcs_db, npcs, items_db, items, env_db, env,
                     eventDB, event_schedule, id, fights, corpses,
                     blocklist, map_area, character_class_db,
                     spells_db, sentiment_db, guilds_db, clouds, races_db,
                     item_history, markets, cultures_db)
        return

    _conjure_item(params, mud, playersDB, players, rooms, npcs_db, npcs,
                  items_db, items, env_db, env, eventDB, event_schedule,
                  id, fights, corpses, blocklist, map_area,
                  character_class_db, spells_db, sentiment_db, guilds_db,
                  clouds, races_db, item_history, markets, cultures_db)


def _destroy_item(params, mud, playersDB: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                  item_history: {}, markets: {}, cultures_db: {}):
    itemName = params.lower()
    if len(itemName) == 0:
        mud.send_message(id, "Specify the name of an item to destroy.\n\n")
        return False

    # Check if it is in the room
    itemID = -1
    destroyedName = ''
    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            if itemName in items_db[items[item]['id']]['name']:
                destroyedName = items_db[items[item]['id']]['name']
                itemID = items[item]['id']
                break
    if itemID == -1:
        mud.send_message(id, "It's not here.\n\n")
        return False

    mud.send_message(id, 'It suddenly vanishes.\n\n')
    del items[item]
    log("Item destroyed: " + destroyedName +
        ' in ' + players[id]['room'], 'info')
    save_universe(rooms, npcs_db, npcs, items_db,
                  items, env_db, env, guilds_db)
    return True


def _destroy_npc(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcs_db: {}, npcs: {}, items_db: {}, items: {},
                 env_db: {}, env: {}, eventDB: {}, event_schedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 map_area: [], character_class_db: {}, spells_db: {},
                 sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                 item_history: {}, markets: {}, cultures_db: {}):
    npcName = params.lower().replace('npc ', '').strip().replace('"', '')
    if len(npcName) == 0:
        mud.send_message(id, "Specify the name of an NPC to destroy.\n\n")
        return False

    # Check if NPC is in the room
    npcID = -1
    destroyedName = ''
    for (nid, pl) in list(npcs.items()):
        if npcs[nid]['room'] == players[id]['room']:
            if npcName.lower() in npcs[nid]['name'].lower():
                destroyedName = npcs[nid]['name']
                npcID = nid
                break

    if npcID == -1:
        mud.send_message(id, "They're not here.\n\n")
        return False

    mud.send_message(id, 'They suddenly vanish.\n\n')
    del npcs[npcID]
    del npcs_db[npcID]
    log("NPC destroyed: " + destroyedName +
        ' in ' + players[id]['room'], 'info')
    save_universe(rooms, npcs_db, npcs, items_db,
                  items, env_db, env, guilds_db)
    return True


def _destroy_room(params, mud, playersDB: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                  item_history: {}, markets: {}, cultures_db: {}):
    params = params.replace('room ', '')
    roomDirection = params.lower().strip()
    possibleDirections = (
        'north',
        'south',
        'east',
        'west',
        'up',
        'down',
        'in',
        'out')
    oppositeDirection = {
        'north': 'south', 'south': 'north', 'east': 'west',
        'west': 'east', 'up': 'down', 'down': 'up',
        'in': 'out', 'out': 'in'
    }
    if roomDirection not in possibleDirections:
        mud.send_message(id, 'Specify a room direction.\n\n')
        return False

    # Is there already a room in that direction?
    roomExits = _get_room_exits(mud, rooms, players, id)
    if not roomExits.get(roomDirection):
        mud.send_message(id, 'There is no room in that direction.\n\n')
        return False

    roomToDestroyID = roomExits.get(roomDirection)
    roomToDestroy = rooms[roomToDestroyID]
    roomExitsToDestroy = roomToDestroy['exits']
    for direction, room_id in roomExitsToDestroy.items():
        # Remove the exit from the other room to this one
        otherRoom = rooms[room_id]
        if otherRoom['exits'].get(oppositeDirection[direction]):
            del otherRoom['exits'][oppositeDirection[direction]]
    del rooms[roomToDestroyID]

    # update the map area
    for rm in rooms:
        rooms[rm]['coords'] = []

    log("Room destroyed: " + roomToDestroyID, 'info')
    save_universe(rooms, npcs_db, npcs, items_db,
                  items, env_db, env, guilds_db)
    mud.send_message(id, "Room destroyed.\n\n")
    return True


def _destroy(params, mud, playersDB: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {},
             env_db: {}, env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return

    if params.startswith('room '):
        _destroy_room(params, mud, playersDB, players, rooms, npcs_db,
                      npcs, items_db, items, env_db, env, eventDB,
                      event_schedule, id, fights, corpses, blocklist,
                      map_area, character_class_db, spells_db,
                      sentiment_db, guilds_db, clouds, races_db,
                      item_history, markets, cultures_db)
    else:
        if params.startswith('npc '):
            _destroy_npc(params, mud, playersDB, players, rooms, npcs_db,
                         npcs, items_db, items, env_db, env, eventDB,
                         event_schedule, id, fights, corpses, blocklist,
                         map_area, character_class_db, spells_db,
                         sentiment_db, guilds_db, clouds, races_db,
                         item_history, markets, cultures_db)
        else:
            _destroy_item(params, mud, playersDB, players, rooms, npcs_db,
                          npcs, items_db, items, env_db, env, eventDB,
                          event_schedule, id, fights, corpses, blocklist,
                          map_area, character_class_db, spells_db,
                          sentiment_db, guilds_db, clouds, races_db,
                          item_history, markets, cultures_db)


def _give(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    if ' to ' not in params:
        desc = (
            "Give to who?"
        )
        mud.send_message(id, random_desc(desc) + '.\n\n')
        return
    recipientName = params.split(' to ')[1].lower()
    recipientId = None
    for pid, playerItem in players.items():
        if pid == id:
            continue
        if recipientName not in playerItem['name'].lower():
            continue
        if playerItem['room'] != players[id]['room']:
            continue
        recipientId = pid
    if not recipientId:
        desc = (
            "You don't see them here"
        )
        mud.send_message(id, random_desc(desc) + '.\n\n')
        return
    giveStr = params.split(' to ')[0].lower()
    moneyStr = None
    denomination = None
    if ' copper piece' in giveStr:
        moneyStr = giveStr.split(' copper piece')[0]
        denomination = 'cp'
    elif ' silver piece' in giveStr:
        moneyStr = giveStr.split(' silver piece')[0]
        denomination = 'sp'
    elif ' electrum piece' in giveStr:
        moneyStr = giveStr.split(' electrum piece')[0]
        denomination = 'ep'
    elif ' gold piece' in giveStr:
        moneyStr = giveStr.split(' gold piece')[0]
        denomination = 'gp'
    elif ' platium piece' in giveStr:
        moneyStr = giveStr.split(' platinum piece')[0]
        denomination = 'pp'
    elif giveStr.endswith('cp'):
        moneyStr = giveStr.split('cp')[0]
        denomination = 'cp'
    elif giveStr.endswith('sp'):
        moneyStr = giveStr.split('sp')[0]
        denomination = 'sp'
    elif giveStr.endswith('ep'):
        moneyStr = giveStr.split('ep')[0]
        denomination = 'ep'
    elif giveStr.endswith('gp'):
        moneyStr = giveStr.split('gp')[0]
        denomination = 'gp'
    elif giveStr.endswith('pp'):
        moneyStr = giveStr.split('pp')[0]
        denomination = 'pp'

    if denomination:
        moneyStr = moneyStr.strip()
        qty = 0
        if moneyStr.isdigit():
            qty = int(moneyStr)
        else:
            qtyDict = {
                'a': 1,
                'one': 1,
                'two': 2,
                'three': 3,
                'four': 4,
                'five': 5,
                'six': 6,
                'seven': 7,
                'eight': 8,
                'nine': 9,
                'ten': 10,
                'twenty': 20
            }
            for qtyStr, value in qtyDict.items():
                if qtyStr in moneyStr:
                    qty = value
                    break
        if qty > 0:
            cost = str(qty) + denomination
            if money_purchase(id, players, cost):
                players[recipientId][denomination] += qty
                desc = (
                    "You give " + cost + " to " + players[recipientId]['name']
                )
                mud.send_message(id, random_desc(desc) + '.\n\n')
                desc = (
                    players[id]['name'] + " gives you " + cost
                )
                mud.send_message(recipientId,
                                 random_desc(desc) + '.\n\n')
                return
            else:
                desc = (
                    "You don't have " + cost
                )
                mud.send_message(id, random_desc(desc) + '.\n\n')
                return
    desc = (
        "You don't have that"
    )
    mud.send_message(id, random_desc(desc) + '.\n\n')
    return


def _drop(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    """Drop an item
    """
    # Check if inventory is empty
    if len(list(players[id]['inv'])) == 0:
        mud.send_message(id, 'You don`t have that!\n\n')
        return

    itemInDB = False
    itemInInventory = False
    itemID = None
    target = str(params).lower()
    if target.startswith('the '):
        target = params.replace('the ', '')

    # Check if item is in player's inventory
    for item in players[id]['inv']:
        for (iid, pl) in list(items_db.items()):
            if str(iid) == str(item):
                if items_db[iid]['name'].lower() == target:
                    itemID = iid
                    itemInInventory = True
                    itemInDB = True
                    break
        if itemInInventory:
            break

    if not itemInInventory:
        # Try a fuzzy match
        for item in players[id]['inv']:
            for (iid, pl) in list(items_db.items()):
                if str(iid) == str(item):
                    if target in items_db[iid]['name'].lower():
                        itemID = iid
                        itemInInventory = True
                        itemInDB = True
                        break

    if itemInDB and itemInInventory:
        if player_is_trapped(id, players, rooms):
            desc = (
                "You're trapped",
                "The trap restricts your ability to drop anything",
                "The trap restricts your movement"
            )
            mud.send_message(id, random_desc(desc) + '.\n\n')
            return

        inventoryCopy = deepcopy(players[id]['inv'])
        for i in inventoryCopy:
            if int(i) == itemID:
                # Remove first matching item from inventory
                players[id]['inv'].remove(i)
                update_player_attributes(id, players, items_db, itemID, -1)
                break

        players[id]['wei'] = player_inventory_weight(id, players, items_db)

        # remove from clothing
        _remove_item_from_clothing(players, id, int(i))

        # Create item on the floor in the same room as the player
        items[get_free_key(items)] = {
            'id': itemID,
            'room': players[id]['room'],
            'whenDropped': int(time.time()),
            'lifespan': 900000000,
            'owner': id
        }

        # Print itemsInWorld to console for debugging purposes
        # for x in itemsInWorld:
        # print (x)
        # for y in itemsInWorld[x]:
        # print(y,':',itemsInWorld[x][y])

        mud.send_message(id, 'You drop ' +
                         items_db[int(i)]['article'] +
                         ' ' +
                         items_db[int(i)]['name'] +
                         ' on the floor.\n\n')

    else:
        mud.send_message(id, 'You don`t have that!\n\n')


def _open_item_unlock(items: {}, items_db: {}, id, iid,
                      players: {}, mud) -> bool:
    """Unlock an item
    """
    unlockItemID = items_db[items[iid]['id']]['lockedWithItem']
    if not str(unlockItemID).isdigit():
        return True
    if unlockItemID <= 0:
        return True
    keyFound = False
    for i in list(players[id]['inv']):
        if int(i) == unlockItemID:
            keyFound = True
            break
    if keyFound:
        mud.send_message(
            id, 'You use ' +
            items_db[unlockItemID]['article'] +
            ' ' + items_db[unlockItemID]['name'])
    else:
        if len(items_db[unlockItemID]['open_failed_description']) > 0:
            mud.send_message(
                id, items_db[unlockItemID]['open_failed_description'] +
                ".\n\n")
        else:
            if items_db[unlockItemID]['state'].startswith('lever '):
                mud.send_message(id, "It's operated with a lever.\n\n")
            else:
                if randint(0, 1) == 1:
                    mud.send_message(
                        id, "You don't have " +
                        items_db[unlockItemID]['article'] +
                        " " + items_db[unlockItemID]['name'] +
                        ".\n\n")
                else:
                    mud.send_message(
                        id, "Looks like you need " +
                        items_db[unlockItemID]['article'] +
                        " " + items_db[unlockItemID]['name'] +
                        " for this.\n\n")
        return False
    return True


def _describe_container_contents(mud, id, items_db: {}, itemID: {}, returnMsg):
    """Describe a container contents
    """
    if not items_db[itemID]['state'].startswith('container open'):
        if returnMsg:
            return ''
        else:
            return
    containsList = items_db[itemID]['contains']
    noOfItems = len(containsList)
    containerMsg = '<f15>You see '

    if noOfItems == 0:
        if 'open always' not in items_db[itemID]['state']:
            mud.send_message(id, containerMsg + 'nothing.\n')
        return ''

    itemCtr = 0
    for contentsID in containsList:
        if itemCtr > 0:
            if itemCtr < noOfItems - 1:
                containerMsg += ', '
            else:
                containerMsg += ' and '

        containerMsg += \
            items_db[int(contentsID)]['article'] + \
            ' <b234><f220>' + \
            items_db[int(contentsID)]['name'] + '<r>'
        itemCtr += 1

    containerMsg = containerMsg + '.\n'
    if returnMsg:
        containerMsg = '\n' + containerMsg
        return containerMsg
    else:
        mud.send_message_wrap(id, '<f220>', containerMsg + '\n')


def _open_item_container(params, mud, playersDB: {}, players: {}, rooms: {},
                         npcs_db: {}, npcs: {}, items_db: {}, items: {},
                         env_db: {}, env: {}, eventDB: {}, event_schedule,
                         id: int, fights: {}, corpses: {}, target,
                         itemsInWorldCopy: {}, iid):
    """Opens a container
    """
    if not _open_item_unlock(items, items_db, id, iid, players, mud):
        return

    itemID = items[iid]['id']
    if items_db[itemID]['state'].startswith('container open'):
        mud.send_message(id, "It's already open\n\n")
        return

    items_db[itemID]['state'] = \
        items_db[itemID]['state'].replace('closed', 'open')
    items_db[itemID]['short_description'] = \
        items_db[itemID]['short_description'].replace('closed', 'open')
    items_db[itemID]['long_description'] = \
        items_db[itemID]['long_description'].replace('closed', 'open')
    items_db[itemID]['long_description'] = \
        items_db[itemID]['long_description'].replace('shut', 'open')

    if len(items_db[itemID]['open_description']) > 0:
        mud.send_message(id, items_db[itemID]['open_description'] + '\n\n')
    else:
        itemArticle = items_db[itemID]['article']
        if itemArticle == 'a':
            itemArticle = 'the'
        mud.send_message(id, 'You open ' + itemArticle +
                         ' ' + items_db[itemID]['name'] + '.\n\n')
    _describe_container_contents(mud, id, items_db, itemID, False)


def _lever_up(params, mud, playersDB: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {},
              env_db: {}, env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, target,
              itemsInWorldCopy: {}, iid):
    """Pull a lever up
    """
    itemID = items[iid]['id']
    linkedItemID = int(items_db[itemID]['linkedItem'])
    room_id = items_db[itemID]['exit']

    items_db[itemID]['state'] = 'lever up'
    items_db[itemID]['short_description'] = \
        items_db[itemID]['short_description'].replace('down', 'up')
    items_db[itemID]['long_description'] = \
        items_db[itemID]['long_description'].replace('down', 'up')
    if '|' in items_db[itemID]['exitName']:
        exitName = items_db[itemID]['exitName'].split('|')

        if linkedItemID > 0:
            desc = items_db[linkedItemID]['short_description']
            items_db[linkedItemID]['short_description'] = \
                desc.replace('open', 'closed')
            desc = items_db[linkedItemID]['long_description']
            items_db[linkedItemID]['long_description'] = \
                desc.replace('open', 'closed')
            items_db[linkedItemID]['state'] = 'closed'
            linkedItemID2 = int(items_db[linkedItemID]['linkedItem'])
            if linkedItemID2 > 0:
                desc = items_db[linkedItemID2]['short_description']
                items_db[linkedItemID2]['short_description'] = \
                    desc.replace('open', 'closed')
                desc = items_db[linkedItemID2]['long_description']
                items_db[linkedItemID2]['long_description'] = \
                    desc.replace('open', 'closed')
                items_db[linkedItemID2]['state'] = 'closed'

        if len(room_id) > 0:
            rm = players[id]['room']
            if exitName[0] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[0]]

            rm = room_id
            if exitName[1] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[1]]

    if len(items_db[itemID]['close_description']) > 0:
        mud.send_message_wrap(id, '<f220>',
                              items_db[itemID]['close_description'] + '\n\n')
    else:
        mud.send_message(
            id, 'You push ' +
            items_db[itemID]['article'] +
            ' ' + items_db[itemID]['name'] +
            '\n\n')


def _lever_down(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, target,
                itemsInWorldCopy: {}, iid):
    if not _open_item_unlock(items, items_db, id, iid, players, mud):
        return

    itemID = items[iid]['id']
    linkedItemID = int(items_db[itemID]['linkedItem'])
    room_id = items_db[itemID]['exit']

    items_db[itemID]['state'] = 'lever down'
    items_db[itemID]['short_description'] = \
        items_db[itemID]['short_description'].replace('up', 'down')
    items_db[itemID]['long_description'] = \
        items_db[itemID]['long_description'].replace('up', 'down')
    if '|' in items_db[itemID]['exitName']:
        exitName = items_db[itemID]['exitName'].split('|')

        if linkedItemID > 0:
            desc = items_db[linkedItemID]['short_description']
            items_db[linkedItemID]['short_description'] = \
                desc.replace('closed', 'open')
            desc = items_db[linkedItemID]['long_description']
            items_db[linkedItemID]['long_description'] = \
                desc.replace('closed', 'open')
            items_db[linkedItemID]['state'] = 'open'
            linkedItemID2 = int(items_db[linkedItemID]['linkedItem'])
            if linkedItemID2 > 0:
                desc = items_db[linkedItemID2]['short_description']
                items_db[linkedItemID2]['short_description'] = \
                    desc.replace('closed', 'open')
                desc = items_db[linkedItemID2]['long_description']
                items_db[linkedItemID2]['long_description'] = \
                    desc.replace('closed', 'open')
                items_db[linkedItemID2]['state'] = 'open'

        if len(room_id) > 0:
            rm = players[id]['room']
            if exitName[0] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[0]]
            rooms[rm]['exits'][exitName[0]] = room_id

            rm = room_id
            if exitName[1] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[1]]
            rooms[rm]['exits'][exitName[1]] = players[id]['room']

    if len(items_db[itemID]['open_description']) > 0:
        mud.send_message_wrap(id, '<f220>',
                              items_db[itemID]['open_description'] +
                              '\n\n')
    else:
        mud.send_message(
            id, 'You pull ' +
            items_db[itemID]['article'] +
            ' ' + items_db[itemID]['name'] +
            '\n\n')


def _open_item_door(params, mud, playersDB: {}, players: {}, rooms: {},
                    npcs_db: {}, npcs: {}, items_db: {}, items: {},
                    env_db: {}, env: {}, eventDB: {}, event_schedule,
                    id: int, fights: {}, corpses: {}, target,
                    itemsInWorldCopy: {}, iid):
    if not _open_item_unlock(items, items_db, id, iid, players, mud):
        return

    itemID = items[iid]['id']
    linkedItemID = int(items_db[itemID]['linkedItem'])
    room_id = items_db[itemID]['exit']
    if '|' in items_db[itemID]['exitName']:
        exitName = items_db[itemID]['exitName'].split('|')

        items_db[itemID]['state'] = 'open'
        desc = items_db[itemID]['short_description']
        items_db[itemID]['short_description'] = \
            desc.replace('closed', 'open').replace('drawn up', 'drawn down')
        desc = items_db[itemID]['long_description']
        items_db[itemID]['long_description'] = \
            desc.replace('closed', 'open').replace('drawn up', 'drawn down')

        if linkedItemID > 0:
            desc = items_db[linkedItemID]['short_description']
            items_db[linkedItemID]['short_description'] = \
                desc.replace('closed',
                             'open').replace('drawn up', 'drawn down')
            desc = items_db[linkedItemID]['long_description']
            items_db[linkedItemID]['long_description'] = \
                desc.replace('closed',
                             'open').replace('drawn up', 'drawn down')
            items_db[linkedItemID]['state'] = 'open'

        if len(room_id) > 0:
            rm = players[id]['room']
            if exitName[0] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[0]]
            rooms[rm]['exits'][exitName[0]] = room_id

            rm = room_id
            if exitName[1] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[1]]
            rooms[rm]['exits'][exitName[1]] = players[id]['room']

    if len(items_db[itemID]['open_description']) > 0:
        mud.send_message(id, items_db[itemID]['open_description'] + '\n\n')
    else:
        mud.send_message(
            id, 'You open ' +
            items_db[itemID]['article'] +
            ' ' + items_db[itemID]['name'] +
            '\n\n')


def _open_item(params, mud, playersDB: {}, players: {}, rooms: {},
               npcs_db: {}, npcs: {}, items_db: {}, items: {},
               env_db: {}, env: {}, eventDB: {}, event_schedule,
               id: int, fights: {}, corpses: {}, blocklist,
               map_area: [], character_class_db: {}, spells_db: {},
               sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
               item_history: {}, markets: {}, cultures_db: {}):
    target = params.lower()

    if target.startswith('registration'):
        _enable_registrations(mud, id, players)
        return

    if target.startswith('the '):
        target = target.replace('the ', '')

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if items_db[items[iid]['id']]['state'] == 'closed':
                    _open_item_door(params, mud, playersDB, players, rooms,
                                    npcs_db, npcs, items_db, items,
                                    env_db, env,
                                    eventDB, event_schedule, id, fights,
                                    corpses, target, itemsInWorldCopy,
                                    iid)
                    return
                idx = items[iid]['id']
                if items_db[idx]['state'].startswith('container closed'):
                    _open_item_container(params, mud, playersDB, players,
                                         rooms, npcs_db, npcs, items_db,
                                         items, env_db, env, eventDB,
                                         event_schedule, id, fights, corpses,
                                         target, itemsInWorldCopy, iid)
                    return
    mud.send_message(id, "You can't open it.\n\n")


def _pull_lever(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist: {},
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    target = params.lower()

    if target.startswith('registration'):
        _enable_registrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if items_db[items[iid]['id']]['state'] == 'lever up':
                    _lever_down(params, mud, playersDB, players, rooms,
                                npcs_db, npcs, items_db, items, env_db,
                                env, eventDB, event_schedule, id, fights,
                                corpses, target, itemsInWorldCopy, iid)
                    return
                else:
                    mud.send_message(id, 'Nothing happens.\n\n')
                    return
    mud.send_message(id, "There's nothing to pull.\n\n")


def _push_lever(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    target = params.lower()
    if target.startswith('the '):
        target = target.replace('the ', '')

    if target.startswith('registration'):
        _enable_registrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if not items_db[items[iid]['id']]['state']:
                    _heave(params, mud, playersDB, players, rooms,
                           npcs_db, npcs, items_db, items, env_db, env,
                           eventDB, event_schedule, id, fights,
                           corpses, blocklist, map_area, character_class_db,
                           spells_db, sentiment_db, guilds_db, clouds,
                           races_db, item_history, markets, cultures_db)
                    return
                elif items_db[items[iid]['id']]['state'] == 'lever down':
                    _lever_up(params, mud, playersDB, players, rooms, npcs_db,
                              npcs, items_db, items, env_db, env, eventDB,
                              event_schedule, id, fights, corpses, target,
                              itemsInWorldCopy, iid)
                    return
    mud.send_message(id, 'Nothing happens.\n\n')


def _wind_lever(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    target = params.lower()

    if target.startswith('registration'):
        _enable_registrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if items_db[items[iid]['id']]['state'] == 'lever up':
                    _lever_down(params, mud, playersDB, players, rooms,
                                npcs_db, npcs, items_db, items, env_db,
                                env, eventDB, event_schedule, id,
                                fights, corpses, target,
                                itemsInWorldCopy, iid)
                    return
                else:
                    mud.send_message(id, "It's wound all the way.\n\n")
                    return
    mud.send_message(id, "There's nothing to wind.\n\n")


def _unwind_lever(params, mud, playersDB: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                  item_history: {}, markets: {}, cultures_db: {}):
    target = params.lower()

    if target.startswith('registration'):
        _enable_registrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if items_db[items[iid]['id']]['state'] == 'lever down':
                    _lever_up(params, mud, playersDB, players, rooms,
                              npcs_db, npcs, items_db, items, env_db, env,
                              eventDB, event_schedule, id, fights,
                              corpses, target, itemsInWorldCopy, iid)
                    return
                else:
                    mud.send_message(id, "It's unwound all the way.\n\n")
                    return
    mud.send_message(id, "There's nothing to unwind.\n\n")


def _close_item_container(params, mud, playersDB: {}, players: {}, rooms: {},
                          npcs_db: {}, npcs: {}, items_db: {}, items: {},
                          env_db: {}, env: {}, eventDB: {}, event_schedule,
                          id: int, fights: {}, corpses: {}, target,
                          itemsInWorldCopy: {}, iid):
    itemID = items[iid]['id']
    if items_db[itemID]['state'].startswith('container closed'):
        mud.send_message(id, "It's already closed\n\n")
        return

    if items_db[itemID]['state'].startswith('container open '):
        mud.send_message(id, "That's not possible.\n\n")
        return

    items_db[itemID]['state'] = \
        items_db[itemID]['state'].replace('open', 'closed')
    items_db[itemID]['short_description'] = \
        items_db[itemID]['short_description'].replace('open', 'closed')
    items_db[itemID]['long_description'] = \
        items_db[itemID]['long_description'].replace('open', 'closed')

    if len(items_db[itemID]['close_description']) > 0:
        mud.send_message(id, items_db[itemID]['close_description'] + '\n\n')
    else:
        itemArticle = items_db[itemID]['article']
        if itemArticle == 'a':
            itemArticle = 'the'
        mud.send_message(id, 'You close ' + itemArticle +
                         ' ' + items_db[itemID]['name'] + '.\n\n')


def _close_item_door(params, mud, playersDB: {}, players: {}, rooms: {},
                     npcs_db: {}, npcs: {}, items_db: {}, items: {},
                     env_db: {}, env: {}, eventDB: {}, event_schedule,
                     id: int, fights: {}, corpses: {}, target,
                     itemsInWorldCopy: {}, iid):
    itemID = items[iid]['id']
    linkedItemID = int(items_db[itemID]['linkedItem'])
    room_id = items_db[itemID]['exit']
    if '|' not in items_db[itemID]['exitName']:
        return

    exitName = items_db[itemID]['exitName'].split('|')

    items_db[itemID]['state'] = 'closed'
    items_db[itemID]['short_description'] = \
        items_db[itemID]['short_description'].replace('open', 'closed')
    items_db[itemID]['long_description'] = \
        items_db[itemID]['long_description'].replace('open', 'closed')

    if linkedItemID > 0:
        desc = items_db[linkedItemID]['short_description']
        items_db[linkedItemID]['short_description'] = \
            desc.replace('open', 'closed').replace('drawn down', 'drawn up')
        desc = items_db[linkedItemID]['long_description']
        items_db[linkedItemID]['long_description'] = \
            desc.replace('open', 'closed').replace('drawn down', 'drawn up')
        items_db[linkedItemID]['state'] = 'closed'

    if len(room_id) > 0:
        rm = players[id]['room']
        if exitName[0] in rooms[rm]['exits']:
            del rooms[rm]['exits'][exitName[0]]

        rm = room_id
        if exitName[1] in rooms[rm]['exits']:
            del rooms[rm]['exits'][exitName[1]]

    if len(items_db[itemID]['close_description']) > 0:
        mud.send_message(id, items_db[itemID]['close_description'] + '\n\n')
    else:
        mud.send_message(id, 'You close ' +
                         items_db[itemID]['article'] + ' ' +
                         items_db[itemID]['name'] + '\n\n')


def _close_item(params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    target = params.lower()

    if target.startswith('registration'):
        _disable_registrations(mud, id, players)
        return

    if target.startswith('the '):
        target = target.replace('the ', '')

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if items_db[items[iid]['id']]['state'] == 'open':
                    _close_item_door(params, mud, playersDB, players,
                                     rooms, npcs_db, npcs, items_db,
                                     items, env_db, env, eventDB,
                                     event_schedule, id, fights,
                                     corpses, target, itemsInWorldCopy,
                                     iid)
                    return
                idx = items[iid]['id']
                if items_db[idx]['state'].startswith('container open'):
                    _close_item_container(params, mud, playersDB, players,
                                          rooms, npcs_db, npcs, items_db,
                                          items, env_db, env, eventDB,
                                          event_schedule, id, fights,
                                          corpses, target, itemsInWorldCopy,
                                          iid)
                    return
    mud.send_message(id, "You can't close it.\n\n")


def _put_item(params, mud, playersDB: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {},
              env_db: {}, env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: {}, character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    if ' in ' not in params:
        if ' on ' not in params:
            if ' into ' not in params:
                if ' onto ' not in params:
                    if ' within ' not in params:
                        return

    target = []
    inon = ' in '
    if ' in ' in params:
        target = params.split(' in ')
    else:
        if ' into ' in params:
            target = params.split(' into ')
        else:
            if ' onto ' in params:
                target = params.split(' onto ')
                inon = ' onto '
            else:
                if ' on ' in params:
                    inon = ' on '
                    target = params.split(' on ')
                else:
                    inon = ' within '
                    target = params.split(' within ')

    if len(target) != 2:
        return

    itemID = 0
    itemName = target[0]
    containerName = target[1]

    if len(list(players[id]['inv'])) > 0:
        itemNameLower = itemName.lower()
        for i in list(players[id]['inv']):
            if items_db[int(i)]['name'].lower() == itemNameLower:
                itemID = int(i)
                itemName = items_db[int(i)]['name']

        if itemID == 0:
            for i in list(players[id]['inv']):
                if itemNameLower in items_db[int(i)]['name'].lower():
                    itemID = int(i)
                    itemName = items_db[int(i)]['name']

    if itemID == 0:
        mud.send_message(id, "You don't have " + itemName + ".\n\n")
        return

    itemsInWorldCopy = deepcopy(items)

    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            iName = items_db[items[iid]['id']]['name'].lower()
            if containerName.lower() in iName:
                idx = items[iid]['id']
                if items_db[idx]['state'].startswith('container open'):
                    if ' noput' not in items_db[idx]['state']:
                        maxItemsInContainer = items_db[idx]['useTimes']
                        len_cont = len(items_db[idx]['contains'])
                        if maxItemsInContainer == 0 or \
                           len_cont < maxItemsInContainer:
                            players[id]['inv'].remove(str(itemID))
                            _remove_item_from_clothing(players, id, itemID)
                            items_db[idx]['contains'].append(str(itemID))
                            idx = items[iid]['id']
                            mud.send_message(id, 'You put ' +
                                             items_db[itemID]['article'] +
                                             ' ' + items_db[itemID]['name'] +
                                             inon +
                                             items_db[idx]['article'] +
                                             ' ' +
                                             items_db[idx]['name'] +
                                             '.\n\n')
                        else:
                            mud.send_message(
                                id, 'No more items can be put ' + inon + ' ' +
                                items_db[items[iid]['id']]['article'] + ' ' +
                                items_db[items[iid]['id']]['name'] + ".\n\n")
                    else:
                        if 'on' in inon:
                            mud.send_message(
                                id, "You can't put anything on that.\n\n")
                        else:
                            mud.send_message(
                                id, "You can't put anything in that.\n\n")
                    return
                else:
                    idx = items[iid]['id']
                    if items_db[idx]['state'].startswith('container closed'):
                        if 'on' in inon:
                            mud.send_message(id, "You can't.\n\n")
                        else:
                            mud.send_message(id, "It's closed.\n\n")
                        return
                    else:
                        if 'on' in inon:
                            mud.send_message(
                                id, "You can't put anything on that.\n\n")
                        else:
                            mud.send_message(
                                id, "It can't contain anything.\n\n")
                        return

    mud.send_message(id, "You don't see " + containerName + ".\n\n")


def _get_random_room_in_regions(rooms: {}, regionsList: []) -> str:
    """Returns a random room within the given regions
    """
    possibleRooms = []
    for roomId, item in rooms.items():
        if item.get('region'):
            if item['region'] in regionsList:
                possibleRooms.append(roomId)
    if not possibleRooms:
        return None
    return random.choice(possibleRooms)


def _take(params, mud, playersDB: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, random_desc(
                players[id]['frozenDescription']) + '\n\n')
        return

    if params:
        if params == 'up':
            _stand(params, mud, playersDB, players, rooms, npcs_db, npcs,
                   items_db, items, env_db, env, eventDB, event_schedule,
                   id, fights, corpses, blocklist, map_area,
                   character_class_db,
                   spells_db, sentiment_db, guilds_db, clouds, races_db,
                   item_history, markets, cultures_db)
            return

        # get into, get through
        if params.startswith('into') or params.startswith('through'):
            _climb(params, mud, playersDB, players, rooms, npcs_db, npcs,
                   items_db, items, env_db, env, eventDB, event_schedule,
                   id, fights, corpses, blocklist, map_area,
                   character_class_db,
                   spells_db, sentiment_db, guilds_db, clouds, races_db,
                   item_history, markets, cultures_db)
            return

    if len(str(params)) < 3:
        return

    paramsStr = str(params)
    if _item_in_inventory(players, id, paramsStr, items_db):
        mud.send_message(id, 'You are already carring ' + str(params) + '\n\n')
        return

    if player_is_prone(id, players):
        mud.send_message(id, random_desc('You stand up<r>\n\n'))
        set_player_prone(id, players, False)
        return

    itemInDB = False
    itemName = None
    itemPickedUp = False
    itemIndex = None
    target = str(params).lower()
    if target.startswith('the '):
        target = params.replace('the ', '')

    for (iid, pl) in list(items.items()):
        iid2 = items[iid]['id']
        if items[iid]['room'] != players[id]['room']:
            continue
        if items_db[iid2]['name'].lower() != target:
            continue
        if int(items_db[iid2]['weight']) == 0:
            if items_db[iid2].get('takeFail'):
                desc = random_desc(items_db[iid2]['takeFail'])
                mud.send_message_wrap(id, '<f220>', desc + "\n\n")
            else:
                mud.send_message(id, "You can't pick that up.\n\n")
            return
        if _item_is_visible(id, players, iid2, items_db):
            # ID of the item to be picked up
            itemName = items_db[iid2]['name']
            itemInDB = True
            itemIndex = iid2
        break

    itemsInWorldCopy = deepcopy(items)

    if not itemInDB:
        # Try fuzzy match of the item name
        for (iid, pl) in list(itemsInWorldCopy.items()):
            if itemsInWorldCopy[iid]['room'] != players[id]['room']:
                continue
            itemIndex = itemsInWorldCopy[iid]['id']
            if target not in items_db[itemIndex]['name'].lower():
                continue
            if int(items_db[itemIndex]['weight']) == 0:
                if items_db[itemIndex].get('takeFail'):
                    desc = random_desc(items_db[itemIndex]['takeFail'])
                    mud.send_message_wrap(id, '<f220>', desc + "\n\n")
                else:
                    mud.send_message(id, "You can't pick that up.\n\n")
                return

            itemName = items_db[itemIndex]['name']
            if _item_in_inventory(players, id, itemName, items_db):
                mud.send_message(
                    id, 'You are already carring ' + itemName + '\n\n')
                return
            if _item_is_visible(id, players, itemIndex, items_db):
                # ID of the item to be picked up
                itemInDB = True
            break

    if itemInDB and itemIndex:
        for (iid, pl) in list(itemsInWorldCopy.items()):
            # item in same room as player
            if itemsInWorldCopy[iid]['room'] != players[id]['room']:
                continue
            itemIndex = itemsInWorldCopy[iid]['id']
            # item has the expected name
            if items_db[itemIndex]['name'] != itemName:
                continue
            # player can move
            if players[id]['canGo'] != 0:
                # is the item too heavy?
                players[id]['wei'] = \
                    player_inventory_weight(id, players, items_db)

                if players[id]['wei'] + items_db[itemIndex]['weight'] > \
                   _get_max_weight(id, players):
                    mud.send_message(id, "You can't carry any more.\n\n")
                    return

                # is the player restricted by a trap
                if player_is_trapped(id, players, rooms):
                    desc = (
                        "You're trapped",
                        "The trap restricts your ability to take anything",
                        "The trap restricts your movement"
                    )
                    mud.send_message(id, random_desc(desc) + '.\n\n')
                    return

                # add the item to the player's inventory
                players[id]['inv'].append(str(itemIndex))
                # update the weight of the player
                players[id]['wei'] = \
                    player_inventory_weight(id, players, items_db)
                update_player_attributes(id, players, items_db, itemIndex, 1)
                # remove the item from the dict
                if not items_db[itemIndex].get('respawnInRegion'):
                    del items[iid]
                else:
                    regionsList = items_db[itemIndex]['respawnInRegion']
                    newRoomId = _get_random_room_in_regions(rooms, regionsList)
                    if not newRoomId:
                        del items[iid]
                    else:
                        items[iid]['room'] = newRoomId
                itemPickedUp = True
                break
            else:
                mud.send_message(id, 'You try to pick up ' + itemName +
                                 " but find that your arms won't move.\n\n")
                return

    if itemPickedUp:
        mud.send_message(id, 'You pick up and place ' +
                         itemName + ' in your inventory.\n\n')
        itemPickedUp = False
    else:
        # are there any open containers with this item?
        if ' from ' in target:
            target2 = target.split(' from ')
            target = target2[0]

        for (iid, pl) in list(itemsInWorldCopy.items()):
            # is the item in the same room as the player?
            if itemsInWorldCopy[iid]['room'] != players[id]['room']:
                continue
            itemIndex = itemsInWorldCopy[iid]['id']
            # is this an open container
            if not items_db[itemIndex]['state'].startswith('container open'):
                continue
            # go through the items within the container
            for containerItemID in items_db[itemIndex]['contains']:
                # does the name match?
                itemName = items_db[int(containerItemID)]['name']
                if target not in itemName.lower():
                    continue
                # can the item be taken?
                if items_db[int(containerItemID)]['weight'] == 0:
                    if items_db[int(containerItemID)].get('takeFail'):
                        idx = int(containerItemID)
                        desc = \
                            random_desc(items_db[idx]['takeFail'])
                        mud.send_message_wrap(id, '<f220>', desc + "\n\n")
                    else:
                        mud.send_message(id, "You can't pick that up.\n\n")
                    return
                else:
                    # can the player move?
                    if players[id]['canGo'] != 0:
                        # is the item too heavy?
                        carryingWeight = \
                            player_inventory_weight(id, players, items_db)
                        idx = int(containerItemID)
                        if carryingWeight + items_db[idx]['weight'] > \
                           _get_max_weight(id, players):
                            mud.send_message(id,
                                             "You can't carry any more.\n\n")
                            return

                        # add the item to the player's inventory
                        players[id]['inv'].append(containerItemID)
                        # remove the item from the container
                        items_db[itemIndex]['contains'].remove(containerItemID)
                        idx = int(containerItemID)
                        mud.send_message(id, 'You take ' +
                                         items_db[idx]['article'] +
                                         ' ' +
                                         items_db[idx]['name'] +
                                         ' from ' +
                                         items_db[itemIndex]['article'] +
                                         ' ' +
                                         items_db[itemIndex]['name'] +
                                         '.\n\n')
                    else:
                        idx = int(containerItemID)
                        mud.send_message(id, 'You try to pick up ' +
                                         items_db[idx]['article'] +
                                         ' ' +
                                         items_db[idx]['name'] +
                                         " but find that your arms won't " +
                                         "move.\n\n")
                    return

        mud.send_message(id, 'You cannot see ' + target + ' anywhere.\n\n')
        itemPickedUp = False


def run_command(command, params, mud, playersDB: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    switcher = {
        "sendCommandError": _send_command_error,
        "go": _go,
        "north": _go_north,
        "n": _go_north,
        "south": _go_south,
        "s": _go_south,
        "east": _go_east,
        "e": _go_east,
        "west": _go_west,
        "w": _go_west,
        "up": _go_up,
        "u": _go_up,
        "down": _go_down,
        "d": _go_down,
        "in": _go_in,
        "out": _go_out,
        "o": _go_out,
        "bio": _bio,
        "health": _health,
        "who": _who,
        "quit": _quit,
        "exit": _quit,
        "look": _look,
        "read": _look,
        "l": _look,
        "examine": _look,
        "ex": _look,
        "inspect": _look,
        "ins": _look,
        "help": _help,
        "say": _say,
        "laugh": _laugh,
        "grimace": _grimace,
        "think": _thinking,
        "thinking": _thinking,
        "applaud": _applaud,
        "clap": _applaud,
        "astonished": _astonished,
        "surprised": _astonished,
        "surprise": _astonished,
        "confused": _confused,
        "bow": _bow,
        "calm": _calm,
        "cheer": _cheer,
        "curious": _curious,
        "curtsey": _curtsey,
        "frown": _frown,
        "scowl": _frown,
        "eyebrow": _eyebrow,
        "giggle": _giggle,
        "chuckle": _giggle,
        "grin": _grin,
        "yawn": _yawn,
        "wave": _wave,
        "nod": _nod,
        "smug": _smug,
        "relieved": _relieved,
        "relief": _relieved,
        "attack": _begin_attack,
        "shoot": _begin_attack,
        "take": _take,
        "get": _take,
        "put": _put_item,
        "give": _give,
        "gift": _give,
        "drop": _drop,
        "check": _check,
        "wear": _wear,
        "don": _wear,
        "unwear": _unwear,
        "unwearall": _unwear,
        "remove": _unwear,
        "removeall": _unwear,
        "use": _wield,
        "hold": _wield,
        "pick": _wield,
        "wield": _wield,
        "brandish": _wield,
        "stow": _stow,
        "step": _step_over,
        "whisper": _whisper,
        "teleport": _teleport,
        "goto": _teleport,
        "summon": _summon,
        "mute": _mute,
        "silence": _mute,
        "unmute": _unmute,
        "unsilence": _unmute,
        "freeze": _freeze,
        "unfreeze": _unfreeze,
        "tell": _tell,
        "taunt": _taunt,
        "jeer": _taunt,
        "jibe": _taunt,
        "gibe": _taunt,
        "deride": _taunt,
        "insult": _taunt,
        "barb": _taunt,
        "curse": _taunt,
        "swear": _taunt,
        "ridicule": _taunt,
        "scorn": _taunt,
        "besmirch": _taunt,
        "command": _tell,
        "instruct": _tell,
        "order": _tell,
        "ask": _tell,
        "open": _open_item,
        "close": _close_item,
        "wind": _wind_lever,
        "unwind": _unwind_lever,
        "pull": _pull_lever,
        "yank": _pull_lever,
        "push": _push_lever,
        "write": _write_on_item,
        "tag": _write_on_item,
        "eat": _eat,
        "drink": _eat,
        "kick": _kick,
        "change": _change_setting,
        "blocklist": _show_blocklist,
        "block": _block,
        "unblock": _unblock,
        "describe": _describe,
        "desc": _describe,
        "description": _describe,
        "conjure": _conjure,
        "make": _conjure,
        "cancel": _destroy,
        "banish": _destroy,
        "speak": _speak,
        "talk": _speak,
        "learn": _prepare_spell,
        "prepare": _prepare_spell,
        "destroy": _destroy,
        "cast": _cast_spell,
        "spell": _cast_spell,
        "spells": _spells,
        "dismiss": _dismiss,
        "clear": _clear_spells,
        "spellbook": _spells,
        "affinity": _affinity,
        "escape": _escape_trap,
        "cut": _escape_trap,
        "slash": _escape_trap,
        "resetuniverse": _resetUniverse,
        "shutdown": _shutdown,
        "inv": _check_inventory,
        "i": _check_inventory,
        "inventory": _check_inventory,
        "squeeze": _climb,
        "clamber": _climb,
        "board": _climb,
        "roll": _heave,
        "heave": _heave,
        "move": _heave,
        "haul": _heave,
        "heave": _heave,
        "displace": _heave,
        "disembark": _climb,
        "climb": _climb,
        "sit": _sit,
        "cross": _climb,
        "traverse": _climb,
        "jump": _jump,
        "images": _graphics,
        "pictures": _graphics,
        "graphics": _graphics,
        "chess": _chess,
        "cards": _help_cards,
        "deal": _deal,
        "hand": _hand_of_cards,
        "swap": _swap_a_card,
        "stick": _stick,
        "shuffle": _shuffle,
        "call": _call_card_game,
        "morris": _morris_game,
        "dodge": _dodge,
        "shove": _shove,
        "prone": _pose_prone,
        "stand": _stand,
        "buy": _buy,
        "purchase": _buy,
        "sell": _sell,
        "trade": _sell,
        "fish": _fish
    }

    try:
        switcher[command](params, mud, playersDB, players, rooms, npcs_db,
                          npcs, items_db, items, env_db, env, eventDB,
                          event_schedule, id, fights, corpses, blocklist,
                          map_area, character_class_db, spells_db,
                          sentiment_db, guilds_db, clouds, races_db,
                          item_history, markets, cultures_db)
    except Exception as e:
        # print(str(e))
        switcher["sendCommandError"](e, mud, playersDB, players, rooms,
                                     npcs_db, npcs, items_db, items,
                                     env_db, env, eventDB, event_schedule,
                                     id, fights, corpses, blocklist,
                                     map_area, character_class_db, spells_db,
                                     sentiment_db, guilds_db, clouds, races_db,
                                     item_history, markets, cultures_db)
