__filename__ = "familiar.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "NPCs"

from functions import random_desc
from functions import deepcopy
# from copy import deepcopy

# Movement modes for familiars
FAMILIAR_MODES = ("follow", "scout", "hide", "see")


def get_familiar_modes():
    return FAMILIAR_MODES


def get_familiar_name(players, id, npcs):
    """Returns the name of the familiar of the given player
    """
    if players[id]['familiar'] != -1:
        for nid, _ in list(npcs.items()):
            if npcs[nid]['familiarOf'] == players[id]['name']:
                return npcs[nid]['name']
    return ''


def familiar_recall(mud, players, id, npcs, npcs_db):
    """Move any familiar to the player's location
    """
    # remove any existing familiars
    removals = []
    for nid, item in list(npcs.items()):
        if item['familiarOf'] == players[id]['name']:
            removals.append(nid)

    for index in removals:
        del npcs[index]

    # By default player has no familiar
    players[id]['familiar'] = -1

    # Find familiar and set its room to that of the player
    for nid, item in list(npcs_db.items()):
        if item['familiarOf'] == players[id]['name']:
            players[id]['familiar'] = int(nid)
            if not npcs.get(nid):
                npcs[nid] = deepcopy(npcs_db[nid])
            npcs[nid]['room'] = players[id]['room']
            mud.send_message(id, "Your familiar is recalled.\n\n")
            break


def familiar_default_mode(nid, npcs, npcs_db):
    npcs[nid]['familiarMode'] = "follow"
    npcs_db[nid]['familiarMode'] = "follow"
    npcs[nid]['moveType'] = ""
    npcs_db[nid]['moveType'] = ""
    npcs[nid]['path'] = []
    npcs_db[nid]['path'] = []


def familiar_sight(mud, nid, npcs, npcs_db, rooms, players, id,
                   items, items_db):
    """familiar reports what it sees
    """
    start_room_id = npcs[nid]['room']
    room_exits = rooms[start_room_id]['exits']

    mud.send_message(id, "Your familiar says:\n")
    if len(room_exits) == 0:
        mud.send_message(id, "There are no exits.")
    else:
        if len(room_exits) > 1:
            mud.send_message(id, "There are " + str(len(room_exits)) +
                             " exits.")
        else:
            exit_description = random_desc("a single|one")
            mud.send_message(id, "There is " + exit_description + " exit.")
    creatures_count = 0
    creatures_friendly = 0
    creatures_races = []
    for plyr in players:
        if players[plyr]['name'] is None:
            continue
        if players[plyr]['room'] == npcs[nid]['room']:
            creatures_count = creatures_count+1
            if players[plyr]['race'] not in creatures_races:
                creatures_races.append(players[plyr]['race'])
            for name, value in players[plyr]['affinity'].items():
                if npcs[nid]['familiarOf'] == name:
                    if value >= 0:
                        creatures_friendly = creatures_friendly + 1

    for n_co in npcs:
        if n_co != nid:
            if npcs[n_co]['room'] == npcs[nid]['room']:
                creatures_count = creatures_count+1
                if npcs[n_co].get('race'):
                    if npcs[n_co]['race'] not in creatures_races:
                        creatures_races.append(npcs[n_co]['race'])
                if npcs[n_co].get('affinity'):
                    for name, value in npcs[n_co]['affinity'].items():
                        if npcs[nid]['familiarOf'] == name:
                            if value >= 0:
                                creatures_friendly = creatures_friendly + 1

    if creatures_count > 0:
        creature_str = random_desc("creature|being|entity")
        creatures_msg = 'I see '
        if creatures_count > 1:
            creatures_msg = creatures_msg + str(creatures_count) + ' ' + \
                creature_str + 's'
        else:
            creatures_msg = creatures_msg + 'one ' + creature_str
        creatures_msg = creatures_msg + ' here.'

        friendly_word = \
            random_desc("friendly|nice|pleasing|not threatening")
        if creatures_friendly > 0:
            if creatures_friendly > 1:
                creatures_msg = creatures_msg + ' ' + \
                    str(creatures_friendly) + ' are ' + friendly_word + '.'
            else:
                if creatures_friendly == creatures_count:
                    creatures_msg = \
                        creatures_msg + ' They are ' + friendly_word + '.'
                else:
                    creatures_msg = \
                        creatures_msg + ' One is ' + friendly_word + '.'
        creatures_msg = creatures_msg + '\n'
        if len(creatures_races) > 0:
            creatures_msg = creatures_msg + 'They are '
            if len(creatures_races) == 1:
                creatures_msg = \
                    creatures_msg + '<f220>' + creatures_races[0] + 's<r>.'
            else:
                if len(creatures_races) == 2:
                    creatures_msg = \
                        creatures_msg + '<f220>' + creatures_races[0] + \
                        's<r> and <f220>' + creatures_races[1] + 's<r>.'
                else:
                    ctr = 0
                    for rac in creatures_races:
                        if ctr == 0:
                            creatures_msg = \
                                creatures_msg + '<f220>' + rac + 's<r>'
                        if ctr > 0:
                            if ctr < len(creatures_races) - 1:
                                creatures_msg = \
                                    creatures_msg + ', <f220>' + rac + 's<r>'
                            else:
                                creatures_msg = \
                                    creatures_msg + ' and <f220>' + \
                                    rac + 's<r>.'
                        ctr = ctr + 1
        mud.send_message(id, creatures_msg)

    items_in_room = 0
    weapons_in_room = 0
    armor_in_room = 0
    edible_in_room = 0
    for iid, _ in list(items.items()):
        if items[iid]['room'] == npcs[nid]['room']:
            if items[iid].get('weight'):
                if items[iid]['weight'] > 0:
                    items_in_room += 1
                    if (items[iid]['mod_str'] > 0 and
                        (items[iid]['clo_lhand'] > 0 or
                         items[iid]['clo_rhand'] > 0)):
                        weapons_in_room += 1
                    if items[iid]['mod_endu'] > 0 and \
                       items[iid]['clo_chest'] > 0:
                        armor_in_room += 1
                    if items[iid]['edible'] != 0:
                        edible_in_room += 1
    if armor_in_room > 0 and weapons_in_room > 0:
        mud.send_message(id, 'There are some weapons and armor here.')
    else:
        if armor_in_room > 0:
            mud.send_message(id, 'There is some armor here.')
        else:
            if weapons_in_room > 0:
                mud.send_message(id, 'There are some weapons here.')
            else:
                mud.send_message(id, 'There are some items here.')
    if edible_in_room:
        mud.send_message(id, 'There are some edibles here.')
    mud.send_message(id, '\n\n')


def familiar_hide(nid, npcs, npcs_db):
    """Causes a familiar to hide
    """
    npcs[nid]['familiarMode'] = "hide"
    npcs_db[nid]['familiarMode'] = "hide"


def familiar_is_hidden(players: {}, id, npcs: {}):
    """Returns true if the familiar of the player is hidden
    TODO: currently unused
    """
    if players[id]['familiar'] != -1:
        for nid, _ in list(npcs.items()):
            if npcs[nid]['familiarOf'] == players[id]['name']:
                if npcs[nid]['familiarMode'] == 'hide':
                    return True
    return False


def _familiar_scout_any_direction(familiarSize, start_room_id,
                                  room_exits, rooms: {}):
    """Scout in any direction
    """
    new_path = [start_room_id]
    for _, rmid in room_exits.items():
        if rooms[rmid]['maxPlayerSize'] > -1:
            if familiarSize > rooms[rmid]['maxPlayerSize']:
                continue
        new_path.append(rmid)
        new_path.append(start_room_id)
    if len(new_path) == 1:
        new_path.clear()
    return new_path


def _familiar_scout_in_direction(mud, players, id, start_room_id, room_exits,
                                 direction, rooms):
    """Scout in the given direction
    """
    new_path = []
    if room_exits.get(direction):
        if rooms[room_exits[direction]]['maxPlayerSize'] > -1:
            if players[id]['siz'] <= \
               rooms[room_exits[direction]]['maxPlayerSize']:
                new_path = [start_room_id, room_exits[direction]]
            else:
                mud.send_message(id, "It's too small to enter!\n\n")
        else:
            new_path = [start_room_id, room_exits[direction]]
    else:
        mud.send_message(id, "I can't go that way!\n\n")
    return new_path


def familiar_scout(mud, players, id, nid, npcs, npcs_db, rooms, direction):
    """familiar begins scouting the surrounding rooms
    """
    start_room_id = npcs[nid]['room']
    room_exits = rooms[start_room_id]['exits']

    new_path = []

    if direction == 'any' or direction == 'all' or len(direction) == 0:
        new_path = \
            _familiar_scout_any_direction(npcs[nid]['siz'], start_room_id,
                                          room_exits, rooms)
    else:
        new_path = \
            _familiar_scout_in_direction(mud, players, id, start_room_id,
                                         room_exits, direction, rooms)

    if len(new_path) > 0:
        npcs[nid]['familiarMode'] = "scout"
        npcs[nid]['moveType'] = "patrol"
        npcs[nid]['path'] = deepcopy(new_path)
        npcs_db[nid]['familiarMode'] = "scout"
        npcs_db[nid]['moveType'] = "patrol"
        npcs_db[nid]['path'] = deepcopy(new_path)
    else:
        familiar_default_mode(nid, npcs, npcs_db)
