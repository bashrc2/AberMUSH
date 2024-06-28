__filename__ = "traps.py"
__author__ = "Bob Mottram"
__credits__ = [""]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "DnD Mechanics"

import time
from random import randint
from functions import random_desc
from functions import time_string_to_sec


def teleport_from_trap(mud, id, players: {}, rooms: {}):
    """Teleport out of a trap
    """
    room_id = players[id]['room']
    if not rooms[room_id]['trap'].get('trappedPlayers'):
        return
    if players[id]['name'] in rooms[room_id]['trap']['trappedPlayers']:
        rooms[room_id]['trap']['trappedPlayers'].remove(players[id]['name'])
        if len(rooms[room_id]['trap']['trappedPlayers']) == 0:
            rooms[room_id]['trap']['trapDamaged'] = 0


def describe_trapped_player(mud, id, players: {}, rooms: {}):
    """Describes being in a trap
    """
    room_id = players[id]['room']
    if not rooms[room_id]['trap'].get('trapType'):
        return

    trap_type = rooms[room_id]['trap']['trapType']
    if trap_type == 'net':
        desc = (
            "You struggle with the net but it's pinning you down",
            "You seem to be trapped in a net",
            "Being covered by a net makes it difficult to move"
        )
        mud.send_message(id, random_desc(desc) + '.\n\n')
    elif trap_type == 'chain net':
        desc = (
            "You struggle with the net but its chain webbing is " +
            "pinning you down",
            "You seem to be trapped in a net made from linked chains",
            "Being covered by a chain net makes it difficult to move"
        )
        mud.send_message(id, random_desc(desc) + '.\n\n')
    elif trap_type == 'tar pit':
        desc = (
            "You have sunk into a pit of sticky tar, " +
            "which prevents you from moving",
            "Sticky tar surrounds you, preventing you from moving"
        )
        mud.send_message(id, random_desc(desc) + '.\n\n')
    elif trap_type == 'pit':
        desc = (
            "You have fallen into a pit in the ground, which you " +
            "don't seem to be able to get out from",
            "You appear to be in a hole in the ground"
        )
        mud.send_message(id, random_desc(desc) + '.\n\n')
    elif trap_type in ('ditch', 'marsh', 'bog'):
        desc = (
            "You have fallen into a " + trap_type + " full of thick mud, " +
            "which is too slippery to get out from",
            "You appear to be swimming very slowly in a " +
            trap_type + " full of thick mud"
        )
        mud.send_message(id, random_desc(desc) + '.\n\n')


def player_is_trapped(id, players: {}, rooms: {}):
    """Returns true if the player is trapped
    """
    room_id = players[id]['room']
    if rooms[room_id].get('trap'):
        if rooms[room_id]['trap'].get('trappedPlayers'):
            if players[id]['name'] in rooms[room_id]['trap']['trappedPlayers']:
                return True
    return False


def _describe_trap_deactivation(mud, room_id, trap, players: {}):
    """Describes when a trap gets reset
    """
    for pid in players:
        if players[pid]['name'] is None:
            continue
        if players[pid]['room'] != room_id:
            continue
        if players[pid]['name'] not in trap['trappedPlayers']:
            continue
        if trap['trapType'] == 'net' or \
           trap['trapType'] == 'chain net':
            desc = 'The ' + trap['trapType'] + ' lifts and you escape'
            mud.send_message(pid, random_desc(desc) + '.\n\n')
        elif trap['trapType'] == 'pit' or trap['trapType'] == 'tar pit':
            desc = 'You clamber out from the ' + \
                trap['trapType']
            mud.send_message(pid, random_desc(desc) + '.\n\n')
        elif (trap['trapType'] == 'ditch' or trap['trapType'] == 'marsh' or
              trap['trapType'] == 'bog'):
            desc = 'With squelching noises, you climb out of the muddy ' + \
                trap['trapType']
            mud.send_message(pid, random_desc(desc) + '.\n\n')


def _holding_cutting_weapon(id, players: {}, items_db: {}):
    """If the player is holding a cutting weapon return its item_id
    """
    item_id = players[id]['clo_rhand']
    if item_id > 0:
        if items_db[item_id]['type'].startswith('slashing'):
            return item_id
    item_id = players[id]['clo_lhand']
    if item_id > 0:
        if items_db[item_id]['type'].startswith('slashing'):
            return item_id
    return -1


def _escape_with_cutting_tool(mud, id, players: {}, rooms: {}, items_db: {}):
    """Escape from a trap using a cutting tool
    """
    item_id = _holding_cutting_weapon(id, players, items_db)
    if item_id == -1:
        desc = (
            "You attempt to escape with your bare hands, " +
            "but remain trapped|You tug and wrestle but can't escape",
            "Looks like you need to use a cutting tool, otherwise " +
            "you'll be here for a while",
            "Looks like you need something to cut with"
        )
        mud.send_message(
            id, random_desc(desc) + '.\n\n')
        return
    room_id = players[id]['room']
    max_trap_damage = rooms[room_id]['trap']['trapDamagedMax']
    tool_damage_max = items_db[item_id]['mod_str']
    slashing_damage = randint(1, tool_damage_max)
    trap_damage = \
        rooms[room_id]['trap']['trapDamaged'] + slashing_damage
    if trap_damage < max_trap_damage:
        rooms[room_id]['trap']['trapDamaged'] = trap_damage
        damage_str = ', causing <f15><b2>* ' + str(slashing_damage) + \
            ' *<r> points of damage to it'
        desc = 'You slash at the ' + rooms[room_id]['trap']['trapType'] + \
            damage_str + '|You cut the ' + \
            rooms[room_id]['trap']['trapType'] + damage_str
        mud.send_message(id, random_desc(desc) + '.\n\n')
    else:
        rooms[room_id]['trap']['trapDamaged'] = 0
        rooms[room_id]['trap']['trappedPlayers'].clear()
        if len(rooms[room_id]['trap']['trapEscapeDescription']) > 0:
            desc = rooms[room_id]['trap']['trapEscapeDescription']
            mud.send_message(id, random_desc(desc) + '.\n\n')
        else:
            desc = 'You cut a large hole in the ' + \
                rooms[room_id]['trap']['trapType'] + ' and escape'
            mud.send_message(
                id, random_desc(desc) + '.\n\n')


def escape_from_trap(mud, id, players: {}, rooms: {}, items_db: {}):
    """Attempt to escape from a trap
    """
    room_id = players[id]['room']
    if not rooms[room_id]['trap'].get('trapEscapeMethod'):
        mud.send_message(
            id, random_desc("Nothing happens") + '.\n\n')
        return
    escape_method = rooms[room_id]['trap']['trapEscapeMethod']
    if 'slash' in escape_method:
        _escape_with_cutting_tool(mud, id, players, rooms, items_db)
    else:
        mud.send_message(
            id, random_desc("Nothing happens") + '.\n\n')


def _trap_activation_describe(mud, id, players, room_id, rooms,
                              penalty_value, trap_tag):
    trap_type = rooms[room_id]['trap']['trapType']
    if trap_type in ('net', 'chain net'):
        if rooms[room_id]['trap']['trap_activation'].startswith('pressure'):
            desc = (
                trap_tag +
                "You hear a click as you step onto a pressure plate. A " +
                trap_type + " falls from above and pins you down"
            )
            mud.send_message(id, random_desc(desc) + '.<r>\n\n')
        else:
            desc = (
                trap_tag + "A " + trap_type +
                " falls from above and pins you down"
            )
            mud.send_message(id, random_desc(desc) + '.<r>\n\n')
    elif trap_type in ('pit', 'tar pit'):
        desc = (
            trap_tag + "You fall into a " + trap_type
        )
        mud.send_message(id, random_desc(desc) + '.<r>\n\n')
    elif trap_type in ('ditch', 'marsh', 'bog'):
        desc = (
            trap_tag + "You fall into a muddy " + trap_type,
            trap_tag + "You slip and fall into a muddy " + trap_type
        )
        mud.send_message(id, random_desc(desc) + '.<r>\n\n')
    elif trap_type.startswith('dart'):
        desc = (
            trap_tag +
            "Poisoned darts emerge from holes in the wall and " +
            "sting you for <r><f15><b88>* " + str(penalty_value) +
            " *<r>" + trap_tag + " hit points"
        )
        mud.send_message(id, random_desc(desc) + '.<r>\n\n')


def trap_activation(mud, id, players: {}, rooms: {}, exit_direction):
    """Activates a trap
    """
    room_id = players[id]['room']
    if not rooms[room_id]['trap'].get('trap_activation'):
        return False
    # Is the trap already activated?
    if rooms[room_id]['trap']['trap_activationTime'] != 0:
        return False
    trap_tag = '<f202>'

    # recognised activation type
    activation_type = rooms[room_id]['trap']['trap_activation']
    if not (activation_type == 'tripwire' or
            activation_type.startswith('move') or
            activation_type.startswith('pressure')):
        return False

    # probability of the trap being activated
    prob = 100
    if rooms[room_id]['trap'].get('trap_activationProbability'):
        prob = rooms[room_id]['trap']['trap_activationProbability']
    rand_percent = randint(1, 100)
    if rand_percent > prob:
        return False

    # which exit activates the trap?
    if not rooms[room_id]['trap'].get('trapExit'):
        return False

    # are we going in that direction?
    if rooms[room_id]['trap']['trapExit'] != exit_direction:
        return False

    # add player to the list of trapped ones
    rooms[room_id]['trap']['trappedPlayers'] = [players[id]['name']]

    # record the time when the trap was activated
    if time_string_to_sec(rooms[room_id]['trap']['trapDuration']) > 0:
        rooms[room_id]['trap']['trap_activationTime'] = \
            int(time.time())

    # reset the amount of damage to the trap
    rooms[room_id]['trap']['trapDamaged'] = 0

    # subtract a trap penalty from the player
    penalty_type = rooms[room_id]['trap']['trapPenaltyType']
    penalty_value = randint(1, rooms[room_id]['trap']['trapPenalty'])
    players[id][penalty_type] -= penalty_value

    # describe the trapped player
    if len(rooms[room_id]['trap']['trap_activationDescription']) > 0:
        desc = rooms[room_id]['trap']['trap_activationDescription']
        mud.send_message(id, trap_tag +
                         random_desc(desc) + '.<r>\n\n')
    else:
        _trap_activation_describe(mud, id, players, room_id, rooms,
                                  penalty_value, trap_tag)
    return True


def run_traps(mud, rooms: {}, players: {}, npcs: {}):
    """Update the status of any traps
    """
    for room_id, room in rooms.items():
        if not room['trap'].get('trappedPlayers'):
            continue
        if len(room['trap']['trappedPlayers']) == 0:
            continue
        if not room.get('trapDuration'):
            continue
        if room['trap']['trap_activationTime'] == 0:
            continue
        now = int(time.time())
        if now >= \
           room['trap']['trap_activationTime'] + \
           time_string_to_sec(room['trap']['trapDuration']):
            _describe_trap_deactivation(mud, room_id,
                                        room['trap'], players)
            room['trap']['trappedPlayers'].clear()
            room['trap']['trap_activationTime'] = 0
            room['trap']['trapDamaged'] = 0
