__filename__ = "commands.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Command Interface"

from functions import playerIsProne
from functions import setPlayerProne
from functions import wearLocation
from functions import isWearing
from functions import playerIsVisible
from functions import messageToPlayersInRoom
from functions import TimeStringToSec
from functions import addToScheduler
from functions import getFreeKey
from functions import getFreeRoomKey
from functions import hash_password
from functions import log
from functions import saveState
from functions import playerInventoryWeight
from functions import saveBlocklist
from functions import saveUniverse
from functions import updatePlayerAttributes
from functions import sizeFromDescription
from functions import stowHands
from functions import randomDescription
from functions import increaseAffinityBetweenPlayers
from functions import decreaseAffinityBetweenPlayers
from functions import getSentiment
from functions import getGuildSentiment
from environment import getRoomCulture
from environment import runTide
from environment import getRainAtCoords
from history import assignItemHistory
from traps import playerIsTrapped
from traps import describeTrappedPlayer
from traps import trapActivation
from traps import teleportFromTrap
from traps import escapeFromTrap
from combat import removePreparedSpell
from combat import healthOfPlayer
from combat import isAttacking
from combat import stopAttack
from combat import getAttackingTarget
from combat import playerBeginsAttack
from combat import isPlayerFighting
from chess import showChessBoard
from chess import initialChessBoard
from chess import moveChessPiece
from cards import dealToPlayers
from cards import showHandOfCards
from cards import swapCard
from cards import shuffleCards
from cards import callCards
from morris import showMorrisBoard
from morris import morrisMove
from morris import resetMorrisBoard
from morris import takeMorrisCounter
from morris import getMorrisBoardName

from proficiencies import thievesCant

from npcs import npcConversation
from npcs import getSolar

from markets import buyItem
from markets import marketBuysItemTypes
from markets import getMarketType

from familiar import getFamiliarName

import os
import re
import sys
# from copy import deepcopy
from functions import deepcopy
import time
import datetime
import os.path
from random import randint

import decimal
dec = decimal.Decimal


def _getMaxWeight(id, players: {}) -> int:
    """Returns the maximum weight which can be carried
    """
    strength = int(players[id]['str'])
    return strength * 15


def _prone(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
           envDB: {}, env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if playerIsTrapped(id, players, rooms):
        describeTrappedPlayer(mud, id, players, rooms)
        return

    if not playerIsProne(id, players):
        msgStr = 'You lie down<r>\n\n'
        mud.sendMessage(id, randomDescription(msgStr))
        setPlayerProne(id, players, True)
    else:
        msgStr = 'You are already lying down<r>\n\n'
        mud.sendMessage(id, randomDescription(msgStr))


def _stand(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
           envDB: {}, env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if playerIsTrapped(id, players, rooms):
        describeTrappedPlayer(mud, id, players, rooms)
        return

    if playerIsProne(id, players):
        msgStr = 'You stand up<r>\n\n'
        mud.sendMessage(id, randomDescription(msgStr))
        setPlayerProne(id, players, True)
    else:
        msgStr = 'You are already standing up<r>\n\n'
        mud.sendMessage(id, randomDescription(msgStr))


def _shove(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
           envDB: {}, env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if playerIsTrapped(id, players, rooms):
        describeTrappedPlayer(mud, id, players, rooms)
        return

    if playerIsProne(id, players):
        mud.sendMessage(id, randomDescription('You stand up<r>\n\n'))
        setPlayerProne(id, players, False)
        return

    if not isPlayerFighting(id, players, fights):
        mud.sendMessage(
            id,
            randomDescription('You try to shove, but to your surprise ' +
                              'discover that you are not in combat ' +
                              'with anyone.') +
            '\n\n')
        return

    if players[id]['canGo'] != 1:
        mud.sendMessage(
            id, randomDescription(
                "You try to shove, but don't seem to be able to move") +
            '\n\n')
        return

    mud.sendMessage(
        id, randomDescription(
            "You get ready to shove...") +
        '\n')
    players[id]['shove'] = 1


def _dodge(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
           envDB: {}, env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if playerIsTrapped(id, players, rooms):
        describeTrappedPlayer(mud, id, players, rooms)
        return

    if playerIsProne(id, players):
        mud.sendMessage(id, randomDescription('You stand up<r>\n\n'))
        setPlayerProne(id, players, False)
        return

    if not isPlayerFighting(id, players, fights):
        mud.sendMessage(
            id, randomDescription(
                "You try dodging, but then realize that you're not actually " +
                "fighting|You practice dodging an imaginary attacker") +
            '\n\n')
        return

    if players[id]['canGo'] != 1:
        mud.sendMessage(
            id, randomDescription(
                "You try to dodge, but don't seem to be able to move") +
            '\n\n')
        return

    mud.sendMessage(
        id, randomDescription(
            "Ok|Ok, here goes...") +
        '\n\n')
    players[id]['dodge'] = 1


def _removeItemFromClothing(players: {}, id: int, itemID: int) -> None:
    """If worn an item is removed
    """
    for c in wearLocation:
        if int(players[id]['clo_' + c]) == itemID:
            players[id]['clo_' + c] = 0


def _sendCommandError(params, mud, playersDB: {}, players: {}, rooms: {},
                      npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                      envDB: {}, env, eventDB: {}, eventSchedule, id: int,
                      fights: {}, corpses, blocklist, mapArea: [],
                      characterClassDB: {}, spellsDB: {},
                      sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                      itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    mud.sendMessage(id, "Unknown command " + str(params) + "!\n")


def _isWitch(id: int, players: {}) -> bool:
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


def _disableRegistrations(mud, id: int, players: {}) -> None:
    """Turns off new registrations
    """
    if not _isWitch(id, players):
        mud.sendMessage(id, "You don't have enough powers.\n\n")
        return
    if os.path.isfile(".disableRegistrations"):
        mud.sendMessage(id, "New registrations are already closed.\n\n")
        return
    with open(".disableRegistrations", 'w') as fp:
        fp.write('')
    mud.sendMessage(id, "New player registrations are now closed.\n\n")


def _enableRegistrations(mud, id: int, players: {}) -> None:
    """Turns on new registrations
    """
    if not _isWitch(id, players):
        mud.sendMessage(id, "You don't have enough powers.\n\n")
        return
    if not os.path.isfile(".disableRegistrations"):
        mud.sendMessage(id, "New registrations are already allowed.\n\n")
        return
    os.remove(".disableRegistrations")
    mud.sendMessage(id, "New player registrations are now permitted.\n\n")


def _teleport(params, mud, playersDB: {}, players: {}, rooms: {}, npcsDB: {},
              npcs: {}, itemsDB: {}, items: {}, envDB: {}, env, eventDB: {},
              eventSchedule, id: int, fights: {}, corpses: {}, blocklist,
              mapArea: [], characterClassDB: {}, spellsDB: {}, sentimentDB: {},
              guildsDB: {}, clouds: {}, racesDB: {},
              itemHistory: {}, markets: {}, culturesDB: {}) -> None:

    if players[id]['permissionLevel'] != 0:
        mud.sendMessage(id, "You don't have enough powers for that.\n\n")
        return

    if _isWitch(id, players):
        if playerIsTrapped(id, players, rooms):
            teleportFromTrap(mud, id, players, rooms)

        targetLocation = params[0:].strip().lower().replace('to ', '', 1)
        if len(targetLocation) != 0:
            currRoom = players[id]['room']
            if rooms[currRoom]['name'].strip().lower() == targetLocation:
                mud.sendMessage(
                    id, "You are already in " +
                    rooms[currRoom]['name'] +
                    "\n\n")
                return
            for rm in rooms:
                if rooms[rm]['name'].strip().lower() == targetLocation:
                    if isAttacking(players, id, fights):
                        stopAttack(players, id, npcs, fights)
                    mud.sendMessage(
                        id, "You teleport to " + rooms[rm]['name'] + "\n\n")
                    pName = players[id]['name']
                    desc = '<f32>{}<r> suddenly vanishes.'.format(pName)
                    messageToPlayersInRoom(mud, players, id, desc + "\n\n")
                    players[id]['room'] = rm
                    desc = '<f32>{}<r> suddenly appears.'.format(pName)

                    messageToPlayersInRoom(mud, players, id, desc + "\n\n")
                    _look('', mud, playersDB, players, rooms, npcsDB, npcs,
                          itemsDB, items, envDB, env, eventDB, eventSchedule,
                          id, fights, corpses, blocklist, mapArea,
                          characterClassDB, spellsDB, sentimentDB,
                          guildsDB, clouds, racesDB, itemHistory, markets,
                          culturesDB)
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
                    mud.sendMessage(
                        id, "You teleport to " + rooms[rm]['name'] + "\n\n")
                    messageToPlayersInRoom(mud, players, id, desc1 + "\n\n")
                    players[id]['room'] = rm
                    messageToPlayersInRoom(mud, players, id, desc2 + "\n\n")
                    _look('', mud, playersDB, players, rooms, npcsDB, npcs,
                          itemsDB, items, envDB, env, eventDB, eventSchedule,
                          id, fights, corpses, blocklist, mapArea,
                          characterClassDB, spellsDB, sentimentDB,
                          guildsDB, clouds, racesDB, itemHistory, markets,
                          culturesDB)
                    return

            mud.sendMessage(
                id, targetLocation +
                " isn't a place you can teleport to.\n\n")
        else:
            mud.sendMessage(id, "That's not a place.\n\n")
    else:
        mud.sendMessage(id, "You don't have enough powers to teleport.\n\n")


def _summon(params, mud, playersDB: {}, players: {}, rooms: {}, npcsDB: {},
            npcs: {}, itemsDB: {}, items: {}, envDB: {}, env, eventDB: {},
            eventSchedule, id: int, fights: {}, corpses: {}, blocklist,
            mapArea: [], characterClassDB: {}, spellsDB: {},
            sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
            itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    if players[id]['permissionLevel'] == 0:
        if _isWitch(id, players):
            targetPlayer = params[0:].strip().lower()
            if len(targetPlayer) != 0:
                for p in players:
                    if players[p]['name'].strip().lower() == targetPlayer:
                        if players[p]['room'] != players[id]['room']:
                            pNam = players[p]['name']
                            desc = '<f32>{}<r> suddenly vanishes.'.format(pNam)
                            messageToPlayersInRoom(mud, players, p,
                                                   desc + "\n")
                            players[p]['room'] = players[id]['room']
                            rm = players[p]['room']
                            mud.sendMessage(id, "You summon " +
                                            players[p]['name'] + "\n\n")
                            mud.sendMessage(p,
                                            "A mist surrounds you. When it " +
                                            "clears you find that you " +
                                            "are now in " +
                                            rooms[rm]['name'] + "\n\n")
                        else:
                            mud.sendMessage(
                                id, players[p]['name'] +
                                " is already here.\n\n")
                        return
        else:
            mud.sendMessage(id, "You don't have enough powers for that.\n\n")


def _mute(params, mud, playersDB: {}, players: {}, rooms: {}, npcsDB: {},
          npcs: {}, itemsDB: {}, items: {}, envDB: {}, env, eventDB: {},
          eventSchedule, id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    if players[id]['permissionLevel'] != 0:
        mud.sendMessage(
            id, "You aren't capable of doing that.\n\n")
        return
    if not _isWitch(id, players):
        mud.sendMessage(
            id, "You aren't capable of doing that.\n\n")
        return
    target = params.partition(' ')[0]
    if len(target) != 0:
        for p in players:
            if players[p]['name'] == target:
                if not _isWitch(p, players):
                    players[p]['canSay'] = 0
                    players[p]['canAttack'] = 0
                    players[p]['canDirectMessage'] = 0
                    mud.sendMessage(
                        id, "You have muted " + target + "\n\n")
                else:
                    mud.sendMessage(
                        id, "You try to mute " + target +
                        " but their power is too strong.\n\n")
                return


def _unmute(params, mud, playersDB: {}, players: {}, rooms: {}, npcsDB: {},
            npcs: {}, itemsDB: {}, items: {}, envDB: {}, env, eventDB: {},
            eventSchedule, id: int, fights: {}, corpses: {}, blocklist,
            mapArea: [], characterClassDB: {}, spellsDB: {},
            sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
            itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    if players[id]['permissionLevel'] != 0:
        mud.sendMessage(
            id, "You aren't capable of doing that.\n\n")
        return
    if not _isWitch(id, players):
        mud.sendMessage(
            id, "You aren't capable of doing that.\n\n")
        return
    target = params.partition(' ')[0]
    if len(target) != 0:
        if target.lower() != 'guest':
            for p in players:
                if players[p]['name'] == target:
                    if not _isWitch(p, players):
                        players[p]['canSay'] = 1
                        players[p]['canAttack'] = 1
                        players[p]['canDirectMessage'] = 1
                        mud.sendMessage(
                            id, "You have unmuted " + target + "\n\n")
                    return


def _freeze(params, mud, playersDB: {}, players: {}, rooms: {}, npcsDB: {},
            npcs: {}, itemsDB: {}, items: {}, envDB: {}, env, eventDB: {},
            eventSchedule, id: int, fights: {}, corpses: {}, blocklist,
            mapArea: [], characterClassDB: {}, spellsDB: {},
            sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
            itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['permissionLevel'] == 0:
        if _isWitch(id, players):
            target = params.partition(' ')[0]
            if len(target) != 0:
                # freeze players
                for p in players:
                    if players[p]['whenDied']:
                        mud.sendMessage(
                            id,
                            "Freezing a player while dead is pointless\n\n")
                        continue
                    if players[p]['frozenStart'] > 0:
                        mud.sendMessage(
                            id, "They are already frozen\n\n")
                        continue
                    if target in players[p]['name']:
                        if not _isWitch(p, players):
                            # remove from any fights
                            for (fight, pl) in fights.items():
                                if fights[fight]['s1id'] == p or \
                                   fights[fight]['s2id'] == p:
                                    del fights[fight]
                                    players[p]['isInCombat'] = 0
                            players[p]['canGo'] = 0
                            players[p]['canAttack'] = 0
                            mud.sendMessage(
                                id, "You have frozen " + target + "\n\n")
                        else:
                            mud.sendMessage(
                                id, "You try to freeze " + target +
                                " but their power is too strong.\n\n")
                        return
                # freeze npcs
                for p in npcs:
                    if npcs[p]['whenDied']:
                        mud.sendMessage(
                            id, "Freezing while dead is pointless\n\n")
                        continue
                    if npcs[p]['frozenStart'] > 0:
                        mud.sendMessage(
                            id, "They are already frozen\n\n")
                        continue
                    if target in npcs[p]['name']:
                        if not _isWitch(p, npcs):
                            # remove from any fights
                            for (fight, pl) in fights.items():
                                if fights[fight]['s1id'] == p or \
                                   fights[fight]['s2id'] == p:
                                    del fights[fight]
                                    npcs[p]['isInCombat'] = 0

                            npcs[p]['canGo'] = 0
                            npcs[p]['canAttack'] = 0
                            mud.sendMessage(
                                id, "You have frozen " + target + "\n\n")
                        else:
                            mud.sendMessage(
                                id, "You try to freeze " + target +
                                " but their power is too strong.\n\n")
                        return


def _unfreeze(params, mud, playersDB: {}, players: {}, rooms: {},
              npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
              envDB: {}, env: {}, eventDB: {}, eventSchedule,
              id: int, fights: {}, corpses: {}, blocklist,
              mapArea: [], characterClassDB: {}, spellsDB: {},
              sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
              itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['permissionLevel'] == 0:
        if _isWitch(id, players):
            target = params.partition(' ')[0]
            if len(target) != 0:
                if target.lower() != 'guest':
                    # unfreeze players
                    for p in players:
                        if target in players[p]['name']:
                            if not _isWitch(p, players):
                                players[p]['canGo'] = 1
                                players[p]['canAttack'] = 1
                                players[p]['frozenStart'] = 0
                                mud.sendMessage(
                                    id, "You have unfrozen " + target + "\n\n")
                            return
                    # unfreeze npcs
                    for p in npcs:
                        if target in npcs[p]['name']:
                            if not _isWitch(p, npcs):
                                npcs[p]['canGo'] = 1
                                npcs[p]['canAttack'] = 1
                                npcs[p]['frozenStart'] = 0
                                mud.sendMessage(
                                    id, "You have unfrozen " + target + "\n\n")
                            return


def _showBlocklist(params, mud, playersDB: {}, players: {}, rooms: {},
                   npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                   envDB: {}, env: {}, eventDB: {}, eventSchedule,
                   id: int, fights: {}, corpses: {}, blocklist,
                   mapArea: [], characterClassDB: {}, spellsDB: {},
                   sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                   itemHistory: {}, markets: {}, culturesDB: {}):
    if not _isWitch(id, players):
        mud.sendMessage(id, "You don't have sufficient powers to do that.\n")
        return

    blocklist.sort()

    blockStr = ''
    for blockedstr in blocklist:
        blockStr = blockStr + blockedstr + '\n'

    mud.sendMessage(id, "Blocked strings are:\n\n" + blockStr + '\n')


def _block(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB: {},
           env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    if not _isWitch(id, players):
        mud.sendMessage(id, "You don't have sufficient powers to do that.\n")
        return

    if len(params) == 0:
        _showBlocklist(params, mud, playersDB, players, rooms, npcsDB, npcs,
                       itemsDB, items, envDB, env, eventDB, eventSchedule,
                       id, fights, corpses, blocklist, mapArea,
                       characterClassDB, spellsDB, sentimentDB, guildsDB,
                       clouds, racesDB, itemHistory, markets, culturesDB)
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
        saveBlocklist("blocked.txt", blocklist)
        mud.sendMessage(id, "Blocklist updated.\n\n")
    else:
        mud.sendMessage(id, "That's already in the blocklist.\n")


def _unblock(params, mud, playersDB: {}, players: {}, rooms: {}, npcsDB: {},
             npcs: {}, itemsDB: {}, items: {}, envDB: {}, env: {},
             eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: [], characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
    if not _isWitch(id, players):
        mud.sendMessage(id, "You don't have sufficient powers to do that.\n")
        return

    if len(params) == 0:
        _showBlocklist(params, mud, playersDB, players, rooms, npcsDB,
                       npcs, itemsDB, items, envDB, env, eventDB,
                       eventSchedule,
                       id, fights, corpses, blocklist, mapArea,
                       characterClassDB, spellsDB, sentimentDB, guildsDB,
                       clouds, racesDB, itemHistory, markets, culturesDB)
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
        saveBlocklist("blocked.txt", blocklist)
        mud.sendMessage(id, "Blocklist updated.\n\n")
    else:
        mud.sendMessage(id, "That's not in the blocklist.\n")


def _kick(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    if not _isWitch(id, players):
        mud.sendMessage(id, "You don't have enough powers.\n\n")
        return

    playerName = params

    if len(playerName) == 0:
        mud.sendMessage(id, "Who?\n\n")
        return

    for (pid, pl) in list(players.items()):
        if players[pid]['name'] == playerName:
            mud.sendMessage(id, "Removing player " + playerName + "\n\n")
            mud.handleDisconnect(pid)
            return

    mud.sendMessage(id, "There are no players with that name.\n\n")


def _shutdown(params, mud, playersDB: {}, players: {}, rooms: {},
              npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
              envDB: {}, env: {}, eventDB: {}, eventSchedule,
              id: int, fights: {}, corpses: {}, blocklist,
              mapArea: [], characterClassDB: {}, spellsDB: {},
              sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
              itemHistory: {}, markets: {}, culturesDB: {}):
    if not _isWitch(id, players):
        mud.sendMessage(id, "You don't have enough power to do that.\n\n")
        return

    mud.sendMessage(id, "\n\nShutdown commenced.\n\n")
    saveUniverse(rooms, npcsDB, npcs, itemsDB, items, envDB, env, guildsDB)
    mud.sendMessage(id, "\n\nUniverse saved.\n\n")
    log("Universe saved", "info")
    for (pid, pl) in list(players.items()):
        mud.sendMessage(pid, "Game server shutting down...\n\n")
        mud.handleDisconnect(pid)
    log("Shutting down", "info")
    sys.exit()


def _resetUniverse(params, mud, playersDB: {}, players: {}, rooms: {},
                   npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                   envDB: {}, env: {}, eventDB: {}, eventSchedule,
                   id: int, fights: {}, corpses: {}, blocklist,
                   mapArea: [], characterClassDB: {}, spellsDB,
                   sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                   itemHistory: {}, markets: {}, culturesDB: {}):
    if not _isWitch(id, players):
        mud.sendMessage(id, "You don't have enough power to do that.\n\n")
        return
    os.system('rm universe*.json')
    log('Universe reset', 'info')
    for (pid, pl) in list(players.items()):
        mud.sendMessage(pid, "Game server shutting down...\n\n")
        mud.handleDisconnect(pid)
    log("Shutting down", "info")
    sys.exit()


def _quit(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    mud.handleDisconnect(id)


def _who(params, mud, playersDB: {}, players: {}, rooms: {},
         npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
         envDB: {}, env: {}, eventDB: {}, eventSchedule,
         id: int, fights: {}, corpses: {}, blocklist,
         mapArea: [], characterClassDB: {}, spellsDB,
         sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
         itemHistory: {}, markets: {}, culturesDB: {}):
    counter = 1
    if players[id]['permissionLevel'] == 0:
        is_witch = _isWitch(id, players)
        for p in players:
            if players[p]['name'] is None:
                continue

            if not is_witch:
                name = players[p]['name']
            else:
                if not _isWitch(p, players):
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

            mud.sendMessage(id, str(counter) + ". " + name + " is in " + room)
            counter += 1
        mud.sendMessage(id, "\n")
    else:
        mud.sendMessage(id, "You do not have permission to do this.\n")


def _tell(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    told = False
    target = params.partition(' ')[0]

    # replace "familiar" with their NPC name
    # as in: "ask familiar to follow"
    if target.lower() == 'familiar':
        newTarget = getFamiliarName(players, id, npcs)
        if len(newTarget) > 0:
            target = newTarget

    message = params.replace(target, "")[1:]
    if len(target) != 0 and len(message) != 0:
        cantStr = thievesCant(message)
        for p in players:
            if players[p]['authenticated'] is not None and \
               players[p]['name'].lower() == target.lower():
                # print("sending a tell")
                if players[id]['name'].lower() == target.lower():
                    mud.sendMessage(
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
                            addToScheduler(
                                "0|msg|<f90>From " +
                                players[id]['name'] +
                                ": " + message +
                                '\n', p, eventSchedule,
                                eventDB)
                            sentimentScore = \
                                getSentiment(message, sentimentDB) + \
                                getGuildSentiment(players, id, players,
                                                  p, guildsDB)
                            if sentimentScore >= 0:
                                increaseAffinityBetweenPlayers(
                                    players, id, players, p, guildsDB)
                            else:
                                decreaseAffinityBetweenPlayers(
                                    players, id, players, p, guildsDB)
                        else:
                            if players[id]['speakLanguage'] != 'cant':
                                addToScheduler(
                                    "0|msg|<f90>From " +
                                    players[id]['name'] +
                                    ": something in " +
                                    players[id]['speakLanguage'] +
                                    '\n', p, eventSchedule,
                                    eventDB)
                            else:
                                addToScheduler(
                                    "0|msg|<f90>From " +
                                    players[id]['name'] +
                                    ": " + cantStr +
                                    '\n', p, eventSchedule,
                                    eventDB)
                    mud.sendMessage(
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
                        npcConversation(mud, npcs, npcsDB, players,
                                        items, itemsDB, rooms, id,
                                        nid, messageLower,
                                        characterClassDB,
                                        sentimentDB, guildsDB,
                                        clouds, racesDB, itemHistory,
                                        culturesDB)
                        told = True
                        break

        if not told:
            mud.sendMessage(
                id, "<f32>" + target +
                "<r> does not appear to be reachable at this moment.\n\n")
    else:
        mud.sendMessage(id, "Huh?\n\n")


def _whisper(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
             envDB: {}, env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: [], characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
    target = params.partition(' ')[0]
    message = params.replace(target, "")

    # if message[0] == " ":
    # message.replace(message[0], "")
    messageSent = False
    # print(message)
    # print(str(len(message)))
    if len(target) > 0:
        if len(message) > 0:
            cantStr = thievesCant(message)
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
                                getSentiment(message[1:], sentimentDB) + \
                                getGuildSentiment(players, id, players,
                                                  p, guildsDB)
                            if sentimentScore >= 0:
                                increaseAffinityBetweenPlayers(
                                    players, id, players, p, guildsDB)
                            else:
                                decreaseAffinityBetweenPlayers(
                                    players, id, players, p, guildsDB)

                            mud.sendMessage(
                                id, "You whisper to <f32>" +
                                players[p]['name'] + "<r>: " +
                                message[1:] + '\n')
                            if not selfOnly:
                                langList = players[p]['language']
                                if players[id]['speakLanguage'] in langList:
                                    mud.sendMessage(
                                        p, "<f162>" + players[id]['name'] +
                                        " whispers: " + message[1:] + '\n')
                                else:
                                    if players[id]['speakLanguage'] != 'cant':
                                        mud.sendMessage(
                                            p, "<f162>" +
                                            players[id]['name'] +
                                            " whispers something in " +
                                            players[id]['speakLanguage'] +
                                            '\n')
                                    else:
                                        mud.sendMessage(
                                            p, "<f162>" + players[id]['name'] +
                                            " whispers:  " + cantStr + '\n')
                            messageSent = True
                            break
                        else:
                            mud.sendMessage(
                                id, "You would probably look rather silly " +
                                "whispering to yourself.\n")
                            messageSent = True
                            break
            if not messageSent:
                mud.sendMessage(
                    id, "<f32>" + target + "<r> is not here with you.\n")
        else:
            mud.sendMessage(id, "What would you like to whisper?\n")
    else:
        mud.sendMessage(id, "Who would you like to whisper to??\n")


def _help(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB,
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    if params.lower().startswith('card'):
        _helpCards(params, mud, playersDB, players,
                   rooms, npcsDB, npcs, itemsDB,
                   items, envDB, env, eventDB, eventSchedule,
                   id, fights, corpses,
                   blocklist, mapArea, characterClassDB,
                   spellsDB, sentimentDB, guildsDB, clouds, racesDB,
                   itemHistory, markets, culturesDB)
        return
    if params.lower().startswith('chess'):
        _helpChess(params, mud, playersDB, players,
                   rooms, npcsDB, npcs, itemsDB,
                   items, envDB, env, eventDB,
                   eventSchedule, id, fights, corpses,
                   blocklist, mapArea, characterClassDB,
                   spellsDB, sentimentDB, guildsDB, clouds, racesDB,
                   itemHistory, markets, culturesDB)
        return
    if params.lower().startswith('morris'):
        _helpMorris(params, mud, playersDB, players,
                    rooms, npcsDB, npcs, itemsDB,
                    items, envDB, env, eventDB,
                    eventSchedule, id, fights, corpses,
                    blocklist, mapArea, characterClassDB,
                    spellsDB, sentimentDB,
                    guildsDB, clouds, racesDB, itemHistory, markets,
                    culturesDB)
        return
    if params.lower().startswith('witch'):
        _helpWitch(params, mud, playersDB, players,
                   rooms, npcsDB, npcs, itemsDB,
                   items, envDB, env, eventDB,
                   eventSchedule, id, fights, corpses,
                   blocklist, mapArea, characterClassDB,
                   spellsDB, sentimentDB, guildsDB, clouds, racesDB,
                   itemHistory, markets, culturesDB)
        return
    if params.lower().startswith('spell'):
        _helpSpell(params, mud, playersDB, players,
                   rooms, npcsDB, npcs, itemsDB,
                   items, envDB, env, eventDB, eventSchedule,
                   id, fights, corpses,
                   blocklist, mapArea, characterClassDB,
                   spellsDB, sentimentDB, guildsDB, clouds, racesDB,
                   itemHistory, markets, culturesDB)
        return
    if params.lower().startswith('emot'):
        _helpEmote(params, mud, playersDB, players,
                   rooms, npcsDB, npcs, itemsDB,
                   items, envDB, env, eventDB, eventSchedule,
                   id, fights, corpses,
                   blocklist, mapArea, characterClassDB,
                   spellsDB, sentimentDB, guildsDB, clouds, racesDB,
                   itemHistory, markets, culturesDB)
        return

    mud.sendMessage(id, '****CLEAR****\n')
    mud.sendMessage(id, 'Commands:')
    mud.sendMessage(id,
                    '  <f220>help witch|spell|emote|cards|chess|morris<f255>' +
                    '     - Show help')
    mud.sendMessage(id,
                    '  <f220>bio [description]<f255>' +
                    '                       - ' +
                    'Set a description of yourself')
    mud.sendMessage(id,
                    '  <f220>graphics [on|off]<f255>' +
                    '                       - ' +
                    'Turn graphic content on or off')
    mud.sendMessage(id,
                    '  <f220>change password [newpassword]<f255>' +
                    '           - ' +
                    'Change your password')
    mud.sendMessage(id,
                    '  <f220>who<f255>' +
                    '                                     - ' +
                    'List players and where they are')
    mud.sendMessage(id,
                    '  <f220>quit/exit<f255>' +
                    '                               - ' +
                    'Leave the game')
    mud.sendMessage(id,
                    '  <f220>eat/drink [item]<f255>' +
                    '                        - ' +
                    'Eat or drink a consumable')
    mud.sendMessage(id,
                    '  <f220>speak [language]<f255>' +
                    '                        - ' +
                    'Switch to speaking a different language')
    mud.sendMessage(id,
                    '  <f220>say [message]<f255>' +
                    '                           - ' +
                    'Says something out loud, ' +
                    "e.g. 'say Hello'")
    mud.sendMessage(id,
                    '  <f220>look/examine<f255>' +
                    '                            - ' +
                    'Examines the ' +
                    "surroundings, items in the room, NPCs or other " +
                    "players e.g. 'examine inn-keeper'")
    mud.sendMessage(id,
                    '  <f220>go [exit]<f255>' +
                    '                               - ' +
                    'Moves through the exit ' +
                    "specified, e.g. 'go outside'")
    mud.sendMessage(id,
                    '  <f220>climb though/up [exit]<f255>' +
                    '                  - ' +
                    'Try to climb through/up an exit')
    mud.sendMessage(id,
                    '  <f220>move/roll/heave [target]<f255>' +
                    '                - ' +
                    'Try to move or roll a heavy object')
    mud.sendMessage(id,
                    '  <f220>jump to [exit]<f255>' +
                    '                          - ' +
                    'Try to jump onto something')
    mud.sendMessage(id,
                    '  <f220>attack [target]<f255>' +
                    '                         - ' +
                    'Attack target ' +
                    "specified, e.g. 'attack knight'")
    mud.sendMessage(id,
                    '  <f220>shove<f255>' +
                    '                                   - ' +
                    'Try to knock a target over ' +
                    'during an attack')
    mud.sendMessage(id,
                    '  <f220>prone<f255>' +
                    '                                   - ' +
                    'Lie down')
    mud.sendMessage(id,
                    '  <f220>stand<f255>' +
                    '                                   - ' +
                    'Stand up')
    mud.sendMessage(id,
                    '  <f220>check inventory<f255>' +
                    '                         - ' +
                    'Check the contents of ' +
                    "your inventory")
    mud.sendMessage(id,
                    '  <f220>take/get [item]<f255>' +
                    '                         - ' +
                    'Pick up an item lying ' +
                    "on the floor")
    mud.sendMessage(id,
                    '  <f220>put [item] in/on [item]<f255>' +
                    '                 - ' +
                    'Put an item into or onto another one')
    mud.sendMessage(id,
                    '  <f220>drop [item]<f255>' +
                    '                             - ' +
                    'Drop an item from your inventory ' +
                    "on the floor")
    mud.sendMessage(id,
                    '  <f220>use/hold/pick/wield [item] ' +
                    '[left|right]<f255> - ' +
                    'Transfer an item to your hands')
    mud.sendMessage(id,
                    '  <f220>stow<f255>' +
                    '                                    - ' +
                    'Free your hands of items')
    mud.sendMessage(id,
                    '  <f220>wear [item]<f255>' +
                    '                             - ' +
                    'Wear an item')
    mud.sendMessage(id,
                    '  <f220>remove/unwear [item]<f255>' +
                    '                    - ' +
                    'Remove a worn item')
    mud.sendMessage(id,
                    '  <f220>whisper [target] [message]<f255>' +
                    '              - ' +
                    'Whisper to a player in the same room')
    mud.sendMessage(id,
                    '  <f220>tell/ask [target] [message]<f255>' +
                    '             - ' +
                    'Send a tell message to another player or NPC')
    mud.sendMessage(id,
                    '  <f220>open [item]<f255>' +
                    '                             - ' +
                    'Open an item or door')
    mud.sendMessage(id,
                    '  <f220>close [item]<f255>' +
                    '                            - ' +
                    'Close an item or door')
    mud.sendMessage(id,
                    '  <f220>push [item]<f255>' +
                    '                             - ' +
                    'Pushes a lever')
    mud.sendMessage(id,
                    '  <f220>pull [item]<f255>' +
                    '                             - ' +
                    'Pulls a lever')
    mud.sendMessage(id,
                    '  <f220>wind [item]<f255>' +
                    '                             - ' +
                    'Winds a lever')
    mud.sendMessage(id,
                    '  <f220>affinity [player name]<f255>' +
                    '                  - ' +
                    'Shows your affinity level with another player')
    mud.sendMessage(id,
                    '  <f220>cut/escape<f255>' +
                    '                              - ' +
                    'Attempt to escape from a trap')
    mud.sendMessage(id,
                    '  <f220>step over tripwire [exit]<f255>' +
                    '               - ' +
                    'Step over a tripwire in the given direction')
    mud.sendMessage(id,
                    '  <f220>dodge<f255>' +
                    '                                   - ' +
                    'Dodge an attacker on the next combat round')
    mud.sendMessage(id, '\n\n')


def _helpSpell(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    mud.sendMessage(id, '\n')
    mud.sendMessage(id,
                    '<f220>prepare spells<f255>' +
                    '                          - ' +
                    'List spells which can be prepared')
    mud.sendMessage(id,
                    '<f220>prepare [spell name]<f255>' +
                    '                    - ' +
                    'Prepares a spell')
    mud.sendMessage(id,
                    '<f220>spells<f255>' +
                    '                                  - ' +
                    'Lists your prepared spells')
    mud.sendMessage(id,
                    '<f220>clear spells<f255>' +
                    '                            - ' +
                    'Clears your prepared spells list')
    mud.sendMessage(id,
                    '<f220>cast find familiar<f255>' +
                    '                      - ' +
                    'Summons a familiar with random form')
    mud.sendMessage(id,
                    '<f220>dismiss familiar<f255>' +
                    '                        - ' +
                    'Dismisses a familiar')
    mud.sendMessage(id,
                    '<f220>cast [spell name] on [target]<f255>' +
                    '           - ' +
                    'Cast a spell on a player or NPC')

    mud.sendMessage(id, '\n\n')


def _helpEmote(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    mud.sendMessage(id, '\n')
    mud.sendMessage(id, '<f220>applaud<f255>')
    mud.sendMessage(id, '<f220>astonished<f255>')
    mud.sendMessage(id, '<f220>bow<f255>')
    mud.sendMessage(id, '<f220>confused<f255>')
    mud.sendMessage(id, '<f220>calm<f255>')
    mud.sendMessage(id, '<f220>cheer<f255>')
    mud.sendMessage(id, '<f220>curious<f255>')
    mud.sendMessage(id, '<f220>curtsey<f255>')
    mud.sendMessage(id, '<f220>eyebrow<f255>')
    mud.sendMessage(id, '<f220>frown<f255>')
    mud.sendMessage(id, '<f220>giggle<f255>')
    mud.sendMessage(id, '<f220>grin<f255>')
    mud.sendMessage(id, '<f220>laugh<f255>')
    mud.sendMessage(id, '<f220>relieved<f255>')
    mud.sendMessage(id, '<f220>smug<f255>')
    mud.sendMessage(id, '<f220>think<f255>')
    mud.sendMessage(id, '<f220>wave<f255>')
    mud.sendMessage(id, '<f220>yawn<f255>')
    mud.sendMessage(id, '\n\n')


def _helpWitch(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    mud.sendMessage(id, '\n')
    if not _isWitch(id, players):
        mud.sendMessage(id, "You're not a witch.\n\n")
        return
    mud.sendMessage(id,
                    '<f220>close registrations<f255>' +
                    '                     - ' +
                    'Closes registrations of new players')
    mud.sendMessage(id,
                    '<f220>open registrations<f255>' +
                    '                      - ' +
                    'Allows registrations of new players')
    mud.sendMessage(id,
                    '<f220>mute/silence [target]<f255>' +
                    '                   - ' +
                    'Mutes a player and prevents them from attacking')
    mud.sendMessage(id,
                    '<f220>unmute/unsilence [target]<f255>' +
                    '               - ' +
                    'Unmutes a player')
    mud.sendMessage(id,
                    '<f220>freeze [target]<f255>' +
                    '                         - ' +
                    'Prevents a player from moving or attacking')
    mud.sendMessage(id,
                    '<f220>unfreeze [target]<f255>' +
                    '                       - ' +
                    'Allows a player to move or attack')
    mud.sendMessage(id,
                    '<f220>teleport [room]<f255>' +
                    '                         - ' +
                    'Teleport to a room')
    mud.sendMessage(id,
                    '<f220>summon [target]<f255>' +
                    '                         - ' +
                    'Summons a player to your location')
    mud.sendMessage(id,
                    '<f220>kick/remove [target]<f255>' +
                    '                    - ' +
                    'Remove a player from the game')
    mud.sendMessage(id,
                    '<f220>blocklist<f255>' +
                    '                               - ' +
                    'Show the current blocklist')
    mud.sendMessage(id,
                    '<f220>block [word or phrase]<f255>' +
                    '                  - ' +
                    'Adds a word or phrase to the blocklist')
    mud.sendMessage(id,
                    '<f220>unblock [word or phrase]<f255>' +
                    '                - ' +
                    'Removes a word or phrase to the blocklist')
    mud.sendMessage(id,
                    '<f220>describe "room" "room name"<f255>' +
                    '             - ' +
                    'Changes the name of the current room')
    mud.sendMessage(id,
                    '<f220>describe "room description"<f255>' +
                    '             - ' +
                    'Changes the current room description')
    mud.sendMessage(id,
                    '<f220>describe "tide" "room description"<f255>' +
                    '      - ' +
                    'Changes the room description when tide is out')
    mud.sendMessage(id,
                    '<f220>describe "item" "item description"<f255>' +
                    '      - ' +
                    'Changes the description of an item in the room')
    mud.sendMessage(id,
                    '<f220>describe "NPC" "NPC description"<f255>' +
                    '        - ' +
                    'Changes the description of an NPC in the room')
    mud.sendMessage(id,
                    '<f220>conjure room [direction]<f255>' +
                    '                - ' +
                    'Creates a new room in the given direction')
    mud.sendMessage(id,
                    '<f220>conjure npc [target]<f255>' +
                    '                    - ' +
                    'Creates a named NPC in the room')
    mud.sendMessage(id,
                    '<f220>conjure [item]<f255>' +
                    '                          - ' +
                    'Creates a new item in the room')
    mud.sendMessage(id,
                    '<f220>destroy room [direction]<f255>' +
                    '                - ' +
                    'Removes the room in the given direction')
    mud.sendMessage(id,
                    '<f220>destroy npc [target]<f255>' +
                    '                    - ' +
                    'Removes a named NPC from the room')
    mud.sendMessage(id,
                    '<f220>destroy [item]<f255>' +
                    '                          - ' +
                    'Removes an item from the room')
    mud.sendMessage(id,
                    '<f220>resetuniverse<f255>' +
                    '                           - ' +
                    'Resets the universe, losing any changes from defaults')
    mud.sendMessage(id,
                    '<f220>shutdown<f255>' +
                    '                                - ' +
                    'Shuts down the game server')
    mud.sendMessage(id, '\n\n')


def _helpMorris(params, mud, playersDB: {}, players: {}, rooms,
                npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                envDB: {}, env: {}, eventDB: {}, eventSchedule,
                id: int, fights: {}, corpses: {}, blocklist,
                mapArea: [], characterClassDB: {}, spellsDB: {},
                sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                itemHistory: {}, markets: {}, culturesDB: {}):
    mud.sendMessage(id, '\n')
    mud.sendMessage(id,
                    '<f220>morris<f255>' +
                    '                                  - ' +
                    'Show the board')
    mud.sendMessage(id,
                    '<f220>morris put [coordinate]<f255>' +
                    '                 - ' +
                    'Place a counter')
    mud.sendMessage(id,
                    '<f220>morris move [from coord] [to coord]<f255>' +
                    '     - ' +
                    'Move a counter')
    mud.sendMessage(id,
                    '<f220>morris take [coordinate]<f255>' +
                    '                - ' +
                    'Remove a counter after mill')
    mud.sendMessage(id,
                    '<f220>morris reset<f255>' +
                    '                            - ' +
                    'Resets the board')
    mud.sendMessage(id, '\n\n')


def _helpChess(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    mud.sendMessage(id, '\n')
    mud.sendMessage(id,
                    '<f220>chess<f255>' +
                    '                                   - ' +
                    'Shows the board')
    mud.sendMessage(id,
                    '<f220>chess reset<f255>' +
                    '                             - ' +
                    'Rests the game')
    mud.sendMessage(id,
                    '<f220>chess move [coords]<f255>' +
                    '                     - ' +
                    'eg. chess move e2e3')
    mud.sendMessage(id,
                    '<f220>chess undo<f255>' +
                    '                              - ' +
                    'undoes the last move')
    mud.sendMessage(id, '\n\n')


def _helpCards(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    mud.sendMessage(id, '\n')
    mud.sendMessage(id,
                    '<f220>shuffle<f255>' +
                    '                                 - ' +
                    'Shuffles the deck')
    mud.sendMessage(id,
                    '<f220>deal to [player names]<f255>' +
                    '                  - ' +
                    'Deals cards')
    mud.sendMessage(id,
                    '<f220>hand<f255>' +
                    '                                    - ' +
                    'View your hand of cards')
    mud.sendMessage(id,
                    '<f220>swap [card description]<f255>' +
                    '                 - ' +
                    'Swaps a card')
    mud.sendMessage(id,
                    '<f220>stick<f255>' +
                    '                 - ' +
                    "Don't swap any cards")
    mud.sendMessage(id,
                    '<f220>call<f255>' +
                    '                                    - ' +
                    'Players show their hands')
    mud.sendMessage(id, 'Possible suits are: <f32>leashes, collars, ' +
                    'swords, horns, coins, clubs, cups, hearts, ' +
                    'diamonds and spades.<r>')
    mud.sendMessage(id, 'In some packs the <f32>Queen<r> is replaced ' +
                    'by a <f32>Knight<r>.')
    mud.sendMessage(id, '\n\n')


def _castSpellOnPlayer(mud, spellName: str, players: {}, id, npcs: {},
                       p, spellDetails):
    if npcs[p]['room'] != players[id]['room']:
        mud.sendMessage(id, "They're not here.\n\n")
        return

    if spellDetails['action'].startswith('protect'):
        npcs[p]['tempHitPoints'] = spellDetails['hp']
        npcs[p]['tempHitPointsDuration'] = \
            TimeStringToSec(spellDetails['duration'])
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
            TimeStringToSec(spellDetails['duration'])
        npcs[p]['tempCharmStart'] = int(time.time())
        if npcs[p]['affinity'].get(charmTarget):
            npcs[p]['affinity'][charmTarget] += charmValue
        else:
            npcs[p]['affinity'][charmTarget] = charmValue

    if spellDetails['action'].startswith('friend'):
        if players[id]['cha'] < npcs[p]['cha']:
            removePreparedSpell(players, id, spellName)
            mud.sendMessage(id, "You don't have enough charisma.\n\n")
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
        npcs[p]['frozenDuration'] = TimeStringToSec(spellDetails['duration'])
        npcs[p]['frozenStart'] = int(time.time())

    _showSpellImage(mud, id, spellName.replace(' ', '_'), players)

    mud.sendMessage(
        id,
        randomDescription(spellDetails['description']).format('<f32>' +
                                                              npcs[p]['name'] +
                                                              '<r>') + '\n\n')

    secondDesc = randomDescription(spellDetails['description_second'])
    if npcs == players and len(secondDesc) > 0:
        mud.sendMessage(
            p,
            secondDesc.format(players[id]['name'],
                              'you') + '\n\n')

    removePreparedSpell(players, id, spellName)


def _castSpellUndirected(params, mud, playersDB: {}, players: {}, rooms: {},
                         npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                         envDB: {}, env: {}, eventDB: {}, eventSchedule,
                         id: int, fights: {}, corpses: {}, blocklist,
                         mapArea: [], characterClassDB: {}, spellsDB: {},
                         sentimentDB: {}, spellName: {}, spellDetails: {},
                         clouds: {}, racesDB: {}, guildsDB: {},
                         itemHistory: {}, markets: {}, culturesDB: {}):
    spellAction = spellDetails['action']
    if spellAction.startswith('familiar'):
        _showSpellImage(mud, id, spellName.replace(' ', '_'), players)
        _conjureNPC(spellDetails['action'], mud, playersDB, players,
                    rooms, npcsDB, npcs, itemsDB, items, envDB, env,
                    eventDB, eventSchedule, id, fights, corpses,
                    blocklist, mapArea, characterClassDB, spellsDB,
                    sentimentDB, guildsDB, clouds, racesDB,
                    itemHistory, markets, culturesDB)
        return
    elif spellAction.startswith('defen'):
        # defense spells
        if spellName.endswith('shield') and spellDetails.get('armor'):
            if not players[id]["magicShield"]:
                removePreparedSpell(players, id, spellName)
                players[id]['magicShield'] = spellDetails['armor']
                players[id]['magicShieldStart'] = now
                players[id]["magicShieldDuration"] = \
                    TimeStringToSec(spellDetails['duration'])
                mud.sendMessage(id, "Magic shield active.\n\n")
            else:
                mud.sendMessage(id, "Magic shield is already active.\n\n")
            return
    mud.sendMessage(id, "Nothing happens.\n\n")


def _castSpell(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if len(params.strip()) == 0:
        mud.sendMessage(id, 'You try to cast a spell but fail horribly.\n\n')
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
        mud.sendMessage(id, "That's not a prepared spell.\n\n")
        return

    spellDetails = None
    if spellsDB.get('cantrip'):
        if spellsDB['cantrip'].get(spellName):
            spellDetails = spellsDB['cantrip'][spellName]
    if spellDetails is None:
        maxSpellLevel = _getPlayerMaxSpellLevel(players, id)
        for level in range(1, maxSpellLevel + 1):
            if spellsDB[str(level)].get(spellName):
                spellDetails = spellsDB[str(level)][spellName]
                break
    if spellDetails is None:
        mud.sendMessage(id, "You have no knowledge of that spell.\n\n")
        return

    if len(castAt) > 0:
        for p in players:
            if castAt not in players[p]['name'].lower():
                continue
            if p == id:
                mud.sendMessage(id, "This is not a hypnosis spell.\n\n")
                return
            _castSpellOnPlayer(
                mud, spellName, players, id, players, p, spellDetails)
            return

        for p in npcs:
            if castAt not in npcs[p]['name'].lower():
                continue

            if npcs[p]['familiarOf'] == players[id]['name']:
                mud.sendMessage(
                    id, "You can't cast a spell on your own familiar!\n\n")
                return

            _castSpellOnPlayer(mud, spellName, players, id, npcs,
                               p, spellDetails)
            return
    else:
        _castSpellUndirected(params, mud, playersDB, players, rooms,
                             npcsDB, npcs, itemsDB, items, envDB,
                             env, eventDB, eventSchedule, id, fights,
                             corpses, blocklist, mapArea,
                             characterClassDB, spellsDB, sentimentDB,
                             spellName, spellDetails,
                             clouds, racesDB, guildsDB, itemHistory, markets,
                             culturesDB)


def _affinity(params, mud, playersDB: {}, players: {}, rooms: {},
              npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
              envDB: {}, env: {}, eventDB: {}, eventSchedule: {},
              id: int, fights: {}, corpses: {}, blocklist,
              mapArea: [], characterClassDB: {}, spellsDB: {},
              sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
              itemHistory: {}, markets: {}, culturesDB: {}):
    otherPlayer = params.lower().strip()
    if len(otherPlayer) == 0:
        mud.sendMessage(id, 'With which player?\n\n')
        return
    if players[id]['affinity'].get(otherPlayer):
        affinity = players[id]['affinity'][otherPlayer]
        if affinity >= 0:
            mud.sendMessage(
                id, 'Your affinity with <f32><u>' +
                otherPlayer + '<r> is <f15><b2>+' +
                str(affinity) + '<r>\n\n')
        else:
            mud.sendMessage(
                id, 'Your affinity with <f32><u>' +
                otherPlayer + '<r> is <f15><b88>' +
                str(affinity) + '<r>\n\n')
        return
    mud.sendMessage(id, "You don't have any affinity with them.\n\n")


def _clearSpells(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                 envDB: {}, env: {}, eventDB: {}, eventSchedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 mapArea: [], characterClassDB: {}, spellsDB: {},
                 sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                 itemHistory: {}, markets: {}, culturesDB: {}):
    if len(players[id]['preparedSpells']) > 0:
        players[id]['preparedSpells'].clear()
        players[id]['spellSlots'].clear()
        mud.sendMessage(id, 'Your prepared spells list has been cleared.\n\n')
        return

    mud.sendMessage(id, "Your don't have any spells prepared.\n\n")


def _spells(params, mud, playersDB: {}, players: {}, rooms: {},
            npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
            envDB: {}, env: {}, eventDB: {}, eventSchedule,
            id: int, fights: {}, corpses: {}, blocklist,
            mapArea: [], characterClassDB: {}, spellsDB: {},
            sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
            itemHistory: {}, markets: {}, culturesDB: {}):
    if len(players[id]['preparedSpells']) > 0:
        mud.sendMessage(id, 'Your prepared spells:\n')
        for name, details in players[id]['preparedSpells'].items():
            mud.sendMessage(id, '  <b234>' + name + '<r>')
        mud.sendMessage(id, '\n')
    else:
        mud.sendMessage(id, 'You have no spells prepared.\n\n')


def _prepareSpellAtLevel(params, mud, playersDB: {}, players: {}, rooms: {},
                         npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                         envDB: {}, env: {}, eventDB: {}, eventSchedule,
                         id: int, fights: {}, corpses: {}, blocklist,
                         mapArea: [], characterClassDB: {}, spellsDB: {},
                         spellName: {}, level: {}):
    for name, details in spellsDB[level].items():
        if name.lower() == spellName:
            if name.lower() not in players[id]['preparedSpells']:
                if len(spellsDB[level][name]['items']) == 0:
                    players[id]['preparedSpells'][name] = 1
                else:
                    for required in spellsDB[level][name]['items']:
                        requiredItemFound = False
                        for i in list(players[id]['inv']):
                            if int(i) == required:
                                requiredItemFound = True
                                break
                        if not requiredItemFound:
                            mud.sendMessage(
                                id, 'You need <b234>' +
                                itemsDB[required]['article'] +
                                ' ' + itemsDB[required]['name'] +
                                '<r>\n\n')
                            return True
                players[id]['prepareSpell'] = spellName
                players[id]['prepareSpellProgress'] = 0
                players[id]['prepareSpellTime'] = TimeStringToSec(
                    details['prepareTime'])
                if len(details['prepareTime']) > 0:
                    mud.sendMessage(
                        id,
                        'You begin preparing the spell <b234>' +
                        spellName + '<r>. It will take ' +
                        details['prepareTime'] + '.\n\n')
                else:
                    mud.sendMessage(
                        id,
                        'You begin preparing the spell <b234>' +
                        spellName + '<r>.\n\n')
                return True
    return False


def _playerMaxCantrips(players: {}, id) -> int:
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


def _getPlayerMaxSpellLevel(players: {}, id) -> int:
    """Returns the maximum spell level of the player
    """
    for prof in players[id]['proficiencies']:
        if isinstance(prof, list):
            spellList = list(prof)
            if len(spellList) > 0:
                if spellList[0].lower() == 'spell':
                    return len(spellList) - 1
    return -1


def _getPlayerSpellSlotsAtSpellLevel(players: {}, id, spellLevel) -> int:
    """Returns the maximum spell slots at the given spell level
    """
    for prof in players[id]['proficiencies']:
        if isinstance(prof, list):
            spellList = list(prof)
            if len(spellList) > 0:
                if spellList[0].lower() == 'spell':
                    return spellList[spellLevel]
    return 0


def _getPlayerUsedSlotsAtSpellLevel(players: {}, id, spellLevel, spellsDB: {}):
    """Returns the used spell slots at the given spell level
    """
    if not spellsDB.get(str(spellLevel)):
        return 0

    usedCounter = 0
    for spellName, details in spellsDB[str(spellLevel)].items():
        if spellName in players[id]['preparedSpells']:
            usedCounter += 1
    return usedCounter


def _playerPreparedCantrips(players, id, spellsDB: {}) -> int:
    """Returns the number of cantrips which the player has prepared
    """
    preparedCounter = 0
    for spellName in players[id]['preparedSpells']:
        for cantripName, details in spellsDB['cantrip'].items():
            if cantripName == spellName:
                preparedCounter += 1
                break
    return preparedCounter


def _prepareSpell(params, mud, playersDB: {}, players: {}, rooms: {},
                  npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                  envDB: {}, env: {}, eventDB: {}, eventSchedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  mapArea: [], characterClassDB: {}, spellsDB: {},
                  sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                  itemHistory: {}, markets: {}, culturesDB: {}):
    spellName = params.lower().strip()

    # "learn spells" or "prepare spells" shows list of spells
    if spellName == 'spell' or spellName == 'spells':
        spellName = ''

    maxCantrips = _playerMaxCantrips(players, id)
    maxSpellLevel = _getPlayerMaxSpellLevel(players, id)

    if maxSpellLevel < 0 and maxCantrips == 0:
        mud.sendMessage(id, "You can't prepare spells.\n\n")
        return

    if len(spellName) == 0:
        # list spells which can be prepared
        mud.sendMessage(id, 'Spells you can prepare are:\n')

        if maxCantrips > 0 and spellsDB.get('cantrip'):
            for name, details in spellsDB['cantrip'].items():
                if name.lower() not in players[id]['preparedSpells']:
                    spellClasses = spellsDB['cantrip'][name]['classes']
                    if players[id]['characterClass'] in spellClasses or \
                       len(spellClasses) == 0:
                        mud.sendMessage(id, '  <f220>-' + name + '<r>')

        if maxSpellLevel > 0:
            for level in range(1, maxSpellLevel + 1):
                if not spellsDB.get(str(level)):
                    continue
                for name, details in spellsDB[str(level)].items():
                    if name.lower() not in players[id]['preparedSpells']:
                        spellClasses = spellsDB[str(level)][name]['classes']
                        if players[id]['characterClass'] in spellClasses or \
                           len(spellClasses) == 0:
                            mud.sendMessage(id, '  <b234>' + name + '<r>')
        mud.sendMessage(id, '\n')
    else:
        if spellName.startswith('the spell '):
            spellName = spellName.replace('the spell ', '')
        if spellName.startswith('spell '):
            spellName = spellName.replace('spell ', '')
        if spellName == players[id]['prepareSpell']:
            mud.sendMessage(id, 'You are already preparing that.\n\n')
            return

        if maxCantrips > 0 and spellsDB.get('cantrip'):
            if _playerPreparedCantrips(players, id, spellsDB) < maxCantrips:
                if _prepareSpellAtLevel(params, mud, playersDB, players,
                                        rooms, npcsDB, npcs, itemsDB,
                                        items, envDB, env, eventDB,
                                        eventSchedule, id, fights,
                                        corpses, blocklist, mapArea,
                                        characterClassDB, spellsDB,
                                        spellName, 'cantrip'):
                    return
            else:
                mud.sendMessage(
                    id, "You can't prepare any more cantrips.\n\n")
                return

        if maxSpellLevel > 0:
            for level in range(1, maxSpellLevel + 1):
                if not spellsDB.get(str(level)):
                    continue
                maxSlots = _getPlayerSpellSlotsAtSpellLevel(players, id, level)
                usedSlots = \
                    _getPlayerUsedSlotsAtSpellLevel(players, id,
                                                    level, spellsDB)
                if usedSlots < maxSlots:
                    if _prepareSpellAtLevel(params, mud, playersDB,
                                            players, rooms, npcsDB, npcs,
                                            itemsDB, items, envDB, env,
                                            eventDB, eventSchedule, id,
                                            fights, corpses, blocklist,
                                            mapArea, characterClassDB,
                                            spellsDB, spellName, str(level)):
                        return
                else:
                    mud.sendMessage(
                        id,
                        "You have prepared the maximum level" +
                        str(level) + " spells.\n\n")
                    return

        mud.sendMessage(id, "That's not a spell.\n\n")


def _speak(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB: {},
           env: {}, eventDB: {}, eventSchedule: {}, id: int,
           fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    lang = params.lower().strip()
    if lang not in players[id]['language']:
        mud.sendMessage(id, "You don't know how to speak that language\n\n")
        return
    players[id]['speakLanguage'] = lang
    mud.sendMessage(id, "You switch to speaking in " + lang + "\n\n")


def _taunt(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
           env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    if not params:
        mud.sendMessageWrap(id, '<f230>', "Who shall be your victim?\n")
        return

    if players[id]['canSay'] == 1:
        if params.startswith('at '):
            params = params.replace('at ', '', 1)
        target = params
        if not target:
            mud.sendMessageWrap(id, '<f230>', "Who shall be your victim?\n")
            return

        # replace "familiar" with their NPC name
        # as in: "taunt familiar"
        if target.lower() == 'familiar':
            newTarget = getFamiliarName(players, id, npcs)
            if len(newTarget) > 0:
                target = newTarget

        fullTarget = target
        if target.startswith('the '):
            target = target.replace('the ', '', 1)

        tauntTypeFirstPerson = \
            randomDescription('taunt|insult|besmirch|' +
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
                    mud.sendMessageWrap(
                        id, '<f230>', "It'd be pointless to taunt yourself!\n")
                else:
                    langList = players[p]['language']
                    if players[id]['speakLanguage'] in langList:
                        mud.sendMessageWrap(
                            p, '<f230>',
                            players[id]['name'] + " " +
                            tauntTypeSecondPerson + " you\n")
                        decreaseAffinityBetweenPlayers(
                            players, p, players, id, guildsDB)
                    else:
                        mud.sendMessageWrap(
                            p, '<f230>',
                            players[id]['name'] + " says something in " +
                            players[id]['speakLanguage'] + '\n')
                    decreaseAffinityBetweenPlayers(
                        players, id, players, p, guildsDB)
                isDone = True
                break
        if not isDone:
            for p in npcs:
                if target.lower() in npcs[p]['name'].lower() and \
                   npcs[p]['room'] == players[id]['room']:
                    if target.lower() in players[id]['name'].lower():
                        mud.sendMessageWrap(
                            id, '<f230>',
                            "It'd be pointless to " + tauntTypeFirstPerson +
                            " yourself!\n")
                    else:
                        langList = npcs[p]['language']
                        if players[id]['speakLanguage'] in langList:
                            decreaseAffinityBetweenPlayers(
                                npcs, p, players, id, guildsDB)
                    decreaseAffinityBetweenPlayers(
                        players, id, npcs, p, guildsDB)
                    isDone = True
                    break

        if isDone:
            tauntTypeFirstPerson
            for p in players:
                if p == id:
                    tauntSeverity = \
                        randomDescription('mercilessly|severely|harshly|' +
                                          'loudly|blatantly|coarsely|' +
                                          'crudely|unremittingly|' +
                                          'witheringly|pitilessly')
                    descr = "You " + tauntSeverity + ' ' + \
                        tauntTypeFirstPerson + ' ' + fullTarget
                    mud.sendMessageWrap(id, '<f230>', descr + ".\n")
                    continue
                if players[p]['room'] == players[id]['room']:
                    mud.sendMessageWrap(
                        id, '<f230>',
                        players[id]['name'] + ' ' + tauntTypeSecondPerson +
                        ' ' + fullTarget + "\n")
        else:
            mud.sendMessageWrap(
                id, '<f230>', target + ' is not here.\n')
    else:
        mud.sendMessageWrap(
            id, '<f230>',
            'To find yourself unable to taunt at this time.\n')


def _say(params, mud, playersDB: {}, players: {}, rooms: {},
         npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
         env: {}, eventDB: {}, eventSchedule,
         id: int, fights: {}, corpses: {}, blocklist,
         mapArea: [], characterClassDB: {}, spellsDB: {},
         sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
         itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['canSay'] == 1:

        # don't say if the string contains a blocked string
        selfOnly = False
        params2 = params.lower()
        for blockedstr in blocklist:
            if blockedstr in params2:
                selfOnly = True
                break

        # go through every player in the game
        cantStr = thievesCant(params)
        for (pid, pl) in list(players.items()):
            # if they're in the same room as the player
            if players[pid]['room'] == players[id]['room']:
                # can the other player see this player?
                if not playerIsVisible(mud, pid, players, id, players):
                    continue
                if selfOnly is False or pid == id:
                    langList = players[pid]['language']
                    if players[id]['speakLanguage'] in langList:
                        sentimentScore = \
                            getSentiment(params, sentimentDB) + \
                            getGuildSentiment(players, id, players,
                                              pid, guildsDB)

                        if sentimentScore >= 0:
                            increaseAffinityBetweenPlayers(
                                players, id, players, pid, guildsDB)
                            increaseAffinityBetweenPlayers(
                                players, pid, players, id, guildsDB)
                        else:
                            decreaseAffinityBetweenPlayers(
                                players, id, players, pid, guildsDB)
                            decreaseAffinityBetweenPlayers(
                                players, pid, players, id, guildsDB)

                        # send them a message telling them what the player said
                        pName = players[id]['name']
                        desc = \
                            '<f220>{}<r> says: <f159>{}'.format(pName, params)
                        mud.sendMessageWrap(
                            pid, '<f230>', desc + "\n\n")
                    else:
                        pName = players[id]['name']
                        if players[id]['speakLanguage'] != 'cant':
                            pLang = players[id]['speakLanguage']
                            desc = \
                                '<f220>{}<r> says '.format(pName) + \
                                'something in <f159>{}<r>'.format(pLang)
                            mud.sendMessageWrap(
                                pid, '<f230>', desc + "\n\n")
                        else:
                            mud.sendMessageWrap(
                                pid, '<f230>',
                                '<f220>{}<r> says: '.format(pName) +
                                '<f159>{}'.format(cantStr) + "\n\n")
    else:
        mud.sendMessageWrap(
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
                if not playerIsVisible(mud, pid, players, id, players):
                    continue

                # send them a message telling them what the player did
                pName = players[id]['name']
                desc = \
                    '<f220>{}<r> {}<f159>'.format(pName, emoteDescription)
                mud.sendMessageWrap(
                    pid, '<f230>', desc + "\n\n")
    else:
        mud.sendMessageWrap(
            id, '<f230>',
            'To your horror, you realise you somehow cannot force ' +
            'yourself to make any expression!\n')


def _laugh(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
           env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'laughs')


def _thinking(params, mud, playersDB: {}, players: {}, rooms: {},
              npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
              env: {}, eventDB: {}, eventSchedule,
              id: int, fights: {}, corpses: {}, blocklist,
              mapArea: [], characterClassDB: {}, spellsDB: {},
              sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
              itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'is thinking')


def _grimace(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
             env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: [], characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'grimaces')


def _applaud(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
             env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: [], characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'applauds')


def _nod(params, mud, playersDB: {}, players: {}, rooms: {},
         npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
         env: {}, eventDB: {}, eventSchedule,
         id: int, fights: {}, corpses: {}, blocklist,
         mapArea: [], characterClassDB: {}, spellsDB: {},
         sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
         itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'nods')


def _wave(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
          env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'waves')


def _astonished(params, mud, playersDB: {}, players: {}, rooms: {},
                npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
                env: {}, eventDB: {}, eventSchedule,
                id: int, fights: {}, corpses: {}, blocklist,
                mapArea: [], characterClassDB: {}, spellsDB: {},
                sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'is astonished')


def _confused(params, mud, playersDB: {}, players: {}, rooms: {},
              npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
              env: {}, eventDB: {}, eventSchedule,
              id: int, fights: {}, corpses: {}, blocklist,
              mapArea: [], characterClassDB: {}, spellsDB: {},
              sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
              itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'looks confused')


def _bow(params, mud, playersDB: {}, players: {}, rooms: {},
         npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
         env: {}, eventDB: {}, eventSchedule,
         id: int, fights: {}, corpses: {}, blocklist,
         mapArea: [], characterClassDB: {}, spellsDB: {},
         sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
         itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'takes a bow')


def _calm(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
          env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'looks calm')


def _cheer(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
           env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'cheers heartily')


def _curious(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
             env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: [], characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'looks curious')


def _curtsey(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
             env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: [], characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'curtseys')


def _frown(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
           env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'frowns')


def _eyebrow(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
             env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: [], characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms,
           id, 'raises an eyebrow')


def _giggle(params, mud, playersDB: {}, players: {}, rooms: {},
            npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
            env: {}, eventDB: {}, eventSchedule,
            id: int, fights: {}, corpses: {}, blocklist,
            mapArea: [], characterClassDB: {}, spellsDB: {},
            sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
            itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'giggles')


def _grin(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
          env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'grins')


def _yawn(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
          env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'yawns')


def _smug(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
          env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'looks smug')


def _relieved(params, mud, playersDB: {}, players: {}, rooms: {},
              npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
              env: {}, eventDB: {}, eventSchedule,
              id: int, fights: {}, corpses: {}, blocklist,
              mapArea: [], characterClassDB: {}, spellsDB: {},
              sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
              itemHistory: {}, markets: {}, culturesDB: {}):
    _emote(params, mud, playersDB, players, rooms, id, 'looks relieved')


def _stick(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
           env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    _say('stick', mud, playersDB, players, rooms,
         npcsDB, npcs, itemsDB, items, envDB,
         env, eventDB, eventSchedule,
         id, fights, corpses, blocklist,
         mapArea, characterClassDB, spellsDB,
         sentimentDB, guildsDB, clouds, racesDB, itemHistory, markets,
         culturesDB)


def _holdingLightSource(players: {}, id, items: {}, itemsDB: {}) -> bool:
    """Is the given player holding a light source?
    """
    itemID = int(players[id]['clo_lhand'])
    if itemID > 0:
        if itemsDB[itemID]['lightSource'] != 0:
            return True
    itemID = int(players[id]['clo_rhand'])
    if itemID > 0:
        if itemsDB[int(itemID)]['lightSource'] != 0:
            return True

    # are there any other players in the same room holding a light source?
    for p in players:
        if p == id:
            continue
        if players[p]['room'] != players[id]['room']:
            continue
        itemID = int(players[p]['clo_lhand'])
        if itemID > 0:
            if itemsDB[itemID]['lightSource'] != 0:
                return True
        itemID = int(players[p]['clo_rhand'])
        if itemID > 0:
            if itemsDB[int(itemID)]['lightSource'] != 0:
                return True

    # is there a light source in the room?
    return _lightSourceInRoom(players, id, items, itemsDB)


def _conditionalRoom(condType: str, cond: str, description: str, id,
                     players: {}, items: {},
                     itemsDB: {}, clouds: {}, mapArea: [],
                     rooms: {}) -> bool:
    if condType == 'sunrise' or \
       condType == 'dawn':
        currTime = datetime.datetime.today()
        currHour = currTime.hour
        sun = getSolar()
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
        sun = getSolar()
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
            if getRainAtCoords(coords, mapArea, clouds):
                return True
        else:
            if not getRainAtCoords(coords, mapArea, clouds):
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
                return _holdingLightSource(players, id, items, itemsDB)
        elif (players[id]['clo_lhand'] == int(cond) or
              players[id]['clo_rhand'] == int(cond)):
            return True

    if condType.startswith('wear'):
        for c in wearLocation:
            if players[id]['clo_' + c] == int(cond):
                return True

    return False


def _conditionalRoomDescription(description: str, tideOutDescription: str,
                                conditional: [], id, players: {}, items: {},
                                itemsDB: {}, clouds: {}, mapArea: [],
                                rooms: {}):
    """Returns a description which can vary depending on conditions
    """
    roomDescription = description
    if len(tideOutDescription) > 0:
        if runTide() < 0.0:
            roomDescription = tideOutDescription

    # Alternative descriptions triggered by conditions
    for possibleDescription in conditional:
        if len(possibleDescription) >= 3:
            condType = possibleDescription[0]
            cond = possibleDescription[1]
            alternativeDescription = possibleDescription[2]
            if _conditionalRoom(condType, cond,
                                alternativeDescription,
                                id, players, items, itemsDB,
                                clouds, mapArea, rooms):
                roomDescription = alternativeDescription
                break

    return roomDescription


def _conditionalRoomImage(conditional: [], id, players: {}, items: {},
                          itemsDB: {}, clouds: {}, mapArea: [],
                          rooms: {}) -> str:
    """If there is an image associated with a conditional
    room description then return its name
    """
    for possibleDescription in conditional:
        if len(possibleDescription) >= 4:
            condType = possibleDescription[0]
            cond = possibleDescription[1]
            alternativeDescription = possibleDescription[2]
            if _conditionalRoom(condType, cond,
                                alternativeDescription,
                                id, players, items, itemsDB, clouds,
                                mapArea, rooms):
                roomImageFilename = \
                    'images/rooms/' + possibleDescription[3]
                if os.path.isfile(roomImageFilename):
                    return possibleDescription[3]
                break
    return None


def _playersInRoom(targetRoom, players, npcs):
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


def _roomRequiresLightSource(players: {}, id, rooms: {}) -> bool:
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


def _lightSourceInRoom(players: {}, id, items: {}, itemsDB: {}) -> bool:
    """Returns true if there is a light source in the room
    """
    for i in items:
        if items[i]['room'].lower() != players[id]['room']:
            continue
        if itemsDB[items[i]['id']]['lightSource'] != 0:
            return True
    return False


def _itemIsVisible(observerId: int, players: {},
                   itemId: int, itemsDB: {}) -> bool:
    """Is the item visible to the observer?
    """
    itemId = int(itemId)
    if not itemsDB[itemId].get('visibleWhenWearing'):
        return True
    if isWearing(observerId, players,
                 itemsDB[itemId]['visibleWhenWearing']):
        return True
    return False


def _itemIsClimbable(climberId: int, players: {},
                     itemId: int, itemsDB: {}) -> bool:
    """Is the item climbable by the player?
    """
    itemId = int(itemId)
    if not itemsDB[itemId].get('climbWhenWearing'):
        return True
    if isWearing(climberId, players,
                 itemsDB[itemId]['climbWhenWearing']):
        return True
    return False


def _moonIllumination(currTime) -> int:
    """Returns additional illumination due to moonlight
    """
    diff = currTime - datetime.datetime(2001, 1, 1)
    days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
    lunations = dec("0.20439731") + (days * dec("0.03386319269"))
    index = int(lunations % dec(1)) & 7
    return int((5-abs(4-index))*2)


def _roomIllumination(roomImage, outdoors: bool):
    """Alters the brightness and contrast of the image to simulate
    evening and night conditions
    """
    if not outdoors:
        return roomImage
    currTime = datetime.datetime.today()
    currHour = currTime.hour
    sun = getSolar()
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

    brightness += _moonIllumination(currTime)
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


def _showRoomImage(mud, id, roomId, rooms: {}, players: {},
                   items: {}, itemsDB: {},
                   clouds: {}, mapArea: []) -> None:
    """Shows an image for the room if it exists
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    conditionalImage = \
        _conditionalRoomImage(rooms[roomId]['conditional'],
                              id, players, items,
                              itemsDB, clouds,
                              mapArea, rooms)
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
        sun = getSolar()
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
        mud.sendImage(id, '\n' + _roomIllumination(roomImageStr, outdoors))


def _showSpellImage(mud, id, spellId, players: {}) -> None:
    """Shows an image for a spell
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    spellImageFilename = 'images/spells/' + spellId
    if not os.path.isfile(spellImageFilename):
        return
    with open(spellImageFilename, 'r') as spellFile:
        mud.sendImage(id, '\n' + spellFile.read())


def _showItemImage(mud, id, itemId, players: {}) -> None:
    """Shows an image for the item if it exists
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    itemImageFilename = 'images/items/' + str(itemId)
    if not os.path.isfile(itemImageFilename):
        return
    with open(itemImageFilename, 'r') as itemFile:
        mud.sendImage(id, '\n' + itemFile.read())


def _showNPCImage(mud, id, npcName, players: {}) -> None:
    """Shows an image for a NPC
    """
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    npcImageFilename = 'images/npcs/' + npcName.replace(' ', '_')
    if not os.path.isfile(npcImageFilename):
        return
    with open(npcImageFilename, 'r') as npcFile:
        mud.sendImage(id, '\n' + npcFile.read())


def _getRoomExits(mud, rooms: {}, players: {}, id) -> {}:
    """Returns a dictionary of exits for the given player
    """
    rm = rooms[players[id]['room']]
    exits = rm['exits']

    if rm.get('tideOutExits'):
        if runTide() < 0.0:
            for direction, roomID in rm['tideOutExits'].items():
                exits[direction] = roomID
        else:
            for direction, roomID in rm['tideOutExits'].items():
                if exits.get(direction):
                    del rm['exits'][direction]

    if rm.get('exitsWhenWearing'):
        directionsAdded = []
        for ex in rm['exitsWhenWearing']:
            if len(ex) < 3:
                continue
            direction = ex[0]
            itemID = ex[1]
            if isWearing(id, players, [itemID]):
                roomID = ex[2]
                exits[direction] = roomID
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


def _itemInPlayerRoom(players: {}, id, items: {}, itemId: int) -> bool:
    """Returns true if the given item is in the given room
    """
    return items[itemId]['room'].lower() == players[id]['room']


def _look(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['canLook'] == 1:
        if len(params) < 1:
            # If no arguments are given, then look around and describe
            # surroundings

            # store the player's current room
            rm = rooms[players[id]['room']]

            # send the player back the description of their current room
            playerRoomId = players[id]['room']
            _showRoomImage(mud, id, playerRoomId,
                           rooms, players, items,
                           itemsDB, clouds, mapArea)
            roomDescription = \
                _conditionalRoomDescription(rm['description'],
                                            rm['tideOutDescription'],
                                            rm['conditional'],
                                            id, players, items, itemsDB,
                                            clouds, mapArea, rooms)

            if rm['trap'].get('trapActivation') and \
               rm['trap'].get('trapPerception'):
                if randint(1, players[id]['per']) > \
                   rm['trap']['trapPerception']:
                    if rm['trap']['trapType'].startswith('dart') and \
                       randint(0, 1) == 1:
                        roomDescription += \
                            randomDescription(" You notice some tiny " +
                                              "holes in the wall.| " +
                                              "There are some small " +
                                              "holes in the wall.|You " +
                                              "observe some tiny holes" +
                                              " in the wall.")
                    else:
                        if rm['trap']['trapActivation'] == 'tripwire':
                            roomDescription += \
                                randomDescription(" A tripwire is " +
                                                  "carefully set along " +
                                                  "the floor.| You notice " +
                                                  "a thin wire across " +
                                                  "the floor.| An almost " +
                                                  "invisible wire runs " +
                                                  "along the floor.")
                        if rm['trap']['trapActivation'].startswith('pressure'):
                            roomDescription += \
                                randomDescription(" The faint outline of " +
                                                  "a pressure plate can be " +
                                                  "seen on the floor.| The " +
                                                  "outline of a pressure " +
                                                  "plate is visible on " +
                                                  "the floor.")

            mud.sendMessageWrap(id, '<f230>',
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
                        if playerIsVisible(mud, id, players, pid, players):
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
                        if playerIsVisible(mud, id, players, nid, npcs):
                            playershere.append(npcs[nid]['name'])

            # Show items in the room
            for (item, pl) in list(items.items()):
                if _itemInPlayerRoom(players, id, items, item):
                    if _itemIsVisible(id, players, items[item]['id'], itemsDB):
                        itemshere.append(
                            itemsDB[items[item]['id']]['article'] + ' ' +
                            itemsDB[items[item]['id']]['name'])

            # send player a message containing the list of players in the room
            if len(playershere) > 0:
                mud.sendMessage(
                    id,
                    '<f230>You see: <f220>{}'.format(', '.join(playershere)))

            # send player a message containing the list of exits from this room
            roomExitsStr = _getRoomExits(mud, rooms, players, id)
            if roomExitsStr:
                desc = \
                    '<f230>Exits are: <f220>{}'.format(', '.join(roomExitsStr))
                mud.sendMessage(id, desc)

            # send player a message containing the list of items in the room
            if len(itemshere) > 0:
                needsLight = _roomRequiresLightSource(players, id, rooms)
                playersWithLight = False
                if needsLight:
                    playersWithLight = \
                        _holdingLightSource(players, id, items, itemsDB)
                if needsLight is False or \
                   (needsLight is True and playersWithLight is True):
                    desc = '<f230>You notice: ' + \
                        '<f220>{}'.format(', '.join(itemshere))
                    mud.sendMessageWrap(id, '<f220>', desc)

            mud.sendMessage(id, "<r>\n")
        else:
            # If argument is given, then evaluate it
            param = params.lower()

            if param.startswith('my '):
                param = params.replace('my ', '', 1)

            # replace "familiar" with the name of the familiar
            if param.startswith('familiar'):
                familiarName = getFamiliarName(players, id, npcs)
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
                        if playerIsVisible(mud, players, id, p, players):
                            _bioOfPlayer(mud, id, p, players, itemsDB)
                            messageSent = True

            message = ""

            # Go through all NPCs in game
            for n in npcs:
                if param in npcs[n]['name'].lower() and \
                   npcs[n]['room'] == players[id]['room']:
                    if playerIsVisible(mud, id, players, n, npcs):
                        if npcs[n]['familiarMode'] != 'hide':
                            nameLower = npcs[n]['name'].lower()
                            _showNPCImage(mud, id, nameLower, players)
                            _bioOfPlayer(mud, id, n, npcs, itemsDB)
                            messageSent = True
                        else:
                            if npcs[n]['familiarOf'] == players[id]['name']:
                                message = "They are hiding somewhere here."
                                messageSent = True

            if len(message) > 0:
                mud.sendMessage(id, "****CLEAR****" + message + "\n\n")
                messageSent = True

            message = ""

            # Go through all Items in game
            itemCounter = 0
            for i in items:
                if _itemInPlayerRoom(players, id, items, i) and \
                   param in itemsDB[items[i]['id']]['name'].lower():
                    if _itemIsVisible(id, players, items[i]['id'], itemsDB):
                        if itemCounter == 0:
                            itemLanguage = itemsDB[items[i]['id']]['language']
                            thisItemID = int(items[i]['id'])
                            idx = items[i]['id']
                            if itemsDB[idx].get('itemName'):
                                message += \
                                    'Name: ' + itemsDB[idx]['itemName'] + '\n'
                            desc = itemsDB[idx]['long_description']
                            message += randomDescription(desc)
                            message += \
                                _describeContainerContents(mud, id,
                                                           itemsDB,
                                                           items[i]['id'],
                                                           True)
                            if len(itemLanguage) == 0:
                                _showItemImage(mud, id, thisItemID, players)
                            else:
                                if itemLanguage in players[id]['language']:
                                    _showItemImage(mud, id, thisItemID,
                                                   players)
                                else:
                                    message += \
                                        "It's written in " + itemLanguage
                            itemName = \
                                itemsDB[items[i]['id']]['article'] + \
                                " " + itemsDB[items[i]['id']]['name']
                        itemCounter += 1

            # Examine items in inventory
            if len(message) == 0:
                playerinv = list(players[id]['inv'])
                if len(playerinv) > 0:
                    # check for exact match of item name
                    invItemFound = False
                    for i in playerinv:
                        thisItemID = int(i)
                        itemsDBEntry = itemsDB[thisItemID]
                        if param == itemsDBEntry['name'].lower():
                            itemLanguage = itemsDBEntry['language']
                            _showItemImage(mud, id, thisItemID, players)
                            if len(itemLanguage) == 0:
                                desc = itemsDBEntry['long_description']
                                message += randomDescription(desc)
                                message += \
                                    _describeContainerContents(
                                        mud, id, itemsDB, thisItemID, True)
                            else:
                                if itemLanguage in players[id]['language']:
                                    desc = itemsDBEntry['long_description']
                                    message += randomDescription(desc)
                                    message += \
                                        _describeContainerContents(
                                            mud, id, itemsDB, thisItemID, True)
                                else:
                                    message += \
                                        "It's written in " + itemLanguage
                            itemName = \
                                itemsDBEntry['article'] + " " + \
                                itemsDBEntry['name']
                            invItemFound = True
                            break
                    if not invItemFound:
                        # check for partial match of item name
                        for i in playerinv:
                            thisItemID = int(i)
                            itemsDBEntry = itemsDB[thisItemID]
                            if param in itemsDBEntry['name'].lower():
                                itemLanguage = itemsDBEntry['language']
                                _showItemImage(mud, id, thisItemID, players)
                                if len(itemLanguage) == 0:
                                    desc = itemsDBEntry['long_description']
                                    message += randomDescription(desc)
                                    message += \
                                        _describeContainerContents(
                                            mud, id, itemsDB, thisItemID, True)
                                else:
                                    if itemLanguage in players[id]['language']:
                                        desc = \
                                            itemsDBEntry['long_description']
                                        message += randomDescription(desc)
                                        message += \
                                            _describeContainerContents(
                                                mud, id, itemsDB,
                                                thisItemID, True)
                                    else:
                                        message += \
                                            "It's written in " + itemLanguage

                                itemName = \
                                    itemsDBEntry['article'] + " " + \
                                    itemsDBEntry['name']
                                break

            if len(message) > 0:
                mud.sendMessage(id, "****CLEAR****It's " + itemName + ".")
                mud.sendMessageWrap(id, '', message + "<r>\n\n")
                messageSent = True
                if itemCounter > 1:
                    mud.sendMessage(
                        id, "You can see " +
                        str(itemCounter) +
                        " of those in the vicinity.<r>\n\n")

            # If no message has been sent, it means no player/npc/item was
            # found
            if not messageSent:
                mud.sendMessage(id, "Look at what?<r>\n")
    else:
        mud.sendMessage(
            id,
            '****CLEAR****' +
            'You somehow cannot muster enough perceptive powers ' +
            'to perceive and describe your immediate surroundings...<r>\n')


def _escapeTrap(params, mud, playersDB: {}, players: {}, rooms: {},
                npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                envDB: {}, env: {}, eventDB: {}, eventSchedule,
                id: int, fights: {}, corpses: {}, blocklist,
                mapArea: [], characterClassDB: {}, spellsDB: {},
                sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                itemHistory: {}, markets: {}, culturesDB: {}):
    if not playerIsTrapped(id, players, rooms):
        mud.sendMessage(
            id, randomDescription(
                "You try to escape but find there's nothing to escape from") +
            '\n\n')

    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if players[id]['canAttack'] == 1:
        escapeFromTrap(mud, id, players, rooms, itemsDB)


def _attack(params, mud, playersDB: {}, players: {}, rooms: {},
            npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
            envDB: {}, env: {}, eventDB: {}, eventSchedule,
            id: int, fights: {}, corpses: {}, blocklist,
            mapArea: [], characterClassDB: {}, spellsDB: {},
            sentimentDB: {}, guildsDB: {}, clouds: {},
            racesDB: {}, itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['frozenStart'] != 0:
        desc = players[id]['frozenDescription']
        mud.sendMessage(
            id, randomDescription(desc) + '\n\n')
        return

    if players[id]['canAttack'] == 1:
        if playerIsTrapped(id, players, rooms):
            mud.sendMessage(
                id, randomDescription(
                    "You're trapped") + '.\n\n')
            return

        if playerIsProne(id, players):
            mud.sendMessage(id, randomDescription('You stand up<r>\n\n'))
            setPlayerProne(id, players, False)
            return

        target = params  # .lower()
        if target.startswith('at '):
            target = params.replace('at ', '')
        if target.startswith('the '):
            target = params.replace('the ', '')

        if not isAttacking(players, id, fights):
            playerBeginsAttack(players, id, target,
                               npcs, fights, mud, racesDB, itemHistory)
        else:
            currentTarget = getAttackingTarget(players, id, fights)
            if not isinstance(currentTarget, int):
                mud.sendMessage(
                    id, 'You are already attacking ' +
                    currentTarget + "\n")
            else:
                mud.sendMessage(
                    id, 'You are already attacking ' +
                    npcs[currentTarget]['name'] + "\n")

        # List fights for debugging purposes
        # for x in fights:
            # print (x)
            # for y in fights[x]:
                # print (y,':',fights[x][y])
    else:
        mud.sendMessage(
            id,
            'Right now, you do not feel like you can force ' +
            'yourself to attack anyone or anything.\n')


def _itemInInventory(players: {}, id, itemName, itemsDB: {}):
    if len(list(players[id]['inv'])) > 0:
        itemNameLower = itemName.lower()
        for i in list(players[id]['inv']):
            if itemsDB[int(i)]['name'].lower() == itemNameLower:
                return True
    return False


def _describe(params, mud, playersDB: {}, players: {}, rooms: {},
              npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
              envDB: {}, env: {}, eventDB: {}, eventSchedule,
              id: int, fights: {}, corpses: {}, blocklist,
              mapArea: [], characterClassDB: {}, spellsDB: {},
              sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
              itemHistory: {}, markets: {}, culturesDB: {}):
    if not _isWitch(id, players):
        mud.sendMessage(id, "You don't have enough powers.\n\n")
        return

    if '"' not in params:
        mud.sendMessage(
            id, 'Descriptions need to be within double quotes.\n\n')
        return

    descriptionStrings = re.findall('"([^"]*)"', params)
    if len(descriptionStrings) == 0:
        mud.sendMessage(
            id, 'Descriptions need to be within double quotes.\n\n')
        return

    if len(descriptionStrings[0].strip()) < 3:
        mud.sendMessage(id, 'Description is too short.\n\n')
        return

    rm = players[id]['room']
    if len(descriptionStrings) == 1:
        rooms[rm]['description'] = descriptionStrings[0]
        mud.sendMessage(id, 'Room description set.\n\n')
        saveUniverse(rooms, npcsDB, npcs,
                     itemsDB, items, envDB,
                     env, guildsDB)
        return

    if len(descriptionStrings) == 2:
        thingDescribed = descriptionStrings[0].lower()
        thingDescription = descriptionStrings[1]

        if len(thingDescription) < 3:
            mud.sendMessage(
                id, 'Description of ' +
                descriptionStrings[0] +
                ' is too short.\n\n')
            return

        if thingDescribed == 'name':
            rooms[rm]['name'] = thingDescription
            mud.sendMessage(
                id, 'Room name changed to ' +
                thingDescription + '.\n\n')
            saveUniverse(rooms, npcsDB, npcs,
                         itemsDB, items, envDB,
                         env, guildsDB)
            return

        if thingDescribed == 'tide':
            rooms[rm]['tideOutDescription'] = thingDescription
            mud.sendMessage(id, 'Tide out description set.\n\n')
            saveUniverse(rooms, npcsDB, npcs,
                         itemsDB, items,
                         envDB, env, guildsDB)
            return

        # change the description of an item in the room
        for (item, pl) in list(items.items()):
            if items[item]['room'] == players[id]['room']:
                idx = items[item]['id']
                if thingDescribed in itemsDB[idx]['name'].lower():
                    itemsDB[idx]['long_description'] = thingDescription
                    mud.sendMessage(id, 'New description set for ' +
                                    itemsDB[idx]['article'] +
                                    ' ' + itemsDB[idx]['name'] +
                                    '.\n\n')
                    saveUniverse(
                        rooms, npcsDB, npcs, itemsDB,
                        items, envDB, env, guildsDB)
                    return

        # Change the description of an NPC in the room
        for (nid, pl) in list(npcs.items()):
            if npcs[nid]['room'] == players[id]['room']:
                if thingDescribed in npcs[nid]['name'].lower():
                    npcs[nid]['lookDescription'] = thingDescription
                    mud.sendMessage(
                        id, 'New description set for ' +
                        npcs[nid]['name'] + '.\n\n')
                    saveUniverse(
                        rooms, npcsDB, npcs, itemsDB,
                        items, envDB, env, guildsDB)
                    return

    if len(descriptionStrings) == 3:
        if descriptionStrings[0].lower() != 'name':
            mud.sendMessage(id, "I don't understand.\n\n")
            return
        thingDescribed = descriptionStrings[1].lower()
        thingName = descriptionStrings[2]
        if len(thingName) < 3:
            mud.sendMessage(
                id, 'Description of ' +
                descriptionStrings[1] +
                ' is too short.\n\n')
            return

        # change the name of an item in the room
        for (item, pl) in list(items.items()):
            if items[item]['room'] == players[id]['room']:
                idx = items[item]['id']
                if thingDescribed in itemsDB[idx]['name'].lower():
                    itemsDB[idx]['name'] = thingName
                    mud.sendMessage(id, 'New description set for ' +
                                    itemsDB[idx]['article'] +
                                    ' ' +
                                    itemsDB[idx]['name'] +
                                    '.\n\n')
                    saveUniverse(
                        rooms, npcsDB, npcs, itemsDB,
                        items, envDB, env, guildsDB)
                    return

        # Change the name of an NPC in the room
        for (nid, pl) in list(npcs.items()):
            if npcs[nid]['room'] == players[id]['room']:
                if thingDescribed in npcs[nid]['name'].lower():
                    npcs[nid]['name'] = thingName
                    mud.sendMessage(
                        id, 'New description set for ' +
                        npcs[nid]['name'] + '.\n\n')
                    saveUniverse(
                        rooms, npcsDB, npcs, itemsDB,
                        items, envDB, env, guildsDB)
                    return


def _checkInventory(params, mud, playersDB: {}, players: {}, rooms: {},
                    npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                    envDB: {}, env: {}, eventDB: {}, eventSchedule,
                    id: int, fights: {}, corpses: {}, blocklist,
                    mapArea: [], characterClassDB: {}, spellsDB: {},
                    sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                    itemHistory: {}, markets: {}, culturesDB: {}):
    mud.sendMessage(id, '****CLEAR****You check your inventory.')

    roomID = players[id]['room']
    _showItemsForSale(mud, rooms, roomID, players, id, itemsDB)

    if len(list(players[id]['inv'])) == 0:
        mud.sendMessage(id, 'You haven`t got any items on you.<r>\n\n')
        return

    mud.sendMessage(id, 'You are currently in possession of:<r>\n')
    for i in list(players[id]['inv']):
        if int(players[id]['clo_lhand']) == int(i):
            mud.sendMessage(id, ' * ' +
                            itemsDB[int(i)]['article'] +
                            ' <b234>' +
                            itemsDB[int(i)]['name'] +
                            '<r> (left hand)')
            continue

        if int(players[id]['clo_lleg']) == int(i):
            mud.sendMessage(id, ' * ' +
                            itemsDB[int(i)]['article'] +
                            ' <b234>' +
                            itemsDB[int(i)]['name'] +
                            '<r> (left leg)')
            continue

        if int(players[id]['clo_rleg']) == int(i):
            mud.sendMessage(id, ' * ' +
                            itemsDB[int(i)]['article'] +
                            ' <b234>' +
                            itemsDB[int(i)]['name'] +
                            '<r> (right leg)')
            continue

        if players[id].get('clo_gloves'):
            if int(players[id]['clo_gloves']) == int(i):
                mud.sendMessage(id, ' * ' +
                                itemsDB[int(i)]['article'] +
                                ' <b234>' +
                                itemsDB[int(i)]['name'] +
                                '<r> (hands)')
                continue

        if int(players[id]['clo_rhand']) == int(i):
            mud.sendMessage(id, ' * ' +
                            itemsDB[int(i)]['article'] +
                            ' <b234>' +
                            itemsDB[int(i)]['name'] +
                            '<r> (right hand)')
            continue

        if int(players[id]['clo_lfinger']) == int(i):
            mud.sendMessage(id, ' * ' +
                            itemsDB[int(i)]['article'] +
                            ' <b234>' +
                            itemsDB[int(i)]['name'] +
                            '<r> (finger of left hand)')
            continue

        if int(players[id]['clo_rfinger']) == int(i):
            mud.sendMessage(id, ' * ' +
                            itemsDB[int(i)]['article'] +
                            ' <b234>' +
                            itemsDB[int(i)]['name'] +
                            '<r> (finger of right hand)')
            continue

        if int(players[id]['clo_waist']) == int(i):
            mud.sendMessage(id, ' * ' +
                            itemsDB[int(i)]['article'] +
                            ' <b234>' +
                            itemsDB[int(i)]['name'] +
                            '<r> (waist)')
            continue

        if int(players[id]['clo_lear']) == int(i):
            mud.sendMessage(id, ' * ' +
                            itemsDB[int(i)]['article'] +
                            ' <b234>' +
                            itemsDB[int(i)]['name'] +
                            '<r> (left ear)')
            continue

        if int(players[id]['clo_rear']) == int(i):
            mud.sendMessage(id, ' * ' +
                            itemsDB[int(i)]['article'] +
                            ' <b234>' +
                            itemsDB[int(i)]['name'] +
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
            mud.sendMessage(id, ' * ' +
                            itemsDB[int(i)]['article'] +
                            ' <b234>' +
                            itemsDB[int(i)]['name'] +
                            '<r> (worn)')
            continue

        mud.sendMessage(id, ' * ' +
                        itemsDB[int(i)]['article'] +
                        ' <b234>' +
                        itemsDB[int(i)]['name'])
    mud.sendMessage(id, '<r>\n\n')


def _changeSetting(params, mud, playersDB: {}, players: {}, rooms: {},
                   npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                   envDB: {}, env: {}, eventDB: {}, eventSchedule,
                   id: int, fights: {}, corpses: {}, blocklist,
                   mapArea: [], characterClassDB: {}, spellsDB: {},
                   sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                   itemHistory: {}, markets: {}, culturesDB: {}):
    newPassword = ''
    if params.startswith('password '):
        newPassword = params.replace('password ', '')
    if params.startswith('pass '):
        newPassword = params.replace('pass ', '')
    if len(newPassword) > 0:
        if len(newPassword) < 6:
            mud.sendMessage(id, "That password is too short.\n\n")
            return
        players[id]['pwd'] = hash_password(newPassword)
        log("Player " + players[id]['name'] +
            " changed their password", "info")
        saveState(players[id], playersDB, True)
        mud.sendMessage(id, "Your password has been changed.\n\n")


def _writeOnItem(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                 envDB: {}, env: {}, eventDB: {}, eventSchedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 mapArea: [], characterClassDB: {}, spellsDB: {},
                 sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                 itemHistory: {}, markets: {}, culturesDB: {}):
    if ' on ' not in params:
        if ' onto ' not in params:
            if ' in ' not in params:
                if ' using ' not in params:
                    if ' with ' not in params:
                        mud.sendMessage(id, 'What?\n\n')
                        return
    msg = ''
    if ' using ' not in params:
        msg = params.split(' using ')[0].remove('"')
    if ' with ' not in params:
        msg = params.split(' with ')[0].remove('"')

    if len(msg) == 0:
        return
    if len(msg) > 64:
        mud.sendMessage(id, 'That message is too long.\n\n')


def _check(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
           envDB: {}, env: {}, eventDB: {}, eventSchedule,
           id: str, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    if params.lower() == 'inventory' or \
       params.lower() == 'inv':
        _checkInventory(params, mud, playersDB, players,
                        rooms, npcsDB, npcs, itemsDB, items,
                        envDB, env, eventDB, eventSchedule,
                        id, fights, corpses, blocklist,
                        mapArea, characterClassDB, spellsDB,
                        sentimentDB, guildsDB, clouds, racesDB,
                        itemHistory, markets, culturesDB)
    elif params.lower() == 'stats':
        mud.sendMessage(id, 'You check your character sheet.\n')
    else:
        mud.sendMessage(id, 'Check what?\n')


def _wear(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if len(params) < 1:
        mud.sendMessage(id, 'Specify an item from your inventory.\n\n')
        return

    if len(list(players[id]['inv'])) == 0:
        mud.sendMessage(id, 'You are not carrying that.\n\n')
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
        if itemsDB[int(i)]['name'].lower() == itemName:
            itemID = int(i)

    if itemID == 0:
        for i in list(players[id]['inv']):
            if itemName in itemsDB[int(i)]['name'].lower():
                itemID = int(i)

    if itemID == 0:
        mud.sendMessage(id, itemName + " is not in your inventory.\n\n")
        return

    for clothingType in wearLocation:
        if _wearClothing(itemID, players, id, clothingType, mud, itemsDB):
            return

    mud.sendMessage(id, "You can't wear that\n\n")


def _wield(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
           envDB: {}, env: {}, eventDB: {}, eventSchedule: {},
           id: int, fights: {}, corpses: {}, blocklist: {},
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if len(params) < 1:
        mud.sendMessage(id, 'Specify an item from your inventory.\n\n')
        return

    if len(list(players[id]['inv'])) == 0:
        mud.sendMessage(id, 'You are not carrying that.\n\n')
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
        if itemsDB[int(i)]['name'].lower() == itemName:
            itemID = int(i)

    if itemID == 0:
        for i in list(players[id]['inv']):
            if itemName in itemsDB[int(i)]['name'].lower():
                itemID = int(i)

    if itemID == 0:
        mud.sendMessage(id, itemName + " is not in your inventory.\n\n")
        return

    if itemsDB[itemID]['clo_lhand'] == 0 and \
       itemsDB[itemID]['clo_rhand'] == 0:
        mud.sendMessage(id, "You can't hold that.\n\n")
        return

    # items stowed on legs
    if int(players[id]['clo_lleg']) == itemID:
        players[id]['clo_lleg'] = 0
    if int(players[id]['clo_rleg']) == itemID:
        players[id]['clo_rleg'] = 0

    if itemHand == 0:
        if int(players[id]['clo_rhand']) == itemID:
            players[id]['clo_rhand'] = 0
        players[id]['clo_lhand'] = itemID
        mud.sendMessage(id, 'You hold <b234>' +
                        itemsDB[itemID]['article'] + ' ' +
                        itemsDB[itemID]['name'] +
                        '<r> in your left hand.\n\n')
    else:
        if int(players[id]['clo_lhand']) == itemID:
            players[id]['clo_lhand'] = 0
        players[id]['clo_rhand'] = itemID
        mud.sendMessage(id, 'You hold <b234>' +
                        itemsDB[itemID]['article'] + ' ' +
                        itemsDB[itemID]['name'] +
                        '<r> in your right hand.\n\n')


def _stow(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    if len(list(players[id]['inv'])) == 0:
        return

    stowFrom = ('clo_lhand', 'clo_rhand')
    for stowLocation in stowFrom:
        itemID = int(players[id][stowLocation])
        if itemID == 0:
            continue
        if int(itemsDB[itemID]['clo_rleg']) > 0:
            if int(players[id]['clo_rleg']) == 0:
                if int(players[id]['clo_lleg']) != itemID:
                    players[id]['clo_rleg'] = itemID
                    mud.sendMessage(id, 'You stow <b234>' +
                                    itemsDB[itemID]['article'] + ' ' +
                                    itemsDB[itemID]['name'] + '<r>\n\n')
                    players[id][stowLocation] = 0
                    continue

        if int(itemsDB[itemID]['clo_lleg']) > 0:
            if int(players[id]['clo_lleg']) == 0:
                if int(players[id]['clo_rleg']) != itemID:
                    players[id]['clo_lleg'] = itemID
                    mud.sendMessage(id, 'You stow <b234>' +
                                    itemsDB[itemID]['article'] + ' ' +
                                    itemsDB[itemID]['name'] + '<r>\n\n')
                    players[id][stowLocation] = 0

    stowHands(id, players, itemsDB, mud)


def _wearClothing(itemID, players: {}, id, clothingType,
                  mud, itemsDB: {}) -> bool:
    clothingParam = 'clo_' + clothingType
    if itemsDB[itemID][clothingParam] > 0:
        players[id][clothingParam] = itemID

        # handle items which are pairs
        if itemsDB[itemID]['article'] == 'some':
            if clothingType == 'lleg' or clothingType == 'rleg':
                players[id]['clo_lleg'] = itemID
                players[id]['clo_rleg'] = itemID
            elif clothingType == 'lhand' or clothingType == 'rhand':
                players[id]['clo_lhand'] = itemID
                players[id]['clo_rhand'] = itemID

        clothingOpened = False
        if len(itemsDB[itemID]['open_description']) > 0:
            # there is a special description for wearing
            desc = \
                randomDescription(itemsDB[itemID]['open_description'])
            if ' open' not in itemsDB[itemID]['open_description']:
                mud.sendMessage(id, desc + '\n\n')
                clothingOpened = True
        if not clothingOpened:
            # generic weating description
            mud.sendMessage(
                id,
                'You put on ' +
                itemsDB[itemID]['article'] +
                ' <b234>' +
                itemsDB[itemID]['name'] +
                '\n\n')
        return True
    return False


def _removeClothing(players: {}, id, clothingType, mud, itemsDB: {}):
    if int(players[id]['clo_' + clothingType]) > 0:
        itemID = int(players[id]['clo_' + clothingType])
        clothingClosed = False
        if len(itemsDB[itemID]['close_description']) > 0:
            desc = itemsDB[itemID]['open_description']
            if ' close ' not in desc and \
               'closed' not in desc and \
               'closing' not in desc and \
               'shut' not in desc:
                desc = \
                    randomDescription(itemsDB[itemID]['close_description'])
                mud.sendMessage(id, desc + '\n\n')
                clothingClosed = True
        if not clothingClosed:
            mud.sendMessage(id, 'You remove ' +
                            itemsDB[itemID]['article'] + ' <b234>' +
                            itemsDB[itemID]['name'] + '\n\n')

        # handle items which are pairs
        if itemsDB[itemID]['article'] == 'some':
            if clothingType == 'lleg' or clothingType == 'rleg':
                players[id]['clo_lleg'] = 0
                players[id]['clo_rleg'] = 0
            elif clothingType == 'lhand' or clothingType == 'rhand':
                players[id]['clo_lhand'] = 0
                players[id]['clo_rhand'] = 0

        players[id]['clo_' + clothingType] = 0


def _unwear(params, mud, playersDB: {}, players: {}, rooms: {},
            npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
            envDB: {}, env: {}, eventDB: {}, eventSchedule,
            id: int, fights: {}, corpses: {}, blocklist,
            mapArea: [], characterClassDB: {}, spellsDB: {},
            sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
            itemHistory: {}, markets: {}, culturesDB: {}):
    if len(list(players[id]['inv'])) == 0:
        return

    for clothingType in wearLocation:
        _removeClothing(players, id, clothingType, mud, itemsDB)


def _playersMoveTogether(id, rm, mud,
                         playersDB, players, rooms: {}, npcsDB: {}, npcs,
                         itemsDB: {}, items: {}, envDB: {}, env, eventDB: {},
                         eventSchedule,
                         fights, corpses, blocklist, mapArea,
                         characterClassDB: {}, spellsDB: {},
                         sentimentDB: {}, guildsDB: {}, clouds, racesDB: {},
                         itemHistory: {}, markets: {}, culturesDB: {}) -> None:
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
            mud.sendMessage(pid, desc + "\n\n")

            _look('', mud, playersDB, players, rooms, npcsDB, npcs,
                  itemsDB, items, envDB, env, eventDB, eventSchedule,
                  pid, fights, corpses, blocklist, mapArea,
                  characterClassDB, spellsDB, sentimentDB, guildsDB,
                  clouds, racesDB, itemHistory, markets, culturesDB)

            if rooms[rm]['eventOnEnter'] != "":
                evID = int(rooms[rm]['eventOnEnter'])
                addToScheduler(evID, pid, eventSchedule, eventDB)


def _bioOfPlayer(mud, id, pid, players: {}, itemsDB: {}) -> None:
    thisPlayer = players[pid]
    if thisPlayer.get('race'):
        if len(thisPlayer['race']) > 0:
            mud.sendMessage(id, '****CLEAR****<f32>' +
                            thisPlayer['name'] + '<r> (' +
                            thisPlayer['race'] + ' ' +
                            thisPlayer['characterClass'] + ')\n')

    if thisPlayer.get('speakLanguage'):
        mud.sendMessage(
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
                mud.sendMessage(id, 'Languages:<r> ' + languagesStr + '\n')

    desc = \
        randomDescription(thisPlayer['lookDescription'])
    mud.sendMessageWrap(id, '', desc + '<r>\n')

    if thisPlayer.get('canGo'):
        if thisPlayer['canGo'] == 0:
            mud.sendMessage(id, 'They are frozen.<r>\n')

    # count items of clothing
    wearingCtr = 0
    for c in wearLocation:
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
        itemName = itemsDB[handItemID]['name']
        if 'right hand ' in itemName:
            itemName = itemName.replace('right hand ', '')
        elif 'right handed ' in itemName:
            itemName = itemName.replace('right handed ', '')
        mud.sendMessage(id, playerName + ' ' + playerName3 + ' ' +
                        itemsDB[handItemID]['article'] +
                        ' ' + itemName +
                        ' in ' + playerName2 + ' right hand.<r>\n')
    if thisPlayer.get('clo_rfinger'):
        if int(thisPlayer['clo_rfinger']) > 0:
            mud.sendMessage(id, playerName + ' ' + playerName3 + ' ' +
                            itemsDB[thisPlayer['clo_rfinger']]['article'] +
                            ' ' +
                            itemsDB[thisPlayer['clo_rfinger']]['name'] +
                            ' on the finger of ' + playerName2 +
                            ' right hand.<r>\n')
    if thisPlayer.get('clo_waist'):
        if int(thisPlayer['clo_waist']) > 0:
            mud.sendMessage(id, playerName + ' ' + playerName3 + ' ' +
                            itemsDB[thisPlayer['clo_waist']]['article'] +
                            ' ' +
                            itemsDB[thisPlayer['clo_waist']]['name'] +
                            ' on waist of ' + playerName2 + '<r>\n')
    if int(thisPlayer['clo_lhand']) > 0:
        handItemID = thisPlayer['clo_lhand']
        itemName = itemsDB[handItemID]['name']
        if 'left hand ' in itemName:
            itemName = itemName.replace('left hand ', '')
        elif 'left handed ' in itemName:
            itemName = itemName.replace('left handed ', '')
        mud.sendMessage(id, playerName + ' ' + playerName3 + ' ' +
                        itemsDB[thisPlayer['clo_lhand']]['article'] +
                        ' ' + itemName +
                        ' in ' + playerName2 + ' left hand.<r>\n')
    if int(thisPlayer['clo_lear']) > 0:
        handItemID = thisPlayer['clo_lear']
        itemName = itemsDB[handItemID]['name']
        mud.sendMessage(id, playerName + ' ' + playerName3 + ' ' +
                        itemsDB[thisPlayer['clo_lear']]['article'] +
                        ' ' + itemName +
                        ' in ' + playerName2 + ' left ear.<r>\n')
    if int(thisPlayer['clo_rear']) > 0:
        handItemID = thisPlayer['clo_rear']
        itemName = itemsDB[handItemID]['name']
        mud.sendMessage(id, playerName + ' ' + playerName3 + ' ' +
                        itemsDB[thisPlayer['clo_rear']]['article'] +
                        ' ' + itemName +
                        ' in ' + playerName2 + ' right ear.<r>\n')
    if thisPlayer.get('clo_lfinger'):
        if int(thisPlayer['clo_lfinger']) > 0:
            mud.sendMessage(id, playerName + ' ' + playerName3 + ' ' +
                            itemsDB[thisPlayer['clo_lfinger']]['article'] +
                            ' ' + itemsDB[thisPlayer['clo_lfinger']]['name'] +
                            ' on the finger of ' + playerName2 +
                            ' left hand.<r>\n')

    if wearingCtr > 0:
        wearingMsg = playerName + ' are wearing'
        wearingCtr2 = 0
        for cl in wearLocation:
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
                    itemsDB[clothingItemID]['article'] + \
                    ' ' + itemsDB[clothingItemID]['name']
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
        mud.sendMessage(id, wearingMsg + '.<r>\n')

    mud.sendMessage(id, '<f15>Health status:<r> ' +
                    healthOfPlayer(pid, players) + '.<r>\n')
    mud.sendMessage(id, '<r>\n')


def _health(params, mud, playersDB: {}, players: {}, rooms: {},
            npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
            envDB: {}, env: {}, eventDB: {}, eventSchedule,
            id: int, fights: {}, corpses: {}, blocklist,
            mapArea: [], characterClassDB: {}, spellsDB: {},
            sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
            itemHistory: {}, markets: {}, culturesDB: {}):
    mud.sendMessage(id, '<r>\n')
    mud.sendMessage(id, '<f15>Health status:<r> ' +
                    healthOfPlayer(id, players) + '.<r>\n')


def _bio(params, mud, playersDB: {}, players: {}, rooms: {},
         npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
         envDB: {}, env: {}, eventDB: {}, eventSchedule,
         id: int, fights: {}, corpses: {}, blocklist,
         mapArea: [], characterClassDB: {}, spellsDB: {},
         sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
         itemHistory: {}, markets: {}, culturesDB: {}):
    if len(params) == 0:
        _bioOfPlayer(mud, id, id, players, itemsDB)
        return

    if params == players[id]['name']:
        _bioOfPlayer(mud, id, id, players, itemsDB)
        return

    # go through all the players in the game
    if players[id]['authenticated'] is not None:
        for (pid, pl) in list(players.items()):
            if players[pid]['name'] == params:
                _bioOfPlayer(mud, id, pid, players, itemsDB)
                return

    if players[id]['name'].lower() == 'guest':
        mud.sendMessage(id, "Guest players cannot set a bio.\n\n")
        return

    if players[id]['canSay'] == 0:
        mud.sendMessage(
            id, "You try to describe yourself, " +
            "but find you have nothing to say.\n\n")
        return

    if '"' in params:
        mud.sendMessage(id, "Your bio must not include double quotes.\n\n")
        return

    if params.startswith(':'):
        params = params.replace(':', '').strip()

    players[id]['lookDescription'] = params
    mud.sendMessage(id, "Your bio has been set.\n\n")


def _eat(params, mud, playersDB: {}, players: {}, rooms: {},
         npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
         envDB: {}, env: {}, eventDB: {}, eventSchedule,
         id: int, fights: {}, corpses: {}, blocklist,
         mapArea: [], characterClassDB: {}, spellsDB: {},
         sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
         itemHistory: {}, markets: {}, culturesDB: {}):
    food = params.lower()
    foodItemID = 0
    if len(list(players[id]['inv'])) > 0:
        for i in list(players[id]['inv']):
            if food in itemsDB[int(i)]['name'].lower():
                if itemsDB[int(i)]['edible'] != 0:
                    foodItemID = int(i)
                    break
                else:
                    mud.sendMessage(id, "That's not consumable.\n\n")
                    return

    if foodItemID == 0:
        mud.sendMessage(id, "Your don't have " + params + ".\n\n")
        return

    mud.sendMessage(id, "You consume " + itemsDB[foodItemID]['article'] +
                    " " + itemsDB[foodItemID]['name'] + ".\n\n")

    # Alter hp
    players[id]['hp'] = players[id]['hp'] + itemsDB[foodItemID]['edible']
    if players[id]['hp'] > 100:
        players[id]['hp'] = 100

    # Consumed
    players[id]['inv'].remove(str(foodItemID))

    # decrement any attributes associated with the food
    updatePlayerAttributes(id, players, itemsDB, foodItemID, -1)

    # Remove from hands
    if int(players[id]['clo_rhand']) == foodItemID:
        players[id]['clo_rhand'] = 0
    if int(players[id]['clo_lhand']) == foodItemID:
        players[id]['clo_lhand'] = 0


def _stepOver(params, mud, playersDB: {}, players: {}, rooms: {},
              npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
              envDB: {}, env: {}, eventDB: {}, eventSchedule,
              id: int, fights: {}, corpses: {}, blocklist,
              mapArea: [], characterClassDB: {}, spellsDB: {},
              sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
              itemHistory: {}, markets: {}, culturesDB: {}):
    roomID = players[id]['room']
    if not rooms[roomID]['trap'].get('trapActivation'):
        mud.sendMessage(
            id, randomDescription("You don't notice a tripwire") +
            '.\n\n')
        return
    if rooms[roomID]['trap']['trapActivation'] != 'tripwire':
        mud.sendMessage(
            id, randomDescription(
                "You don't notice a tripwire|You don't see a tripwire") +
            '.\n\n')
        return
    if 'over ' not in params:
        mud.sendMessage(
            id, randomDescription(
                "Do what?|Eh?") + '.\n\n')
        return

    for direction, ex in rooms[roomID]['exits'].items():
        if direction in params:
            _go('######step######' + direction, mud, playersDB, players,
                rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB,
                eventSchedule, id, fights, corpses, blocklist, mapArea,
                characterClassDB, spellsDB, sentimentDB, guildsDB,
                clouds, racesDB, itemHistory, markets, culturesDB)
            break


def _climbBase(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               sit: bool, itemHistory: {}, markets: {}, culturesDB: {}):
    """Climbing through or into an item takes the player to a different room
    """
    if players[id]['canGo'] != 1:
        mud.sendMessage(id, "You try to move but find that you " +
                        "lack any ability to.\n\n")
        return

    if playerIsProne(id, players):
        mud.sendMessage(id, randomDescription('You stand up<r>\n\n'))
        setPlayerProne(id, players, False)
        return

    failMsg = None
    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            itemId = items[item]['id']

            # can the player see the item?
            if not _itemIsVisible(id, players, itemId, itemsDB):
                continue

            # item fields needed for climbing
            if itemsDB[itemId].get('climbFail'):
                failMsg = itemsDB[itemId]['climbFail']
            if not itemsDB[itemId].get('climbThrough'):
                continue
            if not itemsDB[itemId].get('exit'):
                continue

            # if this is a door is it open?
            if itemsDB[itemId].get('state'):
                if 'open' not in itemsDB[itemId]['state']:
                    mud.sendMessage(id, itemsDB[itemId]['name'] +
                                    " is closed.\n\n")
                    continue

            # is the player too big?
            targetRoom = itemsDB[itemId]['exit']
            if rooms[targetRoom]['maxPlayerSize'] > -1:
                if players[id]['siz'] > rooms[targetRoom]['maxPlayerSize']:
                    mud.sendMessage(id, "You're too big.\n\n")
                    return

            # are there too many players in the room?
            if rooms[targetRoom]['maxPlayers'] > -1:
                if _playersInRoom(targetRoom, players, npcs) >= \
                   rooms[targetRoom]['maxPlayers']:
                    if not sit:
                        mud.sendMessage(id, "It's too crowded.\n\n")
                    else:
                        mud.sendMessage(id, "It's already fully occupied.\n\n")
                    return

            if not _itemIsClimbable(id, players, itemId, itemsDB):
                if failMsg:
                    mud.sendMessage(id, randomDescription(failMsg) + ".\n\n")
                else:
                    if not sit:
                        failMsg = 'You try to climb, but totally fail'
                    else:
                        failMsg = 'You try to sit, but totally fail'
                    mud.sendMessage(id, randomDescription(failMsg) + ".\n\n")
                return

            desc = \
                randomDescription(players[id]['outDescription'])
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   desc + '\n')

            # Trigger old room eventOnLeave for the player
            if rooms[players[id]['room']]['eventOnLeave'] != "":
                evLeave = int(rooms[players[id]['room']]['eventOnLeave'])
                addToScheduler(evLeave, id, eventSchedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = targetRoom
            # climbing message
            desc = \
                randomDescription(itemsDB[itemId]['climbThrough'])
            mud.sendMessageWrap(id, '<f230>', desc + "\n\n")
            time.sleep(3)
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] != "":
                evEnter = int(rooms[players[id]['room']]['eventOnEnter'])
                addToScheduler(evEnter, id, eventSchedule, eventDB)
            # message to other players
            desc = randomDescription(players[id]['inDescription'])
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   desc + "\n\n")
            # look after climbing
            _look('', mud, playersDB, players, rooms,
                  npcsDB, npcs, itemsDB, items,
                  envDB, env, eventDB, eventSchedule,
                  id, fights, corpses, blocklist,
                  mapArea, characterClassDB, spellsDB,
                  sentimentDB, guildsDB, clouds, racesDB,
                  itemHistory, markets, culturesDB)
            return
    if failMsg:
        mud.sendMessage(id, randomDescription(failMsg) + ".\n\n")
    else:
        mud.sendMessage(id, "Nothing happens.\n\n")


def _climb(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
           envDB: {}, env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    _climbBase(params, mud, playersDB, players, rooms,
               npcsDB, npcs, itemsDB, items,
               envDB, env, eventDB, eventSchedule,
               id, fights, corpses, blocklist,
               mapArea, characterClassDB, spellsDB,
               sentimentDB, guildsDB, clouds, racesDB,
               False, itemHistory, markets, culturesDB)


def _sit(params, mud, playersDB: {}, players: {}, rooms: {},
         npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
         envDB: {}, env: {}, eventDB: {}, eventSchedule,
         id: int, fights: {}, corpses: {}, blocklist,
         mapArea: [], characterClassDB: {}, spellsDB: {},
         sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
         itemHistory: {}, markets: {}, culturesDB: {}):
    _climbBase(params, mud, playersDB, players, rooms,
               npcsDB, npcs, itemsDB, items,
               envDB, env, eventDB, eventSchedule,
               id, fights, corpses, blocklist,
               mapArea, characterClassDB, spellsDB,
               sentimentDB, guildsDB, clouds, racesDB,
               True, itemHistory, markets, culturesDB)


def _heave(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
           envDB: {}, env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    """Roll/heave an item takes the player to a different room
    """
    if players[id]['canGo'] != 1:
        mud.sendMessage(id, "You try to move but find that " +
                        "you lack any ability to.\n\n")
        return

    if playerIsProne(id, players):
        mud.sendMessage(id, randomDescription('You stand up<r>\n\n'))
        setPlayerProne(id, players, False)
        return

    target = params.lower()
    if target.startswith('the '):
        target = target.replace('the ', '')

    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            itemId = items[item]['id']
            if not _itemIsVisible(id, players, itemId, itemsDB):
                continue
            if not itemsDB[itemId].get('heave'):
                continue
            if not itemsDB[itemId].get('exit'):
                continue
            if target not in itemsDB[itemId]['name']:
                continue
            if itemsDB[itemId].get('state'):
                if 'open' not in itemsDB[itemId]['state']:
                    mud.sendMessage(id, itemsDB[itemId]['name'] +
                                    " is closed.\n\n")
                    continue
            targetRoom = itemsDB[itemId]['exit']
            if rooms[targetRoom]['maxPlayerSize'] > -1:
                if players[id]['siz'] > rooms[targetRoom]['maxPlayerSize']:
                    mud.sendMessage(id, "You're too big.\n\n")
                    return
            if rooms[targetRoom]['maxPlayers'] > -1:
                if _playersInRoom(targetRoom, players, npcs) >= \
                   rooms[targetRoom]['maxPlayers']:
                    mud.sendMessage(id, "It's too crowded.\n\n")
                    return
            desc = randomDescription(players[id]['outDescription'])
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   desc + '\n')
            # Trigger old room eventOnLeave for the player
            if rooms[players[id]['room']]['eventOnLeave'] != "":
                evLeave = int(rooms[players[id]['room']]['eventOnLeave'])
                addToScheduler(evLeave, id, eventSchedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = targetRoom
            # heave message
            desc = randomDescription(itemsDB[itemId]['heave'])
            mud.sendMessageWrap(id, '<f220>', desc + "\n\n")
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] != "":
                evEnter = int(rooms[players[id]['room']]['eventOnEnter'])
                addToScheduler(evEnter, id, eventSchedule, eventDB)
            # message to other players
            desc = randomDescription(players[id]['inDescription'])
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   desc + "\n\n")
            time.sleep(3)
            # look after climbing
            _look('', mud, playersDB, players, rooms,
                  npcsDB, npcs, itemsDB, items,
                  envDB, env, eventDB, eventSchedule, id,
                  fights, corpses, blocklist,
                  mapArea, characterClassDB, spellsDB,
                  sentimentDB, guildsDB, clouds, racesDB,
                  itemHistory, markets, culturesDB)
            return
    mud.sendMessage(id, "Nothing happens.\n\n")


def _jump(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    """Jumping onto an item takes the player to a different room
    """
    if players[id]['canGo'] != 1:
        mud.sendMessage(id, "You try to move but find that you " +
                        "lack any ability to.\n\n")
        return

    if playerIsProne(id, players):
        mud.sendMessage(id, randomDescription('You stand up<r>\n\n'))
        setPlayerProne(id, players, False)
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
        mud.sendMessage(id, randomDescription(desc) + "\n\n")
        return
    words = params.lower().replace('.', '').split(' ')
    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            itemId = items[item]['id']
            if not _itemIsVisible(id, players, itemId, itemsDB):
                continue
            if not itemsDB[itemId].get('jumpTo'):
                continue
            if not itemsDB[itemId].get('exit'):
                continue
            wordMatched = False
            for w in words:
                if w in itemsDB[itemId]['name'].lower():
                    wordMatched = True
                    break
            if not wordMatched:
                continue
            if itemsDB[itemId].get('state'):
                if 'open' not in itemsDB[itemId]['state']:
                    mud.sendMessage(id, itemsDB[itemId]['name'] +
                                    " is closed.\n\n")
                    continue
            targetRoom = itemsDB[itemId]['exit']
            if rooms[targetRoom]['maxPlayerSize'] > -1:
                if players[id]['siz'] > rooms[targetRoom]['maxPlayerSize']:
                    mud.sendMessage(id, "You're too big.\n\n")
                    return
            if rooms[targetRoom]['maxPlayers'] > -1:
                if _playersInRoom(targetRoom, players, npcs) >= \
                   rooms[targetRoom]['maxPlayers']:
                    mud.sendMessage(id, "It's too crowded.\n\n")
                    return
            desc = \
                randomDescription(players[id]['outDescription'])
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   desc + '\n')
            # Trigger old room eventOnLeave for the player
            if rooms[players[id]['room']]['eventOnLeave'] != "":
                evLeave = int(rooms[players[id]['room']]['eventOnLeave'])
                addToScheduler(evLeave, id, eventSchedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = targetRoom
            # climbing message
            desc = randomDescription(itemsDB[itemId]['jumpTo'])
            mud.sendMessageWrap(id, '<f230>', desc + "\n\n")
            time.sleep(3)
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] != "":
                evEnter = int(rooms[players[id]['room']]['eventOnEnter'])
                addToScheduler(evEnter, id, eventSchedule, eventDB)
            # message to other players
            desc = randomDescription(players[id]['inDescription'])
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   desc + "\n\n")
            # look after climbing
            _look('', mud, playersDB, players,
                  rooms, npcsDB, npcs, itemsDB, items,
                  envDB, env, eventDB, eventSchedule,
                  id, fights, corpses, blocklist,
                  mapArea, characterClassDB, spellsDB,
                  sentimentDB, guildsDB, clouds, racesDB,
                  itemHistory, markets, culturesDB)
            return
    desc = (
        "You jump, expecting something to happen. But it doesn't.",
        "Jumping doesn't help.",
        "You jump. Nothing happens.",
        "In this situation jumping only adds to the confusion.",
        "You jump up and down on the spot.",
        "You jump, and then feel vaguely silly."
    )
    mud.sendMessage(id, randomDescription(desc) + "\n\n")


def _chessBoardInRoom(players: {}, id, rooms: {}, items: {}, itemsDB: {}):
    """Returns the item ID if there is a chess board in the room
    """
    rid = players[id]['room']
    for i in items:
        if items[i]['room'] != rid:
            continue
        if 'chess' in itemsDB[items[i]['id']]['game'].lower():
            return i
    return None


def _chessBoardName(players: {}, id, rooms: {}, items: {}, itemsDB: {}):
    """Returns the name of the chess board if there is one in the room
    This then corresponds to the subdirectory within chessboards, where
    icons exist
    """
    rid = players[id]['room']
    for i in items:
        if items[i]['room'] != rid:
            continue
        if itemsDB[items[i]['id']].get('chessBoardName'):
            return itemsDB[items[i]['id']]['chessBoardName']
    return None


def _deal(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    """Deal cards to other players
    """
    paramsLower = params.lower()
    dealToPlayers(players, id, paramsLower, mud, rooms, items, itemsDB)


def _handOfCards(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                 envDB: {}, env: {}, eventDB: {}, eventSchedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 mapArea: [], characterClassDB: {}, spellsDB: {},
                 sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                 itemHistory: {}, markets: {}, culturesDB: {}):
    """Show hand of cards
    """
    showHandOfCards(players, id, mud, rooms, items, itemsDB)


def _swapACard(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    """Swap a playing card for another from the deck
    """
    swapCard(params, players, id, mud, rooms, items, itemsDB)


def _shuffle(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
             envDB: {}, env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: [], characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
    """Shuffle a deck of cards
    """
    shuffleCards(players, id, mud, rooms, items, itemsDB)


def _callCardGame(params, mud, playersDB: {}, players: {}, rooms: {},
                  npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                  envDB: {}, env: {}, eventDB: {}, eventSchedule,
                  id: int, fights: {}, corpses: {}, blocklist,
                  mapArea: [], characterClassDB: {}, spellsDB: {},
                  sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                  itemHistory: {}, markets: {}, culturesDB: {}):
    """Players show their cards
    """
    callCards(players, id, mud, rooms, items, itemsDB)


def _morrisGame(params, mud, playersDB: {}, players: {}, rooms: {},
                npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                envDB: {}, env: {}, eventDB: {}, eventSchedule,
                id: int, fights: {}, corpses: {}, blocklist,
                mapArea: [], characterClassDB: {}, spellsDB: {},
                sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                itemHistory: {}, markets: {}, culturesDB: {}):
    """Show the nine men's morris board
    """
    params = params.lower()
    if params.startswith('reset') or \
       params.startswith('clear'):
        resetMorrisBoard(players, id, mud, rooms, items, itemsDB)
        return

    if params.startswith('take') or \
       params.startswith('remove') or \
       params.startswith('capture'):
        takeMorrisCounter(params, players, id, mud, rooms, items, itemsDB)
        return

    if params.startswith('move ') or \
       params.startswith('play ') or \
       params.startswith('put ') or \
       params.startswith('counter ') or \
       params.startswith('place '):
        morrisMove(params, players, id, mud, rooms,
                   items, itemsDB)
        return

    boardName = getMorrisBoardName(players, id, rooms, items, itemsDB)
    showMorrisBoard(boardName, players, id, mud, rooms, items, itemsDB)


def _chess(params, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
           envDB: {}, env: {}, eventDB: {}, eventSchedule,
           id: int, fights: {}, corpses: {}, blocklist,
           mapArea: [], characterClassDB: {}, spellsDB: {},
           sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}):
    """Jumping onto an item takes the player to a different room
    """
    # check if board exists in room
    boardItemID = \
        _chessBoardInRoom(players, id, rooms, items, itemsDB)
    if not boardItemID:
        mud.sendMessage(id, "\nThere isn't a chess board here.\n\n")
        return
    # create the game state
    if not items[boardItemID].get('gameState'):
        items[boardItemID]['gameState'] = {}
    if not items[boardItemID]['gameState'].get('state'):
        items[boardItemID]['gameState']['state'] = initialChessBoard()
        items[boardItemID]['gameState']['turn'] = 'white'
        items[boardItemID]['gameState']['history'] = []
    # get the game history
    gameState = items[boardItemID]['gameState']['state']
    gameBoardName = \
        _chessBoardName(players, id, rooms, items, itemsDB)
    if not params:
        showChessBoard(gameBoardName, gameState, id, mud,
                       items[boardItemID]['gameState']['turn'])
        return
    if players[id]['canGo'] != 1 or \
       players[id]['frozenStart'] > 0:
        desc = (
            "You try to make a chess move but find " +
            "that you lack any ability to",
            "You suddenly lose all enthusiasm for chess"
        )
        mud.sendMessage(id, '\n' + randomDescription(desc) + ".\n\n")
        return
    params = params.lower().strip()
    if 'undo' in params:
        if len(items[boardItemID]['gameState']['history']) < 2:
            params = 'reset'
        else:
            mud.sendMessage(id, '\nUndoing last chess move.\n')
            items[boardItemID]['gameState']['history'].pop()
            gameState = items[boardItemID]['gameState']['history'][-1]
            items[boardItemID]['gameState']['state'] = gameState
            if items[boardItemID]['gameState']['turn'] == 'white':
                items[boardItemID]['gameState']['turn'] = 'black'
            else:
                items[boardItemID]['gameState']['turn'] = 'white'
            showChessBoard(gameBoardName, gameState, id, mud,
                           items[boardItemID]['gameState']['turn'])
            return
    # begin a new chess game
    if 'reset' in params or \
       'restart' in params or \
       'start again' in params or \
       'begin again' in params or \
       'new game' in params:
        mud.sendMessage(id, '\nStarting a new game.\n')
        items[boardItemID]['gameState']['state'] = initialChessBoard()
        items[boardItemID]['gameState']['turn'] = 'white'
        items[boardItemID]['gameState']['history'] = []
        gameState = items[boardItemID]['gameState']['state']
        showChessBoard(gameBoardName, gameState, id, mud,
                       items[boardItemID]['gameState']['turn'])
        return
    if 'move' in params:
        params = params.replace('move ', '').replace('to ', '')
        params = params.replace('from ', '').replace('.', '')
        params = params.replace('-', '').strip()
        chessMoves = params.split(' ')

        if len(chessMoves) == 1:
            if len(params) != 4:
                mud.sendMessage(id, "\nEnter a move such as g8f6.\n")
                return
            chessMoves = [params[:2], params[2:]]

        if len(chessMoves) != 2:
            mud.sendMessage(id, "\nThat's not a valid move.\n")
            return
        if len(chessMoves[0]) != 2 or \
           len(chessMoves[1]) != 2:
            mud.sendMessage(id, "\nEnter a move such as g8 f6.\n")
            return
        if moveChessPiece(chessMoves[0] + chessMoves[1],
                          items[boardItemID]['gameState']['state'],
                          items[boardItemID]['gameState']['turn'],
                          id, mud):
            mud.sendMessage(id, "\n" +
                            items[boardItemID]['gameState']['turn'] +
                            " moves from " + chessMoves[0] +
                            " to " + chessMoves[1] + ".\n")
            gameState = items[boardItemID]['gameState']['state']
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
                                showChessBoard(gameBoardName,
                                               gameState, p, mud,
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
                                showChessBoard(gameBoardName, gameState,
                                               p, mud, turnStr)
            items[boardItemID]['gameState']['history'].append(gameState.copy())
            showChessBoard(gameBoardName, gameState, id, mud, currTurn)
            return
        else:
            mud.sendMessage(id, "\nThat's not a valid move.\n")
            return
    showChessBoard(gameBoardName, gameState, id, mud,
                   items[boardItemID]['gameState']['turn'])


def _graphics(params, mud, playersDB: {}, players: {}, rooms: {},
              npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
              envDB: {}, env: {}, eventDB: {}, eventSchedule,
              id: int, fights: {}, corpses: {}, blocklist,
              mapArea: [], characterClassDB: {}, spellsDB: {},
              sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
              itemHistory: {}, markets: {}, culturesDB: {}):
    """Turn graphical output on or off
    """
    graphicsState = params.lower().strip()
    if graphicsState == 'off' or \
       graphicsState == 'false' or \
       graphicsState == 'no':
        players[id]['graphics'] = 'off'
        mud.sendMessage(id, "Graphics have been turned off.\n\n")
    else:
        players[id]['graphics'] = 'on'
        mud.sendMessage(id, "Graphics have been activated.\n\n")


def _showItemsForSale(mud, rooms: {}, roomID, players: {}, id, itemsDB: {}):
    """Shows items for sale within a market
    """
    if not rooms[roomID].get('marketInventory'):
        return
    mud.sendMessage(id, '\nFor Sale\n')
    ctr = 0
    for itemID, item in rooms[roomID]['marketInventory'].items():
        if item['stock'] < 1:
            continue
        itemLine = itemsDB[itemID]['name']
        while len(itemLine) < 30:
            itemLine += '.'
        itemCost = item['cost']
        if itemCost == '0':
            itemLine += 'Free'
        else:
            itemLine += itemCost
        mud.sendMessage(id, itemLine)
        ctr += 1
    mud.sendMessage(id, '\n')
    if ctr == 0:
        mud.sendMessage(id, 'Nothing\n\n')


def _buy(params, mud, playersDB: {}, players: {}, rooms: {},
         npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
         envDB: {}, env: {}, eventDB: {}, eventSchedule,
         id: int, fights: {}, corpses: {}, blocklist,
         mapArea: [], characterClassDB: {}, spellsDB: {},
         sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
         itemHistory: {}, markets: {}, culturesDB: {}):
    """Buy from a market
    """
    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '<r>\n\n')
        return

    if playerIsTrapped(id, players, rooms):
        describeTrappedPlayer(mud, id, players, rooms)
        return

    if playerIsProne(id, players):
        mud.sendMessage(id, randomDescription('You stand up<r>\n\n'))
        setPlayerProne(id, players, False)
        return

    if players[id]['canGo'] != 1:
        mud.sendMessage(id,
                        'Somehow, your body refuses to move.<r>\n')
        return

    roomID = players[id]['room']
    if not rooms[roomID].get('marketInventory'):
        mud.sendMessage(id, 'There is nothing to buy here.<r>\n')
        return

    paramsLower = params.lower()
    if not paramsLower:
        _showItemsForSale(mud, rooms, roomID, players, id, itemsDB)
    else:
        # buy some particular item
        for itemID, item in rooms[roomID]['marketInventory'].items():
            if item['stock'] < 1:
                continue
            itemName = itemsDB[itemID]['name'].lower()
            if itemName not in paramsLower:
                continue
            if _itemInInventory(players, id, itemsDB[itemID]['name'], itemsDB):
                mud.sendMessage(id, 'You already have that\n\n')
                return
            itemCost = item['cost']
            if buyItem(players, id, itemID, itemsDB, itemCost):
                # is the item too heavy?
                players[id]['wei'] = \
                    playerInventoryWeight(id, players, itemsDB)

                if players[id]['wei'] + itemsDB[itemID]['weight'] > \
                   _getMaxWeight(id, players):
                    mud.sendMessage(id, "You can't carry any more.\n\n")
                    return
                # add the item to the player's inventory
                if str(itemID) not in players[id]['inv']:
                    players[id]['inv'].append(str(itemID))
                # update the weight of the player
                players[id]['wei'] = \
                    playerInventoryWeight(id, players, itemsDB)
                updatePlayerAttributes(id, players, itemsDB, itemID, 1)

                mud.sendMessage(id, 'You buy ' + itemsDB[itemID]['article'] +
                                ' ' + itemsDB[itemID]['name'] + '\n\n')
            else:
                if itemCost.endswith('gp'):
                    mud.sendMessage(id,
                                    'You do not have enough gold pieces\n\n')
                elif itemCost.endswith('sp'):
                    mud.sendMessage(id,
                                    'You do not have enough silver pieces\n\n')
                elif itemCost.endswith('cp'):
                    mud.sendMessage(id,
                                    'You do not have enough copper pieces\n\n')
                elif itemCost.endswith('ep'):
                    mud.sendMessage(id,
                                    'You do not have enough ' +
                                    'electrum pieces\n\n')
                elif itemCost.endswith('pp'):
                    mud.sendMessage(id,
                                    'You do not have enough ' +
                                    'platinum pieces\n\n')
                else:
                    mud.sendMessage(id, 'You do not have enough money\n\n')
            return
        mud.sendMessage(id, "That's not sold here\n\n")


def _sell(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    """Sell in a market
    """
    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '<r>\n\n')
        return

    if playerIsTrapped(id, players, rooms):
        describeTrappedPlayer(mud, id, players, rooms)
        return

    if playerIsProne(id, players):
        mud.sendMessage(id, randomDescription('You stand up<r>\n\n'))
        setPlayerProne(id, players, False)
        return

    if players[id]['canGo'] != 1:
        mud.sendMessage(id,
                        'Somehow, your body refuses to move.<r>\n')
        return

    roomID = players[id]['room']
    if not rooms[roomID].get('marketInventory'):
        mud.sendMessage(id, "You can't sell here.<r>\n")
        return

    paramsLower = params.lower()
    if not paramsLower:
        mud.sendMessage(id, 'What do you want to sell?\n')
    else:
        # does this market buy this type of item?
        marketType = getMarketType(rooms[roomID]['name'], markets)
        if not marketType:
            mud.sendMessage(id, "You can't sell here.<r>\n")
            return
        buysItemTypes = marketBuysItemTypes(marketType, markets)
        ableToSell = False
        for itemType in buysItemTypes:
            if itemType in paramsLower:
                ableToSell = True
                break
        if not ableToSell:
            mud.sendMessage(id, "You can't sell that here\n\n")
            return
        itemID = -1
        for (item, pl) in list(items.items()):
            if paramsLower in itemsDB[items[item]['id']]['name'].lower():
                itemID = items[item]['id']
                break
        if itemID == -1:
            mud.sendMessage(id, 'Error: item not found ' + params + ' \n\n')
            return
        # remove from item to the player's inventory
        if str(itemID) in players[id]['inv']:
            players[id]['inv'].remove(str(itemID))
        # update the weight of the player
        players[id]['wei'] = playerInventoryWeight(id, players, itemsDB)
        updatePlayerAttributes(id, players, itemsDB, itemID, 1)

        # Increase your money
        itemCost = itemsDB[itemID]['cost']
        denomination = 'gp'
        if itemCost.endswith('cp'):
            denomination = 'cp'
        elif itemCost.endswith('ep'):
            denomination = 'ep'
        elif itemCost.endswith('pp'):
            denomination = 'pp'
        if denomination in itemCost:
            if denomination in players[id]:
                qty = int(itemCost.replace(denomination, ''))
                players[id][denomination] += qty
        mud.sendMessage(id, 'You have sold ' + itemsDB[itemID]['article'] +
                        ' ' + itemsDB[itemID]['name'] + ' for ' +
                        itemCost + '\n\n')


def _go(params, mud, playersDB: {}, players: {}, rooms: {},
        npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
        envDB: {}, env: {}, eventDB: {}, eventSchedule,
        id: int, fights: {}, corpses: {}, blocklist,
        mapArea: [], characterClassDB: {}, spellsDB: {},
        sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
        itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '<r>\n\n')
        return

    if playerIsTrapped(id, players, rooms):
        describeTrappedPlayer(mud, id, players, rooms)
        return

    if playerIsProne(id, players):
        mud.sendMessage(id, randomDescription('You stand up<r>\n\n'))
        setPlayerProne(id, players, False)
        return

    if players[id]['canGo'] == 1:
        # store the exit name
        ex = params.lower()

        stepping = False
        if '######step######' in ex:
            if rooms[players[id]['room']]['trap'].get('trapActivation'):
                if rooms[players[id]['room']]['trap']['trapActivation'] == \
                   'tripwire':
                    ex = ex.replace('######step######', '')
                    stepping = True

        # store the player's current room
        rm = rooms[players[id]['room']]

        # if the specified exit is found in the room's exits list
        rmExits = _getRoomExits(mud, rooms, players, id)
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
                    if _playersInRoom(targetRoom, players, npcs) >= \
                       rooms[targetRoom]['maxPlayers']:
                        mud.sendMessage(id, 'The room is full.<r>\n\n')
                        return

                # Check that the player is not too tall
                if rooms[targetRoom]['maxPlayerSize'] > -1:
                    if players[id]['siz'] > \
                       rooms[targetRoom]['maxPlayerSize']:
                        mud.sendMessage(id, "The entrance is too small " +
                                        "for you to enter.<r>\n\n")
                        return

                if not stepping:
                    if trapActivation(mud, id, players, rooms, ex):
                        return

                if rooms[players[id]['room']]['onWater'] == 0:
                    desc = \
                        randomDescription(players[id]['outDescription'])
                    messageToPlayersInRoom(mud, players, id, '<f32>' +
                                           players[id]['name'] + '<r> ' +
                                           desc + " via exit " + ex + '\n')

                # stop any fights
                stopAttack(players, id, npcs, fights)

                # Trigger old room eventOnLeave for the player
                if rooms[players[id]['room']]['eventOnLeave'] != "":
                    idx = int(rooms[players[id]['room']]['eventOnLeave'])
                    addToScheduler(idx, id, eventSchedule, eventDB)

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
                                        randomDescription(np['inDescription'])
                                    followersMsg = \
                                        followersMsg + '<f32>' + \
                                        npcs[nid]['name'] + '<r> ' + \
                                        desc + '.\n\n'
                                    desc = \
                                        randomDescription(np['outDescription'])
                                    messageToPlayersInRoom(mud, players, id,
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
                    _playersMoveTogether(id, rm['exits'][ex], mud,
                                         playersDB, players, rooms,
                                         npcsDB, npcs,
                                         itemsDB, items, envDB, env,
                                         eventDB, eventSchedule,
                                         fights, corpses, blocklist, mapArea,
                                         characterClassDB, spellsDB,
                                         sentimentDB, guildsDB, clouds,
                                         racesDB, itemHistory, markets,
                                         culturesDB)
                players[id]['room'] = rm['exits'][ex]
                rm = rooms[players[id]['room']]

                # trigger new room eventOnEnter for the player
                if rooms[players[id]['room']]['eventOnEnter'] != "":
                    idx = \
                        int(rooms[players[id]['room']]['eventOnEnter'])
                    addToScheduler(idx, id, eventSchedule, eventDB)

                if rooms[players[id]['room']]['onWater'] == 0:
                    desc = randomDescription(players[id]['inDescription'])
                    messageToPlayersInRoom(mud, players, id, '<f32>' +
                                           players[id]['name'] + '<r> ' +
                                           desc + "\n\n")
                    # send the player a message telling them where they are now
                    desc = \
                        '****TITLE****You arrive at ' + \
                        '<f106>{}'.format(rooms[players[id]['room']]['name'])
                    mud.sendMessage(id, desc + "<r>\n\n")
                else:
                    # send the player a message telling them where they are now
                    desc = \
                        '****TITLE****You row to ' + \
                        '<f106>{}'.format(rooms[players[id]['room']]['name'])
                    mud.sendMessage(id, desc + "<r>\n\n")

                _look('', mud, playersDB, players, rooms, npcsDB, npcs,
                      itemsDB, items, envDB, env, eventDB, eventSchedule,
                      id, fights, corpses, blocklist, mapArea,
                      characterClassDB, spellsDB, sentimentDB,
                      guildsDB, clouds, racesDB, itemHistory, markets,
                      culturesDB)
                # report any followers
                if len(followersMsg) > 0:
                    messageToPlayersInRoom(mud, players, id, followersMsg)
                    mud.sendMessage(id, followersMsg)
        else:
            # the specified exit wasn't found in the current room
            # send back an 'unknown exit' message
            mud.sendMessage(id, "Unknown exit <f226>'{}'".format(ex) +
                            "<r>\n\n")
    else:
        mud.sendMessage(id,
                        'Somehow, your legs refuse to obey your will.<r>\n')


def _goNorth(params, mud, playersDB, players, rooms,
             npcsDB: {}, npcs, itemsDB: {}, items: {}, envDB: {},
             env, eventDB: {}, eventSchedule, id, fights,
             corpses, blocklist, mapArea, characterClassDB: {},
             spellsDB: {}, sentimentDB: {},
             guildsDB: {}, clouds, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    _go('north', mud, playersDB, players, rooms, npcsDB,
        npcs, itemsDB, items, envDB, env, eventDB, eventSchedule,
        id, fights, corpses, blocklist, mapArea, characterClassDB,
        spellsDB, sentimentDB, guildsDB, clouds, racesDB,
        itemHistory, markets, culturesDB)


def _goSouth(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
             env, eventDB: {}, eventSchedule, id, fights,
             corpses, blocklist, mapArea, characterClassDB: {},
             spellsDB: {}, sentimentDB: {}, guildsDB: {}, clouds, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    _go('south', mud, playersDB, players, rooms, npcsDB,
        npcs, itemsDB, items, envDB, env, eventDB, eventSchedule,
        id, fights, corpses, blocklist, mapArea, characterClassDB,
        spellsDB, sentimentDB, guildsDB, clouds, racesDB,
        itemHistory, markets, culturesDB)


def _goEast(params, mud, playersDB: {}, players: {}, rooms: {},
            npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB: {},
            env, eventDB: {}, eventSchedule, id, fights,
            corpses, blocklist, mapArea, characterClassDB: {},
            spellsDB: {}, sentimentDB: {},
            guildsDB: {}, clouds, racesDB: {},
            itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    _go('east', mud, playersDB, players, rooms, npcsDB,
        npcs, itemsDB, items, envDB, env, eventDB, eventSchedule,
        id, fights, corpses, blocklist, mapArea, characterClassDB,
        spellsDB, sentimentDB, guildsDB, clouds, racesDB,
        itemHistory, markets, culturesDB)


def _goWest(params, mud, playersDB: {}, players: {}, rooms: {},
            npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB,
            env, eventDB: {}, eventSchedule, id, fights,
            corpses, blocklist, mapArea, characterClassDB: {},
            spellsDB: {}, sentimentDB: {}, guildsDB: {}, clouds, racesDB: {},
            itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    _go('west', mud, playersDB, players, rooms, npcsDB,
        npcs, itemsDB, items, envDB, env, eventDB, eventSchedule,
        id, fights, corpses, blocklist, mapArea, characterClassDB,
        spellsDB, sentimentDB, guildsDB, clouds, racesDB,
        itemHistory, markets, culturesDB)


def _goUp(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB: {},
          env, eventDB: {}, eventSchedule, id, fights,
          corpses, blocklist, mapArea, characterClassDB: {},
          spellsDB: {}, sentimentDB: {}, guildsDB: {}, clouds, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    _go('up', mud, playersDB, players, rooms, npcsDB,
        npcs, itemsDB, items, envDB, env, eventDB, eventSchedule,
        id, fights, corpses, blocklist, mapArea, characterClassDB,
        spellsDB, sentimentDB, guildsDB, clouds, racesDB,
        itemHistory, markets, culturesDB)


def _goDown(params, mud, playersDB: {}, players: {}, rooms: {},
            npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB: {},
            env, eventDB: {}, eventSchedule, id, fights,
            corpses, blocklist, mapArea, characterClassDB: {},
            spellsDB: {}, sentimentDB: {}, guildsDB: {}, clouds, racesDB: {},
            itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    _go('down', mud, playersDB, players, rooms, npcsDB,
        npcs, itemsDB, items, envDB, env, eventDB, eventSchedule,
        id, fights, corpses, blocklist, mapArea, characterClassDB,
        spellsDB, sentimentDB, guildsDB, clouds, racesDB,
        itemHistory, markets, culturesDB)


def _goIn(params: str, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB: {},
          env, eventDB: {}, eventSchedule, id, fights: {},
          corpses, blocklist, mapArea, characterClassDB: {},
          spellsDB: {}, sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    _go('in', mud, playersDB, players, rooms, npcsDB,
        npcs, itemsDB, items, envDB, env, eventDB, eventSchedule,
        id, fights, corpses, blocklist, mapArea, characterClassDB,
        spellsDB, sentimentDB, guildsDB, clouds, racesDB,
        itemHistory, markets, culturesDB)


def _goOut(params: str, mud, playersDB: {}, players: {}, rooms: {},
           npcsDB: {}, npcs: {}, itemsDB: {}, items: {}, envDB: {},
           env, eventDB: {}, eventSchedule, id, fights: {},
           corpses, blocklist, mapArea, characterClassDB: {},
           spellsDB: {}, sentimentDB: {}, guildsDB: {},
           clouds: {}, racesDB: {},
           itemHistory: {}, markets: {}, culturesDB: {}) -> None:
    _go('out', mud, playersDB, players, rooms, npcsDB,
        npcs, itemsDB, items, envDB, env, eventDB, eventSchedule,
        id, fights, corpses, blocklist, mapArea, characterClassDB,
        spellsDB, sentimentDB, guildsDB, clouds, racesDB,
        itemHistory, markets, culturesDB)


def _conjureRoom(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                 envDB: {}, env: {}, eventDB: {}, eventSchedule,
                 id: int, fights: {}, corpses: {}, blocklist: {},
                 mapArea: [], characterClassDB: {}, spellsDB: {},
                 sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                 itemHistory: {}, markets: {}, culturesDB: {}):
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
        mud.sendMessage(id, 'Specify a room direction.\n\n')
        return False

    # Is there already a room in that direction?
    playerRoomID = players[id]['room']
    roomExits = _getRoomExits(mud, rooms, players, id)
    if roomExits.get(roomDirection):
        mud.sendMessage(id, 'A room already exists in that direction.\n\n')
        return False

    roomID = getFreeRoomKey(rooms)
    if len(roomID) == 0:
        roomID = '$rid=1$'

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
    rooms[roomID] = newrm
    roomExits[roomDirection] = roomID

    # update the room coordinates
    for rm in rooms:
        rooms[rm]['coords'] = []

    log("New room: " + roomID, 'info')
    saveUniverse(rooms, npcsDB, npcs, itemsDB, items, envDB, env, guildsDB)
    mud.sendMessage(id, 'Room created.\n\n')


def _conjureItem(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                 envDB: {}, env: {}, eventDB: {}, eventSchedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 mapArea: [], characterClassDB: {}, spellsDB: {},
                 sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                 itemHistory: {}, markets: {}, culturesDB: {}):
    itemName = params.lower()
    if len(itemName) == 0:
        mud.sendMessage(id, "Specify the name of an item to conjure.\n\n")
        return False

    # Check if item is in player's inventory
    for item in players[id]['inv']:
        for (iid, pl) in list(itemsDB.items()):
            if str(iid) == item:
                if itemName in itemsDB[iid]['name'].lower():
                    mud.sendMessage(id, "You have " +
                                    itemsDB[iid]['article'] + " " +
                                    itemsDB[iid]['name'] +
                                    " in your inventory already.\n\n")
                    return False
    # Check if it is in the room
    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            if itemName in itemsDB[items[item]['id']]['name'].lower():
                mud.sendMessage(id, "It's already here.\n\n")
                return False

    itemID = -1
    for (item, pl) in list(items.items()):
        if itemName == itemsDB[items[item]['id']]['name'].lower():
            itemID = items[item]['id']
            break

    if itemID == -1:
        for (item, pl) in list(items.items()):
            if itemName in itemsDB[items[item]['id']]['name'].lower():
                itemID = items[item]['id']
                break

    if itemID != -1:
        # Generate item
        itemKey = getFreeKey(items)
        items[itemKey] = {
            'id': itemID,
            'room': players[id]['room'],
            'whenDropped': int(time.time()),
            'lifespan': 900000000, 'owner': id
        }
        keyStr = str(itemKey)
        assignItemHistory(keyStr, items, itemHistory)
        mud.sendMessage(id, itemsDB[itemID]['article'] + ' ' +
                        itemsDB[itemID]['name'] +
                        ' spontaneously materializes in front of you.\n\n')
        saveUniverse(rooms, npcsDB, npcs, itemsDB, items, envDB, env, guildsDB)
        return True
    return False


def _randomFamiliar(npcsDB: {}):
    """Picks a familiar at random and returns its index
    """
    possibleFamiliars = []
    for index, details in npcsDB.items():
        if len(details['familiarType']) > 0:
            if len(details['familiarOf']) == 0:
                possibleFamiliars.append(int(index))
    if len(possibleFamiliars) > 0:
        randIndex = len(possibleFamiliars) - 1
        return possibleFamiliars[randint(0, randIndex)]
    return -1


def _conjureNPC(params, mud, playersDB: {}, players: {}, rooms: {},
                npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                envDB: {}, env: {}, eventDB: {}, eventSchedule,
                id: int, fights: {}, corpses: {}, blocklist,
                mapArea: [], characterClassDB: {}, spellsDB: {},
                sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                itemHistory: {}, markets: {}, culturesDB: {}):
    if not params.startswith('npc '):
        if not params.startswith('familiar'):
            return False

    npcHitPoints = 100
    isFamiliar = False
    npcType = 'NPC'
    if params.startswith('familiar'):
        isFamiliar = True
        npcType = 'Familiar'
        npcIndex = _randomFamiliar(npcsDB)
        if npcIndex < 0:
            mud.sendMessage(id, "No familiars known.\n\n")
            return
        npcName = npcsDB[npcIndex]['name']
        npcHitPoints = 5
        npcSize = 0
        npcStrength = 5
        npcFamiliarOf = players[id]['name']
        npcAnimalType = npcsDB[npcIndex]['animalType']
        npcFamiliarType = npcsDB[npcIndex]['familiarType']
        npcFamiliarMode = "follow"
        npcConv = deepcopy(npcsDB[npcIndex]['conv'])
        npcVocabulary = deepcopy(npcsDB[npcIndex]['vocabulary'])
        npcTalkDelay = npcsDB[npcIndex]['talkDelay']
        npcRandomFactor = npcsDB[npcIndex]['randomFactor']
        npcLookDescription = npcsDB[npcIndex]['lookDescription']
        npcInDescription = npcsDB[npcIndex]['inDescription']
        npcOutDescription = npcsDB[npcIndex]['outDescription']
        npcMoveDelay = npcsDB[npcIndex]['moveDelay']
    else:
        npcName = params.replace('npc ', '', 1).strip().replace('"', '')
        npcSize = sizeFromDescription(npcName)
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
        mud.sendMessage(id, "Specify the name of an NPC to conjure.\n\n")
        return False

    # Check if NPC is in the room
    for (nid, pl) in list(npcs.items()):
        if npcs[nid]['room'] == players[id]['room']:
            if npcName.lower() in npcs[nid]['name'].lower():
                mud.sendMessage(id, npcs[nid]['name'] +
                                " is already here.\n\n")
                return False

    # NPC has the culture assigned to the room
    roomCulture = getRoomCulture(culturesDB, rooms, players[id]['room'])
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
            npcsKey = getFreeKey(npcs)
            players[id]['familiar'] = npcsKey
    else:
        npcsKey = getFreeKey(npcs)

    npcs[npcsKey] = newNPC
    npcsDB[npcsKey] = newNPC
    npcsKeyStr = str(npcsKey)
    log(npcType + ' ' + npcName + ' generated in ' +
        players[id]['room'] + ' with key ' + npcsKeyStr, 'info')
    if isFamiliar:
        mud.sendMessage(
            id,
            'Your familiar, ' +
            npcName +
            ', spontaneously appears.\n\n')
    else:
        mud.sendMessage(id, npcName + ' spontaneously appears.\n\n')
    saveUniverse(rooms, npcsDB, npcs, itemsDB, items, envDB, env, guildsDB)
    return True


def _dismiss(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
             envDB: {}, env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: [], characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
    if params.lower().startswith('familiar'):
        players[id]['familiar'] = -1
        familiarRemoved = False
        removals = []
        for (index, details) in npcsDB.items():
            if details['familiarOf'] == players[id]['name']:
                removals.append(index)
                familiarRemoved = True
        for index in removals:
            del npcsDB[index]

        removals.clear()
        for (index, details) in npcs.items():
            if details['familiarOf'] == players[id]['name']:
                removals.append(index)
        for index in removals:
            del npcs[index]

        if familiarRemoved:
            mud.sendMessage(id, "Your familiar vanishes.\n\n")
        else:
            mud.sendMessage(id, "\n\n")


def _conjure(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
             envDB: {}, env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: [], characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
    if not _isWitch(id, players):
        mud.sendMessage(id, "You don't have enough powers.\n\n")
        return

    if params.startswith('familiar'):
        _conjureNPC(params, mud, playersDB, players, rooms,
                    npcsDB, npcs, itemsDB, items, envDB, env,
                    eventDB, eventSchedule, id, fights, corpses,
                    blocklist, mapArea, characterClassDB,
                    spellsDB, sentimentDB, guildsDB, clouds, racesDB,
                    itemHistory, markets, culturesDB)
        return

    if params.startswith('room '):
        _conjureRoom(params, mud, playersDB, players, rooms, npcsDB,
                     npcs, itemsDB, items, envDB, env, eventDB,
                     eventSchedule, id, fights, corpses, blocklist,
                     mapArea, characterClassDB, spellsDB,
                     sentimentDB, guildsDB, clouds, racesDB,
                     itemHistory, markets, culturesDB)
        return

    if params.startswith('npc '):
        _conjureNPC(params, mud, playersDB, players, rooms,
                    npcsDB, npcs, itemsDB, items, envDB, env,
                    eventDB, eventSchedule, id, fights, corpses,
                    blocklist, mapArea, characterClassDB,
                    spellsDB, sentimentDB, guildsDB, clouds, racesDB,
                    itemHistory, markets, culturesDB)
        return

    _conjureItem(params, mud, playersDB, players, rooms, npcsDB, npcs,
                 itemsDB, items, envDB, env, eventDB, eventSchedule,
                 id, fights, corpses, blocklist, mapArea,
                 characterClassDB, spellsDB, sentimentDB, guildsDB,
                 clouds, racesDB, itemHistory, markets, culturesDB)


def _destroyItem(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                 envDB: {}, env: {}, eventDB: {}, eventSchedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 mapArea: [], characterClassDB: {}, spellsDB: {},
                 sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                 itemHistory: {}, markets: {}, culturesDB: {}):
    itemName = params.lower()
    if len(itemName) == 0:
        mud.sendMessage(id, "Specify the name of an item to destroy.\n\n")
        return False

    # Check if it is in the room
    itemID = -1
    destroyedName = ''
    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            if itemName in itemsDB[items[item]['id']]['name']:
                destroyedName = itemsDB[items[item]['id']]['name']
                itemID = items[item]['id']
                break
    if itemID == -1:
        mud.sendMessage(id, "It's not here.\n\n")
        return False

    mud.sendMessage(id, 'It suddenly vanishes.\n\n')
    del items[item]
    log("Item destroyed: " + destroyedName +
        ' in ' + players[id]['room'], 'info')
    saveUniverse(rooms, npcsDB, npcs, itemsDB,
                 items, envDB, env, guildsDB)
    return True


def _destroyNPC(params, mud, playersDB: {}, players: {}, rooms: {},
                npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                envDB: {}, env: {}, eventDB: {}, eventSchedule,
                id: int, fights: {}, corpses: {}, blocklist,
                mapArea: [], characterClassDB: {}, spellsDB: {},
                sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                itemHistory: {}, markets: {}, culturesDB: {}):
    npcName = params.lower().replace('npc ', '').strip().replace('"', '')
    if len(npcName) == 0:
        mud.sendMessage(id, "Specify the name of an NPC to destroy.\n\n")
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
        mud.sendMessage(id, "They're not here.\n\n")
        return False

    mud.sendMessage(id, 'They suddenly vanish.\n\n')
    del npcs[npcID]
    del npcsDB[npcID]
    log("NPC destroyed: " + destroyedName +
        ' in ' + players[id]['room'], 'info')
    saveUniverse(rooms, npcsDB, npcs, itemsDB,
                 items, envDB, env, guildsDB)
    return True


def _destroyRoom(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                 envDB: {}, env: {}, eventDB: {}, eventSchedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 mapArea: [], characterClassDB: {}, spellsDB: {},
                 sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                 itemHistory: {}, markets: {}, culturesDB: {}):
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
        mud.sendMessage(id, 'Specify a room direction.\n\n')
        return False

    # Is there already a room in that direction?
    roomExits = _getRoomExits(mud, rooms, players, id)
    if not roomExits.get(roomDirection):
        mud.sendMessage(id, 'There is no room in that direction.\n\n')
        return False

    roomToDestroyID = roomExits.get(roomDirection)
    roomToDestroy = rooms[roomToDestroyID]
    roomExitsToDestroy = roomToDestroy['exits']
    for direction, roomID in roomExitsToDestroy.items():
        # Remove the exit from the other room to this one
        otherRoom = rooms[roomID]
        if otherRoom['exits'].get(oppositeDirection[direction]):
            del otherRoom['exits'][oppositeDirection[direction]]
    del rooms[roomToDestroyID]

    # update the map area
    for rm in rooms:
        rooms[rm]['coords'] = []

    log("Room destroyed: " + roomToDestroyID, 'info')
    saveUniverse(rooms, npcsDB, npcs, itemsDB,
                 items, envDB, env, guildsDB)
    mud.sendMessage(id, "Room destroyed.\n\n")
    return True


def _destroy(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
             envDB: {}, env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: [], characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
    if not _isWitch(id, players):
        mud.sendMessage(id, "You don't have enough powers.\n\n")
        return

    if params.startswith('room '):
        _destroyRoom(params, mud, playersDB, players, rooms, npcsDB,
                     npcs, itemsDB, items, envDB, env, eventDB,
                     eventSchedule, id, fights, corpses, blocklist,
                     mapArea, characterClassDB, spellsDB,
                     sentimentDB, guildsDB, clouds, racesDB,
                     itemHistory, markets, culturesDB)
    else:
        if params.startswith('npc '):
            _destroyNPC(params, mud, playersDB, players, rooms, npcsDB,
                        npcs, itemsDB, items, envDB, env, eventDB,
                        eventSchedule, id, fights, corpses, blocklist,
                        mapArea, characterClassDB, spellsDB,
                        sentimentDB, guildsDB, clouds, racesDB,
                        itemHistory, markets, culturesDB)
        else:
            _destroyItem(params, mud, playersDB, players, rooms, npcsDB,
                         npcs, itemsDB, items, envDB, env, eventDB,
                         eventSchedule, id, fights, corpses, blocklist,
                         mapArea, characterClassDB, spellsDB,
                         sentimentDB, guildsDB, clouds, racesDB,
                         itemHistory, markets, culturesDB)


def _drop(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    # Check if inventory is empty
    if len(list(players[id]['inv'])) == 0:
        mud.sendMessage(id, 'You don`t have that!\n\n')
        return

    itemInDB = False
    itemInInventory = False
    itemID = None
    target = str(params).lower()
    if target.startswith('the '):
        target = params.replace('the ', '')

    # Check if item is in player's inventory
    for item in players[id]['inv']:
        for (iid, pl) in list(itemsDB.items()):
            if str(iid) == str(item):
                if itemsDB[iid]['name'].lower() == target:
                    itemID = iid
                    itemInInventory = True
                    itemInDB = True
                    break
        if itemInInventory:
            break

    if not itemInInventory:
        # Try a fuzzy match
        for item in players[id]['inv']:
            for (iid, pl) in list(itemsDB.items()):
                if str(iid) == str(item):
                    if target in itemsDB[iid]['name'].lower():
                        itemID = iid
                        itemInInventory = True
                        itemInDB = True
                        break

    if itemInDB and itemInInventory:
        if playerIsTrapped(id, players, rooms):
            desc = (
                "You're trapped",
                "The trap restricts your ability to drop anything",
                "The trap restricts your movement"
            )
            mud.sendMessage(id, randomDescription(desc) + '.\n\n')
            return

        inventoryCopy = deepcopy(players[id]['inv'])
        for i in inventoryCopy:
            if int(i) == itemID:
                # Remove first matching item from inventory
                players[id]['inv'].remove(i)
                updatePlayerAttributes(id, players, itemsDB, itemID, -1)
                break

        players[id]['wei'] = playerInventoryWeight(id, players, itemsDB)

        # remove from clothing
        _removeItemFromClothing(players, id, int(i))

        # Create item on the floor in the same room as the player
        items[getFreeKey(items)] = {
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

        mud.sendMessage(id, 'You drop ' +
                        itemsDB[int(i)]['article'] +
                        ' ' +
                        itemsDB[int(i)]['name'] +
                        ' on the floor.\n\n')

    else:
        mud.sendMessage(id, 'You don`t have that!\n\n')


def _openItemUnlock(items: {}, itemsDB: {}, id, iid, players: {}, mud) -> bool:
    unlockItemID = itemsDB[items[iid]['id']]['lockedWithItem']
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
        mud.sendMessage(
            id, 'You use ' +
            itemsDB[unlockItemID]['article'] +
            ' ' + itemsDB[unlockItemID]['name'])
    else:
        if len(itemsDB[unlockItemID]['open_failed_description']) > 0:
            mud.sendMessage(
                id, itemsDB[unlockItemID]['open_failed_description'] + ".\n\n")
        else:
            if itemsDB[unlockItemID]['state'].startswith('lever '):
                mud.sendMessage(id, "It's operated with a lever.\n\n")
            else:
                if randint(0, 1) == 1:
                    mud.sendMessage(
                        id, "You don't have " +
                        itemsDB[unlockItemID]['article'] +
                        " " + itemsDB[unlockItemID]['name'] +
                        ".\n\n")
                else:
                    mud.sendMessage(
                        id, "Looks like you need " +
                        itemsDB[unlockItemID]['article'] +
                        " " + itemsDB[unlockItemID]['name'] +
                        " for this.\n\n")
        return False
    return True


def _describeContainerContents(mud, id, itemsDB: {}, itemID: {}, returnMsg):
    if not itemsDB[itemID]['state'].startswith('container open'):
        if returnMsg:
            return ''
        else:
            return
    containsList = itemsDB[itemID]['contains']
    noOfItems = len(containsList)
    containerMsg = '<f15>You see '

    if noOfItems == 0:
        if 'open always' not in itemsDB[itemID]['state']:
            mud.sendMessage(id, containerMsg + 'nothing.\n')
        return ''

    itemCtr = 0
    for contentsID in containsList:
        if itemCtr > 0:
            if itemCtr < noOfItems - 1:
                containerMsg += ', '
            else:
                containerMsg += ' and '

        containerMsg += \
            itemsDB[int(contentsID)]['article'] + \
            ' <b234><f220>' + \
            itemsDB[int(contentsID)]['name'] + '<r>'
        itemCtr += 1

    containerMsg = containerMsg + '.\n'
    if returnMsg:
        containerMsg = '\n' + containerMsg
        return containerMsg
    else:
        mud.sendMessageWrap(id, '<f220>', containerMsg + '\n')


def _openItemContainer(params, mud, playersDB: {}, players: {}, rooms: {},
                       npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                       envDB: {}, env: {}, eventDB: {}, eventSchedule,
                       id: int, fights: {}, corpses: {}, target,
                       itemsInWorldCopy: {}, iid):
    if not _openItemUnlock(items, itemsDB, id, iid, players, mud):
        return

    itemID = items[iid]['id']
    if itemsDB[itemID]['state'].startswith('container open'):
        mud.sendMessage(id, "It's already open\n\n")
        return

    itemsDB[itemID]['state'] = \
        itemsDB[itemID]['state'].replace('closed', 'open')
    itemsDB[itemID]['short_description'] = \
        itemsDB[itemID]['short_description'].replace('closed', 'open')
    itemsDB[itemID]['long_description'] = \
        itemsDB[itemID]['long_description'].replace('closed', 'open')
    itemsDB[itemID]['long_description'] = \
        itemsDB[itemID]['long_description'].replace('shut', 'open')

    if len(itemsDB[itemID]['open_description']) > 0:
        mud.sendMessage(id, itemsDB[itemID]['open_description'] + '\n\n')
    else:
        itemArticle = itemsDB[itemID]['article']
        if itemArticle == 'a':
            itemArticle = 'the'
        mud.sendMessage(id, 'You open ' + itemArticle +
                        ' ' + itemsDB[itemID]['name'] + '.\n\n')
    _describeContainerContents(mud, id, itemsDB, itemID, False)


def _leverUp(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
             envDB: {}, env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, target,
             itemsInWorldCopy: {}, iid):
    itemID = items[iid]['id']
    linkedItemID = int(itemsDB[itemID]['linkedItem'])
    roomID = itemsDB[itemID]['exit']

    itemsDB[itemID]['state'] = 'lever up'
    itemsDB[itemID]['short_description'] = \
        itemsDB[itemID]['short_description'].replace('down', 'up')
    itemsDB[itemID]['long_description'] = \
        itemsDB[itemID]['long_description'].replace('down', 'up')
    if '|' in itemsDB[itemID]['exitName']:
        exitName = itemsDB[itemID]['exitName'].split('|')

        if linkedItemID > 0:
            desc = itemsDB[linkedItemID]['short_description']
            itemsDB[linkedItemID]['short_description'] = \
                desc.replace('open', 'closed')
            desc = itemsDB[linkedItemID]['long_description']
            itemsDB[linkedItemID]['long_description'] = \
                desc.replace('open', 'closed')
            itemsDB[linkedItemID]['state'] = 'closed'
            linkedItemID2 = int(itemsDB[linkedItemID]['linkedItem'])
            if linkedItemID2 > 0:
                desc = itemsDB[linkedItemID2]['short_description']
                itemsDB[linkedItemID2]['short_description'] = \
                    desc.replace('open', 'closed')
                desc = itemsDB[linkedItemID2]['long_description']
                itemsDB[linkedItemID2]['long_description'] = \
                    desc.replace('open', 'closed')
                itemsDB[linkedItemID2]['state'] = 'closed'

        if len(roomID) > 0:
            rm = players[id]['room']
            if exitName[0] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[0]]

            rm = roomID
            if exitName[1] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[1]]

    if len(itemsDB[itemID]['close_description']) > 0:
        mud.sendMessageWrap(id, '<f220>',
                            itemsDB[itemID]['close_description'] + '\n\n')
    else:
        mud.sendMessage(
            id, 'You push ' +
            itemsDB[itemID]['article'] +
            ' ' + itemsDB[itemID]['name'] +
            '\n\n')


def _leverDown(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, target,
               itemsInWorldCopy: {}, iid):
    if not _openItemUnlock(items, itemsDB, id, iid, players, mud):
        return

    itemID = items[iid]['id']
    linkedItemID = int(itemsDB[itemID]['linkedItem'])
    roomID = itemsDB[itemID]['exit']

    itemsDB[itemID]['state'] = 'lever down'
    itemsDB[itemID]['short_description'] = \
        itemsDB[itemID]['short_description'].replace('up', 'down')
    itemsDB[itemID]['long_description'] = \
        itemsDB[itemID]['long_description'].replace('up', 'down')
    if '|' in itemsDB[itemID]['exitName']:
        exitName = itemsDB[itemID]['exitName'].split('|')

        if linkedItemID > 0:
            desc = itemsDB[linkedItemID]['short_description']
            itemsDB[linkedItemID]['short_description'] = \
                desc.replace('closed', 'open')
            desc = itemsDB[linkedItemID]['long_description']
            itemsDB[linkedItemID]['long_description'] = \
                desc.replace('closed', 'open')
            itemsDB[linkedItemID]['state'] = 'open'
            linkedItemID2 = int(itemsDB[linkedItemID]['linkedItem'])
            if linkedItemID2 > 0:
                desc = itemsDB[linkedItemID2]['short_description']
                itemsDB[linkedItemID2]['short_description'] = \
                    desc.replace('closed', 'open')
                desc = itemsDB[linkedItemID2]['long_description']
                itemsDB[linkedItemID2]['long_description'] = \
                    desc.replace('closed', 'open')
                itemsDB[linkedItemID2]['state'] = 'open'

        if len(roomID) > 0:
            rm = players[id]['room']
            if exitName[0] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[0]]
            rooms[rm]['exits'][exitName[0]] = roomID

            rm = roomID
            if exitName[1] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[1]]
            rooms[rm]['exits'][exitName[1]] = players[id]['room']

    if len(itemsDB[itemID]['open_description']) > 0:
        mud.sendMessageWrap(id, '<f220>',
                            itemsDB[itemID]['open_description'] +
                            '\n\n')
    else:
        mud.sendMessage(
            id, 'You pull ' +
            itemsDB[itemID]['article'] +
            ' ' + itemsDB[itemID]['name'] +
            '\n\n')


def _openItemDoor(params, mud, playersDB: {}, players: {}, rooms: {},
                  npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                  envDB: {}, env: {}, eventDB: {}, eventSchedule,
                  id: int, fights: {}, corpses: {}, target,
                  itemsInWorldCopy: {}, iid):
    if not _openItemUnlock(items, itemsDB, id, iid, players, mud):
        return

    itemID = items[iid]['id']
    linkedItemID = int(itemsDB[itemID]['linkedItem'])
    roomID = itemsDB[itemID]['exit']
    if '|' in itemsDB[itemID]['exitName']:
        exitName = itemsDB[itemID]['exitName'].split('|')

        itemsDB[itemID]['state'] = 'open'
        desc = itemsDB[itemID]['short_description']
        itemsDB[itemID]['short_description'] = \
            desc.replace('closed', 'open').replace('drawn up', 'drawn down')
        desc = itemsDB[itemID]['long_description']
        itemsDB[itemID]['long_description'] = \
            desc.replace('closed', 'open').replace('drawn up', 'drawn down')

        if linkedItemID > 0:
            desc = itemsDB[linkedItemID]['short_description']
            itemsDB[linkedItemID]['short_description'] = \
                desc.replace('closed',
                             'open').replace('drawn up', 'drawn down')
            desc = itemsDB[linkedItemID]['long_description']
            itemsDB[linkedItemID]['long_description'] = \
                desc.replace('closed',
                             'open').replace('drawn up', 'drawn down')
            itemsDB[linkedItemID]['state'] = 'open'

        if len(roomID) > 0:
            rm = players[id]['room']
            if exitName[0] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[0]]
            rooms[rm]['exits'][exitName[0]] = roomID

            rm = roomID
            if exitName[1] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[1]]
            rooms[rm]['exits'][exitName[1]] = players[id]['room']

    if len(itemsDB[itemID]['open_description']) > 0:
        mud.sendMessage(id, itemsDB[itemID]['open_description'] + '\n\n')
    else:
        mud.sendMessage(
            id, 'You open ' +
            itemsDB[itemID]['article'] +
            ' ' + itemsDB[itemID]['name'] +
            '\n\n')


def _openItem(params, mud, playersDB: {}, players: {}, rooms: {},
              npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
              envDB: {}, env: {}, eventDB: {}, eventSchedule,
              id: int, fights: {}, corpses: {}, blocklist,
              mapArea: [], characterClassDB: {}, spellsDB: {},
              sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
              itemHistory: {}, markets: {}, culturesDB: {}):
    target = params.lower()

    if target.startswith('registration'):
        _enableRegistrations(mud, id, players)
        return

    if target.startswith('the '):
        target = target.replace('the ', '')

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if itemsDB[items[iid]['id']]['state'] == 'closed':
                    _openItemDoor(params, mud, playersDB, players, rooms,
                                  npcsDB, npcs, itemsDB, items, envDB, env,
                                  eventDB, eventSchedule, id, fights,
                                  corpses, target, itemsInWorldCopy,
                                  iid)
                    return
                idx = items[iid]['id']
                if itemsDB[idx]['state'].startswith('container closed'):
                    _openItemContainer(params, mud, playersDB, players,
                                       rooms, npcsDB, npcs, itemsDB,
                                       items, envDB, env, eventDB,
                                       eventSchedule, id, fights, corpses,
                                       target, itemsInWorldCopy, iid)
                    return
    mud.sendMessage(id, "You can't open it.\n\n")


def _pullLever(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist: {},
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    target = params.lower()

    if target.startswith('registration'):
        _enableRegistrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if itemsDB[items[iid]['id']]['state'] == 'lever up':
                    _leverDown(params, mud, playersDB, players, rooms,
                               npcsDB, npcs, itemsDB, items, envDB,
                               env, eventDB, eventSchedule, id, fights,
                               corpses, target, itemsInWorldCopy, iid)
                    return
                else:
                    mud.sendMessage(id, 'Nothing happens.\n\n')
                    return
    mud.sendMessage(id, "There's nothing to pull.\n\n")


def _pushLever(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    target = params.lower()
    if target.startswith('the '):
        target = target.replace('the ', '')

    if target.startswith('registration'):
        _enableRegistrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if not itemsDB[items[iid]['id']]['state']:
                    _heave(params, mud, playersDB, players, rooms,
                           npcsDB, npcs, itemsDB, items, envDB, env,
                           eventDB, eventSchedule, id, fights,
                           corpses, blocklist, mapArea, characterClassDB,
                           spellsDB, sentimentDB, guildsDB, clouds, racesDB,
                           itemHistory, markets, culturesDB)
                    return
                elif itemsDB[items[iid]['id']]['state'] == 'lever down':
                    _leverUp(params, mud, playersDB, players, rooms, npcsDB,
                             npcs, itemsDB, items, envDB, env, eventDB,
                             eventSchedule, id, fights, corpses, target,
                             itemsInWorldCopy, iid)
                    return
    mud.sendMessage(id, 'Nothing happens.\n\n')


def _windLever(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    target = params.lower()

    if target.startswith('registration'):
        _enableRegistrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if itemsDB[items[iid]['id']]['state'] == 'lever up':
                    _leverDown(params, mud, playersDB, players, rooms,
                               npcsDB, npcs, itemsDB, items, envDB,
                               env, eventDB, eventSchedule, id,
                               fights, corpses, target,
                               itemsInWorldCopy, iid)
                    return
                else:
                    mud.sendMessage(id, "It's wound all the way.\n\n")
                    return
    mud.sendMessage(id, "There's nothing to wind.\n\n")


def _unwindLever(params, mud, playersDB: {}, players: {}, rooms: {},
                 npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                 envDB: {}, env: {}, eventDB: {}, eventSchedule,
                 id: int, fights: {}, corpses: {}, blocklist,
                 mapArea: [], characterClassDB: {}, spellsDB: {},
                 sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
                 itemHistory: {}, markets: {}, culturesDB: {}):
    target = params.lower()

    if target.startswith('registration'):
        _enableRegistrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if itemsDB[items[iid]['id']]['state'] == 'lever down':
                    _leverUp(params, mud, playersDB, players, rooms,
                             npcsDB, npcs, itemsDB, items, envDB, env,
                             eventDB, eventSchedule, id, fights,
                             corpses, target, itemsInWorldCopy, iid)
                    return
                else:
                    mud.sendMessage(id, "It's unwound all the way.\n\n")
                    return
    mud.sendMessage(id, "There's nothing to unwind.\n\n")


def _closeItemContainer(params, mud, playersDB: {}, players: {}, rooms: {},
                        npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                        envDB: {}, env: {}, eventDB: {}, eventSchedule,
                        id: int, fights: {}, corpses: {}, target,
                        itemsInWorldCopy: {}, iid):
    itemID = items[iid]['id']
    if itemsDB[itemID]['state'].startswith('container closed'):
        mud.sendMessage(id, "It's already closed\n\n")
        return

    if itemsDB[itemID]['state'].startswith('container open '):
        mud.sendMessage(id, "That's not possible.\n\n")
        return

    itemsDB[itemID]['state'] = \
        itemsDB[itemID]['state'].replace('open', 'closed')
    itemsDB[itemID]['short_description'] = \
        itemsDB[itemID]['short_description'].replace('open', 'closed')
    itemsDB[itemID]['long_description'] = \
        itemsDB[itemID]['long_description'].replace('open', 'closed')

    if len(itemsDB[itemID]['close_description']) > 0:
        mud.sendMessage(id, itemsDB[itemID]['close_description'] + '\n\n')
    else:
        itemArticle = itemsDB[itemID]['article']
        if itemArticle == 'a':
            itemArticle = 'the'
        mud.sendMessage(id, 'You close ' + itemArticle +
                        ' ' + itemsDB[itemID]['name'] + '.\n\n')


def _closeItemDoor(params, mud, playersDB: {}, players: {}, rooms: {},
                   npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
                   envDB: {}, env: {}, eventDB: {}, eventSchedule,
                   id: int, fights: {}, corpses: {}, target,
                   itemsInWorldCopy: {}, iid):
    itemID = items[iid]['id']
    linkedItemID = int(itemsDB[itemID]['linkedItem'])
    roomID = itemsDB[itemID]['exit']
    if '|' not in itemsDB[itemID]['exitName']:
        return

    exitName = itemsDB[itemID]['exitName'].split('|')

    itemsDB[itemID]['state'] = 'closed'
    itemsDB[itemID]['short_description'] = \
        itemsDB[itemID]['short_description'].replace('open', 'closed')
    itemsDB[itemID]['long_description'] = \
        itemsDB[itemID]['long_description'].replace('open', 'closed')

    if linkedItemID > 0:
        desc = itemsDB[linkedItemID]['short_description']
        itemsDB[linkedItemID]['short_description'] = \
            desc.replace('open', 'closed').replace('drawn down', 'drawn up')
        desc = itemsDB[linkedItemID]['long_description']
        itemsDB[linkedItemID]['long_description'] = \
            desc.replace('open', 'closed').replace('drawn down', 'drawn up')
        itemsDB[linkedItemID]['state'] = 'closed'

    if len(roomID) > 0:
        rm = players[id]['room']
        if exitName[0] in rooms[rm]['exits']:
            del rooms[rm]['exits'][exitName[0]]

        rm = roomID
        if exitName[1] in rooms[rm]['exits']:
            del rooms[rm]['exits'][exitName[1]]

    if len(itemsDB[itemID]['close_description']) > 0:
        mud.sendMessage(id, itemsDB[itemID]['close_description'] + '\n\n')
    else:
        mud.sendMessage(id, 'You close ' +
                        itemsDB[itemID]['article'] + ' ' +
                        itemsDB[itemID]['name'] + '\n\n')


def _closeItem(params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    target = params.lower()

    if target.startswith('registration'):
        _disableRegistrations(mud, id, players)
        return

    if target.startswith('the '):
        target = target.replace('the ', '')

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if itemsDB[items[iid]['id']]['state'] == 'open':
                    _closeItemDoor(params, mud, playersDB, players,
                                   rooms, npcsDB, npcs, itemsDB,
                                   items, envDB, env, eventDB,
                                   eventSchedule, id, fights,
                                   corpses, target, itemsInWorldCopy,
                                   iid)
                    return
                idx = items[iid]['id']
                if itemsDB[idx]['state'].startswith('container open'):
                    _closeItemContainer(params, mud, playersDB, players,
                                        rooms, npcsDB, npcs, itemsDB,
                                        items, envDB, env, eventDB,
                                        eventSchedule, id, fights,
                                        corpses, target, itemsInWorldCopy,
                                        iid)
                    return
    mud.sendMessage(id, "You can't close it.\n\n")


def _putItem(params, mud, playersDB: {}, players: {}, rooms: {},
             npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
             envDB: {}, env: {}, eventDB: {}, eventSchedule,
             id: int, fights: {}, corpses: {}, blocklist,
             mapArea: {}, characterClassDB: {}, spellsDB: {},
             sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
             itemHistory: {}, markets: {}, culturesDB: {}):
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
            if itemsDB[int(i)]['name'].lower() == itemNameLower:
                itemID = int(i)
                itemName = itemsDB[int(i)]['name']

        if itemID == 0:
            for i in list(players[id]['inv']):
                if itemNameLower in itemsDB[int(i)]['name'].lower():
                    itemID = int(i)
                    itemName = itemsDB[int(i)]['name']

    if itemID == 0:
        mud.sendMessage(id, "You don't have " + itemName + ".\n\n")
        return

    itemsInWorldCopy = deepcopy(items)

    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            iName = itemsDB[items[iid]['id']]['name'].lower()
            if containerName.lower() in iName:
                idx = items[iid]['id']
                if itemsDB[idx]['state'].startswith('container open'):
                    if ' noput' not in itemsDB[idx]['state']:
                        maxItemsInContainer = itemsDB[idx]['useTimes']
                        if maxItemsInContainer == 0 or \
                           len(itemsDB[idx]['contains']) < maxItemsInContainer:
                            players[id]['inv'].remove(str(itemID))
                            _removeItemFromClothing(players, id, itemID)
                            itemsDB[idx]['contains'].append(str(itemID))
                            idx = items[iid]['id']
                            mud.sendMessage(id, 'You put ' +
                                            itemsDB[itemID]['article'] +
                                            ' ' + itemsDB[itemID]['name'] +
                                            inon +
                                            itemsDB[idx]['article'] +
                                            ' ' +
                                            itemsDB[idx]['name'] +
                                            '.\n\n')
                        else:
                            mud.sendMessage(
                                id, 'No more items can be put ' + inon + ' ' +
                                itemsDB[items[iid]['id']]['article'] + ' ' +
                                itemsDB[items[iid]['id']]['name'] + ".\n\n")
                    else:
                        if 'on' in inon:
                            mud.sendMessage(
                                id, "You can't put anything on that.\n\n")
                        else:
                            mud.sendMessage(
                                id, "You can't put anything in that.\n\n")
                    return
                else:
                    idx = items[iid]['id']
                    if itemsDB[idx]['state'].startswith('container closed'):
                        if 'on' in inon:
                            mud.sendMessage(id, "You can't.\n\n")
                        else:
                            mud.sendMessage(id, "It's closed.\n\n")
                        return
                    else:
                        if 'on' in inon:
                            mud.sendMessage(
                                id, "You can't put anything on that.\n\n")
                        else:
                            mud.sendMessage(
                                id, "It can't contain anything.\n\n")
                        return

    mud.sendMessage(id, "You don't see " + containerName + ".\n\n")


def _take(params, mud, playersDB: {}, players: {}, rooms: {},
          npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
          envDB: {}, env: {}, eventDB: {}, eventSchedule,
          id: int, fights: {}, corpses: {}, blocklist,
          mapArea: [], characterClassDB: {}, spellsDB: {},
          sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
          itemHistory: {}, markets: {}, culturesDB: {}):
    if players[id]['frozenStart'] != 0:
        mud.sendMessage(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if params:
        if params == 'up':
            _stand(params, mud, playersDB, players, rooms, npcsDB, npcs,
                   itemsDB, items, envDB, env, eventDB, eventSchedule,
                   id, fights, corpses, blocklist, mapArea, characterClassDB,
                   spellsDB, sentimentDB, guildsDB, clouds, racesDB,
                   itemHistory, markets, culturesDB)
            return

        # get into, get through
        if params.startswith('into') or params.startswith('through'):
            _climb(params, mud, playersDB, players, rooms, npcsDB, npcs,
                   itemsDB, items, envDB, env, eventDB, eventSchedule,
                   id, fights, corpses, blocklist, mapArea, characterClassDB,
                   spellsDB, sentimentDB, guildsDB, clouds, racesDB,
                   itemHistory, markets, culturesDB)
            return

    if len(str(params)) < 3:
        return

    paramsStr = str(params)
    if _itemInInventory(players, id, paramsStr, itemsDB):
        mud.sendMessage(id, 'You are already carring ' + str(params) + '\n\n')
        return

    if playerIsProne(id, players):
        mud.sendMessage(id, randomDescription('You stand up<r>\n\n'))
        setPlayerProne(id, players, False)
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
        if itemsDB[iid2]['name'].lower() != target:
            continue
        if int(itemsDB[iid2]['weight']) == 0:
            if itemsDB[iid2].get('takeFail'):
                desc = randomDescription(itemsDB[iid2]['takeFail'])
                mud.sendMessageWrap(id, '<f220>', desc + "\n\n")
            else:
                mud.sendMessage(id, "You can't pick that up.\n\n")
            return
        if _itemIsVisible(id, players, iid2, itemsDB):
            # ID of the item to be picked up
            itemName = itemsDB[iid2]['name']
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
            if target not in itemsDB[itemIndex]['name'].lower():
                continue
            if int(itemsDB[itemIndex]['weight']) == 0:
                if itemsDB[itemIndex].get('takeFail'):
                    desc = randomDescription(itemsDB[itemIndex]['takeFail'])
                    mud.sendMessageWrap(id, '<f220>', desc + "\n\n")
                else:
                    mud.sendMessage(id, "You can't pick that up.\n\n")
                return

            itemName = itemsDB[itemIndex]['name']
            if _itemInInventory(players, id, itemName, itemsDB):
                mud.sendMessage(
                    id, 'You are already carring ' + itemName + '\n\n')
                return
            if _itemIsVisible(id, players, itemIndex, itemsDB):
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
            if itemsDB[itemIndex]['name'] != itemName:
                continue
            # player can move
            if players[id]['canGo'] != 0:
                # is the item too heavy?
                players[id]['wei'] = \
                    playerInventoryWeight(id, players, itemsDB)

                if players[id]['wei'] + itemsDB[itemIndex]['weight'] > \
                   _getMaxWeight(id, players):
                    mud.sendMessage(id, "You can't carry any more.\n\n")
                    return

                # is the player restricted by a trap
                if playerIsTrapped(id, players, rooms):
                    desc = (
                        "You're trapped",
                        "The trap restricts your ability to take anything",
                        "The trap restricts your movement"
                    )
                    mud.sendMessage(id, randomDescription(desc) + '.\n\n')
                    return

                # add the item to the player's inventory
                players[id]['inv'].append(str(itemIndex))
                # update the weight of the player
                players[id]['wei'] = \
                    playerInventoryWeight(id, players, itemsDB)
                updatePlayerAttributes(id, players, itemsDB, itemIndex, 1)
                # remove the item from the dict
                del items[iid]
                itemPickedUp = True
                break
            else:
                mud.sendMessage(id, 'You try to pick up ' + itemName +
                                " but find that your arms won't move.\n\n")
                return

    if itemPickedUp:
        mud.sendMessage(id, 'You pick up and place ' +
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
            if not itemsDB[itemIndex]['state'].startswith('container open'):
                continue
            # go through the items within the container
            for containerItemID in itemsDB[itemIndex]['contains']:
                # does the name match?
                itemName = itemsDB[int(containerItemID)]['name']
                if target not in itemName.lower():
                    continue
                # can the item be taken?
                if itemsDB[int(containerItemID)]['weight'] == 0:
                    if itemsDB[int(containerItemID)].get('takeFail'):
                        idx = int(containerItemID)
                        desc = \
                            randomDescription(itemsDB[idx]['takeFail'])
                        mud.sendMessageWrap(id, '<f220>', desc + "\n\n")
                    else:
                        mud.sendMessage(id, "You can't pick that up.\n\n")
                    return
                else:
                    # can the player move?
                    if players[id]['canGo'] != 0:
                        # is the item too heavy?
                        carryingWeight = \
                            playerInventoryWeight(id, players, itemsDB)
                        idx = int(containerItemID)
                        if carryingWeight + itemsDB[idx]['weight'] > \
                           _getMaxWeight(id, players):
                            mud.sendMessage(id,
                                            "You can't carry any more.\n\n")
                            return

                        # add the item to the player's inventory
                        players[id]['inv'].append(containerItemID)
                        # remove the item from the container
                        itemsDB[itemIndex]['contains'].remove(containerItemID)
                        idx = int(containerItemID)
                        mud.sendMessage(id, 'You take ' +
                                        itemsDB[idx]['article'] +
                                        ' ' +
                                        itemsDB[idx]['name'] +
                                        ' from ' +
                                        itemsDB[itemIndex]['article'] +
                                        ' ' +
                                        itemsDB[itemIndex]['name'] +
                                        '.\n\n')
                    else:
                        idx = int(containerItemID)
                        mud.sendMessage(id, 'You try to pick up ' +
                                        itemsDB[idx]['article'] +
                                        ' ' +
                                        itemsDB[idx]['name'] +
                                        " but find that your arms won't " +
                                        "move.\n\n")
                    return

        mud.sendMessage(id, 'You cannot see ' + target + ' anywhere.\n\n')
        itemPickedUp = False


def runCommand(command, params, mud, playersDB: {}, players: {}, rooms: {},
               npcsDB: {}, npcs: {}, itemsDB: {}, items: {},
               envDB: {}, env: {}, eventDB: {}, eventSchedule,
               id: int, fights: {}, corpses: {}, blocklist,
               mapArea: [], characterClassDB: {}, spellsDB: {},
               sentimentDB: {}, guildsDB: {}, clouds: {}, racesDB: {},
               itemHistory: {}, markets: {}, culturesDB: {}):
    switcher = {
        "sendCommandError": _sendCommandError,
        "go": _go,
        "north": _goNorth,
        "n": _goNorth,
        "south": _goSouth,
        "s": _goSouth,
        "east": _goEast,
        "e": _goEast,
        "west": _goWest,
        "w": _goWest,
        "up": _goUp,
        "u": _goUp,
        "down": _goDown,
        "d": _goDown,
        "in": _goIn,
        "out": _goOut,
        "o": _goOut,
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
        "attack": _attack,
        "shoot": _attack,
        "take": _take,
        "get": _take,
        "put": _putItem,
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
        "step": _stepOver,
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
        "open": _openItem,
        "close": _closeItem,
        "wind": _windLever,
        "unwind": _unwindLever,
        "pull": _pullLever,
        "yank": _pullLever,
        "push": _pushLever,
        "write": _writeOnItem,
        "tag": _writeOnItem,
        "eat": _eat,
        "drink": _eat,
        "kick": _kick,
        "change": _changeSetting,
        "blocklist": _showBlocklist,
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
        "learn": _prepareSpell,
        "prepare": _prepareSpell,
        "destroy": _destroy,
        "cast": _castSpell,
        "spell": _castSpell,
        "spells": _spells,
        "dismiss": _dismiss,
        "clear": _clearSpells,
        "spellbook": _spells,
        "affinity": _affinity,
        "escape": _escapeTrap,
        "cut": _escapeTrap,
        "slash": _escapeTrap,
        "resetuniverse": _resetUniverse,
        "shutdown": _shutdown,
        "inv": _checkInventory,
        "i": _checkInventory,
        "inventory": _checkInventory,
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
        "cards": _helpCards,
        "deal": _deal,
        "hand": _handOfCards,
        "swap": _swapACard,
        "stick": _stick,
        "shuffle": _shuffle,
        "call": _callCardGame,
        "morris": _morrisGame,
        "dodge": _dodge,
        "shove": _shove,
        "prone": _prone,
        "stand": _stand,
        "buy": _buy,
        "purchase": _buy,
        "sell": _sell,
        "trade": _sell
    }

    try:
        switcher[command](params, mud, playersDB, players, rooms, npcsDB,
                          npcs, itemsDB, items, envDB, env, eventDB,
                          eventSchedule, id, fights, corpses, blocklist,
                          mapArea, characterClassDB, spellsDB,
                          sentimentDB, guildsDB, clouds, racesDB,
                          itemHistory, markets, culturesDB)
    except Exception as e:
        # print(str(e))
        switcher["sendCommandError"](e, mud, playersDB, players, rooms,
                                     npcsDB, npcs, itemsDB, items,
                                     envDB, env, eventDB, eventSchedule,
                                     id, fights, corpses, blocklist,
                                     mapArea, characterClassDB, spellsDB,
                                     sentimentDB, guildsDB, clouds, racesDB,
                                     itemHistory, markets, culturesDB)
