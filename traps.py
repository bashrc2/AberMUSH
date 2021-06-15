__filename__ = "traps.py"
__author__ = "Bob Mottram"
__credits__ = [""]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"
__module_group__ = "DnD Mechanics"

import time
from random import randint
from functions import randomDescription
from functions import TimeStringToSec


def teleportFromTrap(mud, id, players: {}, rooms: {}):
    """Teleport out of a trap
    """
    roomID = players[id]['room']
    if not rooms[roomID]['trap'].get('trappedPlayers'):
        return
    if players[id]['name'] in rooms[roomID]['trap']['trappedPlayers']:
        rooms[roomID]['trap']['trappedPlayers'].remove(players[id]['name'])
        if len(rooms[roomID]['trap']['trappedPlayers']) == 0:
            rooms[roomID]['trap']['trapDamaged'] = 0


def describeTrappedPlayer(mud, id, players: {}, rooms: {}):
    """Describes being in a trap
    """
    roomID = players[id]['room']
    if not rooms[roomID]['trap'].get('trapType'):
        return

    trapType = rooms[roomID]['trap']['trapType']
    if trapType == 'net':
        desc = "You struggle with the net but it's pinning you down|" + \
            "You seem to be trapped in a net|Being covered by a net " + \
            "makes it difficult to move"
        mud.sendMessage(id, randomDescription(desc)+'.\n\n')
    elif trapType == 'chain net':
        desc = "You struggle with the net but its chain webbing is " + \
            "pinning you down|You seem to be trapped in a net made " + \
            "from linked chains|Being covered by a chain net makes " + \
            "it difficult to move"
        mud.sendMessage(id, randomDescription(desc)+'.\n\n')
    elif trapType == 'tar pit':
        desc = "You have sunk into a pit of sticky tar, " + \
            "which prevents you from moving|" + \
            "Sticky tar surrounds you, preventing you from moving"
        mud.sendMessage(id, randomDescription(desc)+'.\n\n')
    elif trapType == 'pit':
        desc = "You have fallen into a pit in the ground, which you " + \
            "don't seem to be able to get out from|" + \
            "You appear to be in a hole in the ground"
        mud.sendMessage(id, randomDescription(desc)+'.\n\n')
    elif trapType == 'ditch' or trapType == 'marsh' or trapType == 'bog':
        desc = "You have fallen into a " + \
            trapType + " full of thick mud, " + \
            "which is too slippery to get out from|" + \
            "You appear to be swimming very slowly in a " + \
            trapType + " full of thick mud"
        mud.sendMessage(id, randomDescription(desc)+'.\n\n')


def playerIsTrapped(id, players: {}, rooms: {}):
    """Returns true if the player is trapped
    """
    roomID = players[id]['room']
    if rooms[roomID].get('trap'):
        if rooms[roomID]['trap'].get('trappedPlayers'):
            if players[id]['name'] in rooms[roomID]['trap']['trappedPlayers']:
                return True
    return False


def _describeTrapDeactivation(mud, roomID, trap, players: {}):
    """Describes when a trap gets reset
    """
    for id in players:
        if players[id]['name'] is None:
            continue
        if players[id]['room'] != roomID:
            continue
        if players[id]['name'] not in trap['trappedPlayers']:
            continue
        if trap['trapType'] == 'net' or \
           trap['trapType'] == 'chain net':
            desc = 'The ' + trap['trapType'] + ' lifts and you escape'
            mud.sendMessage(id, randomDescription(desc)+'.\n\n')
        elif trap['trapType'] == 'pit' or trap['trapType'] == 'tar pit':
            desc = 'You clamber out from the ' + \
                trap['trapType']
            mud.sendMessage(id, randomDescription(desc)+'.\n\n')
        elif (trap['trapType'] == 'ditch' or trap['trapType'] == 'marsh' or
              trap['trapType'] == 'bog'):
            desc = 'With squelching noises, you climb out of the muddy ' + \
                trap['trapType']
            mud.sendMessage(id, randomDescription(desc)+'.\n\n')


def _holdingCuttingWeapon(id, players: {}, itemsDB: {}):
    """If the player is holding a cutting weapon return its itemID
    """
    itemID = players[id]['clo_rhand']
    if itemID > 0:
        if itemsDB[itemID]['type'].startswith('slashing'):
            return itemID
    itemID = players[id]['clo_lhand']
    if itemID > 0:
        if itemsDB[itemID]['type'].startswith('slashing'):
            return itemID
    return -1


def _escapeWithCuttingTool(mud, id, players: {}, rooms: {}, itemsDB: {}):
    """Escape from a trap using a cutting tool
    """
    itemID = _holdingCuttingWeapon(id, players, itemsDB)
    if itemID == -1:
        desc = "You attempt to escape with your bare hands, " + \
            "but remain trapped|You tug and wrestle but can't escape|" + \
            "Looks like you need to use a cutting tool, otherwise " + \
            "you'll be here for a while|Looks like you need something " + \
            "to cut with"
        mud.sendMessage(
            id, randomDescription(desc) + '.\n\n')
        return
    roomID = players[id]['room']
    maxTrapDamage = rooms[roomID]['trap']['trapDamagedMax']
    toolDamageMax = itemsDB[itemID]['mod_str']
    slashingDamage = randint(1, toolDamageMax)
    trapDamage = rooms[roomID]['trap']['trapDamaged'] + slashingDamage
    if trapDamage < maxTrapDamage:
        rooms[roomID]['trap']['trapDamaged'] = trapDamage
        damageStr = ', causing <f15><b2>* ' + str(slashingDamage) + \
            ' *<r> points of damage to it'
        desc = 'You slash at the ' + rooms[roomID]['trap']['trapType'] + \
            damageStr + '|You cut the ' + \
            rooms[roomID]['trap']['trapType'] + damageStr
        mud.sendMessage(id, randomDescription(desc) + '.\n\n')
    else:
        rooms[roomID]['trap']['trapDamaged'] = 0
        rooms[roomID]['trap']['trappedPlayers'].clear()
        if len(rooms[roomID]['trap']['trapEscapeDescription']) > 0:
            desc = rooms[roomID]['trap']['trapEscapeDescription']
            mud.sendMessage(id, randomDescription(desc) + '.\n\n')
        else:
            desc = 'You cut a large hole in the ' + \
                rooms[roomID]['trap']['trapType'] + ' and escape'
            mud.sendMessage(
                id, randomDescription(desc) + '.\n\n')


def escapeFromTrap(mud, id, players: {}, rooms: {}, itemsDB: {}):
    """Attempt to escape from a trap
    """
    roomID = players[id]['room']
    if not rooms[roomID]['trap'].get('trapEscapeMethod'):
        mud.sendMessage(
            id, randomDescription("Nothing happens") + '.\n\n')
        return
    escapeMethod = rooms[roomID]['trap']['trapEscapeMethod']
    if 'slash' in escapeMethod:
        _escapeWithCuttingTool(mud, id, players, rooms, itemsDB)
    else:
        mud.sendMessage(
            id, randomDescription("Nothing happens") + '.\n\n')


def _trapActivationDescribe(mud, id, players, roomID, rooms,
                            penaltyValue, trapTag):
    trapType = rooms[roomID]['trap']['trapType']
    if trapType == 'net' or \
       trapType == 'chain net':
        if rooms[roomID]['trap']['trapActivation'].startswith('pressure'):
            desc = trapTag + \
                "You hear a click as you step onto a pressure plate. A " + \
                trapType + " falls from above and pins you down"
            mud.sendMessage(id, randomDescription(desc) + '.<r>\n\n')
        else:
            desc = trapTag + "A " + trapType + \
                " falls from above and pins you down"
            mud.sendMessage(id, randomDescription(desc) + '.<r>\n\n')
    elif trapType == 'pit' or trapType == 'tar pit':
        desc = trapTag + "You fall into a " + trapType
        mud.sendMessage(id, randomDescription(desc) + '.<r>\n\n')
    elif trapType == 'ditch' or trapType == 'marsh' or trapType == 'bog':
        desc = trapTag + "You fall into a muddy " + trapType + "|" + \
            trapTag + "You slip and fall into a muddy " + trapType
        mud.sendMessage(id, randomDescription(desc) + '.<r>\n\n')
    elif trapType.startswith('dart'):
        desc = trapTag + \
            "Poisoned darts emerge from holes in the wall and " + \
            "sting you for <r><f15><b88>* " + str(penaltyValue) + \
            " *<r>" + trapTag + " hit points"
        mud.sendMessage(id, randomDescription(desc) + '.<r>\n\n')


def trapActivation(mud, id, players: {}, rooms: {}, exitDirection):
    """Activates a trap
    """
    roomID = players[id]['room']
    if not rooms[roomID]['trap'].get('trapActivation'):
        return False
    # Is the trap already activated?
    if rooms[roomID]['trap']['trapActivationTime'] != 0:
        return False
    trapTag = '<f202>'

    # recognised activation type
    activationType = rooms[roomID]['trap']['trapActivation']
    if not (activationType == 'tripwire' or
            activationType.startswith('move') or
            activationType.startswith('pressure')):
        return False

    # probability of the trap being activated
    prob = 100
    if rooms[roomID]['trap'].get('trapActivationProbability'):
        prob = rooms[roomID]['trap']['trapActivationProbability']
    randPercent = randint(1, 100)
    if randPercent > prob:
        return False

    # which exit activates the trap?
    if not rooms[roomID]['trap'].get('trapExit'):
        return False

    # are we going in that direction?
    if rooms[roomID]['trap']['trapExit'] != exitDirection:
        return False

    # add player to the list of trapped ones
    rooms[roomID]['trap']['trappedPlayers'] = [players[id]['name']]

    # record the time when the trap was activated
    if TimeStringToSec(rooms[roomID]['trap']['trapDuration']) > 0:
        rooms[roomID]['trap']['trapActivationTime'] = \
            int(time.time())

    # reset the amount of damage to the trap
    rooms[roomID]['trap']['trapDamaged'] = 0

    # subtract a trap penalty from the player
    penaltyType = rooms[roomID]['trap']['trapPenaltyType']
    penaltyValue = randint(1, rooms[roomID]['trap']['trapPenalty'])
    players[id][penaltyType] -= penaltyValue

    # describe the trapped player
    if len(rooms[roomID]['trap']['trapActivationDescription']) > 0:
        desc = rooms[roomID]['trap']['trapActivationDescription']
        mud.sendMessage(id, trapTag +
                        randomDescription(desc) + '.<r>\n\n')
    else:
        _trapActivationDescribe(mud, id, players, roomID, rooms,
                                penaltyValue, trapTag)
    return True


def runTraps(mud, rooms: {}, players: {}, npcs: {}):
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
