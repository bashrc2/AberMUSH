__filename__ = "familiar.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

from functions import randomDescription
from copy import deepcopy

# Movement modes for familiars
familiarModes = ("follow", "scout", "hide", "see")


def getFamiliarModes():
    return familiarModes


def getFamiliarName(players, id, npcs):
    """Returns the name of the familiar of the given player
    """
    if players[id]['familiar'] != -1:
        for (nid, pl) in list(npcs.items()):
            if npcs[nid]['familiarOf'] == players[id]['name']:
                return npcs[nid]['name']
    return ''


def familiarRecall(mud, players, id, npcs, npcsDB):
    """Move any familiar to the player's location
    """
    # remove any existing familiars
    removals = []
    for (nid, pl) in list(npcs.items()):
        if pl['familiarOf'] == players[id]['name']:
            removals.append(nid)

    for index in removals:
        del npcs[index]

    # By default player has no familiar
    players[id]['familiar'] = -1

    # Find familiar and set its room to that of the player
    for (nid, pl) in list(npcsDB.items()):
        if pl['familiarOf'] == players[id]['name']:
            players[id]['familiar'] = int(nid)
            if not npcs.get(nid):
                npcs[nid] = deepcopy(npcsDB[nid])
            npcs[nid]['room'] = players[id]['room']
            mud.sendMessage(id, "Your familiar is recalled.\n\n")
            break


def familiarDefaultMode(nid, npcs, npcsDB):
    npcs[nid]['familiarMode'] = "follow"
    npcsDB[nid]['familiarMode'] = "follow"
    npcs[nid]['moveType'] = ""
    npcsDB[nid]['moveType'] = ""
    npcs[nid]['path'] = []
    npcsDB[nid]['path'] = []


def familiarSight(mud, nid, npcs, npcsDB, rooms, players, id, items, itemsDB):
    """familiar reports what it sees
    """
    startRoomID = npcs[nid]['room']
    roomExits = rooms[startRoomID]['exits']

    mud.sendMessage(id, "Your familiar says:\n")
    if len(roomExits) == 0:
        mud.sendMessage(id, "There are no exits.")
    else:
        if len(roomExits) > 1:
            mud.sendMessage(id, "There are " + str(len(roomExits)) +
                            " exits.")
        else:
            exitDescription = randomDescription("a single|one")
            mud.sendMessage(id, "There is " + exitDescription + " exit.")
    creaturesCount = 0
    creaturesFriendly = 0
    creaturesRaces = []
    for p in players:
        if players[p]['name'] is None:
            continue
        if players[p]['room'] == npcs[nid]['room']:
            creaturesCount = creaturesCount+1
            if players[p]['race'] not in creaturesRaces:
                creaturesRaces.append(players[p]['race'])
            for name, value in players[p]['affinity'].items():
                if npcs[nid]['familiarOf'] == name:
                    if value >= 0:
                        creaturesFriendly = creaturesFriendly + 1

    for n in npcs:
        if n != nid:
            if npcs[n]['room'] == npcs[nid]['room']:
                creaturesCount = creaturesCount+1
                if npcs[n].get('race'):
                    if npcs[n]['race'] not in creaturesRaces:
                        creaturesRaces.append(npcs[n]['race'])
                if npcs[n].get('affinity'):
                    for name, value in npcs[n]['affinity'].items():
                        if npcs[nid]['familiarOf'] == name:
                            if value >= 0:
                                creaturesFriendly = creaturesFriendly + 1

    if creaturesCount > 0:
        creatureStr = randomDescription("creature|being|entity")
        creaturesMsg = 'I see '
        if creaturesCount > 1:
            creaturesMsg = creaturesMsg + str(creaturesCount) + ' ' + \
                creatureStr + 's'
        else:
            creaturesMsg = creaturesMsg + 'one ' + creatureStr
        creaturesMsg = creaturesMsg + ' here.'

        friendlyWord = \
            randomDescription("friendly|nice|pleasing|not threatening")
        if creaturesFriendly > 0:
            if creaturesFriendly > 1:
                creaturesMsg = creaturesMsg + ' ' + \
                    str(creaturesFriendly) + ' are ' + friendlyWord + '.'
            else:
                if creaturesFriendly == creaturesCount:
                    creaturesMsg = \
                        creaturesMsg + ' They are ' + friendlyWord + '.'
                else:
                    creaturesMsg = \
                        creaturesMsg + ' One is ' + friendlyWord + '.'
        creaturesMsg = creaturesMsg + '\n'
        if len(creaturesRaces) > 0:
            creaturesMsg = creaturesMsg + 'They are '
            if len(creaturesRaces) == 1:
                creaturesMsg = \
                    creaturesMsg + '<f220>' + creaturesRaces[0] + 's<r>.'
            else:
                if len(creaturesRaces) == 2:
                    creaturesMsg = \
                        creaturesMsg + '<f220>' + creaturesRaces[0] + \
                        's<r> and <f220>' + creaturesRaces[1] + 's<r>.'
                else:
                    ctr = 0
                    for r in creaturesRaces:
                        if ctr == 0:
                            creaturesMsg = creaturesMsg + '<f220>' + r + 's<r>'
                        if ctr > 0:
                            if ctr < len(creaturesRaces) - 1:
                                creaturesMsg = \
                                    creaturesMsg + ', <f220>' + r + 's<r>'
                            else:
                                creaturesMsg = \
                                    creaturesMsg + ' and <f220>' + r + 's<r>.'
                        ctr = ctr + 1
        mud.sendMessage(id, creaturesMsg)

    itemsInRoom = 0
    weaponsInRoom = 0
    armorInRoom = 0
    edibleInRoom = 0
    for (iid, pl) in list(items.items()):
        if items[iid]['room'] == npcs[nid]['room']:
            if items[iid].get('weight'):
                if items[iid]['weight'] > 0:
                    itemsInRoom += 1
                    if (items[iid]['mod_str'] > 0 and
                        (items[iid]['clo_lhand'] > 0 or
                         items[iid]['clo_rhand'] > 0)):
                        weaponsInRoom += 1
                    if items[iid]['mod_endu'] > 0 and \
                       items[iid]['clo_chest'] > 0:
                        armorInRoom += 1
                    if items[iid]['edible'] != 0:
                        edibleInRoom += 1
    if armorInRoom > 0 and weaponsInRoom > 0:
        mud.sendMessage(id, 'There are some weapons and armor here.')
    else:
        if armorInRoom > 0:
            mud.sendMessage(id, 'There is some armor here.')
        else:
            if weaponsInRoom > 0:
                mud.sendMessage(id, 'There are some weapons here.')
            else:
                mud.sendMessage(id, 'There are some items here.')
    if edibleInRoom:
        mud.sendMessage(id, 'There are some edibles here.')
    mud.sendMessage(id, '\n\n')


def familiarHide(nid, npcs, npcsDB):
    """Causes a familiar to hide
    """
    npcs[nid]['familiarMode'] = "hide"
    npcsDB[nid]['familiarMode'] = "hide"


def familiarIsHidden(players, id, npcs):
    """Returns true if the familiar of the player is hidden
    """
    if players[id]['familiar'] != -1:
        for (nid, pl) in list(npcs.items()):
            if npcs[nid]['familiarOf'] == players[id]['name']:
                if npcs[nid]['familiarMode'] == 'hide':
                    return True
    return False


def familiarScoutAnyDirection(familiarSize, startRoomID, roomExits, rooms):
    """Scout in any direction
    """
    newPath = [startRoomID]
    for ex, rm in roomExits.items():
        if rooms[rm]['maxPlayerSize'] > -1:
            if familiarSize > rooms[rm]['maxPlayerSize']:
                continue
        newPath.append(rm)
        newPath.append(startRoomID)
    if len(newPath) == 1:
        newPath.clear()
    return newPath


def familiarScoutInDirection(mud, players, id, startRoomID, roomExits,
                             direction, rooms):
    """Scout in the given direction
    """
    newPath = []
    if roomExits.get(direction):
        if rooms[roomExits[direction]]['maxPlayerSize'] > -1:
            if players[id]['siz'] <= \
               rooms[roomExits[direction]]['maxPlayerSize']:
                newPath = [startRoomID, roomExits[direction]]
            else:
                mud.sendMessage(id, "It's too small to enter!\n\n")
        else:
            newPath = [startRoomID, roomExits[direction]]
    else:
        mud.sendMessage(id, "I can't go that way!\n\n")
    return newPath


def familiarScout(mud, players, id, nid, npcs, npcsDB, rooms, direction):
    """familiar begins scouting the surrounding rooms
    """
    startRoomID = npcs[nid]['room']
    roomExits = rooms[startRoomID]['exits']

    newPath = []

    if direction == 'any' or direction == 'all' or len(direction) == 0:
        newPath = \
            familiarScoutAnyDirection(npcs[nid]['siz'], startRoomID,
                                      roomExits, rooms)
    else:
        newPath = familiarScoutInDirection(mud, players, id, startRoomID,
                                           roomExits, direction, rooms)

    if len(newPath) > 0:
        npcs[nid]['familiarMode'] = "scout"
        npcs[nid]['moveType'] = "patrol"
        npcs[nid]['path'] = deepcopy(newPath)
        npcsDB[nid]['familiarMode'] = "scout"
        npcsDB[nid]['moveType'] = "patrol"
        npcsDB[nid]['path'] = deepcopy(newPath)
    else:
        familiarDefaultMode(nid, npcs, npcsDB)
