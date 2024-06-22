__filename__ = "npcs.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "NPCs"

import os
import datetime
from suntime import Sun
from functions import add_to_scheduler
from functions import message_to_room_players
from functions import log
from functions import player_inventory_weight
from functions import update_player_attributes
from functions import increase_affinity_between_players
from functions import decrease_affinity_between_players
from functions import get_sentiment
from functions import random_desc
from functions import deepcopy
from functions import parse_cost
from random import randint
# from copy import deepcopy
from familiar import get_familiar_modes
from familiar import familiar_default_mode
from familiar import familiar_scout
from familiar import familiar_hide
from familiar import familiar_sight
from environment import get_rain_at_coords
from environment import get_room_culture

import time


def corpse_exists(corpses: {}, room: str, name: str) -> bool:
    """Returns true if a corpse with the given name exists in the given room
    """
    corpses_copy = deepcopy(corpses)
    for cor, _ in corpses_copy.items():
        if corpses_copy[cor]['room'] == room:
            if corpses_copy[cor]['name'] == name:
                return True
    return False


def npcs_rest(npcs: {}) -> None:
    """Rest restores hit points of NPCs
    """
    for plyr in npcs:
        this_npc = npcs[plyr]
        if this_npc['hp'] < this_npc['hpMax'] + this_npc['tempHitPoints']:
            if randint(0, 100) > 97:
                this_npc['hp'] += 1
        else:
            this_npc['hp'] = this_npc['hpMax'] + this_npc['tempHitPoints']
            this_npc['restRequired'] = 0


def _get_leader_room_index(npcs: {}, players: {}, mud,
                           now, nid: int, move_type: str) -> str:
    """An NPC follows another NPC or player
    This returns the index of the room where the leader is located
    """
    if move_type.startswith('leader:'):
        leader_name = move_type.split(':')[1]
        if len(leader_name) > 0:
            # is the leader an NPC
            for lid, _ in list(npcs.items()):
                leader_npc = npcs[lid]
                if leader_npc['name'] == leader_name:
                    if leader_npc['room'] != npcs[nid]['room']:
                        # follower NPCs are in the same guild
                        npcs[nid]['guild'] = leader_npc['guild']
                        return leader_npc['room']
            # is the leader a player
            for pid, _ in list(players.items()):
                if players[pid]['name'] == leader_name:
                    if players[pid]['room'] != npcs[nid]['room']:
                        npcs[nid]['guild'] = players[pid]['guild']
                        return players[pid]['room']
    return ''


def get_solar():
    return Sun(52.414, 4.081)


def _entity_is_active(id, players: {}, rooms: {},
                      move_times: [], map_area: [], clouds: {}) -> bool:
    if len(move_times) == 0:
        return True

    # These variables are used for matching a number of days
    # as separate time ranges, eg X or Y or Z
    matching_days = False
    days_are_matched = False

    for time_range in move_times:
        if len(time_range) >= 2:
            time_range_type = time_range[0].lower()
            if time_range_type == 'day' or \
               time_range_type == 'weekday' or \
               time_range_type == 'dayofweek' or \
               time_range_type == 'dow':
                curr_day_of_week = datetime.datetime.today().weekday()
                dow_matched = False
                for dow in range(1, len(time_range)):
                    day_of_week = time_range[dow].lower()
                    if day_of_week.startswith('m') and curr_day_of_week == 0:
                        dow_matched = True
                    if day_of_week.startswith('tu') and curr_day_of_week == 1:
                        dow_matched = True
                    if day_of_week.startswith('w') and curr_day_of_week == 2:
                        dow_matched = True
                    if day_of_week.startswith('th') and curr_day_of_week == 3:
                        dow_matched = True
                    if day_of_week.startswith('f') and curr_day_of_week == 4:
                        dow_matched = True
                    if day_of_week.startswith('sa') and curr_day_of_week == 5:
                        dow_matched = True
                    if day_of_week.startswith('su') and curr_day_of_week == 6:
                        dow_matched = True
                if not dow_matched:
                    return False
                continue
            elif time_range_type == 'season':
                curr_month_number = \
                    int(datetime.datetime.today().strftime("%m"))
                season_matched = False
                for season_index in range(1, len(time_range)):
                    season_name = time_range[season_index].lower()
                    if season_name == 'spring':
                        if curr_month_number > 1 and curr_month_number <= 4:
                            season_matched = True
                    elif season_name == 'summer':
                        if curr_month_number > 4 and curr_month_number <= 9:
                            season_matched = True
                    elif season_name == 'autumn':
                        if curr_month_number > 9 and curr_month_number <= 10:
                            season_matched = True
                    elif season_name == 'winter':
                        if curr_month_number > 10 or curr_month_number <= 1:
                            season_matched = True
                if not season_matched:
                    return False
                continue

        if len(time_range) != 3:
            continue
        time_range_type = time_range[0].lower()
        time_range_start = time_range[1]
        time_range_end = time_range[2]

        # sunrise
        if time_range_type == 'sunrise' or \
           time_range_type == 'dawn':
            curr_time = datetime.datetime.today()
            curr_hour = curr_time.hour
            sun = get_solar()
            sun_rise_time = sun.get_local_sunrise_time(curr_time).hour
            if 'true' in time_range_start.lower() or \
               'y' in time_range_start.lower():
                if not (curr_hour >= sun_rise_time - 1 and
                        curr_hour <= sun_rise_time):
                    return False
            else:
                if not (curr_hour < sun_rise_time - 1 or
                        curr_hour > sun_rise_time):
                    return False

        if time_range_type == 'sunset' or \
           time_range_type == 'dusk':
            curr_time = datetime.datetime.today()
            curr_hour = curr_time.hour
            sun = get_solar()
            sun_set_time = sun.get_local_sunset_time(curr_time).hour
            if 'true' in time_range_start.lower() or \
               'y' in time_range_start.lower():
                if not (curr_hour >= sun_set_time and
                        curr_hour <= sun_set_time + 1):
                    return False
            else:
                if not (curr_hour < sun_set_time or
                        curr_hour > sun_set_time + 1):
                    return False

        if time_range_type == 'rain':
            rm = players[id]['room']
            coords = rooms[rm]['coords']
            if 'true' in time_range_start.lower() or \
               'y' in time_range_start.lower():
                if not get_rain_at_coords(coords, map_area, clouds):
                    return False
            else:
                if get_rain_at_coords(coords, map_area, clouds):
                    return False

        if time_range_type == 'rainday':
            curr_time = datetime.datetime.today()
            curr_hour = curr_time.hour
            sun = get_solar()
            sun_rise_time = sun.get_local_sunrise_time(curr_time).hour
            sun_set_time = sun.get_local_sunset_time(curr_time).hour
            if curr_hour < sun_rise_time or \
               curr_hour > sun_set_time:
                return False
            rmid = players[id]['room']
            coords = rooms[rmid]['coords']
            if 'true' in time_range_start.lower() or \
               'y' in time_range_start.lower():
                if not get_rain_at_coords(coords, map_area, clouds):
                    return False
            else:
                if get_rain_at_coords(coords, map_area, clouds):
                    return False

        if time_range_type == 'rainnight':
            curr_time = datetime.datetime.today()
            curr_hour = curr_time.hour
            sun = get_solar()
            sun_rise_time = sun.get_local_sunrise_time(curr_time).hour
            sun_set_time = sun.get_local_sunset_time(curr_time).hour
            if curr_hour >= sun_rise_time and \
               curr_hour <= sun_set_time:
                return False
            rmid = players[id]['room']
            coords = rooms[rmid]['coords']
            if 'true' in time_range_start.lower() or \
               'y' in time_range_start.lower():
                if not get_rain_at_coords(coords, map_area, clouds):
                    return False
            else:
                if get_rain_at_coords(coords, map_area, clouds):
                    return False

        if time_range_type == 'rainmorning':
            curr_time = datetime.datetime.today()
            curr_hour = curr_time.hour
            sun = get_solar()
            sun_rise_time = sun.get_local_sunrise_time(curr_time).hour
            if curr_hour < sun_rise_time or \
               curr_hour > 12:
                return False
            rmid = players[id]['room']
            coords = rooms[rmid]['coords']
            if 'true' in time_range_start.lower() or \
               'y' in time_range_start.lower():
                if not get_rain_at_coords(coords, map_area, clouds):
                    return False
            else:
                if get_rain_at_coords(coords, map_area, clouds):
                    return False

        if time_range_type == 'rainafternoon':
            curr_time = datetime.datetime.today()
            curr_hour = curr_time.hour
            if curr_hour < 12 or curr_hour > 17:
                return False
            rmid = players[id]['room']
            coords = rooms[rmid]['coords']
            if 'true' in time_range_start.lower() or \
               'y' in time_range_start.lower():
                if not get_rain_at_coords(coords, map_area, clouds):
                    return False
            else:
                if get_rain_at_coords(coords, map_area, clouds):
                    return False

        if time_range_type == 'rainevening':
            curr_time = datetime.datetime.today()
            curr_hour = curr_time.hour
            sun = get_solar()
            sun_set_time = sun.get_local_sunset_time(curr_time).hour
            if curr_hour < 17 or \
               curr_hour > sun_set_time:
                return False
            rmid = players[id]['room']
            coords = rooms[rmid]['coords']
            if 'true' in time_range_start.lower() or \
               'y' in time_range_start.lower():
                if not get_rain_at_coords(coords, map_area, clouds):
                    return False
            else:
                if get_rain_at_coords(coords, map_area, clouds):
                    return False

        # hour of day
        if time_range_type.startswith('hour'):
            curr_hour = datetime.datetime.today().hour
            start_hour = int(time_range_start)
            end_hour = int(time_range_end)
            if end_hour >= start_hour:
                if curr_hour < start_hour or curr_hour > end_hour:
                    return False
            else:
                if curr_hour > end_hour and curr_hour < start_hour:
                    return False

        # between months
        if time_range_type.startswith('month'):
            curr_month = int(datetime.datetime.today().strftime("%m"))
            start_month = int(time_range_start)
            end_month = int(time_range_end)
            if end_month >= start_month:
                if curr_month < start_month or curr_month > end_month:
                    return False
            else:
                if curr_month > end_month and curr_month < start_month:
                    return False

        # a particular day of a month
        if time_range_type.startswith('dayofmonth'):
            curr_month = int(datetime.datetime.today().strftime("%m"))
            curr_day_of_month = int(datetime.datetime.today().strftime("%d"))
            month = int(time_range_start)
            monthday = int(time_range_end)
            matching_days = True
            if curr_month == month and curr_day_of_month == monthday:
                days_are_matched = True

        # between days of year
        if time_range_type == 'daysofyear':
            curr_day_of_year = int(datetime.datetime.today().strftime("%j"))
            start_day = int(time_range_start)
            end_day = int(time_range_end)
            if end_day >= start_day:
                if curr_day_of_year < start_day or curr_day_of_year > end_day:
                    return False
            else:
                if curr_day_of_year > end_day and curr_day_of_year < start_day:
                    return False

    # if we are matching a set of days, where any matched?
    if matching_days:
        if not days_are_matched:
            return False

    return True


def _move_npcs(npcs, players, mud, now, nid) -> None:
    """If movement is defined for an NPC this moves it around
    """
    this_npc = npcs[nid]
    if now > this_npc['lastMoved'] + \
       int(this_npc['moveDelay']) + this_npc['randomizer']:
        # Move types:
        #   random, cycle, inverse cycle, patrol, follow, leader:name
        move_type_lower = this_npc['moveType'].lower()

        follow_cycle = False
        if move_type_lower.startswith('f'):
            if len(this_npc['follow']) == 0:
                follow_cycle = True
                # Look for a player to follow
                for pid, _ in list(players.items()):
                    if this_npc['room'] == players[pid]['room']:
                        # follow by name
                        # print(this_npc['name'] + ' starts following ' +
                        # players[pid]['name'] + '\n')
                        this_npc['follow'] = players[pid]['name']
                        follow_cycle = False
            if not follow_cycle:
                return

        if move_type_lower.startswith('c') or \
           move_type_lower.startswith('p') or follow_cycle:
            npc_room_index = 0
            npc_room_curr = this_npc['room']
            for npc_room in this_npc['path']:
                if npc_room == npc_room_curr:
                    npc_room_index = npc_room_index + 1
                    break
                npc_room_index = npc_room_index + 1
            if npc_room_index >= len(this_npc['path']):
                if move_type_lower.startswith('p'):
                    this_npc['moveType'] = 'back'
                    npc_room_index = len(this_npc['path']) - 1
                    if npc_room_index > 0:
                        npc_room_index = npc_room_index - 1
                else:
                    npc_room_index = 0
        else:
            if move_type_lower.startswith('i') or \
               move_type_lower.startswith('b'):
                npc_room_index = 0
                npc_room_curr = this_npc['room']
                for npc_room in this_npc['path']:
                    if npc_room == npc_room_curr:
                        npc_room_index = npc_room_index - 1
                        break
                    npc_room_index = npc_room_index + 1
                if npc_room_index >= len(this_npc['path']):
                    npc_room_index = len(this_npc['path']) - 1
                if npc_room_index < 0:
                    if move_type_lower.startswith('b'):
                        this_npc['moveType'] = 'patrol'
                        npc_room_index = 0
                        if npc_room_index < len(this_npc['path']) - 1:
                            npc_room_index = npc_room_index + 1
                    else:
                        npc_room_index = len(this_npc['path']) - 1
            else:
                npc_room_index = \
                    _get_leader_room_index(npcs, players, mud, now,
                                           nid, move_type_lower)
                if len(npc_room_index) == 0:
                    npc_room_index = randint(0, len(this_npc['path']) - 1)

        rmid = this_npc['path'][npc_room_index]
        if this_npc['room'] != rmid:
            for pid, _ in list(players.items()):
                if this_npc['room'] == players[pid]['room']:
                    mud.send_message(
                        pid, '<f220>' + this_npc['name'] + "<r> " +
                        random_desc(this_npc['outDescription']) +
                        "\n\n")
            this_npc['room'] = rmid
            this_npc['lastRoom'] = rmid
            for pid, _ in list(players.items()):
                if this_npc['room'] == players[pid]['room']:
                    mud.send_message(
                        pid, '<f220>' + this_npc['name'] + "<r> " +
                        random_desc(this_npc['inDescription']) +
                        "\n\n")
        this_npc['randomizer'] = randint(0, this_npc['randomFactor'])
        this_npc['lastMoved'] = now


def _remove_inactive_entity(nid, npcs: {}, nid2, npcs_db: {},
                            npc_active: bool) -> bool:
    """Moves inactive NPCs to and from purgatory
    Returns true when recovering from purgatory
    """
    # Where NPCs go when inactive by default
    purgatory_room = "$rid=1386$"

    for time_range in npcs_db[nid2]['moveTimes']:
        if len(time_range) == 2:
            if time_range[0].startswith('inactive') or \
               time_range[0].startswith('home'):
                purgatory_room = "$rid=" + str(time_range[1]) + "$"
            break

    this_npc = npcs[nid]
    if this_npc['room'] == purgatory_room:
        if npc_active:
            if this_npc.get('lastRoom'):
                # recover from purgatory
                this_npc['room'] = this_npc['lastRoom']
                return True
        return False

    if not npc_active:
        # Move the NPC to purgatory
        this_npc['lastRoom'] = this_npc['room']
        this_npc['room'] = purgatory_room
        return False


def npc_respawns(npcs: {}) -> None:
    """Respawns inactive NPCs
    """
    for nid, _ in list(npcs.items()):
        this_npc = npcs[nid]
        if not this_npc['whenDied']:
            continue
        if int(time.time()) >= this_npc['whenDied'] + this_npc['respawn']:
            if len(this_npc['familiarOf']) == 0:
                this_npc['whenDied'] = None
                # this_npc['room'] = npcsTemplate[nid]['room']
                this_npc['room'] = this_npc['lastRoom']
                hp_str = str(this_npc['hp'])
                log("respawning " + this_npc['name'] +
                    " with " + hp_str +
                    " hit points", "info")


def run_mobile_items(items_db: {}, items: {}, event_schedule,
                     scripted_events_db,
                     rooms: {}, map_area, clouds: {}) -> None:
    """Updates all NPCs
    """
    for item, _ in list(items.items()):
        item_id = items[item]['id']
        # only non-takeable items
        if items_db[item_id]['weight'] > 0:
            continue
        if not items_db[item_id].get('moveTimes'):
            continue
        # Active now?
        item_active = \
            _entity_is_active(item_id, items, rooms,
                              items_db[item_id]['moveTimes'],
                              map_area, clouds)
        # Remove if not active
        _remove_inactive_entity(item, items, item_id, items_db, item_active)
        if not item_active:
            continue


def run_npcs(mud, npcs: {}, players: {}, fights, corpses, scripted_events_db,
             items_db: {}, npcsTemplate, rooms: {}, map_area, clouds: {},
             event_schedule) -> None:
    """Updates all NPCs
    """

    for nid, _ in list(npcs.items()):
        # is the NPC a familiar?
        npc_is_familiar = False
        this_npc = npcs[nid]
        if len(this_npc['familiarOf']) > 0:
            for pid, _ in list(players.items()):
                if this_npc['familiarOf'] == players[pid]['name']:
                    npc_is_familiar = True
                    break

        if not npc_is_familiar:
            # is the NPC active according to moveTimes?
            npc_active = \
                _entity_is_active(nid, npcs, rooms,
                                  this_npc['moveTimes'],
                                  map_area, clouds)
            _remove_inactive_entity(nid, npcs, nid, npcs, npc_active)
            if not npc_active:
                continue

        # Check if any player is in the same room, then send a random
        # message to them
        now = int(time.time())
        if this_npc['vocabulary'][0]:
            if now > \
               this_npc['timeTalked'] + \
               this_npc['talkDelay'] + \
               this_npc['randomizer']:
                rnd = randint(0, len(this_npc['vocabulary']) - 1)
                while rnd is this_npc['lastSaid']:
                    rnd = randint(0, len(this_npc['vocabulary']) - 1)
                for pid, _ in list(players.items()):
                    if this_npc['room'] == players[pid]['room']:
                        if len(this_npc['vocabulary']) > 1:
                            # mud.send_message(pid,
                            # this_npc['vocabulary'][rnd])
                            msg = '<f220>' + this_npc['name'] + \
                                '<r> says: <f86>' + \
                                this_npc['vocabulary'][rnd] + "\n\n"
                            mud.send_message(pid, msg)
                            this_npc['randomizer'] = \
                                randint(0, this_npc['randomFactor'])
                            this_npc['lastSaid'] = rnd
                            this_npc['timeTalked'] = now
                        else:
                            # mud.send_message(pid, this_npc['vocabulary'][0])
                            msg = '<f220>' + this_npc['name'] + \
                                '<r> says: <f86>' + \
                                this_npc['vocabulary'][0] + "\n\n"
                            mud.send_message(pid, msg)
                            this_npc['randomizer'] = \
                                randint(0, this_npc['randomFactor'])
                            this_npc['timeTalked'] = now

        # Iterate through fights and see if anyone is attacking an NPC -
        # if so, attack him too if not in combat (TODO: and isAggressive =
        # true)
        is_in_fight = False
        for fid, _ in list(fights.items()):
            if fights[fid]['s2id'] == nid and \
               npcs[fights[fid]['s2id']]['isInCombat'] == 1 and \
               fights[fid]['s2type'] == 'npc' and \
               fights[fid]['s1type'] == 'pc' and \
               fights[fid]['retaliated'] == 0:
                # print('player is attacking npc')
                # BETA: set las combat action to now when attacking a
                # player
                npcs[fights[fid]['s2id']]['lastCombatAction'] = \
                    int(time.time())
                fights[fid]['retaliated'] = 1
                npcs[fights[fid]['s2id']]['isInCombat'] = 1
                fights[len(fights)] = {
                    's1': npcs[fights[fid]['s2id']]['name'],
                    's2': players[fights[fid]['s1id']]['name'],
                    's1id': nid,
                    's2id': fights[fid]['s1id'],
                    's1type': 'npc',
                    's2type': 'pc',
                    'retaliated': 1
                }
                is_in_fight = True
            elif (fights[fid]['s2id'] == nid and
                  npcs[fights[fid]['s2id']]['isInCombat'] == 1 and
                  fights[fid]['s1type'] == 'npc' and
                  fights[fid]['retaliated'] == 0):
                # print('npc is attacking npc')
                # BETA: set last combat action to now when attacking a player
                npcs[fights[fid]['s2id']]['lastCombatAction'] = \
                    int(time.time())
                fights[fid]['retaliated'] = 1
                npcs[fights[fid]['s2id']]['isInCombat'] = 1
                fights[len(fights)] = {
                    's1': npcs[fights[fid]['s2id']]['name'],
                    's2': players[fights[fid]['s1id']]['name'],
                    's1id': nid,
                    's2id': fights[fid]['s1id'],
                    's1type': 'npc',
                    's2type': 'npc',
                    'retaliated': 1
                }
                is_in_fight = True

        # NPC moves to the next location
        now = int(time.time())
        if is_in_fight is False and \
           len(this_npc['path']) > 0:
            _move_npcs(npcs, players, mud, now, nid)

        # Check if NPC is still alive, if not, remove from room and
        # create a corpse, set isInCombat to 0, set whenDied to now
        # and remove any fights NPC was involved in
        if this_npc['hp'] <= 0:
            this_npc['isInCombat'] = 0
            this_npc['lastRoom'] = this_npc['room']
            this_npc['whenDied'] = int(time.time())

            # if the NPC is a familiar detach it from player
            for plyr in players:
                if players[plyr]['name'] is None:
                    continue
                if players[plyr]['familiar'] == int(nid):
                    players[plyr]['familiar'] -= 1

            fights_copy = deepcopy(fights)
            for fight, _ in fights_copy.items():
                if ((fights_copy[fight]['s1type'] == 'npc' and
                     fights_copy[fight]['s1id'] == nid) or
                    (fights_copy[fight]['s2type'] == 'npc' and
                     fights_copy[fight]['s2id'] == nid)):
                    # clear the combat flag
                    if fights_copy[fight]['s1type'] == 'pc':
                        fid = fights_copy[fight]['s1id']
                        players[fid]['isInCombat'] = 0
                    elif fights_copy[fight]['s1type'] == 'npc':
                        fid = fights_copy[fight]['s1id']
                        npcs[fid]['isInCombat'] = 0
                    if fights_copy[fight]['s2type'] == 'pc':
                        fid = fights_copy[fight]['s2id']
                        players[fid]['isInCombat'] = 0
                    elif fights_copy[fight]['s2type'] == 'npc':
                        fid = fights_copy[fight]['s2id']
                        npcs[fid]['isInCombat'] = 0
                    del fights[fight]
                    corpse_name = str(this_npc['name'] + "'s corpse")
                    if not corpse_exists(corpses,
                                         this_npc['room'],
                                         corpse_name):
                        corpses[len(corpses)] = {
                            'room': this_npc['room'],
                            'name': corpse_name,
                            'inv': deepcopy(this_npc['inv']),
                            'died': int(time.time()),
                            'TTL': this_npc['corpseTTL'],
                            'owner': 1
                        }

            # inform players about the death of an npc
            for pid, _ in list(players.items()):
                if players[pid]['authenticated'] is not None:
                    if players[pid]['authenticated'] is not None and \
                       players[pid]['room'] == this_npc['room']:
                        mud.send_message(
                            pid,
                            "<f220>{}<r> ".format(this_npc['name']) +
                            "<f88>has been killed.\n")
                        this_npc['lastRoom'] = this_npc['room']
                        this_npc['room'] = None
                        this_npc['hp'] = npcsTemplate[nid]['hp']

            # Drop NPC loot on the floor
            dropped_items = []
            for i in this_npc['inv']:
                if not str(i).isdigit():
                    for pid, _ in list(players.items()):
                        mud.send_message(
                            pid, 'NPC drops item: ' +
                            str(i) + ' is not an item number\n')
                    continue
                if randint(0, 100) < 50:
                    item_id_str = str(i)
                    last_room_str = str(this_npc['lastRoom'])
                    add_to_scheduler("0|spawnItem|" + item_id_str + ";" +
                                     last_room_str + ";0;0",
                                     -1, event_schedule, scripted_events_db)
                    print("Dropped!" + str(items_db[int(i)]['name']))
                    dropped_items.append(str(items_db[int(i)]['name']))

            # Inform other players in the room what items got dropped on NPC
            # death
            if len(dropped_items) > 0:
                for plyr in players:
                    if players[plyr]['name'] is None:
                        continue
                    if players[plyr]['room'] == this_npc['lastRoom']:
                        mud.send_message(
                            plyr, "Right before <f220>" +
                            str(this_npc['name']) +
                            "<r>'s lifeless body collapsed to the floor, " +
                            "it had dropped the following items: " +
                            "<f220>{}".format(', '.join(dropped_items)) + "\n")


def _conversation_state(word: str, conversation_states: {},
                        nid, npcs: {},
                        match_ctr: int) -> (bool, bool, int):
    """Is the conversations with this npc in the given state?
       Returns True if the conversation is in the given state
       Also returns True if subsequent words can also be matched
       and the current word match counter
    """
    this_npc = npcs[nid]
    if word.lower().startswith('state:'):
        required_state = word.lower().split(':')[1].strip()
        if this_npc['name'] in conversation_states:
            if conversation_states[this_npc['name']] != required_state:
                return False, False, match_ctr
            return True, True, match_ctr + 1
    return False, True, match_ctr


def _conversation_condition(word: str, conversation_states: {},
                            nid, npcs: {}, match_ctr: int,
                            players: {}, rooms: {},
                            id, cultures_db: {}) -> (bool, bool, int):
    condition_type = ''
    if '>' in word.lower():
        condition_type = '>'
    if '<' in word.lower():
        condition_type = '<'
    if '=' in word.lower():
        condition_type = condition_type + '='

    if len(condition_type) == 0:
        return False, True, match_ctr

    var_str = word.lower().split(condition_type)[0].strip()
    curr_value = -99999
    target_value = None

    if var_str in ('hp', 'hitpoints'):
        curr_value = players[id]['hp']
    if var_str in ('hpPercent', 'hitpointspercent'):
        curr_value = int(players[id]['hp'] * 100 / players[id]['hp'])
    if var_str in ('cul', 'culture'):
        if players[id].get('culture'):
            curr_value = players[id]['culture']
            target_value = word.lower().split(condition_type)[1].strip()
    if var_str in ('roomcul', 'roomculture'):
        curr_value = get_room_culture(cultures_db, rooms, players[id]['room'])
        target_value = word.lower().split(condition_type)[1].strip()
    if var_str in ('str', 'strength'):
        curr_value = players[id]['str']
    if var_str in ('wei', 'weight'):
        curr_value = players[id]['wei']
    if var_str in ('per', 'perception'):
        curr_value = players[id]['per']
    if var_str in ('lvl', 'level'):
        curr_value = players[id]['lvl']
    if var_str in ('exp', 'experience'):
        curr_value = players[id]['exp']
    if var_str in ('endu', 'endurance'):
        curr_value = players[id]['endu']
    if var_str in ('cha', 'charisma'):
        curr_value = players[id]['cha']
    if var_str in ('int', 'intelligence'):
        curr_value = players[id]['int']
    if var_str in ('agi', 'agility'):
        curr_value = players[id]['agi']
    if var_str in ('luc', 'luck'):
        curr_value = players[id]['luc']
    if var_str == 'cred':
        curr_value = players[id]['cred']
    if var_str == 'pp':
        curr_value = players[id]['pp']
    if var_str == 'ep':
        curr_value = players[id]['ep']
    if var_str == 'sp':
        curr_value = players[id]['sp']
    if var_str == 'cp':
        curr_value = players[id]['cp']
    if var_str == 'gp':
        curr_value = players[id]['gp']
    if var_str == 'reflex':
        curr_value = players[id]['ref']
    if var_str == 'cool':
        curr_value = players[id]['cool']
    if var_str == 'rest':
        curr_value = players[id]['restRequired']
    if var_str == 'language':
        curr_value = players[id]['speakLanguage'].lower()
        target_value = word.lower().split(condition_type)[1].strip()
        condition_type = '='
    if var_str == 'notlanguage':
        curr_value = players[id]['speakLanguage'].lower()
        target_value = word.lower().split(condition_type)[1].strip()
        condition_type = '!='
    if var_str == 'guild':
        curr_value = players[id]['guild'].lower()
        target_value = word.lower().split(condition_type)[1].strip()
        condition_type = '='
    if var_str == 'region':
        rmid = players[id]['room']
        curr_value = rooms[rmid]['region'].lower()
        target_value = word.lower().split(condition_type)[1].strip()
        condition_type = '='
    if var_str == 'notguild':
        curr_value = players[id]['guild'].lower()
        target_value = word.lower().split(condition_type)[1].strip()
        condition_type = '!='
    if var_str == 'race':
        curr_value = players[id]['race'].lower()
        target_value = word.lower().split(condition_type)[1].strip()
        condition_type = '='
    if var_str == 'notrace':
        curr_value = players[id]['race'].lower()
        target_value = word.lower().split(condition_type)[1].strip()
        condition_type = '!='
    if var_str == 'characterclass':
        curr_value = players[id]['characterClass'].lower()
        target_value = word.lower().split(condition_type)[1].strip()
        condition_type = '='
    if var_str == 'notcharacterclass':
        curr_value = players[id]['characterClass'].lower()
        target_value = word.lower().split(condition_type)[1].strip()
        condition_type = '!='
    if var_str == 'enemy':
        curr_value = players[id]['enemy'].lower()
        target_value = word.lower().split(condition_type)[1].strip()
        condition_type = '='
    if var_str == 'notenemy':
        curr_value = players[id]['enemy'].lower()
        target_value = word.lower().split(condition_type)[1].strip()
        condition_type = '!='
    if var_str == 'affinity':
        if npcs[nid]['affinity'].get(players[id]['name']):
            curr_value = npcs[nid]['affinity'][players[id]['name']]
        else:
            curr_value = 0

    if target_value is None:
        target_value = int(word.lower().split(condition_type)[1].strip())

    if not isinstance(curr_value, str):
        if curr_value == -99999:
            return False, True, match_ctr

        if condition_type == '>':
            if curr_value <= target_value:
                return False, False, match_ctr

        if condition_type == '<':
            if curr_value >= target_value:
                return False, False, match_ctr

        if condition_type == '>=':
            if curr_value < target_value:
                return False, False, match_ctr

        if condition_type == '<=':
            if curr_value > target_value:
                return False, False, match_ctr

    if condition_type == '=':
        if curr_value != target_value:
            return False, False, match_ctr

    if condition_type == '!=':
        if curr_value == target_value:
            return False, False, match_ctr

    return True, True, match_ctr + 1


def _conversation_word_count(message: str, wordsList: [], npcs: {},
                             nid, conversation_states: {},
                             players: {}, rooms: {}, id,
                             cultures_db: {}) -> int:
    """Returns the number of matched words in the message.
       This is a 'bag of words/conditions' type of approach.
    """
    match_ctr = 0
    for possible_word in wordsList:
        if possible_word.lower().startswith('image:'):
            continue

        # Is the conversation required to be in a certain state?
        state_matched, continue_matching, match_ctr = \
            _conversation_state(possible_word,
                                conversation_states,
                                nid, npcs, match_ctr)

        if not continue_matching:
            break

        if not state_matched:
            # match conditions such as "strength < 10"
            word_matched, continue_matching, match_ctr = \
                _conversation_condition(possible_word,
                                        conversation_states,
                                        nid, npcs,
                                        match_ctr,
                                        players, rooms, id,
                                        cultures_db)

            if not continue_matching:
                break

            if not word_matched:
                if possible_word.lower() in message:
                    match_ctr += 1
    return match_ctr


def _conversation_give(best_match: str, best_match_action: str,
                       thingGivenIDstr: str, players: {}, id,
                       mud, npcs: {}, nid: int, items_db: {},
                       puzzled_str: str, guilds_db: {}) -> bool:
    """Conversation in which an NPC gives something to you
    """
    if best_match_action in ('give', 'gift'):
        this_npc = npcs[nid]
        if len(thingGivenIDstr) > 0:
            item_id = int(thingGivenIDstr)
            if item_id not in list(players[id]['inv']):
                players[id]['inv'].append(str(item_id))
                update_player_attributes(id, players, items_db, item_id, 1)
                players[id]['wei'] = \
                    player_inventory_weight(id, players, items_db)
                increase_affinity_between_players(players, id, npcs, nid,
                                                  guilds_db)
                increase_affinity_between_players(npcs, nid, players, id,
                                                  guilds_db)
                if '#' not in best_match:
                    mud.send_message(
                        id, "<f220>" + this_npc['name'] + "<r> says: " +
                        best_match + ".")
                else:
                    mud.send_message(id, "<f220>" +
                                     best_match.replace('#', '').strip() + ".")
                mud.send_message(
                    id, "<f220>" + this_npc['name'] +
                    "<r> gives you " + items_db[item_id]['article'] +
                    ' ' + items_db[item_id]['name'] + ".\n\n")
                return True
        mud.send_message(
            id, "<f220>" + this_npc['name'] +
            "<r> looks " + puzzled_str + ".\n\n")
        return True
    return False


def _conversation_skill(best_match: str, best_match_action: str,
                        best_match_action_param0: str,
                        best_match_action_param1: str,
                        players: {}, id, mud, npcs: {}, nid, items_db: {},
                        puzzled_str: str, guilds_db: {}) -> bool:
    """Conversation in which an NPC gives or alters a skill
    """
    if best_match_action == 'skill' or \
       best_match_action == 'teach':
        this_npc = npcs[nid]
        if len(best_match_action_param0) > 0 and \
           len(best_match_action_param1) > 0:
            new_skill = best_match_action_param0.lower()
            skill_value_str = best_match_action_param1
            if not players[id].get(new_skill):
                log(new_skill + ' skill does not exist in player instance',
                    'info')
                return False
            if '+' in skill_value_str:
                # increase skill
                players[id][new_skill] = \
                    players[id][new_skill] + \
                    int(skill_value_str.replace('+', ''))
            else:
                # decrease skill
                if '-' in skill_value_str:
                    players[id][new_skill] = \
                        players[id][new_skill] - \
                        int(skill_value_str.replace('-', ''))
                else:
                    # set skill to absolute value
                    players[id][new_skill] = \
                        players[id][new_skill] + \
                        int(skill_value_str)

            increase_affinity_between_players(players, id, npcs,
                                              nid, guilds_db)
            increase_affinity_between_players(npcs, nid, players,
                                              id, guilds_db)

            mud.send_message(
                id, "<f220>" + this_npc['name'] + "<r> says: " + best_match +
                ".\n\n")
            return True
        else:
            mud.send_message(
                id, "<f220>" + this_npc['name'] + "<r> looks " +
                puzzled_str + ".\n\n")
            return False
    return False


def _conversation_experience(
        best_match: str, best_match_action: str,
        best_match_action_param0: str,
        best_match_action_param1: str,
        players: {}, id, mud, npcs: {}, nid, items_db: {},
        puzzled_str: str, guilds_db: {}) -> bool:
    """Conversation in which an NPC increases your experience
    """
    if best_match_action == 'exp' or \
       best_match_action == 'experience':
        if len(best_match_action_param0) > 0:
            exp_value = int(best_match_action_param0)
            players[id]['exp'] = players[id]['exp'] + exp_value
            increase_affinity_between_players(players, id, npcs,
                                              nid, guilds_db)
            increase_affinity_between_players(npcs, nid, players,
                                              id, guilds_db)
            return True
        else:
            mud.send_message(
                id, "<f220>" + npcs[nid]['name'] + "<r> looks " +
                puzzled_str + ".\n\n")
            return False
    return False


def _conversation_join_guild(
        best_match: str, best_match_action: str,
        best_match_action_param0: str,
        best_match_action_param1: str,
        players: {}, id, mud, npcs: {}, nid, items_db: {},
        puzzled_str: str, guilds_db: {}) -> bool:
    """Conversation in which an NPC adds you to a guild
    """
    if best_match_action == 'clan' or \
       best_match_action == 'guild' or \
       best_match_action == 'tribe' or \
       best_match_action == 'house':
        if len(best_match_action_param0) > 0:
            players[id]['guild'] = best_match_action_param0
            if len(best_match_action_param1) > 0:
                players[id]['guildRole'] = best_match_action_param1
            increase_affinity_between_players(players, id, npcs,
                                              nid, guilds_db)
            increase_affinity_between_players(npcs, nid, players,
                                              id, guilds_db)
            return True
        else:
            mud.send_message(
                id, "<f220>" + npcs[nid]['name'] +
                "<r> looks " + puzzled_str + ".\n\n")
            return False
    return False


def _conversation_familiar_mode(
        best_match: str, best_match_action: str,
        best_match_action_param0: str,
        best_match_action_param1: str,
        players: {}, id, mud, npcs: {}, npcs_db: {}, rooms: {},
        nid, items: {}, items_db: {}, puzzled_str: str) -> bool:
    """Switches the mode of a familiar
    """
    this_npc = npcs[nid]
    if best_match_action == 'familiar':
        if len(best_match_action_param0) > 0:
            if this_npc['familiarOf'] == players[id]['name']:
                mode = best_match_action_param0.lower().strip()
                if mode in get_familiar_modes():
                    if mode == 'follow':
                        familiar_default_mode(nid, npcs, npcs_db)
                    if mode == 'hide':
                        familiar_hide(nid, npcs, npcs_db)
                    mud.send_message(
                        id, "<f220>" + this_npc['name'] +
                        "<r> " + best_match + ".\n\n")
                    if mode == 'scout':
                        familiar_scout(mud, players, id, nid,
                                       npcs, npcs_db, rooms,
                                       best_match_action_param1)
                    if mode == 'see':
                        familiar_sight(mud, nid, npcs, npcs_db,
                                       rooms, players, id, items,
                                       items_db)
                    return True
            else:
                mud.send_message(
                    id, this_npc['name'] + " is not your familiar.\n\n")
        else:
            mud.send_message(
                id, "<f220>" + this_npc['name'] +
                "<r> looks " + puzzled_str + ".\n\n")
            return False
    return False


def _conversation_transport(
        best_match_action: str, best_match_action_param0: str,
        mud, id, players: {}, best_match, npcs: {}, nid,
        puzzled_str, guilds_db: {}, rooms: {}) -> bool:
    """Conversation in which an NPC transports you to some location
    """
    if best_match_action == 'transport' or \
       best_match_action == 'ride' or \
       best_match_action == 'teleport':
        this_npc = npcs[nid]
        if len(best_match_action_param0) > 0:
            room_id = best_match_action_param0
            mud.send_message(id, best_match)
            message_to_room_players(
                mud, players, id,
                '<f32>{}<r> leaves.'.format(players[id]['name']) + "\n\n")
            players[id]['room'] = room_id
            this_npc['room'] = room_id
            increase_affinity_between_players(players, id, npcs,
                                              nid, guilds_db)
            increase_affinity_between_players(npcs, nid, players,
                                              id, guilds_db)
            message_to_room_players(
                mud, players, id,
                '<f32>{}<r> arrives.'.format(players[id]['name']) + "\n\n")
            mud.send_message(
                id, "You are in " + rooms[room_id]['name'] + "\n\n")
            return True
        mud.send_message(
            id, "<f220>" + this_npc['name'] + "<r> looks " +
            puzzled_str + ".\n\n")
        return True
    return False


def _conversation_taxi(
        best_match_action: str, best_match_action_param0: str,
        best_match_action_param1: str, players: {},
        id, mud, best_match, npcs: {}, nid, items_db: {},
        puzzled_str: str, guilds_db: {}, rooms: {}) -> bool:
    """Conversation in which an NPC transports you to some
    location in exchange for payment/barter
    """
    if best_match_action == 'taxi':
        this_npc = npcs[nid]
        if len(best_match_action_param0) > 0 and \
           len(best_match_action_param1) > 0:
            room_id = best_match_action_param0
            item_buy_id = int(best_match_action_param1)
            if str(item_buy_id) in list(players[id]['inv']):
                players[id]['inv'].remove(str(item_buy_id))

                increase_affinity_between_players(players, id, npcs,
                                                  nid, guilds_db)
                increase_affinity_between_players(npcs, nid, players,
                                                  id, guilds_db)
                mud.send_message(id, best_match)
                message_to_room_players(
                    mud, players, id,
                    '<f32>{}<r> leaves.'.format(players[id]['name']) + "\n\n")
                players[id]['room'] = room_id
                this_npc['room'] = room_id
                message_to_room_players(
                    mud, players, id,
                    '<f32>{}<r> arrives.'.format(players[id]['name']) + "\n\n")
                mud.send_message(
                    id, "You are in " + rooms[room_id]['name'] + "\n\n")
                return True
            else:
                mud.send_message(
                    id, "<f220>" + this_npc['name'] + "<r> says: Give me " +
                    items_db[item_buy_id]['article'] + ' ' +
                    items_db[item_buy_id]['name'] + ".\n\n")
                return True
        mud.send_message(
            id, "<f220>" + this_npc['name'] + "<r> looks " +
            puzzled_str + ".\n\n")
        return True
    return False


def _conversation_give_on_date(
        best_match_action: str, best_match_action_param0: str,
        best_match_action_param1: str, players: {},
        id, mud, npcs: {}, nid, items_db: {}, best_match,
        puzzled_str: str, guilds_db: {}) -> bool:
    """Conversation in which an NPC gives something to you on
    a particular date of the year eg. Some festival or holiday
    """
    if best_match_action == 'giveondate' or \
       best_match_action == 'giftondate':
        this_npc = npcs[nid]
        if len(best_match_action_param0) > 0:
            item_id = int(best_match_action_param0)
            if item_id not in list(players[id]['inv']):
                if '/' in best_match_action_param1:
                    day_number = int(best_match_action_param1.split('/')[0])
                    if day_number == \
                       int(datetime.datetime.today().strftime("%d")):
                        month_number = \
                            int(best_match_action_param1.split('/')[1])
                        if month_number == \
                           int(datetime.datetime.today().strftime("%m")):
                            players[id]['inv'].append(str(item_id))
                            players[id]['wei'] = \
                                player_inventory_weight(id, players, items_db)
                            update_player_attributes(
                                id, players, items_db, item_id, 1)
                            increase_affinity_between_players(
                                players, id, npcs, nid, guilds_db)
                            increase_affinity_between_players(
                                npcs, nid, players, id, guilds_db)
                            if '#' not in best_match:
                                mud.send_message(
                                    id, "<f220>" + this_npc['name'] +
                                    "<r> says: " + best_match + ".")
                            else:
                                mud.send_message(
                                    id, "<f220>" +
                                    best_match.replace('#', '').strip() + ".")
                            mud.send_message(
                                id, "<f220>" + this_npc['name'] +
                                "<r> gives you " +
                                items_db[item_id]['article'] +
                                ' ' + items_db[item_id]['name'] + ".\n\n")
                            return True
        mud.send_message(
            id, "<f220>" + this_npc['name'] + "<r> looks " +
            puzzled_str + ".\n\n")
        return True
    return False


def _conversation_sell(
        best_match: str, best_match_action: str,
        best_match_action_param0: str,
        npcs: {}, nid, mud, id, players: {}, items_db: {},
        puzzled_str: str, guilds_db: {}) -> bool:
    """Conversation in which a player sells to an NPC
    """
    if best_match_action == 'sell':
        sell_item_ids = best_match_action_param0.split('|')
        if len(best_match_action_param0) > 0 and sell_item_ids:
            for sell_id_str in sell_item_ids:
                sell_id_str = sell_id_str.strip()
                item_sell_id = int(sell_id_str)
                cost = items_db[sell_id_str]['cost']
                qty = 0
                denomination = None
                if cost:
                    qty, denomination = parse_cost(cost)
                if sell_id_str in players[id]['inv'] and \
                   cost and qty and denomination:
                    players[id][denomination] += qty

                    # decrease the players inventory
                    players[id]['inv'].remove(sell_id_str)
                    update_player_attributes(
                        id, players, items_db, item_sell_id, -1)
                    players[id]['wei'] = \
                        player_inventory_weight(id, players, items_db)
                    increase_affinity_between_players(players, id, npcs,
                                                      nid, guilds_db)
                    increase_affinity_between_players(npcs, nid, players,
                                                      id, guilds_db)

                    itemName = \
                        items_db[sell_id_str]['article'] + ' ' + \
                        items_db[sell_id_str]['name']
                    mud.send_message(
                        id, "You sell " + itemName + ".\n\n")
                    return True
    return False


def _conversation_buy_or_exchange(
        best_match: str, best_match_action: str,
        best_match_action_param0: str,
        best_match_action_param1: str,
        npcs: {}, nid, mud, id, players: {}, items_db: {},
        puzzled_str: str, guilds_db: {}) -> bool:
    """Conversation in which an NPC exchanges/swaps some item
    with you or in which you buy some item from them
    """
    if best_match_action == 'buy' or \
       best_match_action == 'exchange' or \
       best_match_action == 'barter' or \
       best_match_action == 'trade':
        this_npc = npcs[nid]
        if len(best_match_action_param0) > 0 and len(
                best_match_action_param1) > 0:
            item_buy_id = int(best_match_action_param0)
            item_sell_id = int(best_match_action_param1)
            if str(item_sell_id) not in list(this_npc['inv']):
                if best_match_action == 'buy':
                    mud.send_message(
                        id, "<f220>" + this_npc['name'] +
                        "<r> says: I don't have any of those to sell.\n\n")
                else:
                    mud.send_message(
                        id, "<f220>" + this_npc['name'] +
                        "<r> says: I don't have any of those to trade.\n\n")
            else:
                if str(item_buy_id) in list(players[id]['inv']):
                    if str(item_sell_id) not in list(players[id]['inv']):
                        players[id]['inv'].remove(str(item_buy_id))
                        update_player_attributes(
                            id, players, items_db, item_buy_id, -1)
                        players[id]['inv'].append(str(item_sell_id))
                        players[id]['wei'] = \
                            player_inventory_weight(id, players, items_db)
                        update_player_attributes(
                            id, players, items_db, item_sell_id, 1)
                        if str(item_buy_id) not in list(this_npc['inv']):
                            this_npc['inv'].append(str(item_buy_id))
                        increase_affinity_between_players(players, id, npcs,
                                                          nid, guilds_db)
                        increase_affinity_between_players(npcs, nid, players,
                                                          id, guilds_db)
                        mud.send_message(
                            id, "<f220>" + this_npc['name'] +
                            "<r> says: " + best_match + ".")
                        mud.send_message(
                            id, "<f220>" + this_npc['name'] +
                            "<r> gives you " +
                            items_db[item_sell_id]['article'] +
                            ' ' + items_db[item_sell_id]['name'] + ".\n\n")
                    else:
                        mud.send_message(id, "<f220>" + this_npc['name'] +
                                         "<r> says: I see you already have " +
                                         items_db[item_sell_id]['article'] +
                                         ' ' +
                                         items_db[item_sell_id]['name'] +
                                         ".\n\n")
                else:
                    if best_match_action == 'buy':
                        mud.send_message(
                            id, "<f220>" + this_npc['name'] + "<r> says: " +
                            items_db[item_sell_id]['article'] + ' ' +
                            items_db[item_sell_id]['name'] + " costs " +
                            items_db[item_buy_id]['article'] + ' ' +
                            items_db[item_buy_id]['name'] + ".\n\n")
                    else:
                        mud.send_message(
                            id, "<f220>" + this_npc['name'] +
                            "<r> says: I'll give you " +
                            items_db[item_sell_id]['article'] +
                            ' ' + items_db[item_sell_id]['name'] +
                            " in exchange for " +
                            items_db[item_buy_id]['article'] + ' ' +
                            items_db[item_buy_id]['name'] + ".\n\n")
        else:
            mud.send_message(
                id, "<f220>" + this_npc['name'] + "<r> looks " +
                puzzled_str + ".\n\n")
            return True
    return False


def npc_conversation(mud, npcs: {}, npcs_db: {}, players: {},
                     items: {}, items_db: {}, rooms: {},
                     id: int, nid: int, message,
                     character_class_db: {}, sentiment_db: {},
                     guilds_db: {}, clouds: {}, races_db: {},
                     item_history: {}, cultures_db: {}) -> None:
    """Conversation with an NPC
    This typically works by matching some words and then
    producing a corresponding response and/or action
    """
    this_npc = npcs[nid]
    if len(this_npc['familiarOf']) > 0:
        # is this a familiar of another player?
        if this_npc['familiarOf'] != players[id]['name']:
            # familiar only talks to its assigned player
            mud.send_message(
                id, "<f220>" + this_npc['name'] +
                "<r> ignores you.\n\n")
            return

    rand_value = randint(0, 100)
    puzzled_str = 'puzzled'
    if rand_value > 25:
        puzzled_str = 'confused'
    if rand_value > 50:
        puzzled_str = 'baffled'
    if rand_value > 75:
        puzzled_str = 'perplexed'

    if this_npc.get('language'):
        if players[id]['speakLanguage'] not in this_npc['language']:
            mud.send_message(
                id, "<f220>" + this_npc['name'] + "<r> looks " +
                puzzled_str +
                ". They don't understand your language.\n\n")
            return

    best_match = ''
    best_match_action = ''
    best_match_action_param0 = ''
    best_match_action_param1 = ''
    image_name = None
    max_match_ctr = 0

    conversation_states = players[id]['convstate']
    conversation_new_state = ''

    # for each entry in the conversation list
    this_npc = npcs[nid]
    for conv in this_npc['conv']:
        # entry must contain matching words and resulting reply
        if len(conv) >= 2:
            # count the number of matches for this line
            match_ctr = \
                _conversation_word_count(message, conv[0], npcs,
                                         nid, conversation_states,
                                         players, rooms, id,
                                         cultures_db)
            # store the best match
            if match_ctr > max_match_ctr:
                max_match_ctr = match_ctr
                best_match = random_desc(conv[1])
                best_match_action = ''
                best_match_action_param0 = ''
                best_match_action_param1 = ''
                conversation_new_state = ''
                image_name = None
                if len(conv) >= 3:
                    idx = 2
                    ctr = 0
                    while idx < len(conv):
                        if ':' not in conv[idx]:
                            if ctr == 0:
                                best_match_action = conv[idx]
                            elif ctr == 1:
                                best_match_action_param0 = conv[idx]
                            elif ctr == 2:
                                best_match_action_param1 = conv[idx]
                            ctr += 1
                            idx += 1
                            continue
                        if conv[idx].lower().startswith('image:'):
                            image_name = \
                                conv[idx].lower().split(':')[1].strip()
                        elif conv[idx].lower().startswith('state:'):
                            conversation_new_state = \
                                conv[idx].lower().split(':')[1].strip()
                        idx += 1

    if get_sentiment(message, sentiment_db) >= 0:
        increase_affinity_between_players(players, id, npcs, nid, guilds_db)
        increase_affinity_between_players(npcs, nid, players, id, guilds_db)
    else:
        decrease_affinity_between_players(players, id, npcs, nid, guilds_db)
        decrease_affinity_between_players(npcs, nid, players, id, guilds_db)

    if len(best_match) > 0:
        # There were some word matches
        if image_name:
            image_filename = 'images/events/' + image_name
            if os.path.isfile(image_filename):
                with open(image_filename, 'r', encoding='utf-8') as fp_image:
                    mud.send_image(id, '\n' + fp_image.read())

        if len(conversation_new_state) > 0:
            # set the new conversation state with this npc
            conversation_states[this_npc['name']] = conversation_new_state

        if len(best_match_action) > 0:
            # give
            if _conversation_give(best_match, best_match_action,
                                  best_match_action_param0, players,
                                  id, mud, npcs, nid, items_db, puzzled_str,
                                  guilds_db):
                return

            # teach skill
            if _conversation_skill(best_match, best_match_action,
                                   best_match_action_param0,
                                   best_match_action_param1, players,
                                   id, mud, npcs, nid, items_db, puzzled_str,
                                   guilds_db):
                return

            # increase experience
            if _conversation_experience(best_match, best_match_action,
                                        best_match_action_param0,
                                        best_match_action_param1, players,
                                        id, mud, npcs, nid, items_db,
                                        puzzled_str, guilds_db):
                return

            # Join a guild
            if _conversation_join_guild(best_match, best_match_action,
                                        best_match_action_param0,
                                        best_match_action_param1, players,
                                        id, mud, npcs, nid, items_db,
                                        puzzled_str, guilds_db):
                return

            # Switch familiar into different modes
            if _conversation_familiar_mode(best_match, best_match_action,
                                           best_match_action_param0,
                                           best_match_action_param1,
                                           players,
                                           id, mud, npcs, npcs_db, rooms,
                                           nid, items, items_db, puzzled_str):
                return

            # transport (free taxi)
            if _conversation_transport(best_match_action,
                                       best_match_action_param0, mud,
                                       id, players, best_match, npcs,
                                       nid, puzzled_str, guilds_db, rooms):
                return

            # taxi (exchange for an item)
            if _conversation_taxi(best_match_action,
                                  best_match_action_param0,
                                  best_match_action_param1, players,
                                  id, mud, best_match, npcs, nid,
                                  items_db, puzzled_str, guilds_db, rooms):
                return

            # give on a date
            if _conversation_give_on_date(best_match_action,
                                          best_match_action_param0,
                                          best_match_action_param1,
                                          players, id, mud, npcs, nid,
                                          items_db, best_match, puzzled_str,
                                          guilds_db):
                return

            # sell
            if _conversation_sell(best_match, best_match_action,
                                  best_match_action_param0,
                                  npcs, nid, mud, id, players,
                                  items_db, puzzled_str, guilds_db):
                return

            # buy or exchange
            if _conversation_buy_or_exchange(best_match, best_match_action,
                                             best_match_action_param0,
                                             best_match_action_param1,
                                             npcs, nid, mud, id, players,
                                             items_db, puzzled_str, guilds_db):
                return

        if this_npc['familiarOf'] == players[id]['name'] or \
           len(this_npc['animalType']) > 0 or \
           '#' in best_match:
            # Talking with a familiar or animal can include
            # non-verbal responses so we remove 'says'
            mud.send_message(
                id, "<f220>" + this_npc['name'] + "<r> " +
                best_match.replace('#', '').strip() + ".\n\n")
        else:
            mud.send_message(
                id, "<f220>" + this_npc['name'] + "<r> says: " +
                best_match + ".\n\n")
    else:
        # No word matches
        mud.send_message(
            id, "<f220>" + this_npc['name'] +
            "<r> looks " + puzzled_str + ".\n\n")
