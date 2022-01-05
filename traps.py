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
from functions import randomDescription
from functions import TimeStringToSec


def teleportFromTrap(mud, id, players: {}, rooms: {}):
    """Teleport out of a trap
    """
    room_id = players[id]['room']
    if not rooms[room_id]['trap'].get('trappedPlayers'):
        return
    if players[id]['name'] in rooms[room_id]['trap']['trappedPlayers']:
        rooms[room_id]['trap']['trappedPlayers'].remove(players[id]['name'])
        if len(rooms[room_id]['trap']['trappedPlayers']) == 0:
            rooms[room_id]['trap']['trapDamaged'] = 0


def describeTrappedPlayer(mud, id, players: {}, rooms: {}):
    """Describes being in a trap
    """
    room_id = players[id]['room']
    if not rooms[room_id]['trap'].get('trapType'):
        return

    trapType = rooms[room_id]['trap']['trapType']
    if trapType == 'net':
        desc = (
            "You struggle with the net but it's pinning you down",
            "You seem to be trapped in a net",
            "Being covered by a net makes it difficult to move"
        )
        mud.send_message(id, randomDescription(desc) + '.\n\n')
    elif trapType == 'chain net':
        desc = (
            "You struggle with the net but its chain webbing is " +
            "pinning you down",
            "You seem to be trapped in a net made from linked chains",
            "Being covered by a chain net makes it difficult to move"
        )
        mud.send_message(id, randomDescription(desc) + '.\n\n')
    elif trapType == 'tar pit':
        desc = (
            "You have sunk into a pit of sticky tar, " +
            "which prevents you from moving",
            "Sticky tar surrounds you, preventing you from moving"
        )
        mud.send_message(id, randomDescription(desc) + '.\n\n')
    elif trapType == 'pit':
        desc = (
            "You have fallen into a pit in the ground, which you " +
            "don't seem to be able to get out from",
            "You appear to be in a hole in the ground"
        )
        mud.send_message(id, randomDescription(desc) + '.\n\n')
    elif trapType == 'ditch' or trapType == 'marsh' or trapType == 'bog':
        desc = (
            "You have fallen into a " + trapType + " full of thick mud, " +
            "which is too slippery to get out from",
            "You appear to be swimming very slowly in a " +
            trapType + " full of thick mud"
        )
        mud.send_message(id, randomDescription(desc) + '.\n\n')


def playerIsTrapped(id, players: {}, rooms: {}):
    """Returns true if the player is trapped
    """
    room_id = players[id]['room']
    if rooms[room_id].get('trap'):
        if rooms[room_id]['trap'].get('trappedPlayers'):
            if players[id]['name'] in rooms[room_id]['trap']['trappedPlayers']:
                return True
    return False


def _describeTrapDeactivation(mud, room_id, trap, players: {}):
    """Describes when a trap gets reset
    """
    for id in players:
        if players[id]['name'] is None:
            continue
        if players[id]['room'] != room_id:
            continue
        if players[id]['name'] not in trap['trappedPlayers']:
            continue
        if trap['trapType'] == 'net' or \
           trap['trapType'] == 'chain net':
            desc = 'The ' + trap['trapType'] + ' lifts and you escape'
            mud.send_message(id, randomDescription(desc) + '.\n\n')
        elif trap['trapType'] == 'pit' or trap['trapType'] == 'tar pit':
            desc = 'You clamber out from the ' + \
                trap['trapType']
            mud.send_message(id, randomDescription(desc) + '.\n\n')
        elif (trap['trapType'] == 'ditch' or trap['trapType'] == 'marsh' or
              trap['trapType'] == 'bog'):
            desc = 'With squelching noises, you climb out of the muddy ' + \
                trap['trapType']
            mud.send_message(id, randomDescription(desc) + '.\n\n')


def _holdingCuttingWeapon(id, players: {}, items_db: {}):
    """If the player is holding a cutting weapon return its itemID
    """
    itemID = players[id]['clo_rhand']
    if itemID > 0:
        if items_db[itemID]['type'].startswith('slashing'):
            return itemID
    itemID = players[id]['clo_lhand']
    if itemID > 0:
        if items_db[itemID]['type'].startswith('slashing'):
            return itemID
    return -1


def _escapeWithCuttingTool(mud, id, players: {}, rooms: {}, items_db: {}):
    """Escape from a trap using a cutting tool
    """
    itemID = _holdingCuttingWeapon(id, players, items_db)
    if itemID == -1:
        desc = (
            "You attempt to escape with your bare hands, " +
            "but remain trapped|You tug and wrestle but can't escape",
            "Looks like you need to use a cutting tool, otherwise " +
            "you'll be here for a while",
            "Looks like you need something to cut with"
        )
        mud.send_message(
            id, randomDescription(desc) + '.\n\n')
        return
    room_id = players[id]['room']
    maxTrapDamage = rooms[room_id]['trap']['trapDamagedMax']
    toolDamageMax = items_db[itemID]['mod_str']
    slashingDamage = randint(1, toolDamageMax)
    trapDamage = rooms[room_id]['trap']['trapDamaged'] + slashingDamage
    if trapDamage < maxTrapDamage:
        rooms[room_id]['trap']['trapDamaged'] = trapDamage
        damageStr = ', causing <f15><b2>* ' + str(slashingDamage) + \
            ' *<r> points of damage to it'
        desc = 'You slash at the ' + rooms[room_id]['trap']['trapType'] + \
            damageStr + '|You cut the ' + \
            rooms[room_id]['trap']['trapType'] + damageStr
        mud.send_message(id, randomDescription(desc) + '.\n\n')
    else:
        rooms[room_id]['trap']['trapDamaged'] = 0
        rooms[room_id]['trap']['trappedPlayers'].clear()
        if len(rooms[room_id]['trap']['trapEscapeDescription']) > 0:
            desc = rooms[room_id]['trap']['trapEscapeDescription']
            mud.send_message(id, randomDescription(desc) + '.\n\n')
        else:
            desc = 'You cut a large hole in the ' + \
                rooms[room_id]['trap']['trapType'] + ' and escape'
            mud.send_message(
                id, randomDescription(desc) + '.\n\n')


def escapeFromTrap(mud, id, players: {}, rooms: {}, items_db: {}):
    """Attempt to escape from a trap
    """
    room_id = players[id]['room']
    if not rooms[room_id]['trap'].get('trapEscapeMethod'):
        mud.send_message(
            id, randomDescription("Nothing happens") + '.\n\n')
        return
    escapeMethod = rooms[room_id]['trap']['trapEscapeMethod']
    if 'slash' in escapeMethod:
        _escapeWithCuttingTool(mud, id, players, rooms, items_db)
    else:
        mud.send_message(
            id, randomDescription("Nothing happens") + '.\n\n')


def _trapActivationDescribe(mud, id, players, room_id, rooms,
                            penaltyValue, trapTag):
    trapType = rooms[room_id]['trap']['trapType']
    if trapType == 'net' or \
       trapType == 'chain net':
        if rooms[room_id]['trap']['trapActivation'].startswith('pressure'):
            desc = (
                trapTag +
                "You hear a click as you step onto a pressure plate. A " +
                trapType + " falls from above and pins you down"
            )
            mud.send_message(id, randomDescription(desc) + '.<r>\n\n')
        else:
            desc = (
                trapTag + "A " + trapType +
                " falls from above and pins you down"
            )
            mud.send_message(id, randomDescription(desc) + '.<r>\n\n')
    elif trapType == 'pit' or trapType == 'tar pit':
        desc = (
            trapTag + "You fall into a " + trapType
        )
        mud.send_message(id, randomDescription(desc) + '.<r>\n\n')
    elif trapType == 'ditch' or trapType == 'marsh' or trapType == 'bog':
        desc = (
            trapTag + "You fall into a muddy " + trapType,
            trapTag + "You slip and fall into a muddy " + trapType
        )
        mud.send_message(id, randomDescription(desc) + '.<r>\n\n')
    elif trapType.startswith('dart'):
        desc = (
            trapTag +
            "Poisoned darts emerge from holes in the wall and " +
            "sting you for <r><f15><b88>* " + str(penaltyValue) +
            " *<r>" + trapTag + " hit points"
        )
        mud.send_message(id, randomDescription(desc) + '.<r>\n\n')


def trapActivation(mud, id, players: {}, rooms: {}, exitDirection):
    """Activates a trap
    """
    room_id = players[id]['room']
    if not rooms[room_id]['trap'].get('trapActivation'):
        return False
    # Is the trap already activated?
    if rooms[room_id]['trap']['trapActivationTime'] != 0:
        return False
    trapTag = '<f202>'

    # recognised activation type
    activationType = rooms[room_id]['trap']['trapActivation']
    if not (activationType == 'tripwire' or
            activationType.startswith('move') or
            activationType.startswith('pressure')):
        return False

    # probability of the trap being activated
    prob = 100
    if rooms[room_id]['trap'].get('trapActivationProbability'):
        prob = rooms[room_id]['trap']['trapActivationProbability']
    randPercent = randint(1, 100)
    if randPercent > prob:
        return False

    # which exit activates the trap?
    if not rooms[room_id]['trap'].get('trapExit'):
        return False

    # are we going in that direction?
    if rooms[room_id]['trap']['trapExit'] != exitDirection:
        return False

    # add player to the list of trapped ones
    rooms[room_id]['trap']['trappedPlayers'] = [players[id]['name']]

    # record the time when the trap was activated
    if TimeStringToSec(rooms[room_id]['trap']['trapDuration']) > 0:
        rooms[room_id]['trap']['trapActivationTime'] = \
            int(time.time())

    # reset the amount of damage to the trap
    rooms[room_id]['trap']['trapDamaged'] = 0

    # subtract a trap penalty from the player
    penaltyType = rooms[room_id]['trap']['trapPenaltyType']
    penaltyValue = randint(1, rooms[room_id]['trap']['trapPenalty'])
    players[id][penaltyType] -= penaltyValue

    # describe the trapped player
    if len(rooms[room_id]['trap']['trapActivationDescription']) > 0:
        desc = rooms[room_id]['trap']['trapActivationDescription']
        mud.send_message(id, trapTag +
                         randomDescription(desc) + '.<r>\n\n')
    else:
        _trapActivationDescribe(mud, id, players, room_id, rooms,
                                penaltyValue, trapTag)
    return True


def run_traps(mud, rooms: {}, players: {}, npcs: {}):
    """Update the status of any traps
    """
    for rm in rooms:
        if not rooms[rm]['trap'].get('trappedPlayers'):
            continue
        if len(rooms[rm]['trap']['trappedPlayers']) == 0:
            continue
        if not rooms[rm].get('trapDuration'):
            continue
        if rooms[rm]['trap']['trapActivationTime'] == 0:
            continue
        now = int(time.time())
        if now >= \
           rooms[rm]['trap']['trapActivationTime'] + \
           TimeStringToSec(rooms[rm]['trap']['trapDuration']):
            _describeTrapDeactivation(mud, rm, rooms[rm]['trap'], players)
            rooms[rm]['trap']['trappedPlayers'].clear()
            rooms[rm]['trap']['trapActivationTime'] = 0
            rooms[rm]['trap']['trapDamaged'] = 0
