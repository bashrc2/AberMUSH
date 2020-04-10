__filename__ = "traps.py"
__author__ = "Bob Mottram"
__credits__ = [""]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

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

    if rooms[roomID]['trap']['trapType'] == 'net':
        desc = "You struggle with the net but it's pinning you down|" + \
            "You seem to be trapped in a net|Being covered by a net " + \
            "makes it difficult to move"
        mud.send_message(id, randomDescription(desc)+'.\n\n')

    if rooms[roomID]['trap']['trapType'] == 'chain net':
        desc = "You struggle with the net but its chain webbing is " + \
            "pinning you down|You seem to be trapped in a net made " + \
            "from linked chains|Being covered by a chain net makes " + \
            "it difficult to move"
        mud.send_message(id, randomDescription(desc)+'.\n\n')


def playerIsTrapped(id, players: {}, rooms: {}):
    """Returns true if the player is trapped
    """
    roomID = players[id]['room']
    if rooms[roomID].get('trap'):
        if rooms[roomID]['trap'].get('trappedPlayers'):
            if players[id]['name'] in rooms[roomID]['trap']['trappedPlayers']:
                return True
    return False


def describeTrapDeactivation(mud, roomID, trap, players: {}):
    """Describes when a trap gets reset
    """
    for id in players:
        if players[id]['name'] is None:
            continue
        if players[id]['room'] != roomID:
            continue
        if players[id]['name'] in trap['trappedPlayers']:
            if trap['trapType'] == 'net' or \
               trap['trapType'] == 'chain net':
                desc = 'The ' + trap['trapType'] + ' lifts and you escape'
                mud.send_message(id, randomDescription(desc)+'.\n\n')


def holdingCuttingWeapon(id, players: {}, itemsDB: {}):
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


def escapeWithCuttingTool(mud, id, players: {}, rooms: {}, itemsDB: {}):
    """Escape from a trap using a cutting tool
    """
    itemID = holdingCuttingWeapon(id, players, itemsDB)
    if itemID == -1:
        desc = "You attempt to escape with your bare hands, " + \
            "but remain trapped|You tug and wrestle but can't escape|" + \
            "Looks like you need to use a cutting tool, otherwise " + \
            "you'll be here for a while|Looks like you need something " + \
            "to cut with"
        mud.send_message(
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
        mud.send_message(id, randomDescription(desc) + '.\n\n')
    else:
        rooms[roomID]['trap']['trapDamaged'] = 0
        rooms[roomID]['trap']['trappedPlayers'].clear()
        if len(rooms[roomID]['trap']['trapEscapeDescription']) > 0:
            desc = rooms[roomID]['trap']['trapEscapeDescription']
            mud.send_message(id, randomDescription(desc) + '.\n\n')
        else:
            desc = 'You cut a large hole in the ' + \
                rooms[roomID]['trap']['trapType'] + ' and escape'
            mud.send_message(
                id, randomDescription(desc) + '.\n\n')


def escapeFromTrap(mud, id, players: {}, rooms: {}, itemsDB: {}):
    """Attempt to escape from a trap
    """
    roomID = players[id]['room']
    if not rooms[roomID]['trap'].get('trapEscapeMethod'):
        mud.send_message(
            id, randomDescription("Nothing happens") + '.\n\n')
        return
    escapeMethod = rooms[roomID]['trap']['trapEscapeMethod']
    if 'slash' in escapeMethod:
        escapeWithCuttingTool(mud, id, players, rooms, itemsDB)


def trapActivationDescribe(mud, id, players, roomID, rooms,
                           penaltyValue, trapTag):
    if rooms[roomID]['trap']['trapType'] == 'net' or \
       rooms[roomID]['trap']['trapType'] == 'chain net':
        if rooms[roomID]['trap']['trapActivation'].startswith('pressure'):
            desc = trapTag + \
                "You hear a click as you step onto a pressure plate. A " + \
                rooms[roomID]['trap']['trapType'] + \
                " falls from above and pins you down"
            mud.send_message(id, randomDescription(desc) + '.<r>\n\n')
        else:
            desc = trapTag + "A " + rooms[roomID]['trap']['trapType'] + \
                " falls from above and pins you down"
            mud.send_message(id, randomDescription(desc) + '.<r>\n\n')

    if rooms[roomID]['trap']['trapType'].startswith('dart'):
        desc = trapTag + \
            "Poisoned darts emerge from holes in the wall and " + \
            "sting you for <r><f15><b88>* " + str(penaltyValue) + \
            " *<r>" + trapTag + " hit points"
        mud.send_message(id, randomDescription(desc) + '.<r>\n\n')


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

    # tripwire
    if rooms[roomID]['trap']['trapActivation'] == 'tripwire':
        if rooms[roomID]['trap'].get('trapExit'):
            if rooms[roomID]['trap']['trapExit'] == exitDirection:
                rooms[roomID]['trap']['trappedPlayers'] = [players[id]['name']]
                if TimeStringToSec(rooms[roomID]['trap']['trapDuration']) > 0:
                    rooms[roomID]['trap']['trapActivationTime'] = \
                        int(time.time())
                rooms[roomID]['trap']['trapDamaged'] = 0
                penaltyType = rooms[roomID]['trap']['trapPenaltyType']
                penaltyValue = randint(1, rooms[roomID]['trap']['trapPenalty'])
                players[id][penaltyType] -= penaltyValue
                if len(rooms[roomID]['trap']['trapActivationDescription']) > 0:
                    desc = rooms[roomID]['trap']['trapActivationDescription']
                    mud.send_message(id, trapTag +
                                     randomDescription(desc) + '.<r>\n\n')
                else:
                    trapActivationDescribe(mud, id, players, roomID, rooms,
                                           penaltyValue, trapTag)
                return True

    # pressure plate
    if rooms[roomID]['trap']['trapActivation'].startswith('pressure'):
        if rooms[roomID]['trap'].get('trapExit'):
            if rooms[roomID]['trap']['trapExit'] == exitDirection:
                rooms[roomID]['trap']['trappedPlayers'] = [players[id]['name']]
                if TimeStringToSec(rooms[roomID]['trap']['trapDuration']) > 0:
                    rooms[roomID]['trap']['trapActivationTime'] = \
                        int(time.time())
                rooms[roomID]['trap']['trapDamaged'] = 0
                penaltyType = rooms[roomID]['trap']['trapPenaltyType']
                penaltyValue = randint(1, rooms[roomID]['trap']['trapPenalty'])
                players[id][penaltyType] -= penaltyValue
                if len(rooms[roomID]['trap']['trapActivationDescription']) > 0:
                    desc = rooms[roomID]['trap']['trapActivationDescription']
                    mud.send_message(id, trapTag +
                                     randomDescription(desc) + '.<r>\n\n')
                else:
                    trapActivationDescribe(mud, id, players, roomID, rooms,
                                           penaltyValue, trapTag)
                return True
    return False


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
            describeTrapDeactivation(mud, rm, rooms[rm]['trap'], players)
            rooms[rm]['trap']['trappedPlayers'].clear()
            rooms[rm]['trap']['trapActivationTime'] = 0
            rooms[rm]['trap']['trapDamaged'] = 0
