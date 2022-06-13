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
from functions import WEAR_LOCATION
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
from combat import holding_throwable
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


def _pose_prone(params, mud, players_db: {}, players: {}, rooms: {},
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
        msg_str = 'You lie down<r>\n\n'
        mud.send_message(id, random_desc(msg_str))
        set_player_prone(id, players, True)
    else:
        msg_str = 'You are already lying down<r>\n\n'
        mud.send_message(id, random_desc(msg_str))


def _stand(params, mud, players_db: {}, players: {}, rooms: {},
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
        msg_str = 'You stand up<r>\n\n'
        mud.send_message(id, random_desc(msg_str))
        set_player_prone(id, players, True)
    else:
        msg_str = 'You are already standing up<r>\n\n'
        mud.send_message(id, random_desc(msg_str))


def _shove(params, mud, players_db: {}, players: {}, rooms: {},
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


def _dodge(params, mud, players_db: {}, players: {}, rooms: {},
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


def _remove_item_from_clothing(players: {}, pid: int, item_id: int) -> None:
    """If worn an item is removed
    """
    for cstr in WEAR_LOCATION:
        if int(players[pid]['clo_' + cstr]) == item_id:
            players[pid]['clo_' + cstr] = 0


def _send_command_error(params, mud, players_db: {}, players: {}, rooms: {},
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
        witch_name = line.strip()
        if witch_name == name:
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
    with open(".disableRegistrations", 'w') as fp_dis:
        fp_dis.write('')
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


def _teleport(params, mud, players_db: {}, players: {}, rooms: {}, npcs_db: {},
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

        target_location = params[0:].strip().lower().replace('to ', '', 1)
        if len(target_location) != 0:
            curr_room = players[id]['room']
            if rooms[curr_room]['name'].strip().lower() == target_location:
                mud.send_message(
                    id, "You are already in " +
                    rooms[curr_room]['name'] +
                    "\n\n")
                return
            for rmid in rooms:
                if rooms[rmid]['name'].strip().lower() == target_location:
                    if is_attacking(players, id, fights):
                        stop_attack(players, id, npcs, fights)
                    mud.send_message(
                        id, "You teleport to " + rooms[rmid]['name'] + "\n\n")
                    pname = players[id]['name']
                    desc = '<f32>{}<r> suddenly vanishes.'.format(pname)
                    message_to_room_players(mud, players, id, desc + "\n\n")
                    players[id]['room'] = rmid
                    desc = '<f32>{}<r> suddenly appears.'.format(pname)

                    message_to_room_players(mud, players, id, desc + "\n\n")
                    _look('', mud, players_db, players, rooms, npcs_db, npcs,
                          items_db, items, env_db, env, eventDB,
                          event_schedule,
                          id, fights, corpses, blocklist, map_area,
                          character_class_db, spells_db, sentiment_db,
                          guilds_db, clouds, races_db, item_history, markets,
                          cultures_db)
                    return

            # try adding or removing "the"
            if target_location.startswith('the '):
                target_location = target_location.replace('the ', '')
            else:
                target_location = 'the ' + target_location

            pname = players[id]['name']
            desc1 = '<f32>{}<r> suddenly vanishes.'.format(pname)
            desc2 = '<f32>{}<r> suddenly appears.'.format(pname)
            for rmid in rooms:
                if rooms[rmid]['name'].strip().lower() == target_location:
                    mud.send_message(
                        id, "You teleport to " + rooms[rmid]['name'] + "\n\n")
                    message_to_room_players(mud, players, id,
                                            desc1 + "\n\n")
                    players[id]['room'] = rmid
                    message_to_room_players(mud, players, id,
                                            desc2 + "\n\n")
                    _look('', mud, players_db, players, rooms, npcs_db, npcs,
                          items_db, items, env_db, env, eventDB,
                          event_schedule,
                          id, fights, corpses, blocklist, map_area,
                          character_class_db, spells_db, sentiment_db,
                          guilds_db, clouds, races_db, item_history, markets,
                          cultures_db)
                    return

            mud.send_message(
                id, target_location +
                " isn't a place you can teleport to.\n\n")
        else:
            mud.send_message(id, "That's not a place.\n\n")
    else:
        mud.send_message(id, "You don't have enough powers to teleport.\n\n")


def _summon(params, mud, players_db: {}, players: {}, rooms: {}, npcs_db: {},
            npcs: {}, items_db: {}, items: {}, env_db: {}, env, eventDB: {},
            event_schedule, id: int, fights: {}, corpses: {}, blocklist,
            map_area: [], character_class_db: {}, spells_db: {},
            sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}) -> None:
    if players[id]['permissionLevel'] == 0:
        if _is_witch(id, players):
            target_player = params[0:].strip().lower()
            if len(target_player) != 0:
                for plyr in players:
                    if players[plyr]['name'].strip().lower() == target_player:
                        if players[plyr]['room'] != players[id]['room']:
                            pnam = players[plyr]['name']
                            desc = '<f32>{}<r> suddenly vanishes.'.format(pnam)
                            message_to_room_players(mud, players, plyr,
                                                    desc + "\n")
                            players[plyr]['room'] = players[id]['room']
                            rmid = players[plyr]['room']
                            mud.send_message(id, "You summon " +
                                             players[plyr]['name'] + "\n\n")
                            mud.send_message(plyr,
                                             "A mist surrounds you. When it " +
                                             "clears you find that you " +
                                             "are now in " +
                                             rooms[rmid]['name'] + "\n\n")
                        else:
                            mud.send_message(
                                id, players[plyr]['name'] +
                                " is already here.\n\n")
                        return
        else:
            mud.send_message(id, "You don't have enough powers for that.\n\n")


def _mute(params, mud, players_db: {}, players: {}, rooms: {}, npcs_db: {},
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
        for plyr in players:
            if players[plyr]['name'] == target:
                if not _is_witch(plyr, players):
                    players[plyr]['canSay'] = 0
                    players[plyr]['canAttack'] = 0
                    players[plyr]['canDirectMessage'] = 0
                    mud.send_message(
                        id, "You have muted " + target + "\n\n")
                else:
                    mud.send_message(
                        id, "You try to mute " + target +
                        " but their power is too strong.\n\n")
                return


def _unmute(params, mud, players_db: {}, players: {}, rooms: {}, npcs_db: {},
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
            for plyr in players:
                if players[plyr]['name'] == target:
                    if not _is_witch(plyr, players):
                        players[plyr]['canSay'] = 1
                        players[plyr]['canAttack'] = 1
                        players[plyr]['canDirectMessage'] = 1
                        mud.send_message(
                            id, "You have unmuted " + target + "\n\n")
                    return


def _freeze(params, mud, players_db: {}, players: {}, rooms: {}, npcs_db: {},
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
                for plyr in players:
                    if players[plyr]['whenDied']:
                        mud.send_message(
                            id,
                            "Freezing a player while dead is pointless\n\n")
                        continue
                    if players[plyr]['frozenStart'] > 0:
                        mud.send_message(
                            id, "They are already frozen\n\n")
                        continue
                    if target in players[plyr]['name']:
                        if not _is_witch(plyr, players):
                            # remove from any fights
                            for fight, _ in fights.items():
                                if plyr in (fights[fight]['s1id'],
                                            fights[fight]['s2id']):
                                    del fights[fight]
                                    players[plyr]['isInCombat'] = 0
                            players[plyr]['canGo'] = 0
                            players[plyr]['canAttack'] = 0
                            mud.send_message(
                                id, "You have frozen " + target + "\n\n")
                        else:
                            mud.send_message(
                                id, "You try to freeze " + target +
                                " but their power is too strong.\n\n")
                        return
                # freeze npcs
                for plyr in npcs:
                    if npcs[plyr]['whenDied']:
                        mud.send_message(
                            id, "Freezing while dead is pointless\n\n")
                        continue
                    if npcs[plyr]['frozenStart'] > 0:
                        mud.send_message(
                            id, "They are already frozen\n\n")
                        continue
                    if target in npcs[plyr]['name']:
                        if not _is_witch(plyr, npcs):
                            # remove from any fights
                            for fight, _ in fights.items():
                                if plyr in (fights[fight]['s1id'],
                                            fights[fight]['s2id']):
                                    del fights[fight]
                                    npcs[plyr]['isInCombat'] = 0

                            npcs[plyr]['canGo'] = 0
                            npcs[plyr]['canAttack'] = 0
                            mud.send_message(
                                id, "You have frozen " + target + "\n\n")
                        else:
                            mud.send_message(
                                id, "You try to freeze " + target +
                                " but their power is too strong.\n\n")
                        return


def _unfreeze(params, mud, players_db: {}, players: {}, rooms: {},
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
                    for plyr in players:
                        if target in players[plyr]['name']:
                            if not _is_witch(plyr, players):
                                players[plyr]['canGo'] = 1
                                players[plyr]['canAttack'] = 1
                                players[plyr]['frozenStart'] = 0
                                mud.send_message(
                                    id, "You have unfrozen " + target + "\n\n")
                            return
                    # unfreeze npcs
                    for plyr in npcs:
                        if target in npcs[plyr]['name']:
                            if not _is_witch(plyr, npcs):
                                npcs[plyr]['canGo'] = 1
                                npcs[plyr]['canAttack'] = 1
                                npcs[plyr]['frozenStart'] = 0
                                mud.send_message(
                                    id, "You have unfrozen " + target + "\n\n")
                            return


def _show_blocklist(params, mud, players_db: {}, players: {}, rooms: {},
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

    block_str = ''
    for blockedstr in blocklist:
        block_str = block_str + blockedstr + '\n'

    mud.send_message(id, "Blocked strings are:\n\n" + block_str + '\n')


def _block(params, mud, players_db: {}, players: {}, rooms: {},
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
        _show_blocklist(params, mud, players_db, players, rooms, npcs_db, npcs,
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


def _unblock(params, mud, players_db: {}, players: {}, rooms: {}, npcs_db: {},
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
        _show_blocklist(params, mud, players_db, players, rooms, npcs_db,
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


def _kick(params, mud, players_db: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    if not _is_witch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return

    player_name = params

    if len(player_name) == 0:
        mud.send_message(id, "Who?\n\n")
        return

    for pid, _ in list(players.items()):
        if players[pid]['name'] == player_name:
            remove_str = "Removing player " + player_name + "\n\n"
            mud.send_message(id, remove_str)
            print(remove_str)
            mud.handle_disconnect(pid)
            return

    mud.send_message(id, "There are no players with that name.\n\n")


def _shutdown(params, mud, players_db: {}, players: {}, rooms: {},
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
    for pid, _ in list(players.items()):
        shutdown_str = "Game server shutting down...\n\n"
        mud.send_message(pid, shutdown_str)
        print(shutdown_str)
        mud.handle_disconnect(pid)
    log("Shutting down", "info")
    sys.exit()


def _resetUniverse(params, mud, players_db: {}, players: {}, rooms: {},
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
    for pid, _ in list(players.items()):
        reset_str = "Game server shutting down...\n\n"
        mud.send_message(pid, reset_str)
        print(reset_str)
        mud.handle_disconnect(pid)
    log("Shutting down", "info")
    sys.exit()


def _quit(params, mud, players_db: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    print('quit command from ' + str(id))
    mud.handle_disconnect(id)


def _who(params, mud, players_db: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {},
         env_db: {}, env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db,
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    counter = 1
    if players[id]['permissionLevel'] == 0:
        is_witch = _is_witch(id, players)
        for plyr in players:
            if players[plyr]['name'] is None:
                continue

            if not is_witch:
                name = players[plyr]['name']
            else:
                if not _is_witch(plyr, players):
                    if players[plyr]['canSay'] == 1:
                        name = players[plyr]['name']
                    else:
                        name = players[plyr]['name'] + " (muted)"
                else:
                    name = "<f32>" + players[plyr]['name'] + "<r>"

            if players[plyr]['room'] is None:
                room = "None"
            else:
                rmid = rooms[players[plyr]['room']]
                room = "<f230>" + rmid['name']

            mud.send_message(id, str(counter) + ". " + name + " is in " + room)
            counter += 1
        mud.send_message(id, "\n")
    else:
        mud.send_message(id, "You do not have permission to do this.\n")


def _tell(params, mud, players_db: {}, players: {}, rooms: {},
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
        new_target = get_familiar_name(players, id, npcs)
        if len(new_target) > 0:
            target = new_target

    message = params.replace(target, "")[1:]
    if len(target) != 0 and len(message) != 0:
        cant_str = thieves_cant(message)
        for plyr in players:
            if players[plyr]['authenticated'] is not None and \
               players[plyr]['name'].lower() == target.lower():
                # print("sending a tell")
                if players[id]['name'].lower() == target.lower():
                    mud.send_message(
                        id, "It'd be pointless to send a tell " +
                        "message to yourself\n")
                    told = True
                    break
                else:
                    # don't tell if the string contains a blocked string
                    self_only = False
                    msglower = message.lower()
                    for blockedstr in blocklist:
                        if blockedstr in msglower:
                            self_only = True
                            break

                    if not self_only:
                        lang_list = players[plyr]['language']
                        if players[id]['speakLanguage'] in lang_list:
                            add_to_scheduler(
                                "0|msg|<f90>From " +
                                players[id]['name'] +
                                ": " + message +
                                '\n', plyr, event_schedule,
                                eventDB)
                            sentiment_score = \
                                get_sentiment(message, sentiment_db) + \
                                get_guild_sentiment(players, id, players,
                                                    plyr, guilds_db)
                            if sentiment_score >= 0:
                                increase_affinity_between_players(
                                    players, id, players, plyr, guilds_db)
                            else:
                                decrease_affinity_between_players(
                                    players, id, players, plyr, guilds_db)
                        else:
                            if players[id]['speakLanguage'] != 'cant':
                                add_to_scheduler(
                                    "0|msg|<f90>From " +
                                    players[id]['name'] +
                                    ": something in " +
                                    players[id]['speakLanguage'] +
                                    '\n', plyr, event_schedule,
                                    eventDB)
                            else:
                                add_to_scheduler(
                                    "0|msg|<f90>From " +
                                    players[id]['name'] +
                                    ": " + cant_str +
                                    '\n', plyr, event_schedule,
                                    eventDB)
                    mud.send_message(
                        id, "<f90>To " +
                        players[plyr]['name'] +
                        ": " + message +
                        "\n\n")
                    told = True
                    break
        if not told:
            for nid, _ in list(npcs.items()):
                if (npcs[nid]['room'] == players[id]['room']) or \
                   npcs[nid]['familiarOf'] == players[id]['name']:
                    if target.lower() in npcs[nid]['name'].lower():
                        message_lower = message.lower()
                        npc_conversation(mud, npcs, npcs_db, players,
                                         items, items_db, rooms, id,
                                         nid, message_lower,
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


def _whisper(params, mud, players_db: {}, players: {}, rooms: {},
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
    message_sent = False
    # print(message)
    # print(str(len(message)))
    if len(target) > 0:
        if len(message) > 0:
            cant_str = thieves_cant(message)
            for plyr in players:
                if players[plyr]['name'] is not None and \
                   players[plyr]['name'].lower() == target.lower():
                    if players[plyr]['room'] == players[id]['room']:
                        if players[plyr]['name'].lower() != \
                           players[id]['name'].lower():

                            # don't whisper if the string contains a blocked
                            # string
                            self_only = False
                            msglower = message[1:].lower()
                            for blockedstr in blocklist:
                                if blockedstr in msglower:
                                    self_only = True
                                    break

                            sentiment_score = \
                                get_sentiment(message[1:], sentiment_db) + \
                                get_guild_sentiment(players, id, players,
                                                    plyr, guilds_db)
                            if sentiment_score >= 0:
                                increase_affinity_between_players(
                                    players, id, players, plyr, guilds_db)
                            else:
                                decrease_affinity_between_players(
                                    players, id, players, plyr, guilds_db)

                            mud.send_message(
                                id, "You whisper to <f32>" +
                                players[plyr]['name'] + "<r>: " +
                                message[1:] + '\n')
                            if not self_only:
                                lang_list = players[plyr]['language']
                                if players[id]['speakLanguage'] in lang_list:
                                    mud.send_message(
                                        plyr, "<f162>" + players[id]['name'] +
                                        " whispers: " + message[1:] + '\n')
                                else:
                                    if players[id]['speakLanguage'] != 'cant':
                                        mud.send_message(
                                            plyr, "<f162>" +
                                            players[id]['name'] +
                                            " whispers something in " +
                                            players[id]['speakLanguage'] +
                                            '\n')
                                    else:
                                        mud.send_message(
                                            plyr, "<f162>" +
                                            players[id]['name'] +
                                            " whispers:  " + cant_str + '\n')
                            message_sent = True
                            break
                        else:
                            mud.send_message(
                                id, "You would probably look rather silly " +
                                "whispering to yourself.\n")
                            message_sent = True
                            break
            if not message_sent:
                mud.send_message(
                    id, "<f32>" + target + "<r> is not here with you.\n")
        else:
            mud.send_message(id, "What would you like to whisper?\n")
    else:
        mud.send_message(id, "Who would you like to whisper to??\n")


def _help(params, mud, players_db: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db,
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    if params.lower().startswith('card'):
        _help_cards(params, mud, players_db, players,
                    rooms, npcs_db, npcs, items_db,
                    items, env_db, env, eventDB, event_schedule,
                    id, fights, corpses,
                    blocklist, map_area, character_class_db,
                    spells_db, sentiment_db, guilds_db, clouds, races_db,
                    item_history, markets, cultures_db)
        return
    if params.lower().startswith('chess'):
        _help_chess(params, mud, players_db, players,
                    rooms, npcs_db, npcs, items_db,
                    items, env_db, env, eventDB,
                    event_schedule, id, fights, corpses,
                    blocklist, map_area, character_class_db,
                    spells_db, sentiment_db, guilds_db, clouds, races_db,
                    item_history, markets, cultures_db)
        return
    if params.lower().startswith('morris'):
        _help_morris(params, mud, players_db, players,
                     rooms, npcs_db, npcs, items_db,
                     items, env_db, env, eventDB,
                     event_schedule, id, fights, corpses,
                     blocklist, map_area, character_class_db,
                     spells_db, sentiment_db,
                     guilds_db, clouds, races_db, item_history, markets,
                     cultures_db)
        return
    if params.lower().startswith('witch'):
        _help_witch(params, mud, players_db, players,
                    rooms, npcs_db, npcs, items_db,
                    items, env_db, env, eventDB,
                    event_schedule, id, fights, corpses,
                    blocklist, map_area, character_class_db,
                    spells_db, sentiment_db, guilds_db, clouds, races_db,
                    item_history, markets, cultures_db)
        return
    if params.lower().startswith('spell'):
        _help_spell(params, mud, players_db, players,
                    rooms, npcs_db, npcs, items_db,
                    items, env_db, env, eventDB, event_schedule,
                    id, fights, corpses,
                    blocklist, map_area, character_class_db,
                    spells_db, sentiment_db, guilds_db, clouds, races_db,
                    item_history, markets, cultures_db)
        return
    if params.lower().startswith('emot'):
        _help_emote(params, mud, players_db, players,
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
                     '  <f220>throw [weapon] at [target]<f255>' +
                     '              - ' +
                     'Throw a weapon at a target, ' +
                     "e.g. 'throw dagger at zombie'")
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


def _help_spell(params, mud, players_db: {}, players: {}, rooms: {},
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


def _help_emote(params, mud, players_db: {}, players: {}, rooms: {},
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


def _help_witch(params, mud, players_db: {}, players: {}, rooms: {},
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


def _help_morris(params, mud, players_db: {}, players: {}, rooms,
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


def _help_chess(params, mud, players_db: {}, players: {}, rooms: {},
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


def _help_cards(params, mud, players_db: {}, players: {}, rooms: {},
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


def _cast_spell_on_player(mud, spell_name: str, players: {}, id, npcs: {},
                          p, spell_details: {}):
    if npcs[p]['room'] != players[id]['room']:
        mud.send_message(id, "They're not here.\n\n")
        return

    if spell_details['action'].startswith('protect'):
        npcs[p]['tempHitPoints'] = spell_details['hp']
        npcs[p]['tempHitPointsDuration'] = \
            time_string_to_sec(spell_details['duration'])
        npcs[p]['tempHitPointsStart'] = int(time.time())

    if spell_details['action'].startswith('cure'):
        if npcs[p]['hp'] < npcs[p]['hpMax']:
            npcs[p]['hp'] += randint(1, spell_details['hp'])
            if npcs[p]['hp'] > npcs[p]['hpMax']:
                npcs[p]['hp'] = npcs[p]['hpMax']

    if spell_details['action'].startswith('charm'):
        charm_target = players[id]['name']
        charm_value = int(npcs[p]['cha'] + players[id]['cha'])
        npcs[p]['tempCharm'] = charm_value
        npcs[p]['tempCharmTarget'] = charm_target
        npcs[p]['tempCharmDuration'] = \
            time_string_to_sec(spell_details['duration'])
        npcs[p]['tempCharmStart'] = int(time.time())
        if npcs[p]['affinity'].get(charm_target):
            npcs[p]['affinity'][charm_target] += charm_value
        else:
            npcs[p]['affinity'][charm_target] = charm_value

    if spell_details['action'].startswith('friend'):
        if players[id]['cha'] < npcs[p]['cha']:
            remove_prepared_spell(players, id, spell_name)
            mud.send_message(id, "You don't have enough charisma.\n\n")
            return
        player_name = players[id]['name']
        if npcs[p]['affinity'].get(player_name):
            npcs[p]['affinity'][player_name] += 1
        else:
            npcs[p]['affinity'][player_name] = 1

    if spell_details['action'].startswith('attack'):
        if len(spell_details['damageType']
               ) == 0 or spell_details['damageType'] == 'str':
            npcs[p]['hp'] = npcs[p]['hp'] - randint(1, spell_details['damage'])
        else:
            damage_type = spell_details['damageType']
            if npcs[p].get(damage_type):
                npcs[p][damage_type] = npcs[p][damage_type] - \
                    randint(1, spell_details['damage'])
                if npcs[p][damage_type] < 0:
                    npcs[p][damage_type] = 0

    if spell_details['action'].startswith('frozen'):
        npcs[p]['frozenDescription'] = spell_details['actionDescription']
        npcs[p]['frozenDuration'] = \
            time_string_to_sec(spell_details['duration'])
        npcs[p]['frozenStart'] = int(time.time())

    _show_spell_image(mud, id, spell_name.replace(' ', '_'), players)

    mud.send_message(
        id,
        random_desc(spell_details['description']).format('<f32>' +
                                                         npcs[p]['name'] +
                                                         '<r>') + '\n\n')

    second_desc = random_desc(spell_details['description_second'])
    if npcs == players and len(second_desc) > 0:
        mud.send_message(
            p,
            second_desc.format(players[id]['name'],
                               'you') + '\n\n')

    remove_prepared_spell(players, id, spell_name)


def _cast_spell_undirected(params, mud, players_db: {}, players: {}, rooms: {},
                           npcs_db: {}, npcs: {}, items_db: {}, items: {},
                           env_db: {}, env: {}, eventDB: {}, event_schedule,
                           id: int, fights: {}, corpses: {}, blocklist,
                           map_area: [], character_class_db: {}, spells_db: {},
                           sentiment_db: {}, spell_name: {}, spell_details: {},
                           clouds: {}, races_db: {}, guilds_db: {},
                           item_history: {}, markets: {}, cultures_db: {}):
    spell_action = spell_details['action']
    if spell_action.startswith('familiar'):
        _show_spell_image(mud, id, spell_name.replace(' ', '_'), players)
        _conjure_npc(spell_details['action'], mud, players_db, players,
                     rooms, npcs_db, npcs, items_db, items, env_db, env,
                     eventDB, event_schedule, id, fights, corpses,
                     blocklist, map_area, character_class_db, spells_db,
                     sentiment_db, guilds_db, clouds, races_db,
                     item_history, markets, cultures_db)
        return
    if spell_action.startswith('defen'):
        # defense spells
        if spell_name.endswith('shield') and spell_details.get('armor'):
            _show_spell_image(mud, id, "magic_shield", players)
            if not players[id]["magicShield"]:
                remove_prepared_spell(players, id, spell_name)
                players[id]['magicShield'] = spell_details['armor']
                players[id]['magicShieldStart'] = int(time.time())
                players[id]["magicShieldDuration"] = \
                    time_string_to_sec(spell_details['duration'])
                mud.send_message(id, "Magic shield active.\n\n")

                # inform other players in the room
                for pid in players:
                    if pid == id:
                        continue
                    if players[pid]['room'] == players[id]['room']:
                        _show_spell_image(mud, pid, "magic_shield", players)
                        msg_str = \
                            '<f32>' + players[id]['name'] + \
                            '<r> activates a magic shield'
                        mud.send_message(pid, msg_str + ".\n\n")
            else:
                mud.send_message(id, "Magic shield is already active.\n\n")
            return
    mud.send_message(id, "Nothing happens.\n\n")


def _cast_spell(params, mud, players_db: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    # cast fishing rod
    if 'fishing' in params or params == 'rod' or params == 'fish':
        _start_fishing(params, mud, players_db, players, rooms,
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

    cast_str = params.lower().strip()
    if cast_str.startswith('the spell '):
        cast_str = cast_str.replace('the spell ', '', 1)
    if cast_str.startswith('a '):
        cast_str = cast_str.replace('a ', '', 1)
    if cast_str.startswith('the '):
        cast_str = cast_str.replace('the ', '', 1)
    if cast_str.startswith('spell '):
        cast_str = cast_str.replace('spell ', '', 1)
    cast_at = ''
    spell_name = ''
    if ' at ' in cast_str:
        spell_name = cast_str.split(' at ')[0].strip()
        cast_at = cast_str.split(' at ')[1].strip()
    else:
        if ' on ' in cast_str:
            spell_name = cast_str.split(' on ')[0].strip()
            cast_at = cast_str.split(' on ')[1].strip()
        else:
            spell_name = cast_str.strip()

    if not players[id]['preparedSpells'].get(spell_name):
        mud.send_message(id, "That's not a prepared spell.\n\n")
        return

    spell_details = None
    if spells_db.get('cantrip'):
        if spells_db['cantrip'].get(spell_name):
            spell_details = spells_db['cantrip'][spell_name]
    if spell_details is None:
        max_spell_level = _get_player_max_spell_level(players, id)
        for level in range(1, max_spell_level + 1):
            if spells_db[str(level)].get(spell_name):
                spell_details = spells_db[str(level)][spell_name]
                break
    if spell_details is None:
        mud.send_message(id, "You have no knowledge of that spell.\n\n")
        return

    if len(cast_at) > 0:
        for p in players:
            if cast_at not in players[p]['name'].lower():
                continue
            if p == id:
                mud.send_message(id, "This is not a hypnosis spell.\n\n")
                return
            _cast_spell_on_player(
                mud, spell_name, players, id, players, p, spell_details)
            return

        for p in npcs:
            if cast_at not in npcs[p]['name'].lower():
                continue

            if npcs[p]['familiarOf'] == players[id]['name']:
                mud.send_message(
                    id, "You can't cast a spell on your own familiar!\n\n")
                return

            _cast_spell_on_player(mud, spell_name, players, id, npcs,
                                  p, spell_details)
            return
    else:
        _cast_spell_undirected(params, mud, players_db, players, rooms,
                               npcs_db, npcs, items_db, items, env_db,
                               env, eventDB, event_schedule, id, fights,
                               corpses, blocklist, map_area,
                               character_class_db, spells_db, sentiment_db,
                               spell_name, spell_details,
                               clouds, races_db, guilds_db,
                               item_history, markets, cultures_db)


def _player_affinity(params, mud, players_db: {}, players: {}, rooms: {},
                     npcs_db: {}, npcs: {}, items_db: {}, items: {},
                     env_db: {}, env: {}, eventDB: {}, event_schedule: {},
                     id: int, fights: {}, corpses: {}, blocklist,
                     map_area: [], character_class_db: {}, spells_db: {},
                     sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                     item_history: {}, markets: {}, cultures_db: {}):
    other_player = params.lower().strip()
    if len(other_player) == 0:
        mud.send_message(id, 'With which player?\n\n')
        return
    if players[id]['affinity'].get(other_player):
        affinity = players[id]['affinity'][other_player]
        if affinity >= 0:
            mud.send_message(
                id, 'Your affinity with <f32><u>' +
                other_player + '<r> is <f15><b2>+' +
                str(affinity) + '<r>\n\n')
        else:
            mud.send_message(
                id, 'Your affinity with <f32><u>' +
                other_player + '<r> is <f15><b88>' +
                str(affinity) + '<r>\n\n')
        return
    mud.send_message(id, "You don't have any affinity with them.\n\n")


def _clear_spells(params, mud, players_db: {}, players: {}, rooms: {},
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


def _spells_list(params, mud, players_db: {}, players: {}, rooms: {},
                 npcs_db: {}, npcs: {}, items_db: {}, items: {},
                 env_db: {}, env: {}, eventDB: {}, event_schedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 map_area: [], character_class_db: {}, spells_db: {},
                 sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                 item_history: {}, markets: {}, cultures_db: {}):
    if len(players[id]['preparedSpells']) > 0:
        mud.send_message(id, 'Your prepared spells:\n')
        for name, _ in players[id]['preparedSpells'].items():
            mud.send_message(id, '  <b234>' + name + '<r>')
        mud.send_message(id, '\n')
    else:
        mud.send_message(id, 'You have no spells prepared.\n\n')


def _prepare_spell_at_level(params, mud, players_db: {},
                            players: {}, rooms: {},
                            npcs_db: {}, npcs: {}, items_db: {}, items: {},
                            env_db: {}, env: {}, eventDB: {}, event_schedule,
                            id: int, fights: {}, corpses: {}, blocklist,
                            map_area: [], character_class_db: {},
                            spells_db: {}, spell_name: {}, level: {}):
    for name, details in spells_db[level].items():
        if name.lower() == spell_name:
            if name.lower() not in players[id]['preparedSpells']:
                if len(spells_db[level][name]['items']) == 0:
                    players[id]['preparedSpells'][name] = 1
                else:
                    for required in spells_db[level][name]['items']:
                        required_item_found = False
                        for i in list(players[id]['inv']):
                            if int(i) == required:
                                required_item_found = True
                                break
                        if not required_item_found:
                            mud.send_message(
                                id, 'You need <b234>' +
                                items_db[required]['article'] +
                                ' ' + items_db[required]['name'] +
                                '<r>\n\n')
                            return True
                players[id]['prepareSpell'] = spell_name
                players[id]['prepareSpellProgress'] = 0
                players[id]['prepareSpellTime'] = time_string_to_sec(
                    details['prepareTime'])
                if len(details['prepareTime']) > 0:
                    mud.send_message(
                        id,
                        'You begin preparing the spell <b234>' +
                        spell_name + '<r>. It will take ' +
                        details['prepareTime'] + '.\n\n')
                else:
                    mud.send_message(
                        id,
                        'You begin preparing the spell <b234>' +
                        spell_name + '<r>.\n\n')
                return True
    return False


def _player_max_cantrips(players: {}, id) -> int:
    """Returns the maximum number of cantrips which the player can prepare
    """
    max_cantrips = 0
    for prof in players[id]['proficiencies']:
        if isinstance(prof, list):
            continue
        if prof.lower().startswith('cantrip'):
            if '(' in prof and ')' in prof:
                cantrips = int(prof.split('(')[1].replace(')', ''))
                if cantrips > max_cantrips:
                    max_cantrips = cantrips
    return max_cantrips


def _get_player_max_spell_level(players: {}, id) -> int:
    """Returns the maximum spell level of the player
    """
    for prof in players[id]['proficiencies']:
        if isinstance(prof, list):
            spell_list = list(prof)
            if len(spell_list) > 0:
                if spell_list[0].lower() == 'spell':
                    return len(spell_list) - 1
    return -1


def _get_player_spell_slots_at_spell_level(players: {}, id,
                                           spell_level: str) -> int:
    """Returns the maximum spell slots at the given spell level
    """
    for prof in players[id]['proficiencies']:
        if isinstance(prof, list):
            spell_list = list(prof)
            if len(spell_list) > 0:
                if spell_list[0].lower() == 'spell':
                    return spell_list[spell_level]
    return 0


def _get_player_used_slots_at_spell_level(players: {}, id, spellLevel,
                                          spells_db: {}):
    """Returns the used spell slots at the given spell level
    """
    if not spells_db.get(str(spellLevel)):
        return 0

    used_counter = 0
    for spell_name, _ in spells_db[str(spellLevel)].items():
        if spell_name in players[id]['preparedSpells']:
            used_counter += 1
    return used_counter


def _player_prepared_cantrips(players, id, spells_db: {}) -> int:
    """Returns the number of cantrips which the player has prepared
    """
    prepared_counter = 0
    for spell_name in players[id]['preparedSpells']:
        for cantripname, _ in spells_db['cantrip'].items():
            if cantripname == spell_name:
                prepared_counter += 1
                break
    return prepared_counter


def _prepare_spell(params, mud, players_db: {}, players: {}, rooms: {},
                   npcs_db: {}, npcs: {}, items_db: {}, items: {},
                   env_db: {}, env: {}, eventDB: {}, event_schedule,
                   id: int, fights: {}, corpses: {}, blocklist,
                   map_area: [], character_class_db: {}, spells_db: {},
                   sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                   item_history: {}, markets: {}, cultures_db: {}):
    spell_name = params.lower().strip()

    # "learn spells" or "prepare spells" shows list of spells
    if spell_name == 'spell' or spell_name == 'spells':
        spell_name = ''

    max_cantrips = _player_max_cantrips(players, id)
    max_spell_level = _get_player_max_spell_level(players, id)

    if max_spell_level < 0 and max_cantrips == 0:
        mud.send_message(id, "You can't prepare spells.\n\n")
        return

    if len(spell_name) == 0:
        # list spells which can be prepared
        mud.send_message(id, 'Spells you can prepare are:\n')

        if max_cantrips > 0 and spells_db.get('cantrip'):
            for name, _ in spells_db['cantrip'].items():
                if name.lower() not in players[id]['preparedSpells']:
                    spell_classes = spells_db['cantrip'][name]['classes']
                    if players[id]['characterClass'] in spell_classes or \
                       len(spell_classes) == 0:
                        mud.send_message(id, '  <f220>-' + name + '<r>')

        if max_spell_level > 0:
            for level in range(1, max_spell_level + 1):
                if not spells_db.get(str(level)):
                    continue
                for name, _ in spells_db[str(level)].items():
                    if name.lower() not in players[id]['preparedSpells']:
                        spell_classes = spells_db[str(level)][name]['classes']
                        if players[id]['characterClass'] in spell_classes or \
                           len(spell_classes) == 0:
                            mud.send_message(id, '  <b234>' + name + '<r>')
        mud.send_message(id, '\n')
    else:
        if spell_name.startswith('the spell '):
            spell_name = spell_name.replace('the spell ', '')
        if spell_name.startswith('spell '):
            spell_name = spell_name.replace('spell ', '')
        if spell_name == players[id]['prepareSpell']:
            mud.send_message(id, 'You are already preparing that.\n\n')
            return

        if max_cantrips > 0 and spells_db.get('cantrip'):
            prepared = _player_prepared_cantrips(players, id, spells_db)
            if prepared < max_cantrips:
                if _prepare_spell_at_level(params, mud, players_db, players,
                                           rooms, npcs_db, npcs, items_db,
                                           items, env_db, env, eventDB,
                                           event_schedule, id, fights,
                                           corpses, blocklist, map_area,
                                           character_class_db, spells_db,
                                           spell_name, 'cantrip'):
                    return
            else:
                mud.send_message(
                    id, "You can't prepare any more cantrips.\n\n")
                return

        if max_spell_level > 0:
            for level in range(1, max_spell_level + 1):
                if not spells_db.get(str(level)):
                    continue
                max_slots = \
                    _get_player_spell_slots_at_spell_level(players, id, level)
                used_slots = \
                    _get_player_used_slots_at_spell_level(players, id,
                                                          level, spells_db)
                if used_slots < max_slots:
                    if _prepare_spell_at_level(params, mud, players_db,
                                               players, rooms, npcs_db, npcs,
                                               items_db, items, env_db, env,
                                               eventDB, event_schedule, id,
                                               fights, corpses, blocklist,
                                               map_area,
                                               character_class_db,
                                               spells_db, spell_name,
                                               str(level)):
                        return
                else:
                    mud.send_message(
                        id,
                        "You have prepared the maximum level" +
                        str(level) + " spells.\n\n")
                    return

        mud.send_message(id, "That's not a spell.\n\n")


def _speak(params, mud, players_db: {}, players: {}, rooms: {},
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


def _taunt(params, mud, players_db: {}, players: {}, rooms: {},
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
            new_target = get_familiar_name(players, id, npcs)
            if len(new_target) > 0:
                target = new_target

        full_target = target
        if target.startswith('the '):
            target = target.replace('the ', '', 1)

        taunt_first_person = \
            random_desc('taunt|insult|besmirch|' +
                        'gibe|ridicule')
        if taunt_first_person != 'besmirch':
            taunt_second_person = taunt_first_person + 's'
        else:
            taunt_second_person = taunt_first_person + 'es'

        is_done = False
        for plyr in players:
            if players[plyr]['authenticated'] is not None and \
               target.lower() in players[plyr]['name'].lower() and \
               players[plyr]['room'] == players[id]['room']:
                if target.lower() in players[id]['name'].lower():
                    mud.send_message_wrap(
                        id, '<f230>', "It'd be pointless to taunt yourself!\n")
                else:
                    lang_list = players[plyr]['language']
                    if players[id]['speakLanguage'] in lang_list:
                        mud.send_message_wrap(
                            plyr, '<f230>',
                            players[id]['name'] + " " +
                            taunt_second_person + " you\n")
                        decrease_affinity_between_players(
                            players, plyr, players, id, guilds_db)
                    else:
                        mud.send_message_wrap(
                            plyr, '<f230>',
                            players[id]['name'] + " says something in " +
                            players[id]['speakLanguage'] + '\n')
                    decrease_affinity_between_players(
                        players, id, players, plyr, guilds_db)
                is_done = True
                break
        if not is_done:
            for plyr in npcs:
                if target.lower() in npcs[plyr]['name'].lower() and \
                   npcs[plyr]['room'] == players[id]['room']:
                    if target.lower() in players[id]['name'].lower():
                        mud.send_message_wrap(
                            id, '<f230>',
                            "It'd be pointless to " + taunt_first_person +
                            " yourself!\n")
                    else:
                        lang_list = npcs[plyr]['language']
                        if players[id]['speakLanguage'] in lang_list:
                            decrease_affinity_between_players(
                                npcs, plyr, players, id, guilds_db)
                    decrease_affinity_between_players(
                        players, id, npcs, plyr, guilds_db)
                    is_done = True
                    break

        if is_done:
            for plyr in players:
                if plyr == id:
                    taunt_severity = \
                        random_desc('mercilessly|severely|harshly|' +
                                    'loudly|blatantly|coarsely|' +
                                    'crudely|unremittingly|' +
                                    'witheringly|pitilessly')
                    descr = "You " + taunt_severity + ' ' + \
                        taunt_first_person + ' ' + full_target
                    mud.send_message_wrap(id, '<f230>', descr + ".\n")
                    continue
                if players[plyr]['room'] == players[id]['room']:
                    mud.send_message_wrap(
                        id, '<f230>',
                        players[id]['name'] + ' ' + taunt_second_person +
                        ' ' + full_target + "\n")
        else:
            mud.send_message_wrap(
                id, '<f230>', target + ' is not here.\n')
    else:
        mud.send_message_wrap(
            id, '<f230>',
            'To find yourself unable to taunt at this time.\n')


def _say(params, mud, players_db: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
         env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    if players[id]['canSay'] == 1:

        # don't say if the string contains a blocked string
        self_only = False
        params2 = params.lower()
        for blockedstr in blocklist:
            if blockedstr in params2:
                self_only = True
                break

        # go through every player in the game
        cant_str = thieves_cant(params)
        for pid, _ in list(players.items()):
            # if they're in the same room as the player
            if players[pid]['room'] == players[id]['room']:
                # can the other player see this player?
                if not player_is_visible(mud, pid, players, id, players):
                    continue
                if self_only is False or pid == id:
                    lang_list = players[pid]['language']
                    if players[id]['speakLanguage'] in lang_list:
                        sentiment_score = \
                            get_sentiment(params, sentiment_db) + \
                            get_guild_sentiment(players, id, players,
                                                pid, guilds_db)

                        if sentiment_score >= 0:
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
                        pname = players[id]['name']
                        desc = \
                            '<f220>{}<r> says: <f159>{}'.format(pname, params)
                        mud.send_message_wrap(
                            pid, '<f230>', desc + "\n\n")
                    else:
                        pname = players[id]['name']
                        if players[id]['speakLanguage'] != 'cant':
                            plang = players[id]['speakLanguage']
                            desc = \
                                '<f220>{}<r> says '.format(pname) + \
                                'something in <f159>{}<r>'.format(plang)
                            mud.send_message_wrap(
                                pid, '<f230>', desc + "\n\n")
                        else:
                            mud.send_message_wrap(
                                pid, '<f230>',
                                '<f220>{}<r> says: '.format(pname) +
                                '<f159>{}'.format(cant_str) + "\n\n")
    else:
        mud.send_message_wrap(
            id, '<f230>',
            'To your horror, you realise you somehow cannot force ' +
            'yourself to utter a single word!\n')


def _emote(params, mud, players_db: {}, players: {}, rooms: {},
           id: int, emoteDescription: str):
    if players[id]['canSay'] == 1:
        # go through every player in the game
        for pid, _ in list(players.items()):
            # if they're in the same room as the player
            if players[pid]['room'] == players[id]['room']:
                # can the other player see this player?
                if not player_is_visible(mud, pid, players, id, players):
                    continue

                # send them a message telling them what the player did
                pname = players[id]['name']
                desc = \
                    '<f220>{}<r> {}<f159>'.format(pname, emoteDescription)
                mud.send_message_wrap(
                    pid, '<f230>', desc + "\n\n")
    else:
        mud.send_message_wrap(
            id, '<f230>',
            'To your horror, you realise you somehow cannot force ' +
            'yourself to make any expression!\n')


def _laugh(params, mud, players_db: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
           env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms, id, 'laughs')


def _thinking(params, mud, players_db: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
              env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms,
           id, 'is thinking')


def _grimace(params, mud, players_db: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms,
           id, 'grimaces')


def _applaud(params, mud, players_db: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms, id, 'applauds')


def _nod(params, mud, players_db: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
         env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms, id, 'nods')


def _wave(params, mud, players_db: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
          env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms, id, 'waves')


def _astonished(params, mud, players_db: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
                env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, blocklist,
                map_area: [], character_class_db: {}, spells_db: {},
                sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms,
           id, 'is astonished')


def _confused(params, mud, players_db: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
              env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms,
           id, 'looks confused')


def _bow(params, mud, players_db: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
         env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms,
           id, 'takes a bow')


def _calm(params, mud, players_db: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
          env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms,
           id, 'looks calm')


def _cheer(params, mud, players_db: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
           env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms,
           id, 'cheers heartily')


def _curious(params, mud, players_db: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms,
           id, 'looks curious')


def _curtsey(params, mud, players_db: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms, id, 'curtseys')


def _frown(params, mud, players_db: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
           env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms, id, 'frowns')


def _eyebrow(params, mud, players_db: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms,
           id, 'raises an eyebrow')


def _giggle(params, mud, players_db: {}, players: {}, rooms: {},
            npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
            env: {}, eventDB: {}, event_schedule,
            id: int, fights: {}, corpses: {}, blocklist,
            map_area: [], character_class_db: {}, spells_db: {},
            sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms, id, 'giggles')


def _grin(params, mud, players_db: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
          env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms, id, 'grins')


def _yawn(params, mud, players_db: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
          env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms, id, 'yawns')


def _smug(params, mud, players_db: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
          env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms, id, 'looks smug')


def _relieved(params, mud, players_db: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
              env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    _emote(params, mud, players_db, players, rooms, id, 'looks relieved')


def _stick(params, mud, players_db: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
           env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    _say('stick', mud, players_db, players, rooms,
         npcs_db, npcs, items_db, items, env_db,
         env, eventDB, event_schedule,
         id, fights, corpses, blocklist,
         map_area, character_class_db, spells_db,
         sentiment_db, guilds_db, clouds, races_db, item_history, markets,
         cultures_db)


def _holding_light_source(players: {}, id, items: {}, items_db: {}) -> bool:
    """Is the given player holding a light source?
    """
    item_id = int(players[id]['clo_lhand'])
    if item_id > 0:
        if items_db[item_id]['lightSource'] != 0:
            return True
    item_id = int(players[id]['clo_rhand'])
    if item_id > 0:
        if items_db[int(item_id)]['lightSource'] != 0:
            return True

    # are there any other players in the same room holding a light source?
    for plyr in players:
        if plyr == id:
            continue
        if players[plyr]['room'] != players[id]['room']:
            continue
        item_id = int(players[plyr]['clo_lhand'])
        if item_id > 0:
            if items_db[item_id]['lightSource'] != 0:
                return True
        item_id = int(players[plyr]['clo_rhand'])
        if item_id > 0:
            if items_db[int(item_id)]['lightSource'] != 0:
                return True

    # is there a light source in the room?
    return _light_source_in_room(players, id, items, items_db)


def _conditional_logic(cond_type: str, cond: str, description: str, id,
                       players: {}, items: {},
                       items_db: {}, clouds: {}, map_area: [],
                       rooms: {}, look_modifier: str) -> bool:
    if look_modifier:
        # look under/above/behind
        if cond_type == look_modifier:
            return True

    if cond_type == 'sunrise' or \
       cond_type == 'dawn':
        curr_time = datetime.datetime.today()
        curr_hour = curr_time.hour
        sun = get_solar()
        sun_rise_time = sun.get_local_sunrise_time(curr_time).hour
        if 'true' in cond.lower() or \
           'y' in cond.lower():
            if curr_hour >= sun_rise_time - 1 and curr_hour <= sun_rise_time:
                return True
        else:
            if curr_hour < sun_rise_time - 1 or curr_hour > sun_rise_time:
                return True

    if cond_type == 'sunset' or \
       cond_type == 'dusk':
        curr_time = datetime.datetime.today()
        curr_hour = curr_time.hour
        sun = get_solar()
        sun_set_time = sun.get_local_sunset_time(curr_time).hour
        if 'true' in cond.lower() or \
           'y' in cond.lower():
            if curr_hour >= sun_set_time and curr_hour <= sun_set_time+1:
                return True
        else:
            if curr_hour < sun_set_time or curr_hour > sun_set_time+1:
                return True

    if cond_type.startswith('rain'):
        rmid = players[id]['room']
        coords = rooms[rmid]['coords']
        if 'true' in cond.lower() or \
           'y' in cond.lower():
            if get_rain_at_coords(coords, map_area, clouds):
                return True
        else:
            if not get_rain_at_coords(coords, map_area, clouds):
                return True

    if cond_type == 'morning':
        curr_hour = datetime.datetime.today().hour
        if curr_hour < 12:
            if 'true' in cond.lower() or \
               'y' in cond.lower():
                return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True
    if cond_type == 'noon':
        curr_hour = datetime.datetime.today().hour
        if curr_hour == 12:
            if 'true' in cond.lower() or \
               'y' in cond.lower():
                return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True
    if cond_type == 'afternoon':
        curr_hour = datetime.datetime.today().hour
        if curr_hour >= 12 and curr_hour < 17:
            if 'true' in cond.lower() or \
               'y' in cond.lower():
                return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True
    if cond_type == 'evening':
        curr_hour = datetime.datetime.today().hour
        if curr_hour >= 17:
            if 'true' in cond.lower() or \
               'y' in cond.lower():
                return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True
    if cond_type == 'night':
        curr_hour = datetime.datetime.today().hour
        if curr_hour >= 22 or curr_hour < 6:
            if 'true' in cond.lower() or \
               'y' in cond.lower():
                return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True

    if cond_type.endswith('moon'):
        curr_time = datetime.datetime.today()
        curr_hour = curr_time.hour
        phase = moon_phase(curr_time)
        if curr_hour >= 22 or curr_hour < 6:
            moon_phase_names = {
                0: "newmoon",
                1: "waxingcrescentmoon",
                2: "firstquartermoon",
                3: "waxinggibbousmoon",
                4: "fullmoon",
                5: "waninggibbousmoon",
                6: "lastquartermoon",
                7: "waningcrescentmoon"
            }
            for moon_index, phase_name in moon_phase_names.items():
                if cond_type == phase_name and phase == moon_index:
                    if 'true' in cond.lower() or \
                       'y' in cond.lower():
                        return True
        else:
            if 'false' in cond.lower() or \
               'n' in cond.lower():
                return True

    if cond_type == 'hour':
        curr_hour = datetime.datetime.today().hour
        cond_hour = \
            cond.replace('>', '').replace('<', '').replace('=', '').strip()
        if '>' in cond:
            if curr_hour > int(cond_hour):
                return True
        if '<' in cond:
            if curr_hour < int(cond_hour):
                return True
        if '=' in cond:
            if curr_hour == int(cond_hour):
                return True

    if cond_type == 'skill':
        if '<=' in cond:
            skill_type = cond.split('<=')[0].strip()
            if players[id].get(skill_type):
                skill_value = int(cond.split('<=')[1].split())
                if players[id][skill_type] <= skill_value:
                    return True
        if '>=' in cond:
            skill_type = cond.split('>=')[0].strip()
            if players[id].get(skill_type):
                skill_value = int(cond.split('>=')[1].split())
                if players[id][skill_type] >= skill_value:
                    return True
        if '>' in cond:
            skill_type = cond.split('>')[0].strip()
            if players[id].get(skill_type):
                skill_value = int(cond.split('>')[1].split())
                if players[id][skill_type] > skill_value:
                    return True
        if '<' in cond:
            skill_type = cond.split('<')[0].strip()
            if players[id].get(skill_type):
                skill_value = int(cond.split('<')[1].split())
                if players[id][skill_type] < skill_value:
                    return True
        if '=' in cond:
            cond = cond.replace('==', '=')
            skill_type = cond.split('=')[0].strip()
            if players[id].get(skill_type):
                skill_value = int(cond.split('=')[1].split())
                if players[id][skill_type] == skill_value:
                    return True

    if cond_type == 'date' or cond_type == 'dayofmonth':
        day_number = int(cond.split('/')[0])
        if day_number == \
           int(datetime.datetime.today().strftime("%d")):
            month_number = int(cond.split('/')[1])
            if month_number == \
               int(datetime.datetime.today().strftime("%m")):
                return True

    if cond_type == 'month':
        if '|' in cond:
            months = cond.split('|')
            for mnth in months:
                if int(mnth) == int(datetime.datetime.today().strftime("%m")):
                    return True
        else:
            curr_month_number = \
                int(datetime.datetime.today().strftime("%m"))
            month_number = int(cond)
            if month_number == curr_month_number:
                return True

    if cond_type == 'season':
        curr_month_number = int(datetime.datetime.today().strftime("%m"))
        if cond == 'spring':
            if curr_month_number > 1 and curr_month_number <= 4:
                return True
        elif cond == 'summer':
            if curr_month_number > 4 and curr_month_number <= 9:
                return True
        elif cond == 'autumn':
            if curr_month_number > 9 and curr_month_number <= 10:
                return True
        elif cond == 'winter':
            if curr_month_number > 10 or curr_month_number <= 1:
                return True

    if cond_type == 'day' or \
       cond_type == 'dayofweek' or cond_type == 'dow' or \
       cond_type == 'weekday':
        day_of_week = int(cond)
        if day_of_week == datetime.datetime.today().weekday():
            return True

    if cond_type == 'held' or cond_type.startswith('hold'):
        if not cond.isdigit():
            if cond.lower() == 'lightsource':
                return _holding_light_source(players, id, items, items_db)
        elif (players[id]['clo_lhand'] == int(cond) or
              players[id]['clo_rhand'] == int(cond)):
            return True

    if cond_type.startswith('wear'):
        for clth in WEAR_LOCATION:
            if players[id]['clo_' + clth] == int(cond):
                return True

    return False


def _conditional_room_desc(description: str, tideOutDescription: str,
                           conditional: [], id, players: {}, items: {},
                           items_db: {}, clouds: {}, map_area: [],
                           rooms: {}):
    """Returns a room description which can vary depending on conditions
    """
    room_description = description
    if len(tideOutDescription) > 0:
        if run_tide() < 0.0:
            room_description = tideOutDescription

    # Alternative descriptions triggered by conditions
    for possible_description in conditional:
        if len(possible_description) >= 3:
            cond_type = possible_description[0]
            cond = possible_description[1]
            alternative_description = possible_description[2]
            if _conditional_logic(cond_type, cond,
                                  alternative_description,
                                  id, players, items, items_db,
                                  clouds, map_area, rooms, None):
                room_description = alternative_description
                break

    return room_description


def _conditional_item_desc(item_id, conditional: [],
                           id, players: {}, items: {},
                           items_db: {}, clouds: {}, map_area: [],
                           rooms: {}, look_modifier: str):
    """Returns an item description which can vary depending on conditions
    """
    item_description = items_db[item_id]['long_description']

    # Alternative descriptions triggered by conditions
    for possible_description in conditional:
        if len(possible_description) >= 2:
            cond_type = possible_description[0]
            cond = None
            if cond_type.startswith('wear') or cond_type.startswith('hold'):
                cond = str(item_id)
                alternative_description = possible_description[1]
            elif len(possible_description) >= 3:
                cond = possible_description[1]
                alternative_description = possible_description[2]
            if cond:
                if _conditional_logic(cond_type, cond,
                                      alternative_description,
                                      id, players, items, items_db,
                                      clouds, map_area, rooms,
                                      look_modifier):
                    item_description = alternative_description
                    break

    return item_description


def _conditional_room_image(conditional: [], id, players: {}, items: {},
                            items_db: {}, clouds: {}, map_area: [],
                            rooms: {}) -> str:
    """If there is an image associated with a conditional
    room description then return its name
    """
    for possible_description in conditional:
        if len(possible_description) < 4:
            continue
        cond_type = possible_description[0]
        cond = possible_description[1]
        alternative_description = possible_description[2]
        if _conditional_logic(cond_type, cond,
                              alternative_description,
                              id, players, items, items_db, clouds,
                              map_area, rooms, None):
            room_image_filename = \
                'images/rooms/' + possible_description[3]
            if os.path.isfile(room_image_filename):
                return possible_description[3]
            break
    return None


def _conditional_item_image(item_id,
                            conditional: [], id, players: {}, items: {},
                            items_db: {}, clouds: {}, map_area: [],
                            rooms: {}, look_modifier: str) -> str:
    """If there is an image associated with a conditional
    item description then return its name
    """
    # Alternative descriptions triggered by conditions
    for possible_description in conditional:
        if len(possible_description) < 3:
            continue
        cond_type = possible_description[0]
        cond = None
        item_id_str = None
        if cond_type.startswith('wear') or cond_type.startswith('hold'):
            cond = str(item_id)
            alternative_description = possible_description[1]
            item_id_str = possible_description[2]
        elif len(possible_description) >= 4:
            cond = possible_description[1]
            alternative_description = possible_description[2]
            item_id_str = possible_description[3]
        if cond and item_id_str:
            if _conditional_logic(cond_type, cond,
                                  alternative_description,
                                  id, players, items, items_db,
                                  clouds, map_area, rooms,
                                  look_modifier):
                return str(item_id_str)
    return str(item_id)


def _players_in_room(target_room, players, npcs):
    """Returns the number of players in the given room.
       This includes NPCs.
    """
    players_ctr = 0
    for pid, _ in list(players.items()):
        # if they're in the same room as the player
        if players[pid]['room'] == target_room:
            players_ctr += 1

    for nid, _ in list(npcs.items()):
        if npcs[nid]['room'] == target_room:
            players_ctr += 1

    return players_ctr


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


def _item_is_visible(observer_id: int, players: {},
                     item_id: int, items_db: {}) -> bool:
    """Is the item visible to the observer?
    """
    item_id = int(item_id)
    if not items_db[item_id].get('visibleWhenWearing'):
        return True
    if is_wearing(observer_id, players,
                  items_db[item_id]['visibleWhenWearing']):
        return True
    return False


def _item_is_climbable(climber_id: int, players: {},
                       item_id: int, items_db: {}) -> bool:
    """Is the item climbable by the player?
    """
    item_id = int(item_id)
    if not items_db[item_id].get('climbWhenWearing'):
        return True
    if is_wearing(climber_id, players,
                  items_db[item_id]['climbWhenWearing']):
        return True
    return False


def _room_illumination(room_image, outdoors: bool):
    """Alters the brightness and contrast of the image to simulate
    evening and night conditions
    """
    if not outdoors:
        return room_image
    curr_time = datetime.datetime.today()
    curr_hour = curr_time.hour
    sun = get_solar()
    sun_rise_time = sun.get_local_sunrise_time(curr_time).hour
    sun_set_time = sun.get_local_sunset_time(curr_time).hour
    if curr_hour > sun_rise_time+1 and curr_hour < sun_set_time-1:
        return room_image
    brightness = 60
    color_variance = 80
    if curr_hour < sun_rise_time or curr_hour > sun_set_time:
        brightness = 30
    # extra dark
    if curr_hour < (sun_rise_time-2) or curr_hour > (sun_set_time+2):
        color_variance = 50

    brightness += moon_illumination(curr_time)
    pixels = room_image.split('[')

    av_intensity = 0
    av_intensity_ctr = 0
    for pix in pixels:
        values = pix.split(';')
        if len(values) != 5:
            continue
        values[4] = values[4].split('m')[0]
        ctr = 0
        for val in values:
            if ctr > 1:
                av_intensity += int(val)
                av_intensity_ctr += 1
            ctr += 1
    av_intensity /= av_intensity_ctr
    new_av_intensity = int(av_intensity * brightness / 100)
    # minimum average illumination
    if new_av_intensity < 20:
        new_av_intensity = 20

    new_room_image = ''
    trailing = None
    first_value = True
    for pix in pixels:
        if first_value:
            new_room_image += pix + '['
            first_value = False
            continue
        values = pix.split(';')
        if len(values) != 5:
            new_room_image += pix + '['
            continue
        trailing = values[4].split('m')[1]
        values[4] = values[4].split('m')[0]
        ctr = 0
        for val in values:
            if ctr > 1:
                # difference from average illumination
                diff = int(int(val) - av_intensity)
                # reduce color variance
                variance = color_variance
                # reduce blue by more than other channels
                if ctr == 2:
                    variance = int(color_variance / 4)
                val = int(new_av_intensity + (diff * variance / 100))
                if val < 0:
                    val = 0
                elif val > 255:
                    val = 255
            values[ctr] = int(val)
            ctr += 1
        dark_str = trailing + '['
        dark_str = ''
        ctr = 0
        for val in values:
            if ctr < 4:
                dark_str += str(val) + ';'
            else:
                dark_str += str(val) + 'm'
            ctr += 1
        new_room_image += dark_str + trailing + '['
    return new_room_image[:len(new_room_image) - 1]


def _show_room_image(mud, id, room_id, rooms: {}, players: {},
                     items: {}, items_db: {},
                     clouds: {}, map_area: []) -> None:
    """Shows an image for the room if it exists
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    conditional_image = \
        _conditional_room_image(rooms[room_id]['conditional'],
                                id, players, items,
                                items_db, clouds,
                                map_area, rooms)
    outdoors = False
    if rooms[room_id]['weather'] == 1:
        outdoors = True
    if not conditional_image:
        room_id_str = str(room_id).replace('rid=', '').replace('$', '')
    else:
        room_id_str = conditional_image
    room_image_filename = 'images/rooms/' + room_id_str
    if os.path.isfile(room_image_filename + '_night'):
        curr_time = datetime.datetime.today()
        sun = get_solar()
        sun_rise_time = sun.get_local_sunrise_time(curr_time).hour
        sun_set_time = sun.get_local_sunset_time(curr_time).hour
        if curr_time.hour < sun_rise_time or \
           curr_time.hour > sun_set_time:
            room_image_filename = room_image_filename + '_night'
            outdoors = False
    if not os.path.isfile(room_image_filename):
        return
    with open(room_image_filename, 'r') as fp_room:
        room_image_str = fp_room.read()
        mud.send_image(id, '\n' + _room_illumination(room_image_str, outdoors))


def _show_spell_image(mud, id, spellId, players: {}) -> None:
    """Shows an image for a spell
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    spell_image_filename = 'images/spells/' + spellId
    if not os.path.isfile(spell_image_filename):
        return
    with open(spell_image_filename, 'r') as fp_spell:
        mud.send_image(id, '\n' + fp_spell.read())


def _show_item_image(mud, id, item_id, room_id, rooms: {}, players: {},
                     items: {}, items_db: {},
                     clouds: {}, map_area: [], look_modifier: str) -> None:
    """Shows an image for the item if it exists
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    item_id_str = \
        _conditional_item_image(item_id,
                                items_db[item_id]['conditional'],
                                id, players, items,
                                items_db, clouds,
                                map_area, rooms, look_modifier)

    # fixed items can have their illumination changed if they are outdoors
    outdoors = False
    if items_db[item_id]['weight'] == 0:
        if rooms[room_id]['weather'] == 1:
            outdoors = True

    item_image_filename = 'images/items/' + item_id_str
    if os.path.isfile(item_image_filename + '_night'):
        curr_time = datetime.datetime.today()
        sun = get_solar()
        sun_rise_time = sun.get_local_sunrise_time(curr_time).hour
        sun_set_time = sun.get_local_sunset_time(curr_time).hour
        if curr_time.hour < sun_rise_time or \
           curr_time.hour > sun_set_time:
            item_image_filename = item_image_filename + '_night'
            outdoors = False
    if not os.path.isfile(item_image_filename):
        return
    with open(item_image_filename, 'r') as fp_item:
        item_image_str = fp_item.read()
        mud.send_image(id, '\n' + _room_illumination(item_image_str, outdoors))


def _show_npc_image(mud, id, npc_name, players: {}) -> None:
    """Shows an image for a NPC
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    npc_image_filename = 'images/npcs/' + npc_name.replace(' ', '_')
    if not os.path.isfile(npc_image_filename):
        return
    with open(npc_image_filename, 'r') as fp_npc:
        mud.send_image(id, '\n' + fp_npc.read())


def _get_room_exits(mud, rooms: {}, players: {}, id) -> {}:
    """Returns a dictionary of exits for the given player
    """
    rm_item = rooms[players[id]['room']]
    exits = rm_item['exits']

    if rm_item.get('tideOutExits'):
        if run_tide() < 0.0:
            for direction, room_id in rm_item['tideOutExits'].items():
                exits[direction] = room_id
        else:
            for direction, room_id in rm_item['tideOutExits'].items():
                if exits.get(direction):
                    del rm_item['exits'][direction]

    if rm_item.get('exitsWhenWearing'):
        directions_added = []
        for ex in rm_item['exitsWhenWearing']:
            if len(ex) < 3:
                continue
            direction = ex[0]
            item_id = ex[1]
            if is_wearing(id, players, [item_id]):
                room_id = ex[2]
                exits[direction] = room_id
                # keep track of directions added via wearing items
                if direction not in directions_added:
                    directions_added.append(direction)
            else:
                if exits.get(direction):
                    # only remove if the direction was not previously added
                    # via another item
                    if direction not in directions_added:
                        del rm_item['exits'][direction]
    return exits


def _item_in_player_room(players: {}, id, items: {}, item_id: int) -> bool:
    """Returns true if the given item is in the given room
    """
    return items[item_id]['room'].lower() == players[id]['room']


def _look(params, mud, players_db: {}, players: {}, rooms: {},
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
            rm_item = rooms[players[id]['room']]

            # send the player back the description of their current room
            player_room_id = players[id]['room']
            _show_room_image(mud, id, player_room_id,
                             rooms, players, items,
                             items_db, clouds, map_area)
            room_description = \
                _conditional_room_desc(rm_item['description'],
                                       rm_item['tideOutDescription'],
                                       rm_item['conditional'],
                                       id, players, items, items_db,
                                       clouds, map_area, rooms)

            if rm_item['trap'].get('trap_activation') and \
               rm_item['trap'].get('trapPerception'):
                if randint(1, players[id]['per']) > \
                   rm_item['trap']['trapPerception']:
                    if rm_item['trap']['trapType'].startswith('dart') and \
                       randint(0, 1) == 1:
                        room_description += \
                            random_desc(" You notice some tiny " +
                                        "holes in the wall.| " +
                                        "There are some small " +
                                        "holes in the wall.|You " +
                                        "observe some tiny holes" +
                                        " in the wall.")
                    else:
                        if rm_item['trap']['trap_activation'] == 'tripwire':
                            room_description += \
                                random_desc(" A tripwire is " +
                                            "carefully set along " +
                                            "the floor.| You notice " +
                                            "a thin wire across " +
                                            "the floor.| An almost " +
                                            "invisible wire runs " +
                                            "along the floor.")
                        trap_act = rm_item['trap']['trap_activation']
                        if trap_act.startswith('pressure'):
                            room_description += \
                                random_desc(" The faint outline of " +
                                            "a pressure plate can be " +
                                            "seen on the floor.| The " +
                                            "outline of a pressure " +
                                            "plate is visible on " +
                                            "the floor.")

            mud.send_message_wrap(id, '<f230>',
                                  "****CLEAR****<f230>" +
                                  room_description.strip())
            playershere = []

            itemshere = []

            # go through every player in the game
            for pid, _ in list(players.items()):
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
            for corpse, _ in list(corpses.items()):
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
            for item, _ in list(items.items()):
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
            room_exits_str = _get_room_exits(mud, rooms, players, id)
            if room_exits_str:
                ex_str = room_exits_str
                desc = \
                    '<f230>Exits are: <f220>{}'.format(', '.join(ex_str))
                mud.send_message(id, desc)

            # send player a message containing the list of items in the room
            if len(itemshere) > 0:
                needs_light = _room_requires_light_source(players, id, rooms)
                players_with_light = False
                if needs_light:
                    players_with_light = \
                        _holding_light_source(players, id, items, items_db)
                if needs_light is False or \
                   (needs_light is True and players_with_light is True):
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
            look_modifier = None
            if param.startswith('under '):
                param = params.replace('under ', '', 1)
                look_modifier = 'under'
            elif param.startswith('below '):
                param = params.replace('below ', '', 1)
                look_modifier = 'under'
            elif param.startswith('beneath '):
                param = params.replace('beneath ', '', 1)
                look_modifier = 'under'
            elif param.startswith('behind '):
                param = params.replace('behind ', '', 1)
                look_modifier = 'behind'
            elif param.startswith('above '):
                param = params.replace('above ', '', 1)
                look_modifier = 'above'
            elif param.startswith('on top of '):
                param = params.replace('on top of ', '', 1)
                look_modifier = 'above'

            # replace "familiar" with the name of the familiar
            if param.startswith('familiar'):
                familiar_name = get_familiar_name(players, id, npcs)
                if len(familiar_name) > 0:
                    param = param.replace('familiar', familiar_name, 1)

            if param.startswith('at the '):
                param = param.replace('at the ', '')
            if param.startswith('the '):
                param = param.replace('the ', '')
            if param.startswith('at '):
                param = param.replace('at ', '')
            if param.startswith('a '):
                param = param.replace('a ', '')
            message_sent = False

            # Go through all players in game
            for plyr in players:
                if players[plyr]['authenticated'] is not None:
                    if players[plyr]['name'].lower() == param and \
                       players[plyr]['room'] == players[id]['room']:
                        if player_is_visible(mud, players, id, plyr, players):
                            _bio_of_player(mud, id, plyr, players, items_db)
                            message_sent = True

            message = ""

            # Go through all NPCs in game
            for nitem in npcs:
                if param in npcs[nitem]['name'].lower() and \
                   npcs[nitem]['room'] == players[id]['room']:
                    if player_is_visible(mud, id, players, nitem, npcs):
                        if npcs[nitem]['familiarMode'] != 'hide':
                            name_lower = npcs[nitem]['name'].lower()
                            _show_npc_image(mud, id, name_lower, players)
                            _bio_of_player(mud, id, nitem, npcs, items_db)
                            message_sent = True
                        else:
                            if npcs[nitem]['familiarOf'] == \
                               players[id]['name']:
                                message = "They are hiding somewhere here."
                                message_sent = True

            if len(message) > 0:
                mud.send_message(id, "****CLEAR****" + message + "\n\n")
                message_sent = True

            message = ""

            # Go through all Items in game
            item_counter = 0
            for i in items:
                if _item_in_player_room(players, id, items, i) and \
                   param in items_db[items[i]['id']]['name'].lower():
                    if _item_is_visible(id, players, items[i]['id'], items_db):
                        if item_counter == 0:
                            item_language = \
                                items_db[items[i]['id']]['language']
                            this_item_id = int(items[i]['id'])
                            idx = items[i]['id']
                            if items_db[idx].get('itemName'):
                                message += \
                                    'Name: ' + items_db[idx]['itemName'] + '\n'
                            cond_desc = []
                            if items_db[idx].get('conditional'):
                                cond_desc = items_db[idx]['conditional']
                            desc = \
                                _conditional_item_desc(idx, cond_desc,
                                                       id, players,
                                                       items, items_db,
                                                       clouds, map_area,
                                                       rooms, look_modifier)
                            message += random_desc(desc)
                            message += \
                                _describe_container_contents(mud, id,
                                                             items_db,
                                                             items[i]['id'],
                                                             True)
                            if len(item_language) == 0:
                                room_id = players[id]['room']
                                _show_item_image(mud, id, idx,
                                                 room_id, rooms, players,
                                                 items, items_db,
                                                 clouds, map_area,
                                                 look_modifier)
                            else:
                                if item_language in players[id]['language']:
                                    room_id = players[id]['room']
                                    _show_item_image(mud, id, idx,
                                                     room_id, rooms, players,
                                                     items, items_db,
                                                     clouds, map_area,
                                                     look_modifier)
                                else:
                                    message += \
                                        "It's written in " + item_language
                            item_name = \
                                items_db[items[i]['id']]['article'] + \
                                " " + items_db[items[i]['id']]['name']
                        item_counter += 1

            # Examine items in inventory
            if len(message) == 0:
                playerinv = list(players[id]['inv'])
                if len(playerinv) > 0:
                    # check for exact match of item name
                    inv_item_found = False
                    for i in playerinv:
                        this_item_id = int(i)
                        items_db_entry = items_db[this_item_id]
                        if param == items_db_entry['name'].lower():
                            item_language = items_db_entry['language']
                            room_id = players[id]['room']
                            _show_item_image(mud, id, this_item_id,
                                             room_id, rooms, players,
                                             items, items_db,
                                             clouds, map_area, None)
                            if len(item_language) == 0:
                                cond_desc = []
                                if items_db_entry.get('conditional'):
                                    cond_desc = items_db_entry['conditional']
                                desc = \
                                    _conditional_item_desc(this_item_id,
                                                           cond_desc,
                                                           id, players,
                                                           items, items_db,
                                                           clouds,
                                                           map_area,
                                                           rooms, None)
                                message += random_desc(desc)
                                message += \
                                    _describe_container_contents(
                                        mud, id, items_db, this_item_id, True)
                            else:
                                if item_language in players[id]['language']:
                                    cond_desc = []
                                    if items_db_entry.get('conditional'):
                                        cond_desc = \
                                            items_db_entry['conditional']
                                    desc = \
                                        _conditional_item_desc(this_item_id,
                                                               cond_desc,
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
                                            mud, id, items_db, this_item_id,
                                            True)
                                else:
                                    message += \
                                        "It's written in " + item_language
                            item_name = \
                                items_db_entry['article'] + " " + \
                                items_db_entry['name']
                            inv_item_found = True
                            break
                    if not inv_item_found:
                        # check for partial match of item name
                        for i in playerinv:
                            this_item_id = int(i)
                            items_db_entry = items_db[this_item_id]
                            if param in items_db_entry['name'].lower():
                                item_language = items_db_entry['language']
                                room_id = players[id]['room']
                                _show_item_image(mud, id, this_item_id,
                                                 room_id, rooms, players,
                                                 items, items_db,
                                                 clouds, map_area, None)
                                if len(item_language) == 0:
                                    cond_desc = []
                                    if items_db_entry.get('conditional'):
                                        cond_desc = \
                                            items_db_entry['conditional']
                                    desc = \
                                        _conditional_item_desc(this_item_id,
                                                               cond_desc,
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
                                            mud, id, items_db, this_item_id,
                                            True)
                                else:
                                    player_langs = players[id]['language']
                                    if item_language in player_langs:
                                        cond_desc = []
                                        if items_db_entry.get('conditional'):
                                            cond_desc = \
                                                items_db_entry['conditional']
                                        this_id = this_item_id
                                        desc = \
                                            _conditional_item_desc(this_id,
                                                                   cond_desc,
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
                                                this_item_id, True)
                                    else:
                                        message += \
                                            "It's written in " + item_language

                                item_name = \
                                    items_db_entry['article'] + " " + \
                                    items_db_entry['name']
                                break

            if len(message) > 0:
                mud.send_message(id, "****CLEAR****It's " + item_name + ".")
                mud.send_message_wrap(id, '', message + "<r>\n\n")
                message_sent = True
                if item_counter > 1:
                    mud.send_message(
                        id, "You can see " +
                        str(item_counter) +
                        " of those in the vicinity.<r>\n\n")

            # If no message has been sent, it means no player/npc/item was
            # found
            if not message_sent:
                mud.send_message(id, "Look at what?<r>\n")
    else:
        mud.send_message(
            id,
            '****CLEAR****' +
            'You somehow cannot muster enough perceptive powers ' +
            'to perceive and describe your immediate surroundings...<r>\n')


def _escape_trap(params, mud, players_db: {}, players: {}, rooms: {},
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


def _begin_attack(params, mud, players_db: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {},
                  races_db: {}, item_history: {}, markets: {},
                  cultures_db: {}):
    thrown = False
    if players[id].get('throwing'):
        del players[id]['throwing']
        thrown = True

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
                                 npcs, fights, mud, races_db,
                                 item_history, thrown)
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


def _begin_throw_attack(params, mud, players_db: {}, players: {}, rooms: {},
                        npcs_db: {}, npcs: {}, items_db: {}, items: {},
                        env_db: {}, env: {}, eventDB: {}, event_schedule,
                        id: int, fights: {}, corpses: {}, blocklist,
                        map_area: [], character_class_db: {}, spells_db: {},
                        sentiment_db: {}, guilds_db: {}, clouds: {},
                        races_db: {}, item_history: {}, markets: {},
                        cultures_db: {}):
    """Throw a weapon
    """
    if not params:
        mud.send_message(id, 'Throw at?\n')
        return
    if params.startswith('the '):
        params = params.replace('the ', '', 1)
    if params.startswith('a '):
        params = params.replace('a ', '', 1)
    if ' at ' in params:
        weapon_name = params.split(' at ', 1)[0]
        params = params.split(' at ', 1)[1]
        players[id]['throwing'] = "yes"
        players[id]['throwing'] = weapon_name
        _wield(weapon_name, mud, players_db, players, rooms,
               npcs_db, npcs, items_db, items,
               env_db, env, eventDB, event_schedule,
               id, fights, corpses, blocklist,
               map_area, character_class_db, spells_db,
               sentiment_db, guilds_db, clouds, races_db,
               item_history, markets, cultures_db)
    elif params.startswith('at '):
        params = params.split('at ', 1)[1]
        players[id]['throwing'] = "yes"
    else:
        if players[id].get('throwing'):
            del players[id]['throwing']
        mud.send_message(id, 'Throw at?\n')
        return
    if holding_throwable(players, id, items_db):
        _begin_attack(params, mud, players_db, players, rooms,
                      npcs_db, npcs, items_db, items,
                      env_db, env, eventDB, event_schedule,
                      id, fights, corpses, blocklist,
                      map_area, character_class_db, spells_db,
                      sentiment_db, guilds_db, clouds,
                      races_db, item_history, markets,
                      cultures_db)
    else:
        mud.send_message(id, "You aren't holding anything throwable.\n")


def _item_in_inventory(players: {}, id, item_name: str, items_db: {}):
    """Is the named item in the player inventory?
    """
    if len(list(players[id]['inv'])) > 0:
        item_name_lower = item_name.lower()
        for i in list(players[id]['inv']):
            if items_db[int(i)]['name'].lower() == item_name_lower:
                return True
    return False


def _describe_thing(params, mud, players_db: {}, players: {}, rooms: {},
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

    description_strings = re.findall('"([^"]*)"', params)
    if len(description_strings) == 0:
        mud.send_message(
            id, 'Descriptions need to be within double quotes.\n\n')
        return

    if len(description_strings[0].strip()) < 3:
        mud.send_message(id, 'Description is too short.\n\n')
        return

    rmid = players[id]['room']
    if len(description_strings) == 1:
        rooms[rmid]['description'] = description_strings[0]
        mud.send_message(id, 'Room description set.\n\n')
        save_universe(rooms, npcs_db, npcs,
                      items_db, items, env_db,
                      env, guilds_db)
        return

    if len(description_strings) == 2:
        thing_described = description_strings[0].lower()
        thing_description = description_strings[1]

        if len(thing_description) < 3:
            mud.send_message(
                id, 'Description of ' +
                description_strings[0] +
                ' is too short.\n\n')
            return

        if thing_described == 'name':
            rooms[rmid]['name'] = thing_description
            mud.send_message(
                id, 'Room name changed to ' +
                thing_description + '.\n\n')
            save_universe(rooms, npcs_db, npcs,
                          items_db, items, env_db,
                          env, guilds_db)
            return

        if thing_described == 'tide':
            rooms[rmid]['tideOutDescription'] = thing_description
            mud.send_message(id, 'Tide out description set.\n\n')
            save_universe(rooms, npcs_db, npcs,
                          items_db, items,
                          env_db, env, guilds_db)
            return

        # change the description of an item in the room
        for item, _ in list(items.items()):
            if items[item]['room'] == players[id]['room']:
                idx = items[item]['id']
                if thing_described in items_db[idx]['name'].lower():
                    items_db[idx]['long_description'] = thing_description
                    mud.send_message(id, 'New description set for ' +
                                     items_db[idx]['article'] +
                                     ' ' + items_db[idx]['name'] +
                                     '.\n\n')
                    save_universe(
                        rooms, npcs_db, npcs, items_db,
                        items, env_db, env, guilds_db)
                    return

        # Change the description of an NPC in the room
        for nid, _ in list(npcs.items()):
            if npcs[nid]['room'] == players[id]['room']:
                if thing_described in npcs[nid]['name'].lower():
                    npcs[nid]['lookDescription'] = thing_description
                    mud.send_message(
                        id, 'New description set for ' +
                        npcs[nid]['name'] + '.\n\n')
                    save_universe(
                        rooms, npcs_db, npcs, items_db,
                        items, env_db, env, guilds_db)
                    return

    if len(description_strings) == 3:
        if description_strings[0].lower() != 'name':
            mud.send_message(id, "I don't understand.\n\n")
            return
        thing_described = description_strings[1].lower()
        thing_name = description_strings[2]
        if len(thing_name) < 3:
            mud.send_message(
                id, 'Description of ' +
                description_strings[1] +
                ' is too short.\n\n')
            return

        # change the name of an item in the room
        for item, _ in list(items.items()):
            if items[item]['room'] == players[id]['room']:
                idx = items[item]['id']
                if thing_described in items_db[idx]['name'].lower():
                    items_db[idx]['name'] = thing_name
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
        for nid, _ in list(npcs.items()):
            if npcs[nid]['room'] == players[id]['room']:
                if thing_described in npcs[nid]['name'].lower():
                    npcs[nid]['name'] = thing_name
                    mud.send_message(
                        id, 'New description set for ' +
                        npcs[nid]['name'] + '.\n\n')
                    save_universe(
                        rooms, npcs_db, npcs, items_db,
                        items, env_db, env, guilds_db)
                    return


def _check_inventory(params, mud, players_db: {}, players: {}, rooms: {},
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


def _change_setting(params, mud, players_db: {}, players: {}, rooms: {},
                    npcs_db: {}, npcs: {}, items_db: {}, items: {},
                    env_db: {}, env: {}, eventDB: {}, event_schedule,
                    id: int, fights: {}, corpses: {}, blocklist,
                    map_area: [], character_class_db: {}, spells_db: {},
                    sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                    item_history: {}, markets: {}, cultures_db: {}):
    new_password = ''
    if params.startswith('password '):
        new_password = params.replace('password ', '')
    if params.startswith('pass '):
        new_password = params.replace('pass ', '')
    if len(new_password) > 0:
        if len(new_password) < 6:
            mud.send_message(id, "That password is too short.\n\n")
            return
        players[id]['pwd'] = hash_password(new_password)
        log("Player " + players[id]['name'] +
            " changed their password", "info")
        save_state(players[id], players_db, True)
        mud.send_message(id, "Your password has been changed.\n\n")


def _write_on_item(params, mud, players_db: {}, players: {}, rooms: {},
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


def _check(params, mud, players_db: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {},
           env_db: {}, env: {}, eventDB: {}, event_schedule,
           id: str, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    if params.lower() == 'inventory' or \
       params.lower() == 'inv':
        _check_inventory(params, mud, players_db, players,
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


def _wear(params, mud, players_db: {}, players: {}, rooms: {},
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

    item_name = params.lower()
    if item_name.startswith('the '):
        item_name = item_name.replace('the ', '')
    if item_name.startswith('my '):
        item_name = item_name.replace('my ', '')
    if item_name.startswith('your '):
        item_name = item_name.replace('your ', '')

    item_id = 0
    for i in list(players[id]['inv']):
        if items_db[int(i)]['name'].lower() == item_name:
            item_id = int(i)

    if item_id == 0:
        for i in list(players[id]['inv']):
            if item_name in items_db[int(i)]['name'].lower():
                item_id = int(i)

    if item_id == 0:
        mud.send_message(id, item_name + " is not in your inventory.\n\n")
        return

    for clothing_type in WEAR_LOCATION:
        if _wear_clothing(item_id, players, id, clothing_type, mud, items_db):
            return

    mud.send_message(id, "You can't wear that\n\n")


def _wield(params, mud, players_db: {}, players: {}, rooms: {},
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

    item_name = params.lower()
    item_hand = 1
    if item_name.startswith('the '):
        item_name = item_name.replace('the ', '')
    if item_name.startswith('my '):
        item_name = item_name.replace('my ', '')
    if item_name.startswith('your '):
        item_name = item_name.replace('your ', '')
    if item_name.endswith(' on left hand'):
        item_name = item_name.replace(' on left hand', '')
        item_hand = 0
    if item_name.endswith(' in left hand'):
        item_name = item_name.replace(' in left hand', '')
        item_hand = 0
    if item_name.endswith(' in my left hand'):
        item_name = item_name.replace(' in my left hand', '')
        item_hand = 0
    if item_name.endswith(' in your left hand'):
        item_name = item_name.replace(' in your left hand', '')
        item_hand = 0
    if item_name.endswith(' left'):
        item_name = item_name.replace(' left', '')
        item_hand = 0
    if item_name.endswith(' in left'):
        item_name = item_name.replace(' in left', '')
        item_hand = 0
    if item_name.endswith(' on left'):
        item_name = item_name.replace(' on left', '')
        item_hand = 0
    if item_name.endswith(' on right hand'):
        item_name = item_name.replace(' on right hand', '')
        item_hand = 1
    if item_name.endswith(' in right hand'):
        item_name = item_name.replace(' in right hand', '')
        item_hand = 1
    if item_name.endswith(' in my right hand'):
        item_name = item_name.replace(' in my right hand', '')
        item_hand = 1
    if item_name.endswith(' in your right hand'):
        item_name = item_name.replace(' in your right hand', '')
        item_hand = 1
    if item_name.endswith(' right'):
        item_name = item_name.replace(' right', '')
        item_hand = 1
    if item_name.endswith(' in right'):
        item_name = item_name.replace(' in right', '')
        item_hand = 1
    if item_name.endswith(' on right'):
        item_name = item_name.replace(' on right', '')
        item_hand = 1

    item_id = 0
    for i in list(players[id]['inv']):
        if items_db[int(i)]['name'].lower() == item_name:
            item_id = int(i)

    if item_id == 0:
        for i in list(players[id]['inv']):
            if item_name in items_db[int(i)]['name'].lower():
                item_id = int(i)

    if item_id == 0:
        mud.send_message(id, item_name + " is not in your inventory.\n\n")
        return

    if items_db[item_id]['clo_lhand'] == 0 and \
       items_db[item_id]['clo_rhand'] == 0:
        mud.send_message(id, "You can't hold that.\n\n")
        return

    # items stowed on legs
    if int(players[id]['clo_lleg']) == item_id:
        players[id]['clo_lleg'] = 0
    if int(players[id]['clo_rleg']) == item_id:
        players[id]['clo_rleg'] = 0

    if 'isFishing' in players[id]:
        del players[id]['isFishing']

    if item_hand == 0:
        if int(players[id]['clo_rhand']) == item_id:
            players[id]['clo_rhand'] = 0
        players[id]['clo_lhand'] = item_id
        mud.send_message(id, 'You hold <b234>' +
                         items_db[item_id]['article'] + ' ' +
                         items_db[item_id]['name'] +
                         '<r> in your left hand.\n\n')
    else:
        if int(players[id]['clo_lhand']) == item_id:
            players[id]['clo_lhand'] = 0
        players[id]['clo_rhand'] = item_id
        mud.send_message(id, 'You hold <b234>' +
                         items_db[item_id]['article'] + ' ' +
                         items_db[item_id]['name'] +
                         '<r> in your right hand.\n\n')


def _stow(params, mud, players_db: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    if len(list(players[id]['inv'])) == 0:
        return

    stow_from = ('clo_lhand', 'clo_rhand')
    for stow_location in stow_from:
        item_id = int(players[id][stow_location])
        if item_id == 0:
            continue
        if int(items_db[item_id]['clo_rleg']) > 0:
            if int(players[id]['clo_rleg']) == 0:
                if int(players[id]['clo_lleg']) != item_id:
                    players[id]['clo_rleg'] = item_id
                    mud.send_message(id, 'You stow <b234>' +
                                     items_db[item_id]['article'] + ' ' +
                                     items_db[item_id]['name'] + '<r>\n\n')
                    players[id][stow_location] = 0
                    continue

        if int(items_db[item_id]['clo_lleg']) > 0:
            if int(players[id]['clo_lleg']) == 0:
                if int(players[id]['clo_rleg']) != item_id:
                    players[id]['clo_lleg'] = item_id
                    mud.send_message(id, 'You stow <b234>' +
                                     items_db[item_id]['article'] + ' ' +
                                     items_db[item_id]['name'] + '<r>\n\n')
                    players[id][stow_location] = 0

    stow_hands(id, players, items_db, mud)

    if 'isFishing' in players[id]:
        del players[id]['isFishing']


def _wear_clothing(item_id, players: {}, id, clothing_type,
                   mud, items_db: {}) -> bool:
    clothing_param = 'clo_' + clothing_type
    if items_db[item_id][clothing_param] > 0:
        players[id][clothing_param] = item_id

        # handle items which are pairs
        if items_db[item_id]['article'] == 'some':
            if clothing_type == 'lleg' or clothing_type == 'rleg':
                players[id]['clo_lleg'] = item_id
                players[id]['clo_rleg'] = item_id
            elif clothing_type == 'lhand' or clothing_type == 'rhand':
                players[id]['clo_lhand'] = item_id
                players[id]['clo_rhand'] = item_id

        clothing_opened = False
        if len(items_db[item_id]['open_description']) > 0:
            # there is a special description for wearing
            desc = \
                random_desc(items_db[item_id]['open_description'])
            if ' open' not in items_db[item_id]['open_description']:
                mud.send_message(id, desc + '\n\n')
                clothing_opened = True
        if not clothing_opened:
            # generic weating description
            mud.send_message(
                id,
                'You put on ' +
                items_db[item_id]['article'] +
                ' <b234>' +
                items_db[item_id]['name'] +
                '\n\n')
        return True
    return False


def _remove_clothing(players: {}, id, clothing_type, mud, items_db: {}):
    if int(players[id]['clo_' + clothing_type]) > 0:
        item_id = int(players[id]['clo_' + clothing_type])
        clothing_closed = False
        if len(items_db[item_id]['close_description']) > 0:
            desc = items_db[item_id]['open_description']
            if ' close ' not in desc and \
               'closed' not in desc and \
               'closing' not in desc and \
               'shut' not in desc:
                desc = \
                    random_desc(items_db[item_id]['close_description'])
                mud.send_message(id, desc + '\n\n')
                clothing_closed = True
        if not clothing_closed:
            mud.send_message(id, 'You remove ' +
                             items_db[item_id]['article'] + ' <b234>' +
                             items_db[item_id]['name'] + '\n\n')

        # handle items which are pairs
        if items_db[item_id]['article'] == 'some':
            if clothing_type == 'lleg' or clothing_type == 'rleg':
                players[id]['clo_lleg'] = 0
                players[id]['clo_rleg'] = 0
            elif clothing_type == 'lhand' or clothing_type == 'rhand':
                players[id]['clo_lhand'] = 0
                players[id]['clo_rhand'] = 0

        players[id]['clo_' + clothing_type] = 0


def _unwear(params, mud, players_db: {}, players: {}, rooms: {},
            npcs_db: {}, npcs: {}, items_db: {}, items: {},
            env_db: {}, env: {}, eventDB: {}, event_schedule,
            id: int, fights: {}, corpses: {}, blocklist,
            map_area: [], character_class_db: {}, spells_db: {},
            sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}):
    if len(list(players[id]['inv'])) == 0:
        return

    for clothing_type in WEAR_LOCATION:
        _remove_clothing(players, id, clothing_type, mud, items_db)


def _players_move_together(id, rm, mud,
                           players_db, players, rooms: {}, npcs_db: {}, npcs,
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
    for pid, _ in list(players.items()):
        # if player is in the same room and isn't the player
        # sending the command
        if players[pid]['room'] == players[id]['room'] and \
           pid != id:
            players[pid]['room'] = rm

            desc = 'You row to <f106>{}'.format(rooms[rm]['name'])
            mud.send_message(pid, desc + "\n\n")

            _look('', mud, players_db, players, rooms, npcs_db, npcs,
                  items_db, items, env_db, env, eventDB, event_schedule,
                  pid, fights, corpses, blocklist, map_area,
                  character_class_db, spells_db, sentiment_db, guilds_db,
                  clouds, races_db, item_history, markets, cultures_db)

            if rooms[rm]['eventOnEnter'] != "":
                ev_id = int(rooms[rm]['eventOnEnter'])
                add_to_scheduler(ev_id, pid, event_schedule, eventDB)


def _bio_of_player(mud, id, pid, players: {}, items_db: {}) -> None:
    """Shows the bio of a player
    """
    this_player = players[pid]
    if this_player.get('race'):
        if len(this_player['race']) > 0:
            mud.send_message(id, '****CLEAR****<f32>' +
                             this_player['name'] + '<r> (' +
                             this_player['race'] + ' ' +
                             this_player['characterClass'] + ')\n')

    if this_player.get('speakLanguage'):
        mud.send_message(
            id,
            '<f15>Speaks:<r> ' +
            this_player['speakLanguage'] +
            '\n')
    if pid == id:
        if players[id].get('language'):
            if len(players[id]['language']) > 1:
                languages_str = ''
                lang_ctr = 0
                for lang in players[id]['language']:
                    if lang_ctr > 0:
                        languages_str = languages_str + ', ' + lang
                    else:
                        languages_str = languages_str + lang
                    lang_ctr += 1
                mud.send_message(id, 'Languages:<r> ' + languages_str + '\n')

    desc = \
        random_desc(this_player['lookDescription'])
    mud.send_message_wrap(id, '', desc + '<r>\n')

    if this_player.get('canGo'):
        if this_player['canGo'] == 0:
            mud.send_message(id, 'They are frozen.<r>\n')

    # count items of clothing
    wearing_ctr = 0
    for clth in WEAR_LOCATION:
        if int(this_player['clo_' + clth]) > 0:
            wearing_ctr += 1

    player_name = 'You'
    player_name2 = 'your'
    player_name3 = 'have'
    if id != pid:
        player_name = 'They'
        player_name2 = 'their'
        player_name3 = 'have'

    if int(this_player['clo_rhand']) > 0:
        hand_item_id = this_player['clo_rhand']
        item_name = items_db[hand_item_id]['name']
        if 'right hand ' in item_name:
            item_name = item_name.replace('right hand ', '')
        elif 'right handed ' in item_name:
            item_name = item_name.replace('right handed ', '')
        mud.send_message(id, player_name + ' ' + player_name3 + ' ' +
                         items_db[hand_item_id]['article'] +
                         ' ' + item_name +
                         ' in ' + player_name2 + ' right hand.<r>\n')
    if this_player.get('clo_rfinger'):
        if int(this_player['clo_rfinger']) > 0:
            mud.send_message(id, player_name + ' ' + player_name3 + ' ' +
                             items_db[this_player['clo_rfinger']]['article'] +
                             ' ' +
                             items_db[this_player['clo_rfinger']]['name'] +
                             ' on the finger of ' + player_name2 +
                             ' right hand.<r>\n')
    if this_player.get('clo_waist'):
        if int(this_player['clo_waist']) > 0:
            mud.send_message(id, player_name + ' ' + player_name3 + ' ' +
                             items_db[this_player['clo_waist']]['article'] +
                             ' ' +
                             items_db[this_player['clo_waist']]['name'] +
                             ' on waist of ' + player_name2 + '<r>\n')
    if int(this_player['clo_lhand']) > 0:
        hand_item_id = this_player['clo_lhand']
        item_name = items_db[hand_item_id]['name']
        if 'left hand ' in item_name:
            item_name = item_name.replace('left hand ', '')
        elif 'left handed ' in item_name:
            item_name = item_name.replace('left handed ', '')
        mud.send_message(id, player_name + ' ' + player_name3 + ' ' +
                         items_db[this_player['clo_lhand']]['article'] +
                         ' ' + item_name +
                         ' in ' + player_name2 + ' left hand.<r>\n')
    if int(this_player['clo_lear']) > 0:
        hand_item_id = this_player['clo_lear']
        item_name = items_db[hand_item_id]['name']
        mud.send_message(id, player_name + ' ' + player_name3 + ' ' +
                         items_db[this_player['clo_lear']]['article'] +
                         ' ' + item_name +
                         ' in ' + player_name2 + ' left ear.<r>\n')
    if int(this_player['clo_rear']) > 0:
        hand_item_id = this_player['clo_rear']
        item_name = items_db[hand_item_id]['name']
        mud.send_message(id, player_name + ' ' + player_name3 + ' ' +
                         items_db[this_player['clo_rear']]['article'] +
                         ' ' + item_name +
                         ' in ' + player_name2 + ' right ear.<r>\n')
    if this_player.get('clo_lfinger'):
        if int(this_player['clo_lfinger']) > 0:
            mud.send_message(id, player_name + ' ' + player_name3 + ' ' +
                             items_db[this_player['clo_lfinger']]['article'] +
                             ' ' +
                             items_db[this_player['clo_lfinger']]['name'] +
                             ' on the finger of ' + player_name2 +
                             ' left hand.<r>\n')

    if wearing_ctr > 0:
        wearing_msg = player_name + ' are wearing'
        wearing_ctr2 = 0
        for clth in WEAR_LOCATION:
            if not this_player.get('clo_' + clth):
                continue
            clothing_item_id = this_player['clo_' + clth]
            if int(clothing_item_id) > 0:
                if wearing_ctr2 > 0:
                    if wearing_ctr2 == wearing_ctr - 1:
                        wearing_msg = wearing_msg + ' and '
                    else:
                        wearing_msg = wearing_msg + ', '
                else:
                    wearing_msg = wearing_msg + ' '
                wearing_msg = wearing_msg + \
                    items_db[clothing_item_id]['article'] + \
                    ' ' + items_db[clothing_item_id]['name']
                if clth == 'neck':
                    wearing_msg = \
                        wearing_msg + ' around ' + player_name2 + ' neck'
                if clth == 'lwrist':
                    wearing_msg = \
                        wearing_msg + ' on ' + player_name2 + ' left wrist'
                if clth == 'rwrist':
                    wearing_msg = \
                        wearing_msg + ' on ' + player_name2 + ' right wrist'
                if clth == 'lleg':
                    wearing_msg = \
                        wearing_msg + ' on ' + player_name2 + ' left leg'
                if clth == 'rleg':
                    wearing_msg = \
                        wearing_msg + ' on ' + player_name2 + ' right leg'
                wearing_ctr2 += 1
        mud.send_message(id, wearing_msg + '.<r>\n')

    mud.send_message(id, '<f15>Health status:<r> ' +
                     health_of_player(pid, players) + '.<r>\n')
    mud.send_message(id, '<r>\n')


def _health(params, mud, players_db: {}, players: {}, rooms: {},
            npcs_db: {}, npcs: {}, items_db: {}, items: {},
            env_db: {}, env: {}, eventDB: {}, event_schedule,
            id: int, fights: {}, corpses: {}, blocklist,
            map_area: [], character_class_db: {}, spells_db: {},
            sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}):
    mud.send_message(id, '<r>\n')
    mud.send_message(id, '<f15>Health status:<r> ' +
                     health_of_player(id, players) + '.<r>\n')


def _bio(params, mud, players_db: {}, players: {}, rooms: {},
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
        for pid, _ in list(players.items()):
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


def _eat(params, mud, players_db: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {},
         env_db: {}, env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    food = params.lower()
    food_item_id = 0
    if len(list(players[id]['inv'])) > 0:
        for i in list(players[id]['inv']):
            if food in items_db[int(i)]['name'].lower():
                if items_db[int(i)]['edible'] != 0:
                    food_item_id = int(i)
                    break
                mud.send_message(id, "That's not consumable.\n\n")
                return

    if food_item_id == 0:
        mud.send_message(id, "Your don't have " + params + ".\n\n")
        return

    edibility = items_db[food_item_id]['edible']

    food_str = \
        items_db[food_item_id]['article'] + " " + \
        items_db[food_item_id]['name']
    if edibility > 1:
        eat_str = "You consume " + food_str
    else:
        eat_str = \
            random_desc(
                "With extreme reluctance, you eat " + food_str + '|' +
                "You eat " + food_str +
                ", but now you wish that you hadn't|" +
                "Revoltingly, you eat " + food_str)
    mud.send_message(id, eat_str + ".\n\n")

    # Alter hp
    players[id]['hp'] = players[id]['hp'] + edibility
    if players[id]['hp'] > 100:
        players[id]['hp'] = 100

    # Consumed
    players[id]['inv'].remove(str(food_item_id))

    # decrement any attributes associated with the food
    update_player_attributes(id, players, items_db, food_item_id, -1)

    # Remove from hands
    if int(players[id]['clo_rhand']) == food_item_id:
        players[id]['clo_rhand'] = 0
    if int(players[id]['clo_lhand']) == food_item_id:
        players[id]['clo_lhand'] = 0


def _step_over(params, mud, players_db: {}, players: {}, rooms: {},
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

    for direction, _ in rooms[room_id]['exits'].items():
        if direction in params:
            _go('######step######' + direction, mud, players_db, players,
                rooms, npcs_db, npcs, items_db, items, env_db, env, eventDB,
                event_schedule, id, fights, corpses, blocklist, map_area,
                character_class_db, spells_db, sentiment_db, guilds_db,
                clouds, races_db, item_history, markets, cultures_db)
            break


def _climb_base(params, mud, players_db: {}, players: {}, rooms: {},
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

    fail_msg = None
    for item, _ in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            item_id = items[item]['id']

            # can the player see the item?
            if not _item_is_visible(id, players, item_id, items_db):
                continue

            # item fields needed for climbing
            if items_db[item_id].get('climbFail'):
                fail_msg = items_db[item_id]['climbFail']
            if not items_db[item_id].get('climbThrough'):
                continue
            if not items_db[item_id].get('exit'):
                continue

            # if this is a door is it open?
            if items_db[item_id].get('state'):
                if 'open' not in items_db[item_id]['state']:
                    mud.send_message(id, items_db[item_id]['name'] +
                                     " is closed.\n\n")
                    continue

            # is the player too big?
            target_room = items_db[item_id]['exit']
            if rooms[target_room]['maxPlayerSize'] > -1:
                if players[id]['siz'] > rooms[target_room]['maxPlayerSize']:
                    mud.send_message(id, "You're too big.\n\n")
                    return

            # are there too many players in the room?
            if rooms[target_room]['maxPlayers'] > -1:
                if _players_in_room(target_room, players, npcs) >= \
                   rooms[target_room]['maxPlayers']:
                    if not sit:
                        mud.send_message(id, "It's too crowded.\n\n")
                    else:
                        mud.send_message(id,
                                         "It's already fully occupied.\n\n")
                    return

            if not _item_is_climbable(id, players, item_id, items_db):
                if fail_msg:
                    mud.send_message_wrap(id, '<f220>',
                                          random_desc(fail_msg) + ".\n\n")
                else:
                    if not sit:
                        fail_msg = 'You try to climb, but totally fail'
                    else:
                        fail_msg = 'You try to sit, but totally fail'
                    mud.send_message(id, random_desc(fail_msg) + ".\n\n")
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
                ev_leave = int(rooms[players[id]['room']]['eventOnLeave'])
                add_to_scheduler(ev_leave, id, event_schedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = target_room
            # climbing message
            desc = \
                random_desc(items_db[item_id]['climbThrough'])
            mud.send_message_wrap(id, '<f230>', desc + "\n\n")
            time.sleep(3)
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] != "":
                ev_enter = int(rooms[players[id]['room']]['eventOnEnter'])
                add_to_scheduler(ev_enter, id, event_schedule, eventDB)
            # message to other players
            desc = random_desc(players[id]['inDescription'])
            message_to_room_players(mud, players, id, '<f32>' +
                                    players[id]['name'] + '<r> ' +
                                    desc + "\n\n")
            # look after climbing
            _look('', mud, players_db, players, rooms,
                  npcs_db, npcs, items_db, items,
                  env_db, env, eventDB, event_schedule,
                  id, fights, corpses, blocklist,
                  map_area, character_class_db, spells_db,
                  sentiment_db, guilds_db, clouds, races_db,
                  item_history, markets, cultures_db)
            return
    if fail_msg:
        fail_msg_str = random_desc(fail_msg)
        mud.send_message_wrap(id, '<f220>', fail_msg_str + ".\n\n")
    else:
        mud.send_message(id, "Nothing happens.\n\n")


def _climb(params, mud, players_db: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {},
           env_db: {}, env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    _climb_base(params, mud, players_db, players, rooms,
                npcs_db, npcs, items_db, items,
                env_db, env, eventDB, event_schedule,
                id, fights, corpses, blocklist,
                map_area, character_class_db, spells_db,
                sentiment_db, guilds_db, clouds, races_db,
                False, item_history, markets, cultures_db)


def _sit(params, mud, players_db: {}, players: {}, rooms: {},
         npcs_db: {}, npcs: {}, items_db: {}, items: {},
         env_db: {}, env: {}, eventDB: {}, event_schedule,
         id: int, fights: {}, corpses: {}, blocklist,
         map_area: [], character_class_db: {}, spells_db: {},
         sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
         item_history: {}, markets: {}, cultures_db: {}):
    _climb_base(params, mud, players_db, players, rooms,
                npcs_db, npcs, items_db, items,
                env_db, env, eventDB, event_schedule,
                id, fights, corpses, blocklist,
                map_area, character_class_db, spells_db,
                sentiment_db, guilds_db, clouds, races_db,
                True, item_history, markets, cultures_db)


def _heave(params, mud, players_db: {}, players: {}, rooms: {},
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

    for item, _ in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            item_id = items[item]['id']
            if not _item_is_visible(id, players, item_id, items_db):
                continue
            if not items_db[item_id].get('heave'):
                continue
            if not items_db[item_id].get('exit'):
                continue
            if target not in items_db[item_id]['name']:
                continue
            if items_db[item_id].get('state'):
                if 'open' not in items_db[item_id]['state']:
                    mud.send_message(id, items_db[item_id]['name'] +
                                     " is closed.\n\n")
                    continue
            target_room = items_db[item_id]['exit']
            if rooms[target_room]['maxPlayerSize'] > -1:
                if players[id]['siz'] > rooms[target_room]['maxPlayerSize']:
                    mud.send_message(id, "You're too big.\n\n")
                    return
            if rooms[target_room]['maxPlayers'] > -1:
                if _players_in_room(target_room, players, npcs) >= \
                   rooms[target_room]['maxPlayers']:
                    mud.send_message(id, "It's too crowded.\n\n")
                    return
            desc = random_desc(players[id]['outDescription'])
            message_to_room_players(mud, players, id, '<f32>' +
                                    players[id]['name'] + '<r> ' +
                                    desc + '\n')
            # Trigger old room eventOnLeave for the player
            if rooms[players[id]['room']]['eventOnLeave'] != "":
                ev_leave = int(rooms[players[id]['room']]['eventOnLeave'])
                add_to_scheduler(ev_leave, id, event_schedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = target_room
            # heave message
            desc = random_desc(items_db[item_id]['heave'])
            mud.send_message_wrap(id, '<f220>', desc + "\n\n")
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] != "":
                ev_enter = int(rooms[players[id]['room']]['eventOnEnter'])
                add_to_scheduler(ev_enter, id, event_schedule, eventDB)
            # message to other players
            desc = random_desc(players[id]['inDescription'])
            message_to_room_players(mud, players, id, '<f32>' +
                                    players[id]['name'] + '<r> ' +
                                    desc + "\n\n")
            time.sleep(3)
            # look after climbing
            _look('', mud, players_db, players, rooms,
                  npcs_db, npcs, items_db, items,
                  env_db, env, eventDB, event_schedule, id,
                  fights, corpses, blocklist,
                  map_area, character_class_db, spells_db,
                  sentiment_db, guilds_db, clouds, races_db,
                  item_history, markets, cultures_db)
            return
    mud.send_message(id, "Nothing happens.\n\n")


def _jump(params, mud, players_db: {}, players: {}, rooms: {},
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
    for item, _ in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            item_id = items[item]['id']
            if not _item_is_visible(id, players, item_id, items_db):
                continue
            if not items_db[item_id].get('jumpTo'):
                continue
            if not items_db[item_id].get('exit'):
                continue
            word_matched = False
            for wrd in words:
                if wrd in items_db[item_id]['name'].lower():
                    word_matched = True
                    break
            if not word_matched:
                continue
            if items_db[item_id].get('state'):
                if 'open' not in items_db[item_id]['state']:
                    mud.send_message(id, items_db[item_id]['name'] +
                                     " is closed.\n\n")
                    continue
            target_room = items_db[item_id]['exit']
            if rooms[target_room]['maxPlayerSize'] > -1:
                if players[id]['siz'] > rooms[target_room]['maxPlayerSize']:
                    mud.send_message(id, "You're too big.\n\n")
                    return
            if rooms[target_room]['maxPlayers'] > -1:
                if _players_in_room(target_room, players, npcs) >= \
                   rooms[target_room]['maxPlayers']:
                    mud.send_message(id, "It's too crowded.\n\n")
                    return
            desc = \
                random_desc(players[id]['outDescription'])
            message_to_room_players(mud, players, id, '<f32>' +
                                    players[id]['name'] + '<r> ' +
                                    desc + '\n')
            # Trigger old room eventOnLeave for the player
            if rooms[players[id]['room']]['eventOnLeave'] != "":
                ev_leave = int(rooms[players[id]['room']]['eventOnLeave'])
                add_to_scheduler(ev_leave, id, event_schedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = target_room
            # climbing message
            desc = random_desc(items_db[item_id]['jumpTo'])
            mud.send_message_wrap(id, '<f230>', desc + "\n\n")
            time.sleep(3)
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] != "":
                ev_enter = int(rooms[players[id]['room']]['eventOnEnter'])
                add_to_scheduler(ev_enter, id, event_schedule, eventDB)
            # message to other players
            desc = random_desc(players[id]['inDescription'])
            message_to_room_players(mud, players, id, '<f32>' +
                                    players[id]['name'] + '<r> ' +
                                    desc + "\n\n")
            # look after climbing
            _look('', mud, players_db, players,
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


def _deal(params, mud, players_db: {}, players: {}, rooms: {},
          npcs_db: {}, npcs: {}, items_db: {}, items: {},
          env_db: {}, env: {}, eventDB: {}, event_schedule,
          id: int, fights: {}, corpses: {}, blocklist,
          map_area: [], character_class_db: {}, spells_db: {},
          sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
          item_history: {}, markets: {}, cultures_db: {}):
    """Deal cards to other players
    """
    params_lower = params.lower()
    deal_to_players(players, id, params_lower, mud, rooms, items, items_db)


def _hand_of_cards(params, mud, players_db: {}, players: {}, rooms: {},
                   npcs_db: {}, npcs: {}, items_db: {}, items: {},
                   env_db: {}, env: {}, eventDB: {}, event_schedule,
                   id: int, fights: {}, corpses: {}, blocklist,
                   map_area: [], character_class_db: {}, spells_db: {},
                   sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                   item_history: {}, markets: {}, cultures_db: {}):
    """Show hand of cards
    """
    hand_of_cards_show(players, id, mud, rooms, items, items_db)


def _swap_a_card(params, mud, players_db: {}, players: {}, rooms: {},
                 npcs_db: {}, npcs: {}, items_db: {}, items: {},
                 env_db: {}, env: {}, eventDB: {}, event_schedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 map_area: [], character_class_db: {}, spells_db: {},
                 sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                 item_history: {}, markets: {}, cultures_db: {}):
    """Swap a playing card for another from the deck
    """
    swap_card(params, players, id, mud, rooms, items, items_db)


def _shuffle(params, mud, players_db: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {},
             env_db: {}, env: {}, eventDB: {}, event_schedule,
             id: int, fights: {}, corpses: {}, blocklist,
             map_area: [], character_class_db: {}, spells_db: {},
             sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}):
    """Shuffle a deck of cards
    """
    shuffle_cards(players, id, mud, rooms, items, items_db)


def _call_card_game(params, mud, players_db: {}, players: {}, rooms: {},
                    npcs_db: {}, npcs: {}, items_db: {}, items: {},
                    env_db: {}, env: {}, eventDB: {}, event_schedule,
                    id: int, fights: {}, corpses: {}, blocklist,
                    map_area: [], character_class_db: {}, spells_db: {},
                    sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                    item_history: {}, markets: {}, cultures_db: {}):
    """Players show their cards
    """
    call_cards(players, id, mud, rooms, items, items_db)


def _morris_game(params, mud, players_db: {}, players: {}, rooms: {},
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

    board_name = get_morris_board_name(players, id, rooms, items, items_db)
    show_morris_board(board_name, players, id, mud, rooms, items, items_db)


def _chess(params, mud, players_db: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {},
           env_db: {}, env: {}, eventDB: {}, event_schedule,
           id: int, fights: {}, corpses: {}, blocklist,
           map_area: [], character_class_db: {}, spells_db: {},
           sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}):
    """Jumping onto an item takes the player to a different room
    """
    # check if board exists in room
    board_item_id = \
        _chess_board_in_room(players, id, rooms, items, items_db)
    if not board_item_id:
        mud.send_message(id, "\nThere isn't a chess board here.\n\n")
        return
    # create the game state
    if not items[board_item_id].get('gameState'):
        items[board_item_id]['gameState'] = {}
    if not items[board_item_id]['gameState'].get('state'):
        items[board_item_id]['gameState']['state'] = initial_chess_board()
        items[board_item_id]['gameState']['turn'] = 'white'
        items[board_item_id]['gameState']['history'] = []
    # get the game history
    game_state = items[board_item_id]['gameState']['state']
    game_board_name = \
        _chess_board_name(players, id, rooms, items, items_db)
    if not params:
        show_chess_board(game_board_name, game_state, id, mud,
                         items[board_item_id]['gameState']['turn'])
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
        if len(items[board_item_id]['gameState']['history']) < 2:
            params = 'reset'
        else:
            mud.send_message(id, '\nUndoing last chess move.\n')
            items[board_item_id]['gameState']['history'].pop()
            game_state = items[board_item_id]['gameState']['history'][-1]
            items[board_item_id]['gameState']['state'] = game_state
            if items[board_item_id]['gameState']['turn'] == 'white':
                items[board_item_id]['gameState']['turn'] = 'black'
            else:
                items[board_item_id]['gameState']['turn'] = 'white'
            show_chess_board(game_board_name, game_state, id, mud,
                             items[board_item_id]['gameState']['turn'])
            return
    # begin a new chess game
    if 'reset' in params or \
       'restart' in params or \
       'start again' in params or \
       'begin again' in params or \
       'new game' in params:
        mud.send_message(id, '\nStarting a new game.\n')
        items[board_item_id]['gameState']['state'] = initial_chess_board()
        items[board_item_id]['gameState']['turn'] = 'white'
        items[board_item_id]['gameState']['history'] = []
        game_state = items[board_item_id]['gameState']['state']
        show_chess_board(game_board_name, game_state, id, mud,
                         items[board_item_id]['gameState']['turn'])
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
                            items[board_item_id]['gameState']['state'],
                            items[board_item_id]['gameState']['turn'],
                            id, mud):
            mud.send_message(id, "\n" +
                             items[board_item_id]['gameState']['turn'] +
                             " moves from " + chess_moves[0] +
                             " to " + chess_moves[1] + ".\n")
            game_state = items[board_item_id]['gameState']['state']
            curr_turn = items[board_item_id]['gameState']['turn']
            if curr_turn == 'white':
                items[board_item_id]['gameState']['player1'] = \
                    players[id]['name']
                items[board_item_id]['gameState']['turn'] = 'black'
                # send a notification to the other player
                if items[board_item_id]['gameState'].get('player2'):
                    for plyr in players:
                        if plyr == id:
                            continue
                        if players[plyr]['name'] == \
                           items[board_item_id]['gameState']['player2']:
                            if players[plyr]['room'] == players[id]['room']:
                                turn_str = \
                                    items[board_item_id]['gameState']['turn']
                                show_chess_board(game_board_name,
                                                 game_state, plyr, mud,
                                                 turn_str)
            else:
                items[board_item_id]['gameState']['player2'] = \
                    players[id]['name']
                items[board_item_id]['gameState']['turn'] = 'white'
                # send a notification to the other player
                if items[board_item_id]['gameState'].get('player1'):
                    for plyr in players:
                        if plyr == id:
                            continue
                        if players[plyr]['name'] == \
                           items[board_item_id]['gameState']['player1']:
                            if players[plyr]['room'] == players[id]['room']:
                                turn_str = \
                                    items[board_item_id]['gameState']['turn']
                                show_chess_board(game_board_name, game_state,
                                                 plyr, mud, turn_str)
            gstate = game_state.copy()
            items[board_item_id]['gameState']['history'].append(gstate)
            show_chess_board(game_board_name, game_state, id, mud, curr_turn)
            return
        mud.send_message(id, "\nThat's not a valid move.\n")
        return
    show_chess_board(game_board_name, game_state, id, mud,
                     items[board_item_id]['gameState']['turn'])


def _graphics(params, mud, players_db: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {},
              env_db: {}, env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, blocklist,
              map_area: [], character_class_db: {}, spells_db: {},
              sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}):
    """Turn graphical output on or off
    """
    graphics_state = params.lower().strip()
    if graphics_state in ('off', 'false', 'no'):
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
    for item_id, item in rooms[room_id]['marketInventory'].items():
        if item['stock'] < 1:
            continue
        item_line = items_db[item_id]['name']
        while len(item_line) < 30:
            item_line += '.'
        item_cost = item['cost']
        if item_cost == '0':
            item_line += 'Free'
        else:
            item_line += item_cost
        mud.send_message(id, item_line)
        ctr += 1
    mud.send_message(id, '\n')
    if ctr == 0:
        mud.send_message(id, 'Nothing\n\n')


def _buy(params, mud, players_db: {}, players: {}, rooms: {},
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

    params_lower = params.lower()
    if not params_lower:
        _show_items_for_sale(mud, rooms, room_id, players, id, items_db)
    else:
        # buy some particular item
        for item_id, item in rooms[room_id]['marketInventory'].items():
            if item['stock'] < 1:
                continue
            item_name = items_db[item_id]['name'].lower()
            if item_name not in params_lower:
                continue
            if _item_in_inventory(players, id,
                                  items_db[item_id]['name'], items_db):
                mud.send_message(id, 'You already have that\n\n')
                return
            item_cost = item['cost']
            if buy_item(players, id, item_id, items_db, item_cost):
                # is the item too heavy?
                players[id]['wei'] = \
                    player_inventory_weight(id, players, items_db)

                if players[id]['wei'] + items_db[item_id]['weight'] > \
                   _get_max_weight(id, players):
                    mud.send_message(id, "You can't carry any more.\n\n")
                    return
                # add the item to the player's inventory
                if str(item_id) not in players[id]['inv']:
                    players[id]['inv'].append(str(item_id))
                # update the weight of the player
                players[id]['wei'] = \
                    player_inventory_weight(id, players, items_db)
                update_player_attributes(id, players, items_db, item_id, 1)

                mud.send_message(id, 'You buy ' +
                                 items_db[item_id]['article'] +
                                 ' ' + items_db[item_id]['name'] + '\n\n')
            else:
                if item_cost.endswith('gp'):
                    mud.send_message(id,
                                     'You do not have enough gold pieces\n\n')
                elif item_cost.endswith('sp'):
                    mud.send_message(id,
                                     'You do not have enough ' +
                                     'silver pieces\n\n')
                elif item_cost.endswith('cp'):
                    mud.send_message(id,
                                     'You do not have enough ' +
                                     'copper pieces\n\n')
                elif item_cost.endswith('ep'):
                    mud.send_message(id,
                                     'You do not have enough ' +
                                     'electrum pieces\n\n')
                elif item_cost.endswith('pp'):
                    mud.send_message(id,
                                     'You do not have enough ' +
                                     'platinum pieces\n\n')
                else:
                    mud.send_message(id, 'You do not have enough money\n\n')
            return
        mud.send_message(id, "That's not sold here\n\n")


def _start_fishing(params, mud, players_db: {}, players: {}, rooms: {},
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
        desc_str = 'You need to be holding a rod|' + \
            'You need to be holding something to fish with'
        mud.send_message(id, random_desc(desc_str) + '<r>\n\n')
        return
    rid = players[id]['room']
    room_name_lower = rooms[rid]['name'].lower()
    if not is_fishing_site(rooms, rid):
        if 'isFishing' in players[id]:
            del players[id]['isFishing']
        desc_str = "This isn't a fishing site|" + \
            "You can't fish here|" + \
            "This does not appear to be a fishing location"
        mud.send_message(id, random_desc(desc_str) + '<r>\n\n')
        return
    if 'lava' in room_name_lower:
        if 'isFishing' in players[id]:
            del players[id]['isFishing']
        desc_str = "You won't find any fish here"
        mud.send_message(id, random_desc(desc_str) + '<r>\n\n')
        return
    if player_is_prone(id, players):
        if 'isFishing' in players[id]:
            del players[id]['isFishing']
        desc_str = "You can't fish while lying down"
        mud.send_message(id, random_desc(desc_str) + '<r>\n\n')
        return
    if 'isFishing' not in players[id]:
        players[id]['isFishing'] = True
        if holding_fly_fishing_rod(players, id, items_db):
            desc_str = "You prepare the fly and then cast it out|" + \
                "You wave the rod back and forth and cast out the fly|" + \
                "Casting out the fly, you begin fishing"
        else:
            desc_str = \
                "With a forwards flick of the rod you cast out the line|" + \
                "Casting out the line with a forward flick of the rod, " + \
                "you begin fishing"
    else:
        desc_str = "You continue fishing"
    mud.send_message(id, random_desc(desc_str) + '<r>\n\n')


def _item_sell(params, mud, players_db: {}, players: {}, rooms: {},
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

    params_lower = params.lower()
    if not params_lower:
        mud.send_message(id, 'What do you want to sell?\n')
    else:
        # does this market buy this type of item?
        market_type = get_market_type(rooms[room_id]['name'], markets)
        if not market_type:
            mud.send_message(id, "You can't sell here.<r>\n")
            return
        buys_item_types = market_buys_item_types(market_type, markets)
        able_to_sell = False
        for item_type in buys_item_types:
            if item_type in params_lower:
                able_to_sell = True
                break
        if not able_to_sell:
            mud.send_message(id, "You can't sell that here\n\n")
            return
        item_id = -1
        for item, _ in list(items.items()):
            if params_lower in items_db[items[item]['id']]['name'].lower():
                item_id = items[item]['id']
                break
        if item_id == -1:
            mud.send_message(id, 'Error: item not found ' + params + ' \n\n')
            return
        # remove from item to the player's inventory
        if str(item_id) in players[id]['inv']:
            players[id]['inv'].remove(str(item_id))
        # update the weight of the player
        players[id]['wei'] = player_inventory_weight(id, players, items_db)
        update_player_attributes(id, players, items_db, item_id, 1)

        # Increase your money
        item_cost = items_db[item_id]['cost']
        # TODO the cost may vary depending upon room/region/time
        qty, denomination = parse_cost(item_cost)
        if denomination:
            if denomination in players[id]:
                qty = int(item_cost.replace(denomination, ''))
                players[id][denomination] += qty
        mud.send_message(id, 'You have sold ' + items_db[item_id]['article'] +
                         ' ' + items_db[item_id]['name'] + ' for ' +
                         item_cost + '\n\n')


def _go(params, mud, players_db: {}, players: {}, rooms: {},
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
        rmid = rooms[players[id]['room']]

        # if the specified exit is found in the room's exits list
        rmexits = _get_room_exits(mud, rooms, players, id)
        if ex in rmexits:
            # check if there is enough room
            target_room = None
            if ex in rmid['exits']:
                target_room = rmid['exits'][ex]
            elif rmid.get('tideOutExits'):
                target_room = rmid['tideOutExits'][ex]
            elif rmid.get('exitsWhenWearing'):
                target_room = rmid['exitsWhenWearing'][ex]
            if target_room:
                if rooms[target_room]['maxPlayers'] > -1:
                    if _players_in_room(target_room, players, npcs) >= \
                       rooms[target_room]['maxPlayers']:
                        mud.send_message(id, 'The room is full.<r>\n\n')
                        return

                # Check that the player is not too tall
                if rooms[target_room]['maxPlayerSize'] > -1:
                    if players[id]['siz'] > \
                       rooms[target_room]['maxPlayerSize']:
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
                followers_msg = ""
                for nid, _ in list(npcs.items()):
                    if ((npcs[nid]['follow'] == players[id]['name'] or
                        npcs[nid]['familiarOf'] == players[id]['name']) and
                       npcs[nid]['familiarMode'] == 'follow'):
                        # is the npc in the same room as the player?
                        if npcs[nid]['room'] == players[id]['room']:
                            # is the player within the permitted npc path?
                            rm_ex = rmid['exits'][ex]
                            if rm_ex in list(npcs[nid]['path']) or \
                               npcs[nid]['familiarOf'] == players[id]['name']:
                                foll_room_id = rmid['exits'][ex]
                                max_pl_size = \
                                    rooms[foll_room_id]['maxPlayerSize']
                                if max_pl_size < 0 or \
                                   npcs[nid]['siz'] <= \
                                   rooms[foll_room_id]['maxPlayerSize']:
                                    npcs[nid]['room'] = foll_room_id
                                    npitem = npcs[nid]
                                    desc = \
                                        random_desc(npitem['inDescription'])
                                    followers_msg = \
                                        followers_msg + '<f32>' + \
                                        npcs[nid]['name'] + '<r> ' + \
                                        desc + '.\n\n'
                                    desc = \
                                        random_desc(npitem['outDescription'])
                                    message_to_room_players(mud, players,
                                                            id,
                                                            '<f32>' +
                                                            npitem['name'] +
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
                    _players_move_together(id, rmid['exits'][ex], mud,
                                           players_db, players, rooms,
                                           npcs_db, npcs,
                                           items_db, items, env_db, env,
                                           eventDB, event_schedule,
                                           fights, corpses, blocklist,
                                           map_area,
                                           character_class_db, spells_db,
                                           sentiment_db, guilds_db, clouds,
                                           races_db, item_history, markets,
                                           cultures_db)
                players[id]['room'] = rmid['exits'][ex]

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

                _look('', mud, players_db, players, rooms, npcs_db, npcs,
                      items_db, items, env_db, env, eventDB, event_schedule,
                      id, fights, corpses, blocklist, map_area,
                      character_class_db, spells_db, sentiment_db,
                      guilds_db, clouds, races_db, item_history, markets,
                      cultures_db)
                # report any followers
                if len(followers_msg) > 0:
                    message_to_room_players(mud, players, id, followers_msg)
                    mud.send_message(id, followers_msg)
        else:
            # the specified exit wasn't found in the current room
            # send back an 'unknown exit' message
            mud.send_message(id, "Unknown exit <f226>'{}'".format(ex) +
                             "<r>\n\n")
    else:
        mud.send_message(id,
                         'Somehow, your legs refuse to obey your will.<r>\n')


def _go_north(params, mud, players_db, players, rooms,
              npcs_db: {}, npcs, items_db: {}, items: {}, env_db: {},
              env, eventDB: {}, event_schedule, id, fights,
              corpses, blocklist, map_area, character_class_db: {},
              spells_db: {}, sentiment_db: {},
              guilds_db: {}, clouds, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('north', mud, players_db, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_south(params, mud, players_db: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
              env, eventDB: {}, event_schedule, id, fights,
              corpses, blocklist, map_area, character_class_db: {},
              spells_db: {}, sentiment_db: {}, guilds_db: {},
              clouds, races_db: {},
              item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('south', mud, players_db, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_east(params, mud, players_db: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
             env, eventDB: {}, event_schedule, id, fights,
             corpses, blocklist, map_area, character_class_db: {},
             spells_db: {}, sentiment_db: {},
             guilds_db: {}, clouds, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('east', mud, players_db, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_west(params, mud, players_db: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db,
             env, eventDB: {}, event_schedule, id, fights,
             corpses, blocklist, map_area, character_class_db: {},
             spells_db: {}, sentiment_db: {}, guilds_db: {},
             clouds, races_db: {},
             item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('west', mud, players_db, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_up(params, mud, players_db: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
           env, eventDB: {}, event_schedule, id, fights,
           corpses, blocklist, map_area, character_class_db: {},
           spells_db: {}, sentiment_db: {}, guilds_db: {},
           clouds, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('up', mud, players_db, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_down(params, mud, players_db: {}, players: {}, rooms: {},
             npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
             env, eventDB: {}, event_schedule, id, fights,
             corpses, blocklist, map_area, character_class_db: {},
             spells_db: {}, sentiment_db: {}, guilds_db: {}, clouds,
             races_db: {}, item_history: {}, markets: {},
             cultures_db: {}) -> None:
    _go('down', mud, players_db, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_in(params: str, mud, players_db: {}, players: {}, rooms: {},
           npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
           env, eventDB: {}, event_schedule, id, fights: {},
           corpses, blocklist, map_area, character_class_db: {},
           spells_db: {}, sentiment_db: {}, guilds_db: {},
           clouds: {}, races_db: {},
           item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('in', mud, players_db, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _go_out(params: str, mud, players_db: {}, players: {}, rooms: {},
            npcs_db: {}, npcs: {}, items_db: {}, items: {}, env_db: {},
            env, eventDB: {}, event_schedule, id, fights: {},
            corpses, blocklist, map_area, character_class_db: {},
            spells_db: {}, sentiment_db: {}, guilds_db: {},
            clouds: {}, races_db: {},
            item_history: {}, markets: {}, cultures_db: {}) -> None:
    _go('out', mud, players_db, players, rooms, npcs_db,
        npcs, items_db, items, env_db, env, eventDB, event_schedule,
        id, fights, corpses, blocklist, map_area, character_class_db,
        spells_db, sentiment_db, guilds_db, clouds, races_db,
        item_history, markets, cultures_db)


def _conjure_room(params, mud, players_db: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist: {},
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                  item_history: {}, markets: {}, cultures_db: {}):
    params = params.replace('room ', '')
    room_direction = params.lower().strip()
    possible_directions = ('north', 'south', 'east', 'west',
                           'up', 'down', 'in', 'out')
    opposite_direction = {
        'north': 'south',
        'south': 'north',
        'east': 'west',
        'west': 'east',
        'up': 'down',
        'down': 'up',
        'in': 'out',
        'out': 'in'
    }
    if room_direction not in possible_directions:
        mud.send_message(id, 'Specify a room direction.\n\n')
        return False

    # Is there already a room in that direction?
    player_room_id = players[id]['room']
    room_exits = _get_room_exits(mud, rooms, players, id)
    if room_exits.get(room_direction):
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
            opposite_direction[room_direction]: player_room_id
        }
    }
    rooms[room_id] = newrm
    room_exits[room_direction] = room_id

    # update the room coordinates
    for rmid in rooms:
        rooms[rmid]['coords'] = []

    log("New room: " + room_id, 'info')
    save_universe(rooms, npcs_db, npcs, items_db, items,
                  env_db, env, guilds_db)
    mud.send_message(id, 'Room created.\n\n')


def _conjure_item(params, mud, players_db: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                  item_history: {}, markets: {}, cultures_db: {}):
    item_name = params.lower()
    if len(item_name) == 0:
        mud.send_message(id, "Specify the name of an item to conjure.\n\n")
        return False

    # Check if item is in player's inventory
    for item in players[id]['inv']:
        for iid, _ in list(items_db.items()):
            if str(iid) == item:
                if item_name in items_db[iid]['name'].lower():
                    mud.send_message(id, "You have " +
                                     items_db[iid]['article'] + " " +
                                     items_db[iid]['name'] +
                                     " in your inventory already.\n\n")
                    return False
    # Check if it is in the room
    for item, _ in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            if item_name in items_db[items[item]['id']]['name'].lower():
                mud.send_message(id, "It's already here.\n\n")
                return False

    item_id = -1
    for item, _ in list(items.items()):
        if item_name == items_db[items[item]['id']]['name'].lower():
            item_id = items[item]['id']
            break

    if item_id == -1:
        for item, _ in list(items.items()):
            if item_name in items_db[items[item]['id']]['name'].lower():
                item_id = items[item]['id']
                break

    if item_id != -1:
        # Generate item
        item_key = get_free_key(items)
        items[item_key] = {
            'id': item_id,
            'room': players[id]['room'],
            'whenDropped': int(time.time()),
            'lifespan': 900000000, 'owner': id
        }
        key_str = str(item_key)
        assign_item_history(key_str, items, item_history)
        mud.send_message(id, items_db[item_id]['article'] + ' ' +
                         items_db[item_id]['name'] +
                         ' spontaneously materializes in front of you.\n\n')
        save_universe(rooms, npcs_db, npcs, items_db, items, env_db,
                      env, guilds_db)
        return True
    return False


def _random_familiar(npcs_db: {}):
    """Picks a familiar at random and returns its index
    """
    possible_familiars = []
    for index, details in npcs_db.items():
        if len(details['familiarType']) > 0:
            if len(details['familiarOf']) == 0:
                possible_familiars.append(int(index))
    if len(possible_familiars) > 0:
        rand_index = len(possible_familiars) - 1
        return possible_familiars[randint(0, rand_index)]
    return -1


def _conjure_npc(params, mud, players_db: {}, players: {}, rooms: {},
                 npcs_db: {}, npcs: {}, items_db: {}, items: {},
                 env_db: {}, env: {}, eventDB: {}, event_schedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 map_area: [], character_class_db: {}, spells_db: {},
                 sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                 item_history: {}, markets: {}, cultures_db: {}):
    if not params.startswith('npc '):
        if not params.startswith('familiar'):
            return False

    npc_hit_points = 100
    is_familiar = False
    npc_type = 'NPC'
    if params.startswith('familiar'):
        is_familiar = True
        npc_type = 'Familiar'
        npc_index = _random_familiar(npcs_db)
        if npc_index < 0:
            mud.send_message(id, "No familiars known.\n\n")
            return
        npc_name = npcs_db[npc_index]['name']
        npc_hit_points = 5
        npc_size = 0
        npc_strength = 5
        npc_familiar_of = players[id]['name']
        npc_animal_type = npcs_db[npc_index]['animalType']
        npc_familiar_type = npcs_db[npc_index]['familiarType']
        npc_familiar_mode = "follow"
        npc_conv = deepcopy(npcs_db[npc_index]['conv'])
        npc_vocabulary = deepcopy(npcs_db[npc_index]['vocabulary'])
        npc_talk_delay = npcs_db[npc_index]['talkDelay']
        npc_random_factor = npcs_db[npc_index]['randomFactor']
        npc_look_description = npcs_db[npc_index]['lookDescription']
        npc_in_description = npcs_db[npc_index]['inDescription']
        npc_out_description = npcs_db[npc_index]['outDescription']
        npc_move_delay = npcs_db[npc_index]['moveDelay']
    else:
        npc_name = params.replace('npc ', '', 1).strip().replace('"', '')
        npc_size = size_from_description(npc_name)
        npc_strength = 80
        npc_familiar_of = ""
        npc_animal_type = ""
        npc_familiar_type = ""
        npc_familiar_mode = ""
        npc_conv = []
        npc_vocabulary = [""]
        npc_talk_delay = 300
        npc_random_factor = 100
        npc_look_description = "A new NPC, not yet described"
        npc_in_description = "arrives"
        npc_out_description = "goes"
        npc_move_delay = 300

    if len(npc_name) == 0:
        mud.send_message(id, "Specify the name of an NPC to conjure.\n\n")
        return False

    # Check if NPC is in the room
    for nid, _ in list(npcs.items()):
        if npcs[nid]['room'] == players[id]['room']:
            if npc_name.lower() in npcs[nid]['name'].lower():
                mud.send_message(id, npcs[nid]['name'] +
                                 " is already here.\n\n")
                return False

    # NPC has the culture assigned to the room
    room_culture = get_room_culture(cultures_db, rooms, players[id]['room'])
    if room_culture is None:
        room_culture = ''

    # default medium size
    new_npc = {
        "name": npc_name,
        "whenDied": None,
        "isAggressive": 0,
        "inv": [],
        "speakLanguage": "common",
        "language": ["common"],
        "culture": room_culture,
        "conv": npc_conv,
        "room": players[id]['room'],
        "path": [],
        "bodyType": "",
        "moveDelay": npc_move_delay,
        "moveType": "",
        "moveTimes": [],
        "vocabulary": npc_vocabulary,
        "talkDelay": npc_talk_delay,
        "timeTalked": 0,
        "lastSaid": 0,
        "lastRoom": None,
        "lastMoved": 0,
        "randomizer": 0,
        "randomFactor": npc_random_factor,
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
        "hpMax": npc_hit_points,
        "hp": npc_hit_points,
        "charge": 1233,
        "lvl": 5,
        "exp": 32,
        "str": npc_strength,
        "siz": npc_size,
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
        "inDescription": npc_in_description,
        "outDescription": npc_out_description,
        "lookDescription": npc_look_description,
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
        "familiarOf": npc_familiar_of,
        "familiarTarget": "",
        "familiarType": npc_familiar_type,
        "familiarMode": npc_familiar_mode,
        "animalType": npc_animal_type
    }

    if is_familiar:
        if players[id]['familiar'] != -1:
            npcs_key = players[id]['familiar']
        else:
            npcs_key = get_free_key(npcs)
            players[id]['familiar'] = npcs_key
    else:
        npcs_key = get_free_key(npcs)

    npcs[npcs_key] = new_npc
    npcs_db[npcs_key] = new_npc
    npcs_key_str = str(npcs_key)
    log(npc_type + ' ' + npc_name + ' generated in ' +
        players[id]['room'] + ' with key ' + npcs_key_str, 'info')
    if is_familiar:
        mud.send_message(
            id,
            'Your familiar, ' + npc_name +
            ', spontaneously appears.\n\n')
    else:
        mud.send_message(id, npc_name + ' spontaneously appears.\n\n')
    save_universe(rooms, npcs_db, npcs, items_db, items,
                  env_db, env, guilds_db)
    return True


def _dismiss(params, mud, players_db: {}, players: {}, rooms: {},
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
        familiar_removed = False
        removals = []
        for (index, details) in npcs_db.items():
            if details['familiarOf'] == players[id]['name']:
                removals.append(index)
                familiar_removed = True
        for index in removals:
            del npcs_db[index]

        removals.clear()
        for (index, details) in npcs.items():
            if details['familiarOf'] == players[id]['name']:
                removals.append(index)
        for index in removals:
            del npcs[index]

        if familiar_removed:
            mud.send_message(id, "Your familiar vanishes.\n\n")
        else:
            mud.send_message(id, "\n\n")


def _conjure(params, mud, players_db: {}, players: {}, rooms: {},
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
        _conjure_npc(params, mud, players_db, players, rooms,
                     npcs_db, npcs, items_db, items, env_db, env,
                     eventDB, event_schedule, id, fights, corpses,
                     blocklist, map_area, character_class_db,
                     spells_db, sentiment_db, guilds_db, clouds, races_db,
                     item_history, markets, cultures_db)
        return

    if params.startswith('room '):
        _conjure_room(params, mud, players_db, players, rooms, npcs_db,
                      npcs, items_db, items, env_db, env, eventDB,
                      event_schedule, id, fights, corpses, blocklist,
                      map_area, character_class_db, spells_db,
                      sentiment_db, guilds_db, clouds, races_db,
                      item_history, markets, cultures_db)
        return

    if params.startswith('npc '):
        _conjure_npc(params, mud, players_db, players, rooms,
                     npcs_db, npcs, items_db, items, env_db, env,
                     eventDB, event_schedule, id, fights, corpses,
                     blocklist, map_area, character_class_db,
                     spells_db, sentiment_db, guilds_db, clouds, races_db,
                     item_history, markets, cultures_db)
        return

    _conjure_item(params, mud, players_db, players, rooms, npcs_db, npcs,
                  items_db, items, env_db, env, eventDB, event_schedule,
                  id, fights, corpses, blocklist, map_area,
                  character_class_db, spells_db, sentiment_db, guilds_db,
                  clouds, races_db, item_history, markets, cultures_db)


def _destroy_item(params, mud, players_db: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                  item_history: {}, markets: {}, cultures_db: {}):
    item_name = params.lower()
    if len(item_name) == 0:
        mud.send_message(id, "Specify the name of an item to destroy.\n\n")
        return False

    # Check if it is in the room
    item_id = -1
    found_item = None
    destroyed_name = ''
    for item, _ in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            if item_name in items_db[items[item]['id']]['name']:
                destroyed_name = items_db[items[item]['id']]['name']
                item_id = items[item]['id']
                found_item = item
                break
    if item_id == -1:
        mud.send_message(id, "It's not here.\n\n")
        return False

    mud.send_message(id, 'It suddenly vanishes.\n\n')
    del items[found_item]
    log("Item destroyed: " + destroyed_name +
        ' in ' + players[id]['room'], 'info')
    save_universe(rooms, npcs_db, npcs, items_db,
                  items, env_db, env, guilds_db)
    return True


def _destroy_npc(params, mud, players_db: {}, players: {}, rooms: {},
                 npcs_db: {}, npcs: {}, items_db: {}, items: {},
                 env_db: {}, env: {}, eventDB: {}, event_schedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 map_area: [], character_class_db: {}, spells_db: {},
                 sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                 item_history: {}, markets: {}, cultures_db: {}):
    npc_name = params.lower().replace('npc ', '').strip().replace('"', '')
    if len(npc_name) == 0:
        mud.send_message(id, "Specify the name of an NPC to destroy.\n\n")
        return False

    # Check if NPC is in the room
    npc_id = -1
    destroyed_name = ''
    for nid, _ in list(npcs.items()):
        if npcs[nid]['room'] == players[id]['room']:
            if npc_name.lower() in npcs[nid]['name'].lower():
                destroyed_name = npcs[nid]['name']
                npc_id = nid
                break

    if npc_id == -1:
        mud.send_message(id, "They're not here.\n\n")
        return False

    mud.send_message(id, 'They suddenly vanish.\n\n')
    del npcs[npc_id]
    del npcs_db[npc_id]
    log("NPC destroyed: " + destroyed_name +
        ' in ' + players[id]['room'], 'info')
    save_universe(rooms, npcs_db, npcs, items_db,
                  items, env_db, env, guilds_db)
    return True


def _destroy_room(params, mud, players_db: {}, players: {}, rooms: {},
                  npcs_db: {}, npcs: {}, items_db: {}, items: {},
                  env_db: {}, env: {}, eventDB: {}, event_schedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  map_area: [], character_class_db: {}, spells_db: {},
                  sentiment_db: {}, guilds_db: {}, clouds: {}, races_db: {},
                  item_history: {}, markets: {}, cultures_db: {}):
    params = params.replace('room ', '')
    room_direction = params.lower().strip()
    possible_directions = (
        'north',
        'south',
        'east',
        'west',
        'up',
        'down',
        'in',
        'out')
    opposite_direction = {
        'north': 'south', 'south': 'north', 'east': 'west',
        'west': 'east', 'up': 'down', 'down': 'up',
        'in': 'out', 'out': 'in'
    }
    if room_direction not in possible_directions:
        mud.send_message(id, 'Specify a room direction.\n\n')
        return False

    # Is there already a room in that direction?
    room_exits = _get_room_exits(mud, rooms, players, id)
    if not room_exits.get(room_direction):
        mud.send_message(id, 'There is no room in that direction.\n\n')
        return False

    room_to_destroy_id = room_exits.get(room_direction)
    room_to_destroy = rooms[room_to_destroy_id]
    room_exits_to_destroy = room_to_destroy['exits']
    for direction, room_id in room_exits_to_destroy.items():
        # Remove the exit from the other room to this one
        other_room = rooms[room_id]
        if other_room['exits'].get(opposite_direction[direction]):
            del other_room['exits'][opposite_direction[direction]]
    del rooms[room_to_destroy_id]

    # update the map area
    for rmid in rooms:
        rooms[rmid]['coords'] = []

    log("Room destroyed: " + room_to_destroy_id, 'info')
    save_universe(rooms, npcs_db, npcs, items_db,
                  items, env_db, env, guilds_db)
    mud.send_message(id, "Room destroyed.\n\n")
    return True


def _destroy(params, mud, players_db: {}, players: {}, rooms: {},
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
        _destroy_room(params, mud, players_db, players, rooms, npcs_db,
                      npcs, items_db, items, env_db, env, eventDB,
                      event_schedule, id, fights, corpses, blocklist,
                      map_area, character_class_db, spells_db,
                      sentiment_db, guilds_db, clouds, races_db,
                      item_history, markets, cultures_db)
    else:
        if params.startswith('npc '):
            _destroy_npc(params, mud, players_db, players, rooms, npcs_db,
                         npcs, items_db, items, env_db, env, eventDB,
                         event_schedule, id, fights, corpses, blocklist,
                         map_area, character_class_db, spells_db,
                         sentiment_db, guilds_db, clouds, races_db,
                         item_history, markets, cultures_db)
        else:
            _destroy_item(params, mud, players_db, players, rooms, npcs_db,
                          npcs, items_db, items, env_db, env, eventDB,
                          event_schedule, id, fights, corpses, blocklist,
                          map_area, character_class_db, spells_db,
                          sentiment_db, guilds_db, clouds, races_db,
                          item_history, markets, cultures_db)


def _item_give(params, mud, players_db: {}, players: {}, rooms: {},
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
    recipient_name = params.split(' to ')[1].lower()
    recipient_id = None
    for pid, player_item in players.items():
        if pid == id:
            continue
        if recipient_name not in player_item['name'].lower():
            continue
        if player_item['room'] != players[id]['room']:
            continue
        recipient_id = pid
    if not recipient_id:
        desc = (
            "You don't see them here"
        )
        mud.send_message(id, random_desc(desc) + '.\n\n')
        return
    give_str = params.split(' to ')[0].lower()
    money_str = None
    denomination = None
    if ' copper piece' in give_str:
        money_str = give_str.split(' copper piece')[0]
        denomination = 'cp'
    elif ' silver piece' in give_str:
        money_str = give_str.split(' silver piece')[0]
        denomination = 'sp'
    elif ' electrum piece' in give_str:
        money_str = give_str.split(' electrum piece')[0]
        denomination = 'ep'
    elif ' gold piece' in give_str:
        money_str = give_str.split(' gold piece')[0]
        denomination = 'gp'
    elif ' platium piece' in give_str:
        money_str = give_str.split(' platinum piece')[0]
        denomination = 'pp'
    elif give_str.endswith('cp'):
        money_str = give_str.split('cp')[0]
        denomination = 'cp'
    elif give_str.endswith('sp'):
        money_str = give_str.split('sp')[0]
        denomination = 'sp'
    elif give_str.endswith('ep'):
        money_str = give_str.split('ep')[0]
        denomination = 'ep'
    elif give_str.endswith('gp'):
        money_str = give_str.split('gp')[0]
        denomination = 'gp'
    elif give_str.endswith('pp'):
        money_str = give_str.split('pp')[0]
        denomination = 'pp'

    if denomination:
        money_str = money_str.strip()
        qty = 0
        if money_str.isdigit():
            qty = int(money_str)
        else:
            qty_dict = {
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
            for qty_str, value in qty_dict.items():
                if qty_str in money_str:
                    qty = value
                    break
        if qty > 0:
            cost = str(qty) + denomination
            if money_purchase(id, players, cost):
                players[recipient_id][denomination] += qty
                desc = (
                    "You give " + cost + " to " + players[recipient_id]['name']
                )
                mud.send_message(id, random_desc(desc) + '.\n\n')
                desc = (
                    players[id]['name'] + " gives you " + cost
                )
                mud.send_message(recipient_id,
                                 random_desc(desc) + '.\n\n')
                return
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


def _drop(params, mud, players_db: {}, players: {}, rooms: {},
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

    item_in_db = False
    item_in_inventory = False
    item_id = None
    target = str(params).lower()
    if target.startswith('the '):
        target = params.replace('the ', '')

    # Check if item is in player's inventory
    for item in players[id]['inv']:
        for iid, _ in list(items_db.items()):
            if str(iid) == str(item):
                if items_db[iid]['name'].lower() == target:
                    item_id = iid
                    item_in_inventory = True
                    item_in_db = True
                    break
        if item_in_inventory:
            break

    if not item_in_inventory:
        # Try a fuzzy match
        for item in players[id]['inv']:
            for iid, _ in list(items_db.items()):
                if str(iid) == str(item):
                    if target in items_db[iid]['name'].lower():
                        item_id = iid
                        item_in_inventory = True
                        item_in_db = True
                        break

    if item_in_db and item_in_inventory:
        if player_is_trapped(id, players, rooms):
            desc = (
                "You're trapped",
                "The trap restricts your ability to drop anything",
                "The trap restricts your movement"
            )
            mud.send_message(id, random_desc(desc) + '.\n\n')
            return

        inventory_copy = deepcopy(players[id]['inv'])
        for i in inventory_copy:
            if int(i) == item_id:
                # Remove first matching item from inventory
                players[id]['inv'].remove(i)
                update_player_attributes(id, players, items_db, item_id, -1)
                break

        players[id]['wei'] = player_inventory_weight(id, players, items_db)

        # remove from clothing
        _remove_item_from_clothing(players, id, item_id)

        # Create item on the floor in the same room as the player
        items[get_free_key(items)] = {
            'id': item_id,
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
                         items_db[item_id]['article'] +
                         ' ' +
                         items_db[item_id]['name'] +
                         ' on the floor.\n\n')

    else:
        mud.send_message(id, 'You don`t have that!\n\n')


def _open_item_unlock(items: {}, items_db: {}, id, iid,
                      players: {}, mud) -> bool:
    """Unlock an item
    """
    unlock_item_id = items_db[items[iid]['id']]['lockedWithItem']
    if not str(unlock_item_id).isdigit():
        return True
    if unlock_item_id <= 0:
        return True
    key_found = False
    for i in list(players[id]['inv']):
        if int(i) == unlock_item_id:
            key_found = True
            break
    if key_found:
        mud.send_message(
            id, 'You use ' +
            items_db[unlock_item_id]['article'] +
            ' ' + items_db[unlock_item_id]['name'])
    else:
        if len(items_db[unlock_item_id]['open_failed_description']) > 0:
            mud.send_message(
                id, items_db[unlock_item_id]['open_failed_description'] +
                ".\n\n")
        else:
            if items_db[unlock_item_id]['state'].startswith('lever '):
                mud.send_message(id, "It's operated with a lever.\n\n")
            else:
                if randint(0, 1) == 1:
                    mud.send_message(
                        id, "You don't have " +
                        items_db[unlock_item_id]['article'] +
                        " " + items_db[unlock_item_id]['name'] +
                        ".\n\n")
                else:
                    mud.send_message(
                        id, "Looks like you need " +
                        items_db[unlock_item_id]['article'] +
                        " " + items_db[unlock_item_id]['name'] +
                        " for this.\n\n")
        return False
    return True


def _describe_container_contents(mud, id, items_db: {}, item_id: {},
                                 return_msg) -> None:
    """Describe a container contents
    """
    if not items_db[item_id]['state'].startswith('container open'):
        if return_msg:
            return ''
        return
    contains_list = items_db[item_id]['contains']
    no_of_items = len(contains_list)
    container_msg = '<f15>You see '

    if no_of_items == 0:
        if 'open always' not in items_db[item_id]['state']:
            mud.send_message(id, container_msg + 'nothing.\n')
        return ''

    item_ctr = 0
    for contents_id in contains_list:
        if item_ctr > 0:
            if item_ctr < no_of_items - 1:
                container_msg += ', '
            else:
                container_msg += ' and '

        container_msg += \
            items_db[int(contents_id)]['article'] + \
            ' <b234><f220>' + \
            items_db[int(contents_id)]['name'] + '<r>'
        item_ctr += 1

    container_msg = container_msg + '.\n'
    if return_msg:
        container_msg = '\n' + container_msg
        return container_msg
    mud.send_message_wrap(id, '<f220>', container_msg + '\n')


def _open_item_container(params, mud, players_db: {}, players: {}, rooms: {},
                         npcs_db: {}, npcs: {}, items_db: {}, items: {},
                         env_db: {}, env: {}, eventDB: {}, event_schedule,
                         id: int, fights: {}, corpses: {}, target,
                         items_in_world_copy: {}, iid):
    """Opens a container
    """
    if not _open_item_unlock(items, items_db, id, iid, players, mud):
        return

    item_id = items[iid]['id']
    if items_db[item_id]['state'].startswith('container open'):
        mud.send_message(id, "It's already open\n\n")
        return

    items_db[item_id]['state'] = \
        items_db[item_id]['state'].replace('closed', 'open')
    items_db[item_id]['short_description'] = \
        items_db[item_id]['short_description'].replace('closed', 'open')
    items_db[item_id]['long_description'] = \
        items_db[item_id]['long_description'].replace('closed', 'open')
    items_db[item_id]['long_description'] = \
        items_db[item_id]['long_description'].replace('shut', 'open')

    if len(items_db[item_id]['open_description']) > 0:
        mud.send_message(id, items_db[item_id]['open_description'] + '\n\n')
    else:
        item_article = items_db[item_id]['article']
        if item_article == 'a':
            item_article = 'the'
        mud.send_message(id, 'You open ' + item_article +
                         ' ' + items_db[item_id]['name'] + '.\n\n')
    _describe_container_contents(mud, id, items_db, item_id, False)


def _lever_up(params, mud, players_db: {}, players: {}, rooms: {},
              npcs_db: {}, npcs: {}, items_db: {}, items: {},
              env_db: {}, env: {}, eventDB: {}, event_schedule,
              id: int, fights: {}, corpses: {}, target,
              items_in_world_copy: {}, iid):
    """Pull a lever up
    """
    item_id = items[iid]['id']
    linked_item_id = int(items_db[item_id]['linkedItem'])
    room_id = items_db[item_id]['exit']

    items_db[item_id]['state'] = 'lever up'
    items_db[item_id]['short_description'] = \
        items_db[item_id]['short_description'].replace('down', 'up')
    items_db[item_id]['long_description'] = \
        items_db[item_id]['long_description'].replace('down', 'up')
    if '|' in items_db[item_id]['exitName']:
        exit_name = items_db[item_id]['exitName'].split('|')

        if linked_item_id > 0:
            desc = items_db[linked_item_id]['short_description']
            items_db[linked_item_id]['short_description'] = \
                desc.replace('open', 'closed')
            desc = items_db[linked_item_id]['long_description']
            items_db[linked_item_id]['long_description'] = \
                desc.replace('open', 'closed')
            items_db[linked_item_id]['state'] = 'closed'
            linked_item_id2 = int(items_db[linked_item_id]['linkedItem'])
            if linked_item_id2 > 0:
                desc = items_db[linked_item_id2]['short_description']
                items_db[linked_item_id2]['short_description'] = \
                    desc.replace('open', 'closed')
                desc = items_db[linked_item_id2]['long_description']
                items_db[linked_item_id2]['long_description'] = \
                    desc.replace('open', 'closed')
                items_db[linked_item_id2]['state'] = 'closed'

        if len(room_id) > 0:
            rmid = players[id]['room']
            if exit_name[0] in rooms[rmid]['exits']:
                del rooms[rmid]['exits'][exit_name[0]]

            rmid = room_id
            if exit_name[1] in rooms[rmid]['exits']:
                del rooms[rmid]['exits'][exit_name[1]]

    if len(items_db[item_id]['close_description']) > 0:
        mud.send_message_wrap(id, '<f220>',
                              items_db[item_id]['close_description'] + '\n\n')
    else:
        mud.send_message(
            id, 'You push ' +
            items_db[item_id]['article'] +
            ' ' + items_db[item_id]['name'] +
            '\n\n')


def _lever_down(params, mud, players_db: {}, players: {}, rooms: {},
                npcs_db: {}, npcs: {}, items_db: {}, items: {},
                env_db: {}, env: {}, eventDB: {}, event_schedule,
                id: int, fights: {}, corpses: {}, target,
                items_in_world_copy: {}, iid):
    if not _open_item_unlock(items, items_db, id, iid, players, mud):
        return

    item_id = items[iid]['id']
    linked_item_id = int(items_db[item_id]['linkedItem'])
    room_id = items_db[item_id]['exit']

    items_db[item_id]['state'] = 'lever down'
    items_db[item_id]['short_description'] = \
        items_db[item_id]['short_description'].replace('up', 'down')
    items_db[item_id]['long_description'] = \
        items_db[item_id]['long_description'].replace('up', 'down')
    if '|' in items_db[item_id]['exitName']:
        exit_name = items_db[item_id]['exitName'].split('|')

        if linked_item_id > 0:
            desc = items_db[linked_item_id]['short_description']
            items_db[linked_item_id]['short_description'] = \
                desc.replace('closed', 'open')
            desc = items_db[linked_item_id]['long_description']
            items_db[linked_item_id]['long_description'] = \
                desc.replace('closed', 'open')
            items_db[linked_item_id]['state'] = 'open'
            linked_item_id2 = int(items_db[linked_item_id]['linkedItem'])
            if linked_item_id2 > 0:
                desc = items_db[linked_item_id2]['short_description']
                items_db[linked_item_id2]['short_description'] = \
                    desc.replace('closed', 'open')
                desc = items_db[linked_item_id2]['long_description']
                items_db[linked_item_id2]['long_description'] = \
                    desc.replace('closed', 'open')
                items_db[linked_item_id2]['state'] = 'open'

        if len(room_id) > 0:
            rmid = players[id]['room']
            if exit_name[0] in rooms[rmid]['exits']:
                del rooms[rmid]['exits'][exit_name[0]]
            rooms[rmid]['exits'][exit_name[0]] = room_id

            rmid = room_id
            if exit_name[1] in rooms[rmid]['exits']:
                del rooms[rmid]['exits'][exit_name[1]]
            rooms[rmid]['exits'][exit_name[1]] = players[id]['room']

    if len(items_db[item_id]['open_description']) > 0:
        mud.send_message_wrap(id, '<f220>',
                              items_db[item_id]['open_description'] +
                              '\n\n')
    else:
        mud.send_message(
            id, 'You pull ' +
            items_db[item_id]['article'] +
            ' ' + items_db[item_id]['name'] +
            '\n\n')


def _open_item_door(params, mud, players_db: {}, players: {}, rooms: {},
                    npcs_db: {}, npcs: {}, items_db: {}, items: {},
                    env_db: {}, env: {}, eventDB: {}, event_schedule,
                    id: int, fights: {}, corpses: {}, target,
                    items_in_world_copy: {}, iid):
    if not _open_item_unlock(items, items_db, id, iid, players, mud):
        return

    item_id = items[iid]['id']
    linked_item_id = int(items_db[item_id]['linkedItem'])
    room_id = items_db[item_id]['exit']
    if '|' in items_db[item_id]['exitName']:
        exit_name = items_db[item_id]['exitName'].split('|')

        items_db[item_id]['state'] = 'open'
        desc = items_db[item_id]['short_description']
        items_db[item_id]['short_description'] = \
            desc.replace('closed', 'open').replace('drawn up', 'drawn down')
        desc = items_db[item_id]['long_description']
        items_db[item_id]['long_description'] = \
            desc.replace('closed', 'open').replace('drawn up', 'drawn down')

        if linked_item_id > 0:
            desc = items_db[linked_item_id]['short_description']
            items_db[linked_item_id]['short_description'] = \
                desc.replace('closed',
                             'open').replace('drawn up', 'drawn down')
            desc = items_db[linked_item_id]['long_description']
            items_db[linked_item_id]['long_description'] = \
                desc.replace('closed',
                             'open').replace('drawn up', 'drawn down')
            items_db[linked_item_id]['state'] = 'open'

        if len(room_id) > 0:
            rmid = players[id]['room']
            if exit_name[0] in rooms[rmid]['exits']:
                del rooms[rmid]['exits'][exit_name[0]]
            rooms[rmid]['exits'][exit_name[0]] = room_id

            rmid = room_id
            if exit_name[1] in rooms[rmid]['exits']:
                del rooms[rmid]['exits'][exit_name[1]]
            rooms[rmid]['exits'][exit_name[1]] = players[id]['room']

    if len(items_db[item_id]['open_description']) > 0:
        mud.send_message(id, items_db[item_id]['open_description'] + '\n\n')
    else:
        mud.send_message(
            id, 'You open ' +
            items_db[item_id]['article'] +
            ' ' + items_db[item_id]['name'] +
            '\n\n')


def _open_item(params, mud, players_db: {}, players: {}, rooms: {},
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

    items_in_world_copy = deepcopy(items)
    for (iid, pl) in list(items_in_world_copy.items()):
        if items_in_world_copy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if items_db[items[iid]['id']]['state'] == 'closed':
                    _open_item_door(params, mud, players_db, players, rooms,
                                    npcs_db, npcs, items_db, items,
                                    env_db, env,
                                    eventDB, event_schedule, id, fights,
                                    corpses, target, items_in_world_copy,
                                    iid)
                    return
                idx = items[iid]['id']
                if items_db[idx]['state'].startswith('container closed'):
                    _open_item_container(params, mud, players_db, players,
                                         rooms, npcs_db, npcs, items_db,
                                         items, env_db, env, eventDB,
                                         event_schedule, id, fights, corpses,
                                         target, items_in_world_copy, iid)
                    return
    mud.send_message(id, "You can't open it.\n\n")


def _pull_lever(params, mud, players_db: {}, players: {}, rooms: {},
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

    items_in_world_copy = deepcopy(items)
    for iid, _ in list(items_in_world_copy.items()):
        if items_in_world_copy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if items_db[items[iid]['id']]['state'] == 'lever up':
                    _lever_down(params, mud, players_db, players, rooms,
                                npcs_db, npcs, items_db, items, env_db,
                                env, eventDB, event_schedule, id, fights,
                                corpses, target, items_in_world_copy, iid)
                    return
                mud.send_message(id, 'Nothing happens.\n\n')
                return
    mud.send_message(id, "There's nothing to pull.\n\n")


def _push_lever(params, mud, players_db: {}, players: {}, rooms: {},
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

    items_in_world_copy = deepcopy(items)
    for iid, _ in list(items_in_world_copy.items()):
        if items_in_world_copy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if not items_db[items[iid]['id']]['state']:
                    _heave(params, mud, players_db, players, rooms,
                           npcs_db, npcs, items_db, items, env_db, env,
                           eventDB, event_schedule, id, fights,
                           corpses, blocklist, map_area, character_class_db,
                           spells_db, sentiment_db, guilds_db, clouds,
                           races_db, item_history, markets, cultures_db)
                    return
                if items_db[items[iid]['id']]['state'] == 'lever down':
                    _lever_up(params, mud, players_db, players, rooms, npcs_db,
                              npcs, items_db, items, env_db, env, eventDB,
                              event_schedule, id, fights, corpses, target,
                              items_in_world_copy, iid)
                    return
    mud.send_message(id, 'Nothing happens.\n\n')


def _wind_lever(params, mud, players_db: {}, players: {}, rooms: {},
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

    items_in_world_copy = deepcopy(items)
    for iid, _ in list(items_in_world_copy.items()):
        if items_in_world_copy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if items_db[items[iid]['id']]['state'] == 'lever up':
                    _lever_down(params, mud, players_db, players, rooms,
                                npcs_db, npcs, items_db, items, env_db,
                                env, eventDB, event_schedule, id,
                                fights, corpses, target,
                                items_in_world_copy, iid)
                    return
                mud.send_message(id, "It's wound all the way.\n\n")
                return
    mud.send_message(id, "There's nothing to wind.\n\n")


def _unwind_lever(params, mud, players_db: {}, players: {}, rooms: {},
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

    items_in_world_copy = deepcopy(items)
    for iid, _ in list(items_in_world_copy.items()):
        if items_in_world_copy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if items_db[items[iid]['id']]['state'] == 'lever down':
                    _lever_up(params, mud, players_db, players, rooms,
                              npcs_db, npcs, items_db, items, env_db, env,
                              eventDB, event_schedule, id, fights,
                              corpses, target, items_in_world_copy, iid)
                    return
                mud.send_message(id, "It's unwound all the way.\n\n")
                return
    mud.send_message(id, "There's nothing to unwind.\n\n")


def _close_item_container(params, mud, players_db: {}, players: {}, rooms: {},
                          npcs_db: {}, npcs: {}, items_db: {}, items: {},
                          env_db: {}, env: {}, eventDB: {}, event_schedule,
                          id: int, fights: {}, corpses: {}, target,
                          items_in_world_copy: {}, iid):
    item_id = items[iid]['id']
    if items_db[item_id]['state'].startswith('container closed'):
        mud.send_message(id, "It's already closed\n\n")
        return

    if items_db[item_id]['state'].startswith('container open '):
        mud.send_message(id, "That's not possible.\n\n")
        return

    items_db[item_id]['state'] = \
        items_db[item_id]['state'].replace('open', 'closed')
    items_db[item_id]['short_description'] = \
        items_db[item_id]['short_description'].replace('open', 'closed')
    items_db[item_id]['long_description'] = \
        items_db[item_id]['long_description'].replace('open', 'closed')

    if len(items_db[item_id]['close_description']) > 0:
        mud.send_message(id, items_db[item_id]['close_description'] + '\n\n')
    else:
        item_article = items_db[item_id]['article']
        if item_article == 'a':
            item_article = 'the'
        mud.send_message(id, 'You close ' + item_article +
                         ' ' + items_db[item_id]['name'] + '.\n\n')


def _close_item_door(params, mud, players_db: {}, players: {}, rooms: {},
                     npcs_db: {}, npcs: {}, items_db: {}, items: {},
                     env_db: {}, env: {}, eventDB: {}, event_schedule,
                     id: int, fights: {}, corpses: {}, target,
                     items_in_world_copy: {}, iid):
    item_id = items[iid]['id']
    linked_item_id = int(items_db[item_id]['linkedItem'])
    room_id = items_db[item_id]['exit']
    if '|' not in items_db[item_id]['exitName']:
        return

    exit_name = items_db[item_id]['exitName'].split('|')

    items_db[item_id]['state'] = 'closed'
    items_db[item_id]['short_description'] = \
        items_db[item_id]['short_description'].replace('open', 'closed')
    items_db[item_id]['long_description'] = \
        items_db[item_id]['long_description'].replace('open', 'closed')

    if linked_item_id > 0:
        desc = items_db[linked_item_id]['short_description']
        items_db[linked_item_id]['short_description'] = \
            desc.replace('open', 'closed').replace('drawn down', 'drawn up')
        desc = items_db[linked_item_id]['long_description']
        items_db[linked_item_id]['long_description'] = \
            desc.replace('open', 'closed').replace('drawn down', 'drawn up')
        items_db[linked_item_id]['state'] = 'closed'

    if len(room_id) > 0:
        rmid = players[id]['room']
        if exit_name[0] in rooms[rmid]['exits']:
            del rooms[rmid]['exits'][exit_name[0]]

        rmid = room_id
        if exit_name[1] in rooms[rmid]['exits']:
            del rooms[rmid]['exits'][exit_name[1]]

    if len(items_db[item_id]['close_description']) > 0:
        mud.send_message(id, items_db[item_id]['close_description'] + '\n\n')
    else:
        mud.send_message(id, 'You close ' +
                         items_db[item_id]['article'] + ' ' +
                         items_db[item_id]['name'] + '\n\n')


def _close_item(params, mud, players_db: {}, players: {}, rooms: {},
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

    items_in_world_copy = deepcopy(items)
    for iid, _ in list(items_in_world_copy.items()):
        if items_in_world_copy[iid]['room'] == players[id]['room']:
            if target in items_db[items[iid]['id']]['name'].lower():
                if items_db[items[iid]['id']]['state'] == 'open':
                    _close_item_door(params, mud, players_db, players,
                                     rooms, npcs_db, npcs, items_db,
                                     items, env_db, env, eventDB,
                                     event_schedule, id, fights,
                                     corpses, target, items_in_world_copy,
                                     iid)
                    return
                idx = items[iid]['id']
                if items_db[idx]['state'].startswith('container open'):
                    _close_item_container(params, mud, players_db, players,
                                          rooms, npcs_db, npcs, items_db,
                                          items, env_db, env, eventDB,
                                          event_schedule, id, fights,
                                          corpses, target, items_in_world_copy,
                                          iid)
                    return
    mud.send_message(id, "You can't close it.\n\n")


def _put_item(params, mud, players_db: {}, players: {}, rooms: {},
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

    item_id = 0
    item_name = target[0]
    container_name = target[1]

    if len(list(players[id]['inv'])) > 0:
        item_name_lower = item_name.lower()
        for i in list(players[id]['inv']):
            if items_db[int(i)]['name'].lower() == item_name_lower:
                item_id = int(i)
                item_name = items_db[int(i)]['name']

        if item_id == 0:
            for i in list(players[id]['inv']):
                if item_name_lower in items_db[int(i)]['name'].lower():
                    item_id = int(i)
                    item_name = items_db[int(i)]['name']

    if item_id == 0:
        mud.send_message(id, "You don't have " + item_name + ".\n\n")
        return

    items_in_world_copy = deepcopy(items)

    for iid, _ in list(items_in_world_copy.items()):
        if items_in_world_copy[iid]['room'] == players[id]['room']:
            iname = items_db[items[iid]['id']]['name'].lower()
            if container_name.lower() in iname:
                idx = items[iid]['id']
                if items_db[idx]['state'].startswith('container open'):
                    if ' noput' not in items_db[idx]['state']:
                        max_items_in_container = items_db[idx]['useTimes']
                        len_cont = len(items_db[idx]['contains'])
                        if max_items_in_container == 0 or \
                           len_cont < max_items_in_container:
                            players[id]['inv'].remove(str(item_id))
                            _remove_item_from_clothing(players, id, item_id)
                            items_db[idx]['contains'].append(str(item_id))
                            idx = items[iid]['id']
                            mud.send_message(id, 'You put ' +
                                             items_db[item_id]['article'] +
                                             ' ' + items_db[item_id]['name'] +
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

                idx = items[iid]['id']
                if items_db[idx]['state'].startswith('container closed'):
                    if 'on' in inon:
                        mud.send_message(id, "You can't.\n\n")
                    else:
                        mud.send_message(id, "It's closed.\n\n")
                    return
                if 'on' in inon:
                    mud.send_message(
                        id, "You can't put anything on that.\n\n")
                else:
                    mud.send_message(
                        id, "It can't contain anything.\n\n")
                return

    mud.send_message(id, "You don't see " + container_name + ".\n\n")


def _get_random_room_in_regions(rooms: {}, regions_list: []) -> str:
    """Returns a random room within the given regions
    """
    possible_rooms = []
    for room_id, item in rooms.items():
        if item.get('region'):
            if item['region'] in regions_list:
                possible_rooms.append(room_id)
    if not possible_rooms:
        return None
    return random.choice(possible_rooms)


def _take(params, mud, players_db: {}, players: {}, rooms: {},
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
            _stand(params, mud, players_db, players, rooms, npcs_db, npcs,
                   items_db, items, env_db, env, eventDB, event_schedule,
                   id, fights, corpses, blocklist, map_area,
                   character_class_db,
                   spells_db, sentiment_db, guilds_db, clouds, races_db,
                   item_history, markets, cultures_db)
            return

        # get into, get through
        if params.startswith('into') or params.startswith('through'):
            _climb(params, mud, players_db, players, rooms, npcs_db, npcs,
                   items_db, items, env_db, env, eventDB, event_schedule,
                   id, fights, corpses, blocklist, map_area,
                   character_class_db,
                   spells_db, sentiment_db, guilds_db, clouds, races_db,
                   item_history, markets, cultures_db)
            return

    if len(str(params)) < 3:
        return

    params_str = str(params)
    if _item_in_inventory(players, id, params_str, items_db):
        mud.send_message(id, 'You are already carring ' + str(params) + '\n\n')
        return

    if player_is_prone(id, players):
        mud.send_message(id, random_desc('You stand up<r>\n\n'))
        set_player_prone(id, players, False)
        return

    item_in_db = False
    item_name = None
    item_picked_up = False
    item_index = None
    target = str(params).lower()
    if target.startswith('the '):
        target = params.replace('the ', '')

    for iid, _ in list(items.items()):
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
            item_name = items_db[iid2]['name']
            item_in_db = True
            item_index = iid2
        break

    items_in_world_copy = deepcopy(items)

    if not item_in_db:
        # Try fuzzy match of the item name
        for iid, _ in list(items_in_world_copy.items()):
            if items_in_world_copy[iid]['room'] != players[id]['room']:
                continue
            item_index = items_in_world_copy[iid]['id']
            if target not in items_db[item_index]['name'].lower():
                continue
            if int(items_db[item_index]['weight']) == 0:
                if items_db[item_index].get('takeFail'):
                    desc = random_desc(items_db[item_index]['takeFail'])
                    mud.send_message_wrap(id, '<f220>', desc + "\n\n")
                else:
                    mud.send_message(id, "You can't pick that up.\n\n")
                return

            item_name = items_db[item_index]['name']
            if _item_in_inventory(players, id, item_name, items_db):
                mud.send_message(
                    id, 'You are already carring ' + item_name + '\n\n')
                return
            if _item_is_visible(id, players, item_index, items_db):
                # ID of the item to be picked up
                item_in_db = True
            break

    if item_in_db and item_index:
        for iid, _ in list(items_in_world_copy.items()):
            # item in same room as player
            if items_in_world_copy[iid]['room'] != players[id]['room']:
                continue
            item_index = items_in_world_copy[iid]['id']
            # item has the expected name
            if items_db[item_index]['name'] != item_name:
                continue
            # player can move
            if players[id]['canGo'] != 0:
                # is the item too heavy?
                players[id]['wei'] = \
                    player_inventory_weight(id, players, items_db)

                if players[id]['wei'] + items_db[item_index]['weight'] > \
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
                players[id]['inv'].append(str(item_index))
                # update the weight of the player
                players[id]['wei'] = \
                    player_inventory_weight(id, players, items_db)
                update_player_attributes(id, players, items_db, item_index, 1)
                # remove the item from the dict
                if not items_db[item_index].get('respawnInRegion'):
                    del items[iid]
                else:
                    regions_list = items_db[item_index]['respawnInRegion']
                    new_room_id = \
                        _get_random_room_in_regions(rooms, regions_list)
                    if not new_room_id:
                        del items[iid]
                    else:
                        items[iid]['room'] = new_room_id
                item_picked_up = True
                break
            mud.send_message(id, 'You try to pick up ' + item_name +
                             " but find that your arms won't move.\n\n")
            return

    if item_picked_up:
        mud.send_message(id, 'You pick up and place ' +
                         item_name + ' in your inventory.\n\n')
        item_picked_up = False
    else:
        # are there any open containers with this item?
        if ' from ' in target:
            target2 = target.split(' from ')
            target = target2[0]

        for iid, _ in list(items_in_world_copy.items()):
            # is the item in the same room as the player?
            if items_in_world_copy[iid]['room'] != players[id]['room']:
                continue
            item_index = items_in_world_copy[iid]['id']
            # is this an open container
            if not items_db[item_index]['state'].startswith('container open'):
                continue
            # go through the items within the container
            for container_item_id in items_db[item_index]['contains']:
                # does the name match?
                item_name = items_db[int(container_item_id)]['name']
                if target not in item_name.lower():
                    continue
                # can the item be taken?
                if items_db[int(container_item_id)]['weight'] == 0:
                    if items_db[int(container_item_id)].get('takeFail'):
                        idx = int(container_item_id)
                        desc = \
                            random_desc(items_db[idx]['takeFail'])
                        mud.send_message_wrap(id, '<f220>', desc + "\n\n")
                    else:
                        mud.send_message(id, "You can't pick that up.\n\n")
                    return
                # can the player move?
                if players[id]['canGo'] != 0:
                    # is the item too heavy?
                    carrying_weight = \
                        player_inventory_weight(id, players, items_db)
                    idx = int(container_item_id)
                    if carrying_weight + items_db[idx]['weight'] > \
                       _get_max_weight(id, players):
                        mud.send_message(id,
                                         "You can't carry any more.\n\n")
                        return

                    # add the item to the player's inventory
                    players[id]['inv'].append(container_item_id)
                    # remove the item from the container
                    items_db[item_index]['contains'].remove(container_item_id)
                    idx = int(container_item_id)
                    mud.send_message(id, 'You take ' +
                                     items_db[idx]['article'] +
                                     ' ' +
                                     items_db[idx]['name'] +
                                     ' from ' +
                                     items_db[item_index]['article'] +
                                     ' ' +
                                     items_db[item_index]['name'] +
                                     '.\n\n')
                else:
                    idx = int(container_item_id)
                    mud.send_message(id, 'You try to pick up ' +
                                     items_db[idx]['article'] +
                                     ' ' +
                                     items_db[idx]['name'] +
                                     " but find that your arms won't " +
                                     "move.\n\n")
                return

        mud.send_message(id, 'You cannot see ' + target + ' anywhere.\n\n')
        item_picked_up = False


def run_command(command, params, mud, players_db: {}, players: {}, rooms: {},
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
        "throw": _begin_throw_attack,
        "chuck": _begin_throw_attack,
        "hurl": _begin_throw_attack,
        "attack": _begin_attack,
        "shoot": _begin_attack,
        "take": _take,
        "get": _take,
        "put": _put_item,
        "give": _item_give,
        "gift": _item_give,
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
        "describe": _describe_thing,
        "desc": _describe_thing,
        "description": _describe_thing,
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
        "spells": _spells_list,
        "dismiss": _dismiss,
        "clear": _clear_spells,
        "spellbook": _spells_list,
        "affinity": _player_affinity,
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
        "sell": _item_sell,
        "trade": _item_sell,
        "fish": _start_fishing
    }

    try:
        switcher[command](params, mud, players_db, players, rooms, npcs_db,
                          npcs, items_db, items, env_db, env, eventDB,
                          event_schedule, id, fights, corpses, blocklist,
                          map_area, character_class_db, spells_db,
                          sentiment_db, guilds_db, clouds, races_db,
                          item_history, markets, cultures_db)
    except Exception as ex:
        switcher["sendCommandError"](str(ex),
                                     mud, players_db, players, rooms,
                                     npcs_db, npcs, items_db, items,
                                     env_db, env, eventDB, event_schedule,
                                     id, fights, corpses, blocklist,
                                     map_area, character_class_db, spells_db,
                                     sentiment_db, guilds_db, clouds, races_db,
                                     item_history, markets, cultures_db)
