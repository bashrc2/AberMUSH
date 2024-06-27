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


def get_familiar_name(players: {}, id, npcs: {}) -> str:
    """Returns the name of the familiar of the given player
    """
    plyr = players[id]
    if plyr['familiar'] != -1:
        for _, npc1 in list(npcs.items()):
            if npc1['familiarOf'] == plyr['name']:
                return npc1['name']
    return ''


def familiar_recall(mud, players: {}, id, npcs: {}, npcs_db: {}):
    """Move any familiar to the player's location
    """
    plyr = players[id]

    # remove any existing familiars
    removals = []
    for nid, npc1 in npcs.items():
        if npc1['familiarOf'] == plyr['name']:
            removals.append(nid)

    for index in removals:
        del npcs[index]

    # By default player has no familiar
    plyr['familiar'] = -1

    # Find familiar and set its room to that of the player
    for nid, npc1 in npcs_db.items():
        if npc1['familiarOf'] != plyr['name']:
            continue
        plyr['familiar'] = int(nid)
        if not npcs.get(nid):
            npcs[nid] = deepcopy(npcs_db[nid])
        npcs[nid]['room'] = plyr['room']
        mud.send_message(id, "Your familiar is recalled.\n\n")
        break


def familiar_default_mode(nid, npcs: {}, npcs_db: {}):
    npcs[nid]['familiarMode'] = "follow"
    npcs_db[nid]['familiarMode'] = "follow"
    npcs[nid]['moveType'] = ""
    npcs_db[nid]['moveType'] = ""
    npcs[nid]['path'] = []
    npcs_db[nid]['path'] = []


def familiar_sight(mud, nid, npcs: {}, npcs_db: {}, rooms: {},
                   players: {}, id,
                   items: {}, items_db: {}):
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
    for _, plyr in players.items():
        if plyr['name'] is None:
            continue
        if plyr['room'] == npcs[nid]['room']:
            creatures_count = creatures_count+1
            if plyr['race'] not in creatures_races:
                creatures_races.append(plyr['race'])
            for name, value in plyr['affinity'].items():
                if npcs[nid]['familiarOf'] == name:
                    if value >= 0:
                        creatures_friendly = creatures_friendly + 1

    for n_co, npc1 in npcs.items():
        if n_co == nid:
            continue
        if npc1['room'] == npcs[nid]['room']:
            creatures_count = creatures_count+1
            if npc1.get('race'):
                if npc1['race'] not in creatures_races:
                    creatures_races.append(npc1['race'])
            if npc1.get('affinity'):
                for name, value in npc1['affinity'].items():
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
    for _, itemobj in items.items():
        if itemobj['room'] != npcs[nid]['room']:
            continue
        if not itemobj.get('weight'):
            continue
        if itemobj['weight'] > 0:
            items_in_room += 1
            if (itemobj['mod_str'] > 0 and
                (itemobj['clo_lhand'] > 0 or
                 itemobj['clo_rhand'] > 0)):
                weapons_in_room += 1
            if itemobj['mod_endu'] > 0 and \
               itemobj['clo_chest'] > 0:
                armor_in_room += 1
            if itemobj['edible'] != 0:
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


def familiar_is_hidden(players: {}, id, npcs: {}) -> bool:
    """Returns true if the familiar of the player is hidden
    TODO: currently unused
    """
    plyr = players[id]
    if plyr['familiar'] != -1:
        for _, npc1 in npcs.items():
            if npc1['familiarOf'] == plyr['name']:
                if npc1['familiarMode'] == 'hide':
                    return True
    return False


def _familiar_scout_any_direction(familiar_size: int, start_room_id,
                                  room_exits: {}, rooms: {}) -> []:
    """Scout in any direction
    """
    new_path = [start_room_id]
    for _, rmid in room_exits.items():
        if rooms[rmid]['maxPlayerSize'] > -1:
            if familiar_size > rooms[rmid]['maxPlayerSize']:
                continue
        new_path.append(rmid)
        new_path.append(start_room_id)
    if len(new_path) == 1:
        new_path.clear()
    return new_path


def _familiar_scout_in_direction(mud, players: {}, id, start_room_id,
                                 room_exits: {},
                                 direction, rooms: {}) -> []:
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


def familiar_scout(mud, players: {}, id, nid, npcs: {},
                   npcs_db: {}, rooms: {}, direction):
    """familiar begins scouting the surrounding rooms
    """
    npc1 = npcs[nid]
    start_room_id = npc1['room']
    room_exits = rooms[start_room_id]['exits']

    new_path = []

    if direction == 'any' or direction == 'all' or len(direction) == 0:
        new_path = \
            _familiar_scout_any_direction(npc1['siz'], start_room_id,
                                          room_exits, rooms)
    else:
        new_path = \
            _familiar_scout_in_direction(mud, players, id, start_room_id,
                                         room_exits, direction, rooms)

    if len(new_path) > 0:
        npc1['familiarMode'] = "scout"
        npc1['moveType'] = "patrol"
        npc1['path'] = deepcopy(new_path)
        npcs_db[nid]['familiarMode'] = "scout"
        npcs_db[nid]['moveType'] = "patrol"
        npcs_db[nid]['path'] = deepcopy(new_path)
    else:
        familiar_default_mode(nid, npcs, npcs_db)
