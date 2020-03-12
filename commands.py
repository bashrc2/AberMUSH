__filename__ = "commands.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

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
from environment import runTide
from environment import assignCoordinates
from environment import getRainAtCoords
from traps import playerIsTrapped
from traps import describeTrappedPlayer
from traps import trapActivation
from traps import teleportFromTrap
from traps import escapeFromTrap
from combat import isAttacking
from combat import getAttackingTarget
from combat import playerBeginsAttack
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

from proficiencies import thievesCant

from npcs import npcConversation

from familiar import getFamiliarName
from familiar import familiarIsHidden

import os
import re
import sys
from copy import deepcopy
import time
import datetime
import os.path
from random import randint

from dateutil import tz
from suntime import Sun

import decimal
dec = decimal.Decimal

wearLocation=('head','neck','lwrist','rwrist','larm','rarm','chest','feet','lfinger','rfinger','back','lleg','rleg')

'''
Command function template:

def commandname(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB,guildsDB,clouds):
        print("I'm in!")
'''

# maximum weight of items which can be carried
maxWeight = 100


def removeItemFromClothing(players: {}, id: int, itemID: int) -> None:
    """If worn an item is removed
    """
    for c in wearLocation:
        if int(players[id]['clo_'+c]) == itemID:
            players[id]['clo_'+c] = 0

def sendCommandError(params,mud,playersDB: {},players: {},rooms: {}, \
                     npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                     envDB: {},env,eventDB: {},eventSchedule,id: int, \
                     fights: {},corpses,blocklist,mapArea: [], \
                     characterClassDB: {},spellsDB: {}, \
                     sentimentDB: {},guildsDB: {},clouds: {}) -> None:
    mud.send_message(id, "Unknown command " + str(params) + "!\n")


def isWitch(id: int, players: {}) -> bool:
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


def disableRegistrations(mud, id: int, players: {}) -> None:
    """Turns off new registrations
    """
    if not isWitch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return
    if os.path.isfile(".disableRegistrations"):
        mud.send_message(id, "New registrations are already closed.\n\n")
        return
    with open(".disableRegistrations", 'w') as fp:
        fp.write('')
    mud.send_message(id, "New player registrations are now closed.\n\n")


def enableRegistrations(mud, id: int, players: {}) -> None:
    """Turns on new registrations
    """
    if not isWitch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return
    if not os.path.isfile(".disableRegistrations"):
        mud.send_message(id, "New registrations are already allowed.\n\n")
        return
    os.remove(".disableRegistrations")
    mud.send_message(id, "New player registrations are now permitted.\n\n")


def teleport(params,mud,playersDB: {},players: {},rooms: {},npcsDB: {}, \
             npcs: {},itemsDB: {},items: {},envDB: {},env,eventDB: {}, \
             eventSchedule,id: int,fights: {},corpses: {},blocklist, \
             mapArea: [],characterClassDB: {},spellsDB: {},sentimentDB: {}, \
             guildsDB: {},clouds: {}) -> None:

    if players[id]['permissionLevel'] != 0:
        mud.send_message(id, "You don't have enough powers for that.\n\n")
        return

    if isWitch(id, players):
        if playerIsTrapped(id,players,rooms):
            teleportFromTrap(mud,id,players,rooms)

        targetLocation = params[0:].strip().lower().replace('to ', '',1)
        if len(targetLocation) != 0:
            currRoom = players[id]['room']
            if rooms[currRoom]['name'].strip().lower() == targetLocation:
                mud.send_message(
                    id, "You are already in " + \
                    rooms[currRoom]['name'] + \
                    "\n\n")
                return
            for rm in rooms:
                if rooms[rm]['name'].strip().lower() == targetLocation:
                    mud.send_message(
                        id, "You teleport to " + rooms[rm]['name'] + "\n\n")
                    messageToPlayersInRoom(mud, players, id, \
                                           '<f32>{}<r> suddenly vanishes.'.format(players[id]['name']) + "\n\n")
                    players[id]['room'] = rm
                    messageToPlayersInRoom(mud, players, id, \
                                           '<f32>{}<r> suddenly appears.'.format(players[id]['name']) + "\n\n")
                    look('',mud,playersDB,players,rooms,npcsDB,npcs, \
                         itemsDB,items,envDB,env,eventDB,eventSchedule, \
                         id,fights,corpses,blocklist,mapArea, \
                         characterClassDB,spellsDB,sentimentDB, \
                         guildsDB,clouds)
                    return

            # try adding or removing "the"
            if targetLocation.startswith('the '):
                targetLocation=targetLocation.replace('the ','')
            else:
                targetLocation='the '+targetLocation
                
            for rm in rooms:
                if rooms[rm]['name'].strip().lower() == targetLocation:
                    mud.send_message(
                        id, "You teleport to " + rooms[rm]['name'] + "\n\n")
                    messageToPlayersInRoom(
                        mud, players, id, '<f32>{}<r> suddenly vanishes.'.format(players[id]['name']) + "\n\n")
                    players[id]['room'] = rm
                    messageToPlayersInRoom(
                        mud, players, id, '<f32>{}<r> suddenly appears.'.format(players[id]['name']) + "\n\n")
                    look('',mud,playersDB,players,rooms,npcsDB,npcs, \
                         itemsDB,items,envDB,env,eventDB,eventSchedule, \
                         id,fights,corpses,blocklist,mapArea, \
                         characterClassDB,spellsDB,sentimentDB, \
                         guildsDB,clouds)
                    return

            mud.send_message(
                id, targetLocation+" isn't a place you can teleport to.\n\n")
        else:
            mud.send_message(id, "That's not a place.\n\n")
    else:
        mud.send_message(id, "You don't have enough powers to teleport.\n\n")

def summon(params,mud,playersDB: {},players: {},rooms: {},npcsDB: {}, \
           npcs: {},itemsDB: {},items: {},envDB: {},env,eventDB: {}, \
           eventSchedule,id: int,fights: {},corpses: {},blocklist, \
           mapArea: [],characterClassDB: {},spellsDB: {}, \
           sentimentDB: {},guildsDB: {},clouds: {}) -> None:
    if players[id]['permissionLevel'] == 0:
        if isWitch(id, players):
            targetPlayer = params[0:].strip().lower()
            if len(targetPlayer) != 0:
                for p in players:
                    if players[p]['name'].strip().lower() == targetPlayer:
                        if players[p]['room'] != players[id]['room']:
                            messageToPlayersInRoom(
                                mud, players, p, '<f32>{}<r> suddenly vanishes.'.format(
                                    players[p]['name']) + "\n")
                            players[p]['room'] = players[id]['room']
                            rm = players[p]['room']
                            mud.send_message(
                                id, "You summon " + players[p]['name'] + "\n\n")
                            mud.send_message(p, \
                                             "A mist surrounds you. When it "+ \
                                             "clears you find that you are now in "+ \
                                             rooms[rm]['name']+"\n\n")
                        else:
                            mud.send_message(
                                id, players[p]['name'] + " is already here.\n\n")
                        return
        else:
            mud.send_message(id, "You don't have enough powers for that.\n\n")


def mute(params,mud,playersDB: {},players: {},rooms: {},npcsDB: {}, \
         npcs: {},itemsDB: {},items: {},envDB: {},env,eventDB: {}, \
         eventSchedule,id: int,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB: {}, \
         sentimentDB: {},guildsDB: {},clouds: {}) -> None:
    if players[id]['permissionLevel'] != 0:
        mud.send_message(
            id, "You aren't capable of doing that.\n\n")
        return
    if not isWitch(id, players):
        mud.send_message(
            id, "You aren't capable of doing that.\n\n")
        return
    target = params.partition(' ')[0]
    if len(target) != 0:
        for p in players:
            if players[p]['name'] == target:
                if not isWitch(p, players):
                    players[p]['canSay'] = 0
                    players[p]['canAttack'] = 0
                    players[p]['canDirectMessage'] = 0
                    mud.send_message(
                        id, "You have muted " + target + "\n\n")
                else:
                    mud.send_message(
                        id, "You try to mute " + target + \
                        " but their power is too strong.\n\n")
                return


def unmute(params,mud,playersDB: {},players: {},rooms: {},npcsDB: {}, \
           npcs: {},itemsDB: {},items: {},envDB: {},env,eventDB: {}, \
           eventSchedule,id: int,fights: {},corpses: {},blocklist, \
           mapArea: [],characterClassDB: {},spellsDB: {}, \
           sentimentDB: {},guildsDB: {},clouds: {}) -> None:
    if players[id]['permissionLevel'] != 0:
        mud.send_message(
            id, "You aren't capable of doing that.\n\n")
        return
    if not isWitch(id, players):
        mud.send_message(
            id, "You aren't capable of doing that.\n\n")
        return
    target = params.partition(' ')[0]
    if len(target) != 0:
        if target.lower() != 'guest':
            for p in players:
                if players[p]['name'] == target:
                    if not isWitch(p, players):
                        players[p]['canSay'] = 1
                        players[p]['canAttack'] = 1
                        players[p]['canDirectMessage'] = 1
                        mud.send_message(
                            id, "You have unmuted " + target + "\n\n")
                    return


def freeze(params,mud,playersDB: {},players: {},rooms: {},npcsDB: {}, \
           npcs: {},itemsDB: {},items: {},envDB: {},env,eventDB: {}, \
           eventSchedule,id: int,fights: {},corpses: {},blocklist, \
           mapArea: [],characterClassDB: {},spellsDB: {}, \
           sentimentDB: {},guildsDB: {},clouds: {}):
    if players[id]['permissionLevel'] == 0:
        if isWitch(id, players):
            target = params.partition(' ')[0]
            if len(target) != 0:
                # freeze players
                for p in players:
                    if players[p]['whenDied']:
                        mud.send_message(
                            id, "Freezing a player while dead is pointless\n\n")
                        continue
                    if players[p]['frozenStart'] > 0:
                        mud.send_message(
                            id, "They are already frozen\n\n")
                        continue
                    if target in players[p]['name']:
                        if not isWitch(p, players):
                            # remove from any fights
                            for (fight, pl) in fights.items():
                                if fights[fight]['s1id']==p or \
                                   fights[fight]['s2id']==p:
                                    del fights[fight]
                            players[p]['canGo'] = 0
                            players[p]['canAttack'] = 0
                            mud.send_message(
                                id, "You have frozen " + target + "\n\n")
                        else:
                            mud.send_message(
                                id, "You try to freeze " + target + " but their power is too strong.\n\n")
                        return
                # freeze npcs
                for p in npcs:
                    if npcs[p]['whenDied']:
                        mud.send_message(
                            id, "Freezing while dead is pointless\n\n")
                        continue
                    if npcs[p]['frozenStart'] > 0:
                        mud.send_message(
                            id, "They are already frozen\n\n")
                        continue
                    if target in npcs[p]['name']:
                        if not isWitch(p, npcs):
                            # remove from any fights
                            for (fight, pl) in fights.items():
                                if fights[fight]['s1id']==p or \
                                   fights[fight]['s2id']==p:
                                    del fights[fight]

                            npcs[p]['canGo'] = 0
                            npcs[p]['canAttack'] = 0
                            mud.send_message(
                                id, "You have frozen " + target + "\n\n")
                        else:
                            mud.send_message(
                                id, "You try to freeze " + target + " but their power is too strong.\n\n")
                        return


def unfreeze(params,mud,playersDB: {},players: {},rooms: {},\
             npcsDB: {}, npcs: {},itemsDB: {},items: {}, \
             envDB: {},env: {},eventDB: {},eventSchedule, \
             id: int,fights: {},corpses: {},blocklist, \
             mapArea: [],characterClassDB: {},spellsDB: {},
             sentimentDB: {},guildsDB: {},clouds: {}):
    if players[id]['permissionLevel'] == 0:
        if isWitch(id, players):
            target = params.partition(' ')[0]
            if len(target) != 0:
                if target.lower() != 'guest':
                    # unfreeze players
                    for p in players:
                        if target in players[p]['name']:
                            if not isWitch(p, players):
                                players[p]['canGo'] = 1
                                players[p]['canAttack'] = 1
                                players[p]['frozenStart'] = 0
                                mud.send_message(
                                    id, "You have unfrozen " + target + "\n\n")
                            return
                    # unfreeze npcs
                    for p in npcs:
                        if target in npcs[p]['name']:
                            if not isWitch(p, npcs):
                                npcs[p]['canGo'] = 1
                                npcs[p]['canAttack'] = 1
                                npcs[p]['frozenStart'] = 0
                                mud.send_message(
                                    id, "You have unfrozen " + target + "\n\n")
                            return


def showBlocklist(params,mud,playersDB: {},players: {},rooms: {}, \
                  npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                  envDB: {},env: {},eventDB: {},eventSchedule, \
                  id: int,fights: {},corpses: {},blocklist, \
                  mapArea: [],characterClassDB: {},spellsDB: {},
                  sentimentDB: {},guildsDB: {},clouds: {}):
    if not isWitch(id, players):
        mud.send_message(id, "You don't have sufficient powers to do that.\n")
        return

    blocklist.sort()

    blockStr = ''
    for blockedstr in blocklist:
        blockStr = blockStr + blockedstr + '\n'

    mud.send_message(id, "Blocked strings are:\n\n" + blockStr + '\n')


def block(params,mud,playersDB: {},players: {},rooms: {}, \
          npcsDB: {},npcs: {},itemsDB: {},items: {},envDB: {}, \
          env: {},eventDB: {},eventSchedule, \
          id: int,fights: {},corpses: {},blocklist, \
          mapArea: [],characterClassDB: {},spellsDB: {}, \
          sentimentDB: {},guildsDB: {},clouds: {}):
    if not isWitch(id, players):
        mud.send_message(id, "You don't have sufficient powers to do that.\n")
        return

    if len(params) == 0:
        showBlocklist(params,mud,playersDB,players,rooms,npcsDB,npcs, \
                      itemsDB,items,envDB,env,eventDB,eventSchedule, \
                      id,fights,corpses,blocklist,mapArea,characterClassDB, \
                      spellsDB,sentimentDB,guildsDB,clouds)
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
        mud.send_message(id, "Blocklist updated.\n\n")
    else:
        mud.send_message(id, "That's already in the blocklist.\n")


def unblock(params,mud,playersDB: {},players: {},rooms: {},npcsDB: {}, \
            npcs: {},itemsDB: {},items: {},envDB: {},env: {}, \
            eventDB: {},eventSchedule, \
            id: int,fights: {},corpses: {},blocklist, \
            mapArea: [],characterClassDB: {},spellsDB: {}, \
            sentimentDB: {},guildsDB: {},clouds: {}):
    if not isWitch(id, players):
        mud.send_message(id, "You don't have sufficient powers to do that.\n")
        return

    if len(params) == 0:
        showBlocklist(params,mud,playersDB,players,rooms,npcsDB, \
                      npcs,itemsDB,items,envDB,env,eventDB,eventSchedule, \
                      id,fights,corpses,blocklist,mapArea, \
                      characterClassDB,spellsDB,sentimentDB,guildsDB, \
                      clouds)
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
        mud.send_message(id, "Blocklist updated.\n\n")
    else:
        mud.send_message(id, "That's not in the blocklist.\n")


def kick(params,mud,playersDB: {},players: {},rooms: {}, \
         npcsDB: {},npcs: {},itemsDB: {},items: {}, \
         envDB: {},env: {},eventDB: {},eventSchedule, \
         id: int,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB: {}, \
         sentimentDB: {},guildsDB: {},clouds: {}):
    if not isWitch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return

    playerName = params

    if len(playerName) == 0:
        mud.send_message(id, "Who?\n\n")
        return

    for (pid, pl) in list(players.items()):
        if players[pid]['name'] == playerName:
            mud.send_message(id, "Removing player " + playerName + "\n\n")
            mud._handle_disconnect(pid)
            return

    mud.send_message(id, "There are no players with that name.\n\n")

def shutdown(params,mud,playersDB: {},players: {},rooms: {}, \
             npcsDB: {},npcs: {},itemsDB: {},items: {}, \
             envDB: {},env: {},eventDB: {},eventSchedule, \
             id: int,fights: {},corpses: {},blocklist, \
             mapArea: [],characterClassDB: {},spellsDB: {},
             sentimentDB: {},guildsDB: {},clouds: {}):
    if not isWitch(id, players):
        mud.send_message(id, "You don't have enough power to do that.\n\n")
        return

    mud.send_message(id, "\n\nShutdown commenced.\n\n")
    saveUniverse(rooms, npcsDB, npcs, itemsDB, items, envDB, env, guildsDB)
    mud.send_message(id, "\n\nUniverse saved.\n\n")
    log("Universe saved", "info")
    for (pid, pl) in list(players.items()):
        mud.send_message(pid, "Game server shutting down...\n\n")
        mud._handle_disconnect(pid)
    log("Shutting down", "info")
    sys.exit()


def resetUniverse(params,mud,playersDB: {},players: {},rooms: {}, \
                  npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                  envDB: {},env: {},eventDB: {},eventSchedule, \
                  id: int,fights: {},corpses: {},blocklist, \
                  mapArea: [],characterClassDB: {},spellsDB, \
                  sentimentDB: {},guildsDB: {},clouds: {}):
    if not isWitch(id, players):
        mud.send_message(id, "You don't have enough power to do that.\n\n")
        return
    os.system('rm universe*.json')
    log('Universe reset', 'info')
    for (pid, pl) in list(players.items()):
        mud.send_message(pid, "Game server shutting down...\n\n")
        mud._handle_disconnect(pid)
    log("Shutting down", "info")
    sys.exit()


def quit(params,mud,playersDB: {},players: {},rooms: {}, \
         npcsDB: {},npcs: {},itemsDB: {},items: {}, \
         envDB: {},env: {},eventDB: {},eventSchedule, \
         id: int,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB: {}, \
         sentimentDB: {},guildsDB: {},clouds: {}):
    mud._handle_disconnect(id)


def who(params,mud,playersDB: {},players: {},rooms: {}, \
        npcsDB: {},npcs: {},itemsDB: {},items: {}, \
        envDB: {},env: {},eventDB: {},eventSchedule, \
        id: int,fights: {},corpses: {},blocklist, \
        mapArea: [],characterClassDB: {},spellsDB, \
        sentimentDB: {},guildsDB: {},clouds: {}):
    counter = 1
    if players[id]['permissionLevel'] == 0:
        is_witch = isWitch(id, players)
        for p in players:
            if players[p]['name'] is None:
                continue

            if not is_witch:
                name = players[p]['name']
            else:
                if not isWitch(p, players):
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

            mud.send_message(id, str(counter) + ". " + name + " is in " + room)
            counter += 1
        mud.send_message(id, "\n")
    else:
        mud.send_message(id, "You do not have permission to do this.\n")
    
def tell(params,mud,playersDB: {},players: {},rooms: {}, \
         npcsDB: {},npcs: {},itemsDB: {},items: {}, \
         envDB: {},env: {},eventDB: {},eventSchedule, \
         id: int,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB: {}, \
         sentimentDB: {},guildsDB: {},clouds: {}):
    told = False
    target = params.partition(' ')[0]

    # replace "familiar" with their NPC name
    # as in: "ask familiar to follow"
    if target.lower()=='familiar':
        newTarget=getFamiliarName(players,id,npcs)
        if len(newTarget)>0:
            target=newTarget

    message = params.replace(target, "")[1:]
    if len(target) != 0 and len(message) != 0:
        cantStr = thievesCant(message)
        for p in players:
            if players[p]['authenticated'] is not None and players[p]['name'].lower() == target.lower():
                #print("sending a tell")
                if players[id]['name'].lower() == target.lower():
                    mud.send_message(
                        id, "It'd be pointless to send a tell message to yourself\n")
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
                        if players[id]['speakLanguage'] in players[p]['language']:
                            addToScheduler(
                                "0|msg|<f90>From " +
                                players[id]['name'] +
                                ": " +
                                message +
                                '\n',
                                p,
                                eventSchedule,
                                eventDB)
                            sentimentScore= \
                                getSentiment(message, sentimentDB) + \
                                getGuildSentiment(players, id, players, p, guildsDB)
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
                                    '\n',
                                    p,
                                    eventSchedule,
                                    eventDB)
                            else:
                                addToScheduler(
                                    "0|msg|<f90>From " +
                                    players[id]['name'] +
                                    ": " +
                                    cantStr +
                                    '\n',
                                    p,
                                    eventSchedule,
                                    eventDB)
                    mud.send_message(
                        id,
                        "<f90>To " +
                        players[p]['name'] +
                        ": " +
                        message +
                        "\n\n")
                    told = True
                    break
        if not told:            
            for (nid, pl) in list(npcs.items()):
                if (npcs[nid]['room'] == players[id]['room']) or \
                   npcs[nid]['familiarOf'] == players[id]['name']:
                    if target.lower() in npcs[nid]['name'].lower():
                        npcConversation(
                            mud,
                            npcs,
                            npcsDB,
                            players,
                            items,
                            itemsDB,
                            rooms,
                            id,
                            nid,
                            message.lower(),
                            characterClassDB,
                            sentimentDB,
                            guildsDB,
                            clouds)
                        told = True
                        break

        if not told:
            mud.send_message(
                id,
                "<f32>" +
                target +
                "<r> does not appear to be reachable at this moment.\n\n")
    else:
        mud.send_message(id, "Huh?\n\n")


def whisper(params,mud,playersDB: {},players: {},rooms: {}, \
            npcsDB: {},npcs: {},itemsDB: {},items: {}, \
            envDB: {},env: {},eventDB: {},eventSchedule, \
            id: int,fights: {},corpses: {},blocklist, \
            mapArea: [],characterClassDB: {},spellsDB: {}, \
            sentimentDB: {},guildsDB: {},clouds: {}):
    target = params.partition(' ')[0]
    message = params.replace(target, "")

    # if message[0] == " ":
    #message.replace(message[0], "")
    messageSent = False
    # print(message)
    # print(str(len(message)))
    if len(target) > 0:
        if len(message) > 0:
            cantStr = thievesCant(message)
            for p in players:
                if players[p]['name'] is not None and players[p]['name'].lower(
                ) == target.lower():
                    if players[p]['room'] == players[id]['room']:
                        if players[p]['name'].lower(
                        ) != players[id]['name'].lower():

                            # don't whisper if the string contains a blocked
                            # string
                            selfOnly = False
                            msglower = message[1:].lower()
                            for blockedstr in blocklist:
                                if blockedstr in msglower:
                                    selfOnly = True
                                    break

                            sentimentScore= \
                                getSentiment(message[1:], sentimentDB) + \
                                getGuildSentiment(players, id, players, p, guildsDB)
                            if sentimentScore >= 0:
                                increaseAffinityBetweenPlayers(
                                    players, id, players, p, guildsDB)
                            else:
                                decreaseAffinityBetweenPlayers(
                                    players, id, players, p, guildsDB)

                            mud.send_message(
                                id, "You whisper to <f32>" + players[p]['name'] + "<r>: " + message[1:] + '\n')
                            if not selfOnly:
                                if players[id]['speakLanguage'] in players[p]['language']:

                                    mud.send_message(
                                        p, "<f162>" + players[id]['name'] + " whispers: " + message[1:] + '\n')
                                else:
                                    if players[id]['speakLanguage'] != 'cant':
                                        mud.send_message(
                                            p,
                                            "<f162>" +
                                            players[id]['name'] +
                                            " whispers something in " +
                                            players[id]['speakLanguage'] +
                                            '\n')
                                    else:
                                        mud.send_message(
                                            p, "<f162>" + players[id]['name'] + " whispers:  " + cantStr + '\n')
                            messageSent = True
                            break
                        else:
                            mud.send_message(
                                id, "You would probably look rather silly whispering to yourself.\n")
                            messageSent = True
                            break
            if not messageSent:
                mud.send_message(
                    id, "<f32>" + target + "<r> is not here with you.\n")
        else:
            mud.send_message(id, "What would you like to whisper?\n")
    else:
        mud.send_message(id, "Who would you like to whisper to??\n")


def help(params,mud,playersDB: {},players: {},rooms: {}, \
         npcsDB: {},npcs: {},itemsDB: {},items: {}, \
         envDB: {},env: {},eventDB: {},eventSchedule, \
         id: int,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB, \
         sentimentDB: {},guildsDB: {},clouds: {}):
    if params.lower().startswith('card'):
        helpCards(params,mud,playersDB,players,rooms,npcsDB,npcs,itemsDB, \
                  items,envDB,env,eventDB,eventSchedule,id,fights,corpses, \
                  blocklist,mapArea,characterClassDB,spellsDB,sentimentDB, \
                  guildsDB,clouds)
        return
    if params.lower().startswith('chess'):
        helpChess(params,mud,playersDB,players,rooms,npcsDB,npcs,itemsDB, \
                  items,envDB,env,eventDB,eventSchedule,id,fights,corpses, \
                  blocklist,mapArea,characterClassDB,spellsDB,sentimentDB, \
                  guildsDB,clouds)
        return
    if params.lower().startswith('morris'):
        helpMorris(params,mud,playersDB,players,rooms,npcsDB,npcs,itemsDB, \
                   items,envDB,env,eventDB,eventSchedule,id,fights,corpses, \
                   blocklist,mapArea,characterClassDB,spellsDB,sentimentDB, \
                   guildsDB,clouds)
        return
    if params.lower().startswith('witch'):
        helpWitch(params,mud,playersDB,players,rooms,npcsDB,npcs,itemsDB, \
                  items,envDB,env,eventDB,eventSchedule,id,fights,corpses, \
                  blocklist,mapArea,characterClassDB,spellsDB,sentimentDB, \
                  guildsDB,clouds)
        return
    if params.lower().startswith('spell'):
        helpSpell(params,mud,playersDB,players,rooms,npcsDB,npcs,itemsDB, \
                  items,envDB,env,eventDB,eventSchedule,id,fights,corpses, \
                  blocklist,mapArea,characterClassDB,spellsDB,sentimentDB, \
                  guildsDB,clouds)
        return

    mud.send_message(id, '\n')
    mud.send_message(id, 'Commands:')
    mud.send_message(id, \
                     '  help witch|spell|cards|chess|morris     - Show help')
    mud.send_message(id, \
                     '  bio [description]                       - Set a description of yourself')
    mud.send_message(id, \
                     '  graphics [on|off]                       - Turn graphic content on or off')
    mud.send_message(id, \
                     '  change password [newpassword]           - Change your password')
    mud.send_message(id, \
                     '  who                                     - List players and where they are')
    mud.send_message(id, \
                     '  quit/exit                               - Leave the game')
    mud.send_message(id, \
                     '  eat/drink [item]                        - Eat or drink a consumable')
    mud.send_message(id, \
                     '  speak [language]                        - Switch to speaking a different language')
    mud.send_message(id, \
                     '  say [message]                           - Says something out loud, ' +
                     "e.g. 'say Hello'")
    mud.send_message(id, \
                     '  look/examine                            - Examines the ' +
                     "surroundings, items in the room, NPCs or other players e.g. 'examine inn-keeper'")
    mud.send_message(id, \
                     '  go [exit]                               - Moves through the exit ' +
                     "specified, e.g. 'go outside'")
    mud.send_message(id, \
                     '  climb though [exit]                     - Try to climb through an exit');
    mud.send_message(id, \
                     '  move/roll/heave [target]                - Try to move or roll a heavy object');
    mud.send_message(id, \
                     '  jump to [exit]                          - Try to jump onto something');    
    mud.send_message(id, \
                     '  attack [target]                         - Attack target ' +
                     "specified, e.g. 'attack knight'")
    mud.send_message(id, \
                     '  check inventory                         - Check the contents of ' +
                     "your inventory")
    mud.send_message(id, \
                     '  take/get [item]                         - Pick up an item lying ' + \
                     "on the floor")
    mud.send_message(id, \
                     '  put [item] in/on [item]                 - Put an item into or onto another one')
    mud.send_message(id, \
                     '  drop [item]                             - Drop an item from your inventory ' + \
                     "on the floor")
    mud.send_message(id, \
                     '  use/hold/pick/wield [item] [left|right] - Transfer an item to your hands')
    mud.send_message(id, \
                     '  stow                                    - Free your hands of items')
    mud.send_message(id, \
                     '  wear [item]                             - Wear an item')
    mud.send_message(id, \
                     '  remove/unwear [item]                    - Remove a worn item')
    mud.send_message(id, \
                     '  whisper [target] [message]              - Whisper to a player in the same room')
    mud.send_message(id, \
                     '  tell/ask [target] [message]             - Send a tell message to another player or NPC')
    mud.send_message(id, \
                     '  open [item]                             - Open an item or door')
    mud.send_message(id, \
                     '  close [item]                            - Close an item or door')
    mud.send_message(id, \
                     '  push [item]                             - Pushes a lever')
    mud.send_message(id, \
                     '  pull [item]                             - Pulls a lever')
    mud.send_message(id, \
                     '  wind [item]                             - Winds a lever')
    mud.send_message(id, \
                     '  affinity [player name]                  - Shows your affinity level with another player')
    mud.send_message(id, \
                     '  cut/escape                              - Attempt to escape from a trap')
    mud.send_message(id, \
                     '  step over tripwire [exit]               - Step over a tripwire in the given direction')
    mud.send_message(id, '\n\n')


def helpSpell(params,mud,playersDB: {},players: {},rooms: {}, \
              npcsDB: {},npcs: {},itemsDB: {},items: {}, \
              envDB: {},env: {},eventDB: {},eventSchedule, \
              id: int,fights: {},corpses: {},blocklist, \
              mapArea: [],characterClassDB: {},spellsDB: {}, \
              sentimentDB: {},guildsDB: {},clouds: {}):
    mud.send_message(id, '\n')
    mud.send_message(id, \
                     'prepare spells                          - List spells which can be prepared')
    mud.send_message(id, \
                     'prepare [spell name]                    - Prepares a spell')
    mud.send_message(id, \
                     'spells                                  - Lists your prepared spells')
    mud.send_message(id, \
                     'clear spells                            - Clears your prepared spells list')
    mud.send_message(id, \
                     'cast find familiar                      - Summons a familiar with random form')
    mud.send_message(id, \
                     'dismiss familiar                        - Dismisses a familiar')
    mud.send_message(id, \
                     'cast [spell name] on [target]           - Cast a spell on a player or NPC')

    mud.send_message(id, '\n\n')


def helpWitch(params,mud,playersDB: {},players: {},rooms: {}, \
              npcsDB: {},npcs: {},itemsDB: {},items: {}, \
              envDB: {},env: {},eventDB: {},eventSchedule, \
              id: int,fights: {},corpses: {},blocklist, \
              mapArea: [],characterClassDB: {},spellsDB: {},
              sentimentDB: {},guildsDB: {},clouds: {}):
    mud.send_message(id, '\n')
    if not isWitch(id, players):        
        mud.send_message(id, "You're not a witch.\n\n")
        return
    mud.send_message(id, \
                         'close registrations                     - Closes registrations of new players')
    mud.send_message(id, \
                         'open registrations                      - Allows registrations of new players')
    mud.send_message(id, \
                         'mute/silence [target]                   - Mutes a player and prevents them from attacking')
    mud.send_message(id, \
                         'unmute/unsilence [target]               - Unmutes a player')
    mud.send_message(id, \
                         'freeze [target]                         - Prevents a player from moving or attacking')
    mud.send_message(id, \
                         'unfreeze [target]                       - Allows a player to move or attack')
    mud.send_message(id, \
                         'teleport [room]                         - Teleport to a room')
    mud.send_message(id, \
                         'summon [target]                         - Summons a player to your location')
    mud.send_message(id, \
                         'kick/remove [target]                    - Remove a player from the game')
    mud.send_message(id, \
                         'blocklist                               - Show the current blocklist')
    mud.send_message(id, \
                         'block [word or phrase]                  - Adds a word or phrase to the blocklist')
    mud.send_message(id, \
                         'unblock [word or phrase]                - Removes a word or phrase to the blocklist')
    mud.send_message(id, \
                         'describe "room" "room name"             - Changes the name of the current room')
    mud.send_message(id, \
                         'describe "room description"             - Changes the current room description')
    mud.send_message(id, \
                         'describe "tide" "room description"      - Changes the room description when tide is out')
    mud.send_message(id, \
                         'describe "item" "item description"      - Changes the description of an item in the room')
    mud.send_message(id, \
                         'describe "NPC" "NPC description"        - Changes the description of an NPC in the room')
    mud.send_message(id, \
                         'conjure room [direction]                - Creates a new room in the given direction')
    mud.send_message(id, \
                         'conjure npc [target]                    - Creates a named NPC in the room')
    mud.send_message(id, \
                         'conjure [item]                          - Creates a new item in the room')
    mud.send_message(id, \
                         'destroy room [direction]                - Removes the room in the given direction')
    mud.send_message(id, \
                         'destroy npc [target]                    - Removes a named NPC from the room')
    mud.send_message(id, \
                         'destroy [item]                          - Removes an item from the room')
    mud.send_message(id, \
                         'resetuniverse                           - Resets the universe, losing any changes from defaults')
    mud.send_message(id, \
                         'shutdown                                - Shuts down the game server')
    mud.send_message(id, '\n\n')


def helpMorris(params,mud,playersDB: {},players: {},rooms, \
               npcsDB: {},npcs: {},itemsDB: {},items: {}, \
               envDB: {},env: {},eventDB: {},eventSchedule, \
               id: int,fights: {},corpses: {},blocklist, \
               mapArea: [],characterClassDB: {},spellsDB: {}, \
               sentimentDB: {},guildsDB: {},clouds: {}):
    mud.send_message(id, '\n')
    mud.send_message(id, \
                     'morris                                  - Show the board')
    mud.send_message(id, \
                     'morris put [coordinate]                 - Place a counter')
    mud.send_message(id, \
                     'morris move [from coord] [to coord]     - Move a counter')
    mud.send_message(id, \
                     'morris take [coordinate]                - Remove a counter after mill')
    mud.send_message(id, \
                     'morris reset                            - Resets the board')
    mud.send_message(id, '\n\n')

def helpChess(params,mud,playersDB: {},players: {},rooms: {}, \
              npcsDB: {},npcs: {},itemsDB: {},items: {}, \
              envDB: {},env: {},eventDB: {},eventSchedule, \
              id: int,fights: {},corpses: {},blocklist, \
              mapArea: [],characterClassDB: {},spellsDB: {}, \
              sentimentDB: {},guildsDB: {},clouds: {}):
    mud.send_message(id, '\n')
    mud.send_message(id, \
                     'chess                                   - Shows the board')
    mud.send_message(id, \
                     'chess reset                             - Rests the game')
    mud.send_message(id, \
                     'chess move [coords]                     - eg. chess move e2e3')
    mud.send_message(id, \
                     'chess undo                              - undoes the last move')
    mud.send_message(id, '\n\n')

def helpCards(params,mud,playersDB: {},players: {},rooms: {}, \
              npcsDB: {},npcs: {},itemsDB: {},items: {}, \
              envDB: {},env: {},eventDB: {},eventSchedule, \
              id: int,fights: {},corpses: {},blocklist, \
              mapArea: [],characterClassDB: {},spellsDB: {}, \
              sentimentDB: {},guildsDB: {},clouds: {}):
    mud.send_message(id, '\n')
    mud.send_message(id, \
                     'shuffle                                 - Shuffles the deck')
    mud.send_message(id, \
                     'deal to [player names]                  - Deals cards')
    mud.send_message(id, \
                     'hand                                    - View your hand of cards')
    mud.send_message(id, \
                     'swap [card description]                 - Swaps a card')
    mud.send_message(id, \
                     'call                                    - Players show their hands')
    mud.send_message(id, '\n\n')


def removePreparedSpell(players, id, spellName):
    del players[id]['preparedSpells'][spellName]
    del players[id]['spellSlots'][spellName]


def castSpellOnPlayer(mud, spellName, players: {}, id, npcs: {}, p, spellDetails):
    if npcs[p]['room'] != players[id]['room']:
        mud.send_message(id, "They're not here.\n\n")
        return

    if spellDetails['action'].startswith('protect'):
        npcs[p]['tempHitPoints'] = spellDetails['hp']
        npcs[p]['tempHitPointsDuration'] = TimeStringToSec(spellDetails['duration'])
        npcs[p]['tempHitPointsStart'] = int(time.time())

    if spellDetails['action'].startswith('cure'):
        if npcs[p]['hp'] < npcs[p]['hpMax']:
            npcs[p]['hp'] += randint(1,spellDetails['hp'])
            if npcs[p]['hp'] > npcs[p]['hpMax']:
                npcs[p]['hp'] = npcs[p]['hpMax']

    if spellDetails['action'].startswith('charm'):
        charmTarget=players[id]['name']
        charmValue=int(npcs[p]['cha'] + players[id]['cha'])
        npcs[p]['tempCharm'] = charmValue
        npcs[p]['tempCharmTarget'] = charmTarget
        npcs[p]['tempCharmDuration'] = TimeStringToSec(spellDetails['duration'])
        npcs[p]['tempCharmStart'] = int(time.time())
        if npcs[p]['affinity'].get(charmTarget):
            npcs[p]['affinity'][charmTarget]+=charmValue
        else:
            npcs[p]['affinity'][charmTarget]=charmValue

    if spellDetails['action'].startswith('friend'):
        if players[id]['cha'] < npcs[p]['cha']:
            removePreparedSpell(players, id, spellName)
            mud.send_message(id, "You don't have enough charisma.\n\n")
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

    showSpellImage(mud,id,spellName.replace(' ','_'),players)

    mud.send_message(
        id,
        randomDescription(spellDetails['description']).format('<f32>' + \
                                                              npcs[p]['name'] + \
                                                              '<r>') + '\n\n')

    secondDesc = randomDescription(spellDetails['description_second'])
    if npcs == players and len(secondDesc) > 0:
        mud.send_message(
            p,
            secondDesc.format(players[id]['name'], \
                              'you') + '\n\n')

    removePreparedSpell(players, id, spellName)


def castSpellUndirected(params,mud,playersDB: {},players: {},rooms: {}, \
                        npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                        envDB: {},env: {},eventDB: {},eventSchedule, \
                        id: int,fights: {},corpses: {},blocklist, \
                        mapArea: [],characterClassDB: {},spellsDB: {}, \
                        sentimentDB: {},spellName: {},spellDetails: {}):
    if spellDetails['action'].startswith('familiar'):
        showSpellImage(mud,id,spellName.replace(' ','_'),players)
        conjureNPC(spellDetails['action'],mud,playersDB,players, \
                   rooms,npcsDB,npcs,itemsDB,items,envDB,env, \
                   eventDB,eventSchedule,id,fights,corpses, \
                   blocklist,mapArea,characterClassDB,spellsDB, \
                   sentimentDB,guildsDB,clouds)
        return
    mud.send_message(id, "Nothing happens.\n\n")

def castSpell(params,mud,playersDB: {},players: {},rooms: {}, \
              npcsDB: {},npcs: {},itemsDB: {},items: {}, \
              envDB: {},env: {},eventDB: {},eventSchedule, \
              id: int,fights: {},corpses: {},blocklist, \
              mapArea: [],characterClassDB: {},spellsDB: {}, \
              sentimentDB: {},guildsDB: {},clouds: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if len(params.strip()) == 0:
        mud.send_message(id, 'You try to cast a spell but fail horribly.\n\n')
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
        mud.send_message(id, "That's not a prepared spell.\n\n")
        return

    spellDetails = None
    if spellsDB.get('cantrip'):
        if spellsDB['cantrip'].get(spellName):
            spellDetails = spellsDB['cantrip'][spellName]
    if spellDetails is None:
        maxSpellLevel = getPlayerMaxSpellLevel(players, id)
        for level in range(1, maxSpellLevel + 1):
            if spellsDB[str(level)].get(spellName):
                spellDetails = spellsDB[str(level)][spellName]
                break
    if spellDetails is None:
        mud.send_message(id, "You have no knowledge of that spell.\n\n")
        return

    if len(castAt) > 0:
        for p in players:
            if castAt not in players[p]['name'].lower():
                continue
            if p == id:
                mud.send_message(id, "This is not a hypnosis spell.\n\n")
                return
            castSpellOnPlayer(
                mud,spellName,players,id,players,p,spellDetails)
            return

        for p in npcs:
            if castAt not in npcs[p]['name'].lower():
                continue

            if npcs[p]['familiarOf'] == players[id]['name']:
                mud.send_message(
                    id, "You can't cast a spell on your own familiar!\n\n")
                return

            castSpellOnPlayer(mud,spellName,players,id,npcs, \
                              p,spellDetails)
            return
    else:
        castSpellUndirected(params,mud,playersDB,players,rooms, \
                            npcsDB,npcs,itemsDB,items,envDB, \
                            env,eventDB,eventSchedule,id,fights, \
                            corpses,blocklist,mapArea, \
                            characterClassDB,spellsDB,sentimentDB, \
                            spellName,spellDetails)


def affinity(params,mud,playersDB: {},players: {},rooms: {}, \
             npcsDB: {},npcs: {},itemsDB: {},items: {}, \
             envDB: {},env: {},eventDB: {},eventSchedule: {}, \
             id: int,fights: {},corpses: {},blocklist, \
             mapArea: [],characterClassDB: {},spellsDB: {}, \
             sentimentDB: {},guildsDB: {},clouds: {}):
    otherPlayer = params.lower().strip()
    if len(otherPlayer) == 0:
        mud.send_message(id, 'With which player?\n\n')
        return
    if players[id]['affinity'].get(otherPlayer):
        affinity = players[id]['affinity'][otherPlayer]
        if affinity >= 0:
            mud.send_message(
                id,
                'Your affinity with <f32><u>' +
                otherPlayer +
                '<r> is <f15><b2>+' +
                str(affinity) +
                '<r>\n\n')
        else:
            mud.send_message(
                id,
                'Your affinity with <f32><u>' +
                otherPlayer +
                '<r> is <f15><b88>' +
                str(affinity) +
                '<r>\n\n')
        return
    mud.send_message(id, "You don't have any affinity with them.\n\n")


def clearSpells(params,mud,playersDB: {},players: {},rooms: {}, \
                npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                envDB: {},env: {},eventDB: {},eventSchedule, \
                id: int,fights: {},corpses: {},blocklist, \
                mapArea: [],characterClassDB: {},spellsDB: {}, \
                sentimentDB: {},guildsDB: {},clouds: {}):
    if len(players[id]['preparedSpells']) > 0:
        players[id]['preparedSpells'].clear()
        players[id]['spellSlots'].clear()
        mud.send_message(id, 'Your prepared spells list has been cleared.\n\n')
        return

    mud.send_message(id, "Your don't have any spells prepared.\n\n")


def spells(params,mud,playersDB: {},players: {},rooms: {}, \
           npcsDB: {},npcs: {},itemsDB: {},items: {}, \
           envDB: {},env: {},eventDB: {},eventSchedule, \
           id: int,fights: {},corpses: {},blocklist, \
           mapArea: [],characterClassDB: {},spellsDB: {}, \
           sentimentDB: {},guildsDB: {},clouds: {}):
    if len(players[id]['preparedSpells']) > 0:
        mud.send_message(id, 'Your prepared spells:\n')
        for name, details in players[id]['preparedSpells'].items():
            mud.send_message(id, '  <b234>' + name + '<r>')
        mud.send_message(id, '\n')
    else:
        mud.send_message(id, 'You have no spells prepared.\n\n')


def prepareSpellAtLevel(params,mud,playersDB: {},players: {},rooms: {}, \
                        npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                        envDB: {},env: {},eventDB: {},eventSchedule, \
                        id: int,fights: {},corpses: {},blocklist, \
                        mapArea: [],characterClassDB: {},spellsDB: {}, \
                        spellName: {},level: {}):
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
                            mud.send_message(
                                id,
                                'You need <b234>' +
                                itemsDB[required]['article'] +
                                ' ' +
                                itemsDB[required]['name'] +
                                '<r>\n\n')
                            return True
                players[id]['prepareSpell'] = spellName
                players[id]['prepareSpellProgress'] = 0
                players[id]['prepareSpellTime'] = TimeStringToSec(
                    details['prepareTime'])
                if len(details['prepareTime']) > 0:
                    mud.send_message(
                        id,
                        'You begin preparing the spell <b234>' +
                        spellName +
                        '<r>. It will take ' +
                        details['prepareTime'] +
                        '.\n\n')
                else:
                    mud.send_message(
                        id,
                        'You begin preparing the spell <b234>' +
                        spellName +
                        '<r>.\n\n')
                return True
    return False


def playerMaxCantrips(players: {}, id) -> int:
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


def getPlayerMaxSpellLevel(players: {}, id) -> int:
    """Returns the maximum spell level of the player
    """
    for prof in players[id]['proficiencies']:
        if isinstance(prof, list):
            spellList = list(prof)
            if len(spellList) > 0:
                if spellList[0].lower() == 'spell':
                    return len(spellList) - 1
    return -1


def getPlayerSpellSlotsAtSpellLevel(players: {}, id, spellLevel) -> int:
    """Returns the maximum spell slots at the given spell level
    """
    for prof in players[id]['proficiencies']:
        if isinstance(prof, list):
            spellList = list(prof)
            if len(spellList) > 0:
                if spellList[0].lower() == 'spell':
                    return spellList[spellLevel]
    return 0


def getPlayerUsedSlotsAtSpellLevel(players: {}, id, spellLevel, spellsDB):
    """Returns the used spell slots at the given spell level
    """
    if not spellsDB.get(str(spellLevel)):
        return 0

    usedCounter = 0
    for spellName, details in spellsDB[str(spellLevel)].items():
        if spellName in players[id]['preparedSpells']:
            usedCounter += 1
    return usedCounter


def playerPreparedCantrips(players, id, spellsDB: {}) -> int:
    """Returns the number of cantrips which the player has prepared
    """
    preparedCounter = 0
    for spellName in players[id]['preparedSpells']:
        for cantripName, details in spellsDB['cantrip'].items():
            if cantripName == spellName:
                preparedCounter += 1
                break
    return preparedCounter


def prepareSpell(params,mud,playersDB: {},players: {},rooms: {}, \
                 npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                 envDB: {},env: {},eventDB: {},eventSchedule, \
                 id: int,fights: {},corpses: {},blocklist, \
                 mapArea: [],characterClassDB: {},spellsDB: {}, \
                 sentimentDB: {},guildsDB: {},clouds: {}):
    spellName = params.lower().strip()

    # "learn spells" or "prepare spells" shows list of spells
    if spellName == 'spell' or spellName == 'spells':
        spellName = ''

    maxCantrips = playerMaxCantrips(players, id)
    maxSpellLevel = getPlayerMaxSpellLevel(players, id)

    if maxSpellLevel < 0 and maxCantrips == 0:
        mud.send_message(id, "You can't prepare spells.\n\n")
        return

    if len(spellName) == 0:
        # list spells which can be prepared
        mud.send_message(id, 'Spells you can prepare are:\n')

        if maxCantrips > 0 and spellsDB.get('cantrip'):
            for name, details in spellsDB['cantrip'].items():
                if name.lower() not in players[id]['preparedSpells']:
                    spellClasses = spellsDB['cantrip'][name]['classes']
                    if players[id]['characterClass'] in spellClasses or \
                       len(spellClasses) == 0:
                        mud.send_message(id, '  <f220>-' + name + '<r>')

        if maxSpellLevel > 0:
            for level in range(1, maxSpellLevel + 1):
                if not spellsDB.get(str(level)):
                    continue
                for name, details in spellsDB[str(level)].items():
                    if name.lower() not in players[id]['preparedSpells']:
                        spellClasses = spellsDB[str(level)][name]['classes']
                        if players[id]['characterClass'] in spellClasses or \
                           len(spellClasses) == 0:
                            mud.send_message(id, '  <b234>' + name + '<r>')
        mud.send_message(id, '\n')
    else:
        if spellName.startswith('the spell '):
            spellName = spellName.replace('the spell ', '')
        if spellName.startswith('spell '):
            spellName = spellName.replace('spell ', '')
        if spellName == players[id]['prepareSpell']:
            mud.send_message(id, 'You are already preparing that.\n\n')
            return

        if maxCantrips > 0 and spellsDB.get('cantrip'):
            if playerPreparedCantrips(players, id, spellsDB) < maxCantrips:
                if prepareSpellAtLevel(params,mud,playersDB,players, \
                                       rooms,npcsDB,npcs,itemsDB, \
                                       items,envDB,env,eventDB, \
                                       eventSchedule,id,fights, \
                                       corpses,blocklist,mapArea, \
                                       characterClassDB,spellsDB, \
                                       spellName,'cantrip'):
                    return
            else:
                mud.send_message(
                    id, "You can't prepare any more cantrips.\n\n")
                return

        if maxSpellLevel > 0:
            for level in range(1, maxSpellLevel + 1):
                if not spellsDB.get(str(level)):
                    continue
                maxSlots = getPlayerSpellSlotsAtSpellLevel(players, id, level)
                usedSlots = getPlayerUsedSlotsAtSpellLevel(
                    players, id, level, spellsDB)
                if usedSlots < maxSlots:
                    if prepareSpellAtLevel(params,mud,playersDB, \
                                           players,rooms,npcsDB,npcs, \
                                           itemsDB,items,envDB,env, \
                                           eventDB,eventSchedule,id, \
                                           fights,corpses,blocklist, \
                                           mapArea,characterClassDB, \
                                           spellsDB,spellName,str(level)):
                        return
                else:
                    mud.send_message(
                        id,
                        "You have prepared the maximum level" +
                        str(level) +
                        " spells.\n\n")
                    return

        mud.send_message(id, "That's not a spell.\n\n")


def speak(params,mud,playersDB: {},players: {},rooms: {}, \
          npcsDB: {},npcs: {},itemsDB: {},items: {},envDB: {}, \
          env: {},eventDB: {},eventSchedule: {},id: int, \
          fights: {},corpses: {},blocklist, \
          mapArea: [],characterClassDB: {},spellsDB: {}, \
          sentimentDB: {},guildsDB: {},clouds: {}):
    lang = params.lower().strip()
    if lang not in players[id]['language']:
        mud.send_message(id, "You don't know how to speak that language\n\n")
        return
    players[id]['speakLanguage'] = lang
    mud.send_message(id, "You switch to speaking in " + lang + "\n\n")


def say(params,mud,playersDB: {},players: {},rooms: {}, \
        npcsDB: {},npcs: {},itemsDB: {},items: {},envDB, \
        env: {},eventDB: {},eventSchedule, \
        id: int,fights: {},corpses: {},blocklist, \
        mapArea: [],characterClassDB: {},spellsDB: {}, \
        sentimentDB: {},guildsDB: {},clouds: {}):
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
                if not playerIsVisible(pid,id,players):
                    continue
                if selfOnly == False or pid == id:
                    if players[id]['speakLanguage'] in players[pid]['language']:
                        sentimentScore= \
                            getSentiment(params, sentimentDB) + \
                            getGuildSentiment(players, id, players, pid, guildsDB)
                        
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
                        mud.send_message_wrap(
                            pid, '<f230>', \
                            '<f220>{}<r> says: <f159>{}'.format(players[id]['name'], params) + "\n\n")
                    else:
                        if players[id]['speakLanguage'] != 'cant':
                            mud.send_message_wrap(
                                pid, '<f230>', \
                                '<f220>{}<r> says something in <f159>{}<r>'.format(players[id]['name'], players[id]['speakLanguage']) + "\n\n")
                        else:
                            mud.send_message_wrap(
                                pid, '<f230>', \
                                '<f220>{}<r> says: <f159>{}'.format(players[id]['name'], cantStr) + "\n\n")
    else:
        mud.send_message_wrap(
            id, '<f230>', \
            'To your horror, you realise you somehow cannot force yourself to utter a single word!\n')

def holdingLightSource(players: {},id,items: {},itemsDB: {}) -> bool:
    """Is the given player holding a light source?
    """
    itemID=int(players[id]['clo_lhand'])
    if itemID>0:
        if itemsDB[itemID]['lightSource']!=0:
            return True
    itemID=int(players[id]['clo_rhand'])
    if itemID>0:
        if itemsDB[int(itemID)]['lightSource']!=0:
            return True

    # are there any other players in the same room holding a light source?
    for p in players:
        if p == id:
            continue
        if players[p]['room'] != players[id]['room']:
            continue
        itemID=int(players[p]['clo_lhand'])
        if itemID>0:
            if itemsDB[itemID]['lightSource']!=0:
                return True
        itemID=int(players[p]['clo_rhand'])
        if itemID>0:
            if itemsDB[int(itemID)]['lightSource']!=0:
                return True        

    # is there a light source in the room?
    return lightSourceInRoom(players,id,items,itemsDB)

def conditionalRoom(condType: str,cond: str,description: str,id, \
                    players: {},items: {}, \
                    itemsDB: {},clouds: {},mapArea: [], \
                    rooms: {}) -> bool:
    if condType == 'sunrise' or \
       condType == 'dawn':
        currTime=datetime.datetime.today()
        currHour=currTime.hour
        sun=Sun(52.414, 4.081)
        sunRiseTime=sun.get_local_sunrise_time(currTime).hour
        if 'true' in cond.lower() or \
           'y' in cond.lower():
            if currHour>=sunRiseTime-1 and currHour<=sunRiseTime:
                return True
        else:
            if currHour<sunRiseTime-1 or currHour>sunRiseTime:
                return True

    if condType == 'sunset' or \
       condType == 'dusk':
        currTime=datetime.datetime.today()
        currHour=currTime.hour
        sun=Sun(52.414, 4.081)
        sunSetTime=sun.get_local_sunset_time(currTime).hour
        if 'true' in cond.lower() or \
           'y' in cond.lower():
            if currHour>=sunSetTime and currHour<=sunSetTime+1:
                return True
        else:
            if currHour<sunSetTime or currHour>sunSetTime+1:
                return True

    if condType.startswith('rain'):
        rm=players[id]['room']
        coords=rooms[rm]['coords']
        if 'true' in cond.lower() or \
           'y' in cond.lower():
            if getRainAtCoords(coords,mapArea,clouds):
                return True
        else:
            if not getRainAtCoords(coords,mapArea,clouds):
                return True

    if condType == 'hour':
        currHour = datetime.datetime.today().hour
        condHour = \
            cond.replace('>','').replace('<','').replace('=','').strip()
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
        if dayNumber == int(datetime.datetime.today().strftime("%d")):
            monthNumber = int(cond.split('/')[1])
            if monthNumber == int(datetime.datetime.today().strftime("%m")):
                return True

    if condType == 'month':
        if '|' in cond:
            months = cond.split('|')
            for m in months:
                if int(m) == int(datetime.datetime.today().strftime("%m")):
                    return True
        else:
            currMonthNumber=int(datetime.datetime.today().strftime("%m"))                
            monthNumber = int(cond)
            if monthNumber == currMonthNumber:
                return True

    if condType == 'season':
        currMonthNumber=int(datetime.datetime.today().strftime("%m"))
        if cond=='spring':
            if currMonthNumber > 1 and currMonthNumber <= 4:
                return True
        elif cond=='summer':
            if currMonthNumber > 4 and currMonthNumber <= 9:
                return True
        elif cond=='autumn':
            if currMonthNumber > 9 and currMonthNumber <= 10:
                return True
        elif cond=='winter':
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
            if cond.lower()=='lightsource':
                return holdingLightSource(players,id,items,itemsDB)
        elif players[id]['clo_lhand'] == int(cond) or \
           players[id]['clo_rhand'] == int(cond):
            return True

    if condType.startswith('wear'):
        for c in wearLocation:
            if players[id]['clo_'+c] == int(cond):
                return True

    return False


def conditionalRoomDescription(description: str,tideOutDescription: str, \
                               conditional: [],id,players: {},items: {}, \
                               itemsDB: {},clouds: {},mapArea: [],rooms: {}):
    """Returns a description which can vary depending on conditions
    """
    roomDescription = description
    if len(tideOutDescription) > 0:
        if runTide() < 0:
            roomDescription = rm['tideOutDescription']

    # Alternative descriptions triggered by conditions
    for possibleDescription in conditional:
        if len(possibleDescription) >= 3:
            condType = possibleDescription[0]
            cond = possibleDescription[1]
            alternativeDescription = possibleDescription[2]
            if conditionalRoom(condType,cond, \
                               alternativeDescription, \
                               id,players,items,itemsDB, \
                               clouds,mapArea,rooms):
                roomDescription = alternativeDescription
                break

    return roomDescription

def conditionalRoomImage(conditional: [],id,players: {},items: {}, \
                         itemsDB: {},clouds: {},mapArea: [],rooms: {}) -> str:
    """If there is an image associated with a conditional
    room description then return its name
    """
    for possibleDescription in conditional:
        if len(possibleDescription) >= 4:
            condType = possibleDescription[0]
            cond = possibleDescription[1]
            alternativeDescription = possibleDescription[2]
            if conditionalRoom(condType,cond, \
                               alternativeDescription, \
                               id,players,items,itemsDB,clouds, \
                               mapArea,rooms):
                roomImageFilename='images/rooms/'+possibleDescription[3]
                if os.path.isfile(roomImageFilename):
                    return possibleDescription[3]
                break
    return None

def playersInRoom(targetRoom,players,npcs):
    """Returns the number of players in the given room.
       This includes NPCs.
    """
    playersCtr=0
    for (pid, pl) in list(players.items()):
        # if they're in the same room as the player
        if players[pid]['room'] == targetRoom:
            playersCtr += 1

    for (nid, pl) in list(npcs.items()):
        if npcs[nid]['room'] == targetRoom:
            playersCtr += 1

    return playersCtr


def playerIsVisible(observerId,otherPlayerId,players: {}) -> bool:
    """Is the other player visible to the observer?
    """
    if not players[otherPlayerId].get('visibleWhenWearing'):
        return True
    if isWearing(observerId,players, \
                 players[otherPlayerId]['visibleWhenWearing']):
        return True
    return False


def roomRequiresLightSource(players: {},id,rooms: {}) -> bool:
    """Returns true if the room requires a light source
    """
    rid=players[id]['room']
    if not rooms[rid]['conditional']:
        return False
    for cond in rooms[rid]['conditional']:
        if len(cond)>2:
            if cond[0].lower()=='hold' and \
               cond[1].lower()=='lightsource':
                return True
    return False

def lightSourceInRoom(players: {},id,items: {},itemsDB: {}) -> bool:
    """Returns true if there is a light source in the room
    """
    rid=players[id]['room']
    for i in items:                
        if items[i]['room'].lower() != players[id]['room']:
            continue
        if itemsDB[items[i]['id']]['lightSource'] != 0:
            return True    
    return False

def itemIsVisible(observerId,players: {},itemId,itemsDB: {}) -> bool:
    """Is the item visible to the observer?
    """
    if not itemsDB[itemId].get('visibleWhenWearing'):
        return True
    if isWearing(observerId,players, \
                 itemsDB[itemId]['visibleWhenWearing']):
        return True
    return False

def moonIllumination(currTime) -> int:
    """Returns additional illumination due to moonlight
    """
    diff = currTime - datetime.datetime(2001, 1, 1)
    days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
    lunations = dec("0.20439731") + (days * dec("0.03386319269"))
    index=int(lunations % dec(1)) & 7
    return int((5-abs(4-index))*2)   

def roomIllumination(roomImage,outdoors: bool):
    """Alters the brightness and contrast of the image to simulate
    evening and night conditions
    """
    if not outdoors:
        return roomImage
    currTime = datetime.datetime.today()
    currHour=currTime.hour
    sun = Sun(52.414, 4.081)
    sunRiseTime = sun.get_local_sunrise_time(currTime).hour
    sunSetTime = sun.get_local_sunset_time(currTime).hour
    if currHour>sunRiseTime+1 and currHour<sunSetTime-1:
        return roomImage
    brightness=60
    colorVariance=80
    if currHour<sunRiseTime or currHour>sunSetTime:
        brightness=30
    # extra dark
    if currHour<(sunRiseTime-2) or currHour>(sunSetTime+2):
        colorVariance=50

    brightness+=moonIllumination(currTime)
    pixels=roomImage.split('[')

    averageIntensity=0
    averageIntensityCtr=0
    for p in pixels:
        values=p.split(';')
        if len(values)!=5:
            continue
        values[4]=values[4].split('m')[0]
        ctr=0
        for v in values:
            if ctr>1:
                averageIntensity+=int(v)
                averageIntensityCtr+=1
            ctr+=1
    averageIntensity/=averageIntensityCtr
    newAverageIntensity=int(averageIntensity*brightness/100)
    # minimum average illumination
    if newAverageIntensity<20:
        newAverageIntensity=20

    newRoomImage=''
    trailing=None
    firstValue=True
    for p in pixels:
        if firstValue:
            newRoomImage+=p+'['
            firstValue=False
            continue
        values=p.split(';')
        if len(values)!=5:
            newRoomImage+=p+'['
            continue
        trailing=values[4].split('m')[1]
        values[4]=values[4].split('m')[0]
        ctr=0
        for v in values:
            if ctr>1:
                # difference from average illumination
                diff=int(int(v)-averageIntensity)
                # reduce color variance
                variance=colorVariance
                # reduce blue by more than other channels
                if ctr==2:
                    variance=int(colorVariance/4)
                v=int(newAverageIntensity+(diff*variance/100))
                if v<0:
                    v=0
                elif v>255:
                    v=255
            values[ctr]=int(v)
            ctr+=1
        darkStr=trailing+'['
        darkStr=''
        ctr=0
        for v in values:
            if ctr<4:
                darkStr+=str(v)+';'
            else:
                darkStr+=str(v)+'m'
            ctr+=1
        newRoomImage+=darkStr+trailing+'['
    return newRoomImage[:len(newRoomImage)-1]

def showRoomImage(mud,id,roomId,rooms: {},players: {},items: {},itemsDB: {}, \
                  clouds: {},mapArea: []) -> None:
    """Shows an image for the room if it exists
    """
    if players[id].get('graphics'):
        if players[id]['graphics']=='off':
            return
    conditionalImage= \
        conditionalRoomImage(rooms[roomId]['conditional'], \
                             id,players,items,itemsDB,clouds, \
                             mapArea,rooms)
    outdoors=False
    if rooms[roomId]['weather']==1:
        outdoors=True
    if not conditionalImage:
        roomIdStr=str(roomId).replace('rid=','').replace('$','')
    else:
        roomIdStr=conditionalImage
    roomImageFilename='images/rooms/'+roomIdStr
    if os.path.isfile(roomImageFilename+'_night'):
        currTime = datetime.datetime.today()
        sun = Sun(52.414, 4.081)
        sunRiseTime = sun.get_local_sunrise_time(currTime).hour
        sunSetTime = sun.get_local_sunset_time(currTime).hour
        if currTime.hour<sunRiseTime or currTime.hour>sunSetTime:
            roomImageFilename=roomImageFilename+'_night'
            outdoors=False
    if not os.path.isfile(roomImageFilename):
        return
    with open(roomImageFilename, 'r') as roomFile:
        mud.send_image(id,'\n'+roomIllumination(roomFile.read(),outdoors))

def showSpellImage(mud,id,spellId,players: {}) -> None:
    """Shows an image for a spell
    """
    if players[id].get('graphics'):
        if players[id]['graphics']=='off':
            return
    spellImageFilename='images/spells/'+spellId
    if not os.path.isfile(spellImageFilename):
        return
    with open(spellImageFilename, 'r') as spellFile:
        mud.send_image(id,'\n'+spellFile.read())

def showItemImage(mud,id,itemId,players: {}) -> None:
    """Shows an image for the item if it exists
    """
    if players[id].get('graphics'):
        if players[id]['graphics']=='off':
            return
    itemImageFilename='images/items/'+str(itemId)
    if not os.path.isfile(itemImageFilename):
        return
    with open(itemImageFilename, 'r') as itemFile:
        mud.send_image(id,'\n'+itemFile.read())

def showNPCImage(mud,id,npcName,players: {}) -> None:
    """Shows an image for a NPC
    """
    if players[id].get('graphics'):
        if players[id]['graphics']=='off':
            return
    npcImageFilename='images/npcs/'+npcName.replace(' ','_')
    if not os.path.isfile(npcImageFilename):
        return
    with open(npcImageFilename, 'r') as npcFile:
        mud.send_image(id,'\n'+npcFile.read())

def getRoomExits(rooms: {},players: {},id) -> []:
    """Returns a list of exits for the given player
    """
    rm = rooms[players[id]['room']]
    exits = rm['exits']

    if rm.get('tideOutExits'):
        if runTide() < 0:
            if rm['tideOutExits'] not in exits:
                exits += rm['tideOutExits']

    if rm.get('exitsWhenWearing'):
        for ex in rm['exitsWhenWearing']:
            if len(ex)<3:
                continue
            itemID=ex[1]
            if isWearing(id,players,[itemID]):
                direction=ex[0]
                roomID=ex[2]
                exits[direction]=roomID
    return exits

def look(params,mud,playersDB: {},players: {},rooms: {}, \
         npcsDB: {},npcs: {},itemsDB: {},items: {}, \
         envDB: {},env: {},eventDB: {},eventSchedule, \
         id: int,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB: {}, \
         sentimentDB: {},guildsDB: {},clouds: {}):
    if players[id]['canLook'] == 1:
        if len(params) < 1:
            # If no arguments are given, then look around and describe
            # surroundings

            # store the player's current room
            rm = rooms[players[id]['room']]

            # send the player back the description of their current room
            playerRoomId=players[id]['room']
            showRoomImage(mud,id,playerRoomId,rooms,players,items, \
                          itemsDB,clouds,mapArea)
            roomDescription = rm['description']
            if len(rm['conditional']) > 0:
                roomDescription = \
                    conditionalRoomDescription(roomDescription, \
                                               rm['tideOutDescription'], \
                                               rm['conditional'], \
                                               id, players,items,itemsDB, \
                                               clouds,mapArea,rooms)

            if rm['trap'].get('trapActivation') and rm['trap'].get('trapPerception'):
                if randint(1,players[id]['per'])>rm['trap']['trapPerception']:
                    if rm['trap']['trapType'].startswith('dart') and randint(0,1)==1:
                        roomDescription += \
                            randomDescription(" You notice some tiny holes in the wall.| There are some small holes in the wall.|You observe some tiny holes in the wall.")
                    else:
                        if rm['trap']['trapActivation']=='tripwire':
                            roomDescription += \
                                randomDescription(" A tripwire is carefully set along the floor.| You notice a thin wire across the floor.| An almost invisible wire runs along the floor.")
                        if rm['trap']['trapActivation'].startswith('pressure'):
                            roomDescription += \
                                randomDescription(" The faint outline of a pressure plate can be seen on the floor.| The outline of a pressure plate is visible on the floor.")

            mud.send_message_wrap(id, '<f230>', "<f230>" + roomDescription.strip())
            playershere = []

            itemshere = []

            # go through every player in the game
            for (pid, pl) in list(players.items()):
                # if they're in the same room as the player
                if players[pid]['room'] == players[id]['room']:
                    # ... and they have a name to be shown
                    if players[pid]['name'] is not None and \
                       players[pid]['name'] is not players[id]['name']:
                        if playerIsVisible(id,pid,players):
                            # add their name to the list
                            if players[pid]['prefix'] == "None":
                                playershere.append(players[pid]['name'])
                            else:
                                playershere.append(
                                    "[" + players[pid]['prefix'] + "] " + \
                                    players[pid]['name'])

            # Show corpses in the room
            for (corpse, pl) in list(corpses.items()):
                if corpses[corpse]['room'] == players[id]['room']:
                    playershere.append(corpses[corpse]['name'])

            ##### Show NPCs in the room #####
            for (nid, pl) in list(npcs.items()):
                if npcs[nid]['room'] == players[id]['room']:
                    # Don't show hidden familiars
                    if npcs[nid]['familiarMode'] != 'hide' or \
                       (len(npcs[nid]['familiarOf'])>0 and \
                        npcs[nid]['familiarOf']==players[id]['name']):
                        if playerIsVisible(id,nid,npcs):
                            playershere.append(npcs[nid]['name'])

            # Show items in the room
            for (item, pl) in list(items.items()):
                if items[item]['room'] == players[id]['room']:
                    if itemIsVisible(id,players,items[item]['id'],itemsDB):
                        itemshere.append(
                            itemsDB[items[item]['id']]['article'] + ' ' + \
                            itemsDB[items[item]['id']]['name'])

            # send player a message containing the list of players in the room
            if len(playershere) > 0:
                mud.send_message(
                    id, '<f230>You see: <f220>{}'.format(
                        ', '.join(playershere)))

            # send player a message containing the list of exits from this room
            roomExitsStr=getRoomExits(rooms,players,id)
            if roomExitsStr:
                mud.send_message(
                    id, '<f230>Exits are: <f220>{}'.format(', '.join(roomExitsStr)))

            # send player a message containing the list of items in the room
            if len(itemshere) > 0:
                needsLight=roomRequiresLightSource(players,id,rooms)
                playersWithLight=False
                if needsLight:
                    playersWithLight= \
                        holdingLightSource(players,id,items,itemsDB)
                if needsLight==False or (needsLight==True and playersWithLight==True):
                    mud.send_message_wrap(id,'<f220>', \
                                          '<f230>You notice: <f220>{}'.format(', '.join(itemshere)))

            mud.send_message(id, "\n")
        else:
            # If argument is given, then evaluate it
            param = params.lower()

            if param.startswith('my '):
                param = params.replace('my ', '',1)
                
            # replace "familiar" with the name of the familiar
            if param.startswith('familiar'):
                familiarName=getFamiliarName(players,id,npcs)
                if len(familiarName)>0:
                    param = param.replace('familiar',familiarName,1)
            
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
                    if players[p]['name'].lower(
                    ) == param and players[p]['room'] == players[id]['room']:
                        if playerIsVisible(id,p,players):
                            bioOfPlayer(mud, id, p, players, itemsDB)
                            messageSent = True

            message = ""

            # Go through all NPCs in game
            for n in npcs:
                if param in npcs[n]['name'].lower() \
                   and npcs[n]['room'] == players[id]['room']:
                    if playerIsVisible(id,n,npcs):
                        if npcs[n]['familiarMode']!='hide':
                            showNPCImage(mud,id,npcs[n]['name'].lower(),players)
                            bioOfPlayer(mud, id, n, npcs, itemsDB)
                            messageSent = True
                        else:
                            if npcs[n]['familiarOf']==players[id]['name']:
                                message="They are hiding somewhere here."
                                messageSent = True

            if len(message) > 0:
                mud.send_message(id, message + "\n\n")
                messageSent = True

            message = ""

            # Go through all Items in game
            itemCounter = 0
            for i in items:                
                if items[i]['room'].lower() == players[id]['room'] and \
                   param in itemsDB[items[i]['id']]['name'].lower():
                    if itemIsVisible(id,players,items[i]['id'],itemsDB):
                        if itemCounter == 0:
                            itemLanguage = itemsDB[items[i]['id']]['language']
                            if len(itemLanguage) == 0:
                                showItemImage(mud,id,int(items[i]['id']),players)
                                message += randomDescription(itemsDB[items[i]['id']]['long_description'])
                                message += describeContainerContents(
                                    mud, id, itemsDB, items[i]['id'], True)
                            else:
                                if itemLanguage in players[id]['language']:
                                    showItemImage(mud,id,int(items[i]['id']),players)
                                    message += randomDescription(itemsDB[items[i]['id']]['long_description'])
                                    message += describeContainerContents(
                                        mud, id, itemsDB, items[i]['id'], True)
                                else:
                                    message += "It's written in " + itemLanguage
                            itemName = itemsDB[items[i]['id']]['article'] + \
                                " " + itemsDB[items[i]['id']]['name']
                        itemCounter += 1

            # Examine items in inventory
            if len(message) == 0:
                playerinv = list(players[id]['inv'])
                if len(playerinv) > 0:
                    # check for exact match of item name
                    invItemFound = False
                    for i in playerinv:
                        if param == itemsDB[int(i)]['name'].lower():
                            itemLanguage = itemsDB[int(i)]['language']
                            showItemImage(mud,id,int(i),players)
                            if len(itemLanguage) == 0:
                                message += randomDescription(itemsDB[int(i)]['long_description'])
                                message += describeContainerContents(
                                    mud, id, itemsDB, int(i), True)
                            else:
                                if itemLanguage in players[id]['language']:
                                    message += randomDescription(itemsDB[int(i)]['long_description'])
                                    message += describeContainerContents(
                                        mud, id, itemsDB, int(i), True)
                                else:
                                    message += "It's written in " + itemLanguage
                            itemName = itemsDB[int(
                                i)]['article'] + " " + itemsDB[int(i)]['name']
                            invItemFound = True
                            break
                    if not invItemFound:
                        # check for partial match of item name
                        for i in playerinv:
                            if param in itemsDB[int(i)]['name'].lower():
                                itemLanguage = itemsDB[int(i)]['language']
                                showItemImage(mud,id,int(i),players)
                                if len(itemLanguage) == 0:
                                    message += randomDescription(itemsDB[int(i)]['long_description'])
                                    message += describeContainerContents(
                                        mud, id, itemsDB, int(i), True)
                                else:
                                    if itemLanguage in players[id]['language']:
                                        message += randomDescription(itemsDB[int(i)]['long_description'])
                                        message += describeContainerContents(
                                            mud, id, itemsDB, int(i), True)
                                    else:
                                        message += "It's written in " + itemLanguage

                                itemName = itemsDB[int(
                                    i)]['article'] + " " + itemsDB[int(i)]['name']
                                break

            if len(message) > 0:
                mud.send_message(id, "It's " + itemName + ".")
                mud.send_message_wrap(id, '', message + "\n\n")
                messageSent = True
                if itemCounter > 1:
                    mud.send_message(
                        id,
                        "You can see " +
                        str(itemCounter) +
                        " of those in the vicinity.\n\n")

            # If no message has been sent, it means no player/npc/item was
            # found
            if not messageSent:
                mud.send_message(id, "Look at what?\n")
    else:
        mud.send_message(
            id,
            'You somehow cannot muster enough perceptive powers to perceive and describe your immediate surroundings...\n')

def escapeTrap(params,mud,playersDB: {},players: {},rooms: {}, \
               npcsDB: {},npcs: {},itemsDB: {},items: {}, \
               envDB: {},env: {},eventDB: {},eventSchedule, \
               id: int,fights: {},corpses: {},blocklist, \
               mapArea: [],characterClassDB: {},spellsDB: {}, \
               sentimentDB: {},guildsDB: {},clouds: {}):
    if not playerIsTrapped(id,players,rooms):
        mud.send_message(
            id, randomDescription(
                "You try to escape but find there's nothing to escape from") + '\n\n')
        
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if players[id]['canAttack'] == 1:
        escapeFromTrap(mud,id,players,rooms,itemsDB)                


def attack(params,mud,playersDB: {},players: {},rooms: {}, \
           npcsDB: {},npcs: {},itemsDB: {},items: {}, \
           envDB: {},env: {},eventDB: {},eventSchedule, \
           id: int,fights: {},corpses: {},blocklist, \
           mapArea: [],characterClassDB: {},spellsDB: {},
           sentimentDB: {},guildsDB: {},clouds: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, \
            randomDescription(players[id]['frozenDescription']) + '\n\n')
        return

    if players[id]['canAttack'] == 1:
        if playerIsTrapped(id,players,rooms):
            mud.send_message(
                id, randomDescription(
                    "You're trapped") + '.\n\n')
            return
        
        target = params  # .lower()
        if target.startswith('at '):
            target = params.replace('at ', '')
        if target.startswith('the '):
            target = params.replace('the ', '')

        if not isAttacking(players,id,fights):
            playerBeginsAttack(players,id,target,npcs,fights,mud)
        else:
            currentTarget = getAttackingTarget(players,id,fights)
            if not isinstance(currentTarget, int):
                mud.send_message(
                    id,
                    'You are already attacking ' +
                    currentTarget +
                    "\n")
            else:
                mud.send_message(
                    id,
                    'You are already attacking ' +
                    npcs[currentTarget]['name'] +
                    "\n")

        # List fights for debugging purposes
        # for x in fights:
            # print (x)
            # for y in fights[x]:
                # print (y,':',fights[x][y])
    else:
        mud.send_message(
            id,
            'Right now, you do not feel like you can force yourself to attack anyone or anything.\n')


def itemInInventory(players: {}, id, itemName, itemsDB: {}):
    if len(list(players[id]['inv'])) > 0:
        itemNameLower = itemName.lower()
        for i in list(players[id]['inv']):
            if itemsDB[int(i)]['name'].lower() == itemNameLower:
                return True
    return False


def describe(params,mud,playersDB: {},players: {},rooms: {}, \
             npcsDB: {},npcs: {},itemsDB: {},items: {}, \
             envDB: {},env: {},eventDB: {},eventSchedule, \
             id: int,fights: {},corpses: {},blocklist, \
             mapArea: [],characterClassDB: {},spellsDB: {}, \
             sentimentDB: {},guildsDB: {},clouds: {}):
    if not isWitch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return

    if '"' not in params:
        mud.send_message(
            id, 'Descriptions need to be within double quotes.\n\n')
        return

    descriptionStrings = re.findall('"([^"]*)"', params)
    if len(descriptionStrings) == 0:
        mud.send_message(
            id, 'Descriptions need to be within double quotes.\n\n')
        return

    if len(descriptionStrings[0].strip()) < 3:
        mud.send_message(id, 'Description is too short.\n\n')
        return

    rm = players[id]['room']
    if len(descriptionStrings) == 1:
        rooms[rm]['description'] = descriptionStrings[0]
        mud.send_message(id, 'Room description set.\n\n')
        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env,guildsDB)
        return

    if len(descriptionStrings) == 2:
        thingDescribed = descriptionStrings[0].lower()
        thingDescription = descriptionStrings[1]

        if len(thingDescription) < 3:
            mud.send_message(
                id,
                'Description of ' +
                descriptionStrings[0] +
                ' is too short.\n\n')
            return

        if thingDescribed == 'name':
            rooms[rm]['name'] = thingDescription
            mud.send_message(
                id,
                'Room name changed to ' +
                thingDescription +
                '.\n\n')
            saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env,guildsDB)
            return

        if thingDescribed == 'tide':
            rooms[rm]['tideOutDescription'] = thingDescription
            mud.send_message(id, 'Tide out description set.\n\n')
            saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env,guildsDB)
            return

        # change the description of an item in the room
        for (item, pl) in list(items.items()):
            if items[item]['room'] == players[id]['room']:
                if thingDescribed in itemsDB[items[item]
                                             ['id']]['name'].lower():
                    itemsDB[items[item]['id']]['long_description'] = thingDescription
                    mud.send_message(id, 'New description set for ' +
                                     itemsDB[items[item]['id']]['article'] +
                                     ' ' +
                                     itemsDB[items[item]['id']]['name'] +
                                     '.\n\n')
                    saveUniverse(
                        rooms,npcsDB,npcs,itemsDB,items,envDB,env,guildsDB)
                    return

        # Change the description of an NPC in the room
        for (nid, pl) in list(npcs.items()):
            if npcs[nid]['room'] == players[id]['room']:
                if thingDescribed in npcs[nid]['name'].lower():
                    npcs[nid]['lookDescription'] = thingDescription
                    mud.send_message(
                        id,
                        'New description set for ' +
                        npcs[nid]['name'] +
                        '.\n\n')
                    saveUniverse(
                        rooms,npcsDB,npcs,itemsDB,items,envDB,env,guildsDB)
                    return

    if len(descriptionStrings) == 3:
        if descriptionStrings[0].lower() != 'name':
            mud.send_message(id, "I don't understand.\n\n")
            return
        thingDescribed = descriptionStrings[1].lower()
        thingName = descriptionStrings[2]
        if len(thingName) < 3:
            mud.send_message(
                id,
                'Description of ' +
                descriptionStrings[1] +
                ' is too short.\n\n')
            return

        # change the name of an item in the room
        for (item, pl) in list(items.items()):
            if items[item]['room'] == players[id]['room']:
                if thingDescribed in itemsDB[items[item]
                                             ['id']]['name'].lower():
                    itemsDB[items[item]['id']]['name'] = thingName
                    mud.send_message(id, 'New description set for ' +
                                     itemsDB[items[item]['id']]['article'] +
                                     ' ' +
                                     itemsDB[items[item]['id']]['name'] +
                                     '.\n\n')
                    saveUniverse(
                        rooms,npcsDB,npcs,itemsDB,items,envDB,env,guildsDB)
                    return

        # Change the name of an NPC in the room
        for (nid, pl) in list(npcs.items()):
            if npcs[nid]['room'] == players[id]['room']:
                if thingDescribed in npcs[nid]['name'].lower():
                    npcs[nid]['name'] = thingName
                    mud.send_message(
                        id,
                        'New description set for ' +
                        npcs[nid]['name'] +
                        '.\n\n')
                    saveUniverse(
                        rooms,npcsDB,npcs,itemsDB,items,envDB,env,guildsDB)
                    return

def isWearing(id,players: {},itemList: []) -> bool:
    """Given a list of possible item IDs is the player wearing any of them?
    """
    if not itemList:
        return False

    for itemID in itemList:
        if not str(itemID).isdigit():
            print('isWearing: '+str(itemID)+' is not a digit')
            continue
        itemID=int(itemID)
        for locn in wearLocation:
            if int(players[id]['clo_'+locn]) == itemID:
                return True            
        if int(players[id]['clo_lhand']) == itemID or \
           int(players[id]['clo_rhand']) == itemID:
            return True
    return False
                
def checkInventory(params,mud,playersDB: {},players: {},rooms: {}, \
                   npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                   envDB: {},env: {},eventDB: {},eventSchedule, \
                   id: int,fights: {},corpses: {},blocklist, \
                   mapArea: [],characterClassDB: {},spellsDB: {}, \
                   sentimentDB: {},guildsDB: {},clouds: {}):
    mud.send_message(id, 'You check your inventory.')
    if len(list(players[id]['inv'])) == 0:
        mud.send_message(id, 'You haven`t got any items on you.\n\n')
        return

    mud.send_message(id, 'You are currently in possession of:\n')
    for i in list(players[id]['inv']):
        if int(players[id]['clo_lhand']) == int(i):
            mud.send_message(id, ' * ' +
                             itemsDB[int(i)]['article'] +
                             ' <b234>' +
                             itemsDB[int(i)]['name'] +
                             '<r> (left hand)')
            continue

        if int(players[id]['clo_lleg']) == int(i):
            mud.send_message(id, ' * ' +
                             itemsDB[int(i)]['article'] +
                             ' <b234>' +
                             itemsDB[int(i)]['name'] +
                             '<r> (left leg)')
            continue

        if int(players[id]['clo_rleg']) == int(i):
            mud.send_message(id, ' * ' +
                             itemsDB[int(i)]['article'] +
                             ' <b234>' +
                             itemsDB[int(i)]['name'] +
                             '<r> (right leg)')
            continue

        if int(players[id]['clo_rhand']) == int(i):
            mud.send_message(id, ' * ' +
                             itemsDB[int(i)]['article'] +
                             ' <b234>' +
                             itemsDB[int(i)]['name'] +
                             '<r> (right hand)')
            continue

        if int(players[id]['clo_lfinger']) == int(i):
            mud.send_message(id, ' * ' +
                             itemsDB[int(i)]['article'] +
                             ' <b234>' +
                             itemsDB[int(i)]['name'] +
                             '<r> (finger of left hand)')
            continue

        if int(players[id]['clo_rfinger']) == int(i):
            mud.send_message(id, ' * ' +
                             itemsDB[int(i)]['article'] +
                             ' <b234>' +
                             itemsDB[int(i)]['name'] +
                             '<r> (finger of right hand)')
            continue

        if int(players[id]['clo_head']) == int(i) or \
           int(players[id]['clo_lwrist']) == int(i) or \
           int(players[id]['clo_rwrist']) == int(i) or \
           int(players[id]['clo_larm']) == int(i) or \
           int(players[id]['clo_rarm']) == int(i) or \
           int(players[id]['clo_lfinger']) == int(i) or \
           int(players[id]['clo_rfinger']) == int(i) or \
           int(players[id]['clo_neck']) == int(i) or \
           int(players[id]['clo_chest']) == int(i) or \
           int(players[id]['clo_back']) == int(i) or \
           int(players[id]['clo_feet']) == int(i):
            mud.send_message(id, ' * ' +
                             itemsDB[int(i)]['article'] +
                             ' <b234>' +
                             itemsDB[int(i)]['name'] +
                             '<r> (worn)')
            continue

        mud.send_message(id, ' * ' +
                         itemsDB[int(i)]['article'] +
                         ' <b234>' +
                         itemsDB[int(i)]['name'])
    mud.send_message(id, '\n\n')

def changeSetting(params,mud,playersDB: {},players: {},rooms: {}, \
                  npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                  envDB: {},env: {},eventDB: {},eventSchedule, \
                  id: int,fights: {},corpses: {},blocklist, \
                  mapArea: [],characterClassDB: {},spellsDB: {}, \
                  sentimentDB: {},guildsDB: {},clouds: {}):
    newPassword = ''
    if params.startswith('password '):
        newPassword = params.replace('password ', '')
    if params.startswith('pass '):
        newPassword = params.replace('pass ', '')
    if len(newPassword) > 0:
        if len(newPassword) < 6:
            mud.send_message(id, "That password is too short.\n\n")
            return
        players[id]['pwd'] = hash_password(newPassword)
        log("Player " + players[id]['name'] +
            " changed their password", "info")
        saveState(players[id], playersDB, True)
        mud.send_message(id, "Your password has been changed.\n\n")


def writeOnItem(params,mud,playersDB: {},players: {},rooms: {}, \
                npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                envDB: {},env: {},eventDB: {},eventSchedule, \
                id: int,fights: {},corpses: {},blocklist, \
                mapArea: [],characterClassDB: {},spellsDB: {}, \
                sentimentDB: {},guildsDB: {},clouds: {}):
    if ' on ' not in params:
        if ' onto ' not in params:
            if ' in ' not in params:
                if ' using ' not in params:
                    if ' with ' not in params:
                        mud.send_message(id, 'What?\n\n')
                        return
    writeItemName = ''
    msg = ''
    if ' using ' not in params:
        msg = params.split(' using ')[0].remove('"')
        writeItemName = params.split(' using ')[1].lower()
    if ' with ' not in params:
        msg = params.split(' with ')[0].remove('"')
        writeItemName = params.split(' with ')[1].lower()

    if len(msg) == 0:
        return
    if len(msg) > 64:
        mud.send_message(id, 'That message is too long.\n\n')


def check(params,mud,playersDB: {},players: {},rooms: {}, \
          npcsDB: {},npcs: {},itemsDB: {},items: {}, \
          envDB: {},env: {},eventDB: {},eventSchedule, \
          id: str,fights: {},corpses: {},blocklist, \
          mapArea: [],characterClassDB: {},spellsDB: {}, \
          sentimentDB: {},guildsDB: {},clouds: {}):
    if params.lower() == 'inventory' or \
       params.lower() == 'inv':
        checkInventory(params,mud,playersDB,players, \
                       rooms,npcsDB,npcs,itemsDB,items, \
                       envDB,env,eventDB,eventSchedule, \
                       id,fights,corpses,blocklist, \
                       mapArea,characterClassDB,spellsDB, \
                       sentimentDB,guildsDB,clouds)
    elif params.lower() == 'stats':
        mud.send_message(id, 'You check your character sheet.\n')
    else:
        mud.send_message(id, 'Check what?\n')

def wear(params,mud,playersDB: {},players: {},rooms: {}, \
         npcsDB: {},npcs: {},itemsDB: {},items: {}, \
         envDB: {},env: {},eventDB: {},eventSchedule, \
         id: int,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB: {}, \
         sentimentDB: {},guildsDB: {},clouds: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if len(params) < 1:
        mud.send_message(id, 'Specify an item from your inventory.\n\n')
        return

    if len(list(players[id]['inv'])) == 0:
        mud.send_message(id, 'You are not carrying that.\n\n')
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
        mud.send_message(id, itemName + " is not in your inventory.\n\n")
        return

    for clothingType in wearLocation:
        if wearClothing(itemID,players,id,clothingType,mud,itemsDB):
            return

    mud.send_message(id, "You can't wear that\n\n")

def wield(params,mud,playersDB: {},players: {},rooms: {}, \
          npcsDB: {},npcs: {},itemsDB: {},items: {}, \
          envDB: {},env: {},eventDB: {},eventSchedule: {}, \
          id: int,fights: {},corpses: {},blocklist: {}, \
          mapArea: [],characterClassDB: {},spellsDB: {}, \
          sentimentDB: {},guildsDB: {},clouds: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if len(params) < 1:
        mud.send_message(id, 'Specify an item from your inventory.\n\n')
        return

    if len(list(players[id]['inv'])) == 0:
        mud.send_message(id, 'You are not carrying that.\n\n')
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
        mud.send_message(id, itemName + " is not in your inventory.\n\n")
        return

    if itemsDB[itemID]['clo_lhand'] == 0 and \
       itemsDB[itemID]['clo_rhand'] == 0:
        mud.send_message(id, "You can't hold that.\n\n")
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
        mud.send_message(id,'You hold <b234>'+ \
                         itemsDB[itemID]['article']+' '+ \
                         itemsDB[itemID]['name']+ \
                         '<r> in your left hand.\n\n')
    else:
        if int(players[id]['clo_lhand']) == itemID:
            players[id]['clo_lhand'] = 0
        players[id]['clo_rhand'] = itemID
        mud.send_message(id,'You hold <b234>'+ \
                         itemsDB[itemID]['article']+' '+ \
                         itemsDB[itemID]['name']+ \
                         '<r> in your right hand.\n\n')


def stow(params,mud,playersDB: {},players: {},rooms: {}, \
         npcsDB: {},npcs: {},itemsDB: {},items: {}, \
         envDB: {},env: {},eventDB: {},eventSchedule, \
         id,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB: {}, \
         sentimentDB: {},guildsDB: {},clouds: {}):
    if len(list(players[id]['inv'])) == 0:
        return

    stowFrom=('clo_lhand','clo_rhand')
    for stowLocation in stowFrom:
        itemID=int(players[id][stowLocation])
        if itemID==0:
            continue
        if int(itemsDB[itemID]['clo_rleg']) > 0:
            if int(players[id]['clo_rleg']) == 0:
                if int(players[id]['clo_lleg']) != itemID:
                    players[id]['clo_rleg'] = itemID
                    mud.send_message(id,'You stow <b234>'+ \
                                     itemsDB[itemID]['article']+' '+ \
                                     itemsDB[itemID]['name']+'<r>\n\n')
                    players[id][stowLocation] = 0                    
                    continue

        if int(itemsDB[itemID]['clo_lleg']) > 0:
            if int(players[id]['clo_lleg']) == 0:
                if int(players[id]['clo_rleg']) != itemID:
                    players[id]['clo_lleg'] = itemID
                    mud.send_message(id,'You stow <b234>'+ \
                                     itemsDB[itemID]['article']+' '+ \
                                     itemsDB[itemID]['name']+'<r>\n\n')
                    players[id][stowLocation] = 0                    

    stowHands(id, players, itemsDB, mud)

def wearClothing(itemID,players: {},id,clothingType,mud,itemsDB: {}) -> bool:
    if itemsDB[itemID]['clo_'+clothingType] > 0:
        players[id]['clo_'+clothingType] = itemID
        clothingOpened=False
        if len(itemsDB[itemID]['open_description'])>0:
            if ' open' not in itemsDB[itemID]['open_description']:
                mud.send_message(id, randomDescription(itemsDB[itemID]['open_description']) + '\n\n')
                clothingOpened=True
        if not clothingOpened:
            mud.send_message(
                id,
                'You put on ' +
                itemsDB[itemID]['article'] +
                ' <b234>' +
                itemsDB[itemID]['name'] +
                '\n\n')
        return True
    return False

def unwearClothing(players: {},id,clothingType,mud,itemsDB: {}):
    if int(players[id]['clo_'+clothingType]) > 0:
        itemID = int(players[id]['clo_'+clothingType])
        clothingClosed=False
        if len(itemsDB[itemID]['close_description'])>0:
            if ' close ' not in itemsDB[itemID]['open_description'] and \
               'closed' not in itemsDB[itemID]['open_description'] and \
               'closing' not in itemsDB[itemID]['open_description'] and \
               'shut' not in itemsDB[itemID]['open_description']:
                mud.send_message(id, randomDescription(itemsDB[itemID]['close_description']) + '\n\n')
                clothingClosed=True
        if not clothingClosed:    
            mud.send_message(id, 'You remove ' +
                             itemsDB[itemID]['article'] + ' <b234>' +
                             itemsDB[itemID]['name'] + '\n\n')
        players[id]['clo_'+clothingType] = 0
    
def unwear(params,mud,playersDB: {},players: {},rooms: {}, \
           npcsDB: {},npcs: {},itemsDB: {},items: {}, \
           envDB: {},env: {},eventDB: {},eventSchedule, \
           id: int,fights: {},corpses: {},blocklist, \
           mapArea: [],characterClassDB: {},spellsDB: {}, \
           sentimentDB: {},guildsDB: {},clouds: {}):
    if len(list(players[id]['inv'])) == 0:
        return

    for clothingType in wearLocation:
        unwearClothing(players,id,clothingType,mud,itemsDB)

def playersMoveTogether(id,rm,mud, \
                        playersDB,players,rooms,npcsDB,npcs, \
                        itemsDB,items,envDB,env,eventDB,eventSchedule, \
                        fights,corpses,blocklist,mapArea, \
                        characterClassDB,spellsDB,sentimentDB,guildsDB) -> None:
    """In boats when one player rows the rest move with them
    """
    # go through all the players in the game
    for (pid, pl) in list(players.items()):
        # if player is in the same room and isn't the player
        # sending the command
        if players[pid]['room'] == players[id]['room'] and \
           pid != id:
            players[pid]['room'] = rm

            mud.send_message(pid, \
                             'You row to <f106>{}'.format(rooms[rm]['name']) + "\n\n")

            look('',mud,playersDB,players,rooms,npcsDB,npcs, \
                 itemsDB,items,envDB,env,eventDB,eventSchedule, \
                 pid,fights,corpses,blocklist,mapArea, \
                 characterClassDB,spellsDB,sentimentDB,guildsDB,clouds)

            if rooms[rm]['eventOnEnter'] is not "":
                addToScheduler(int(rooms[rm]['eventOnEnter']),
                               pid, eventSchedule, eventDB)
        
def messageToPlayersInRoom(mud, players, id, msg):
    # go through all the players in the game
    for (pid, pl) in list(players.items()):
        # if player is in the same room and isn't the player
        # sending the command
        if players[pid]['room'] == players[id]['room'] and \
           pid != id:
            if playerIsVisible(pid,id,players):
                mud.send_message(pid, msg)

def bioOfPlayer(mud, id, pid, players, itemsDB):
    if players[pid].get('race'):
        if len(players[pid]['race']) > 0:
            mud.send_message(id, '<f32>' + players[pid]['name'] + '<r> (' +
                             players[pid]['race'] + ' ' +
                             players[pid]['characterClass'] + ')\n')

    if players[pid].get('speakLanguage'):
        mud.send_message(
            id,
            '<f15>Speaks:<r> ' +
            players[pid]['speakLanguage'] +
            '\n')
    if pid == id:
        if players[id].get('language'):
            if len(players[id]['language']) > 1:
                languagesStr = ''
                langCtr = 0
                for lang in players[id]['language']:
                    if langCtr > 0:
                        languagesStr=languagesStr+', '+lang
                    else:
                        languagesStr=languagesStr+lang
                    langCtr += 1
                mud.send_message(id,'Languages: '+languagesStr+'\n')

    mud.send_message_wrap(id, '', \
                          randomDescription(players[pid]['lookDescription']) + '\n')
    
    if players[pid].get('canGo'):
        if players[pid]['canGo'] == 0:
            mud.send_message(id, 'They are frozen.\n')

    # count items of clothing
    wearingCtr = 0
    for c in wearLocation:
        if int(players[pid]['clo_'+c]) > 0:
            wearingCtr += 1

    playerName = 'You'
    playerName2 = 'your'
    playerName3 = 'have'
    if id != pid:
        playerName = 'They'
        playerName2 = 'their'
        playerName3 = 'have'

    if int(players[pid]['clo_rhand']) > 0:
        mud.send_message(id,playerName+' '+playerName3+' '+ \
                         itemsDB[players[pid]['clo_rhand']]['article']+ \
                         ' '+itemsDB[players[pid]['clo_rhand']]['name']+ \
                         ' in '+playerName2+' right hand.\n')
    if players[pid].get('clo_rfinger'):
        if int(players[pid]['clo_rfinger']) > 0:
            mud.send_message(id,playerName+' '+playerName3+' ' + \
                             itemsDB[players[pid]['clo_rfinger']]['article'] + \
                             ' ' + itemsDB[players[pid]['clo_rfinger']]['name'] + \
                             ' on the finger of '+playerName2+' right hand.\n')
    if int(players[pid]['clo_lhand']) > 0:
        mud.send_message(id,playerName + ' ' + playerName3 + ' ' + \
                         itemsDB[players[pid]['clo_lhand']]['article'] + \
                         ' ' + itemsDB[players[pid]['clo_lhand']]['name'] + \
                         ' in ' + playerName2 + ' left hand.\n')
    if players[pid].get('clo_lfinger'):
        if int(players[pid]['clo_lfinger']) > 0:
            mud.send_message(id,playerName+' '+playerName3+' '+ \
                             itemsDB[players[pid]['clo_lfinger']]['article']+ \
                             ' '+itemsDB[players[pid]['clo_lfinger']]['name']+ \
                             ' on the finger of '+playerName2+' left hand.\n')

    if wearingCtr > 0:
        wearingMsg = playerName + ' are wearing'
        wearingCtr2 = 0
        for cl in wearLocation:
            if int(players[pid]['clo_'+cl]) > 0:
                if wearingCtr2 > 0:
                    if wearingCtr2 == wearingCtr - 1:
                        wearingMsg = wearingMsg + ' and '
                    else:
                        wearingMsg = wearingMsg + ', '
                else:
                    wearingMsg = wearingMsg + ' '
                wearingMsg = wearingMsg + itemsDB[players[pid]['clo_'+cl]]['article'] + \
                    ' ' + itemsDB[players[pid]['clo_'+cl]]['name']
                if cl == 'neck':
                    wearingMsg = wearingMsg + ' around ' + playerName2 + ' neck'
                if cl == 'lwrist':
                    wearingMsg = wearingMsg + ' on ' + playerName2 + ' left wrist'
                if cl == 'rwrist':
                    wearingMsg = wearingMsg + ' on ' + playerName2 + ' right wrist'
                if cl == 'lleg':
                    wearingMsg = wearingMsg + ' on ' + playerName2 + ' left leg'
                if cl == 'rleg':
                    wearingMsg = wearingMsg + ' on ' + playerName2 + ' right leg'
                wearingCtr2 += 1
        mud.send_message(id, wearingMsg + '.\n')
    mud.send_message(id, '\n')

def bio(params,mud,playersDB: {},players: {},rooms: {}, \
        npcsDB: {},npcs: {},itemsDB: {},items: {}, \
        envDB: {},env: {},eventDB: {},eventSchedule, \
        id: int,fights: {},corpses: {},blocklist, \
        mapArea: [],characterClassDB: {},spellsDB: {}, \
        sentimentDB: {},guildsDB: {},clouds: {}):
    if len(params) == 0:
        bioOfPlayer(mud, id, id, players, itemsDB)
        return

    if params == players[id]['name']:
        bioOfPlayer(mud, id, id, players, itemsDB)
        return

    # go through all the players in the game
    if players[id]['authenticated'] is not None:
        for (pid, pl) in list(players.items()):
            if players[pid]['name'] == params:
                bioOfPlayer(mud, id, pid, players, itemsDB)
                return

    if players[id]['name'].lower() == 'guest':
        mud.send_message(id, "Guest players cannot set a bio.\n\n")
        return

    if players[id]['canSay'] == 0:
        mud.send_message(
            id, "You try to describe yourself, but find you have nothing to say.\n\n")
        return

    if '"' in params:
        mud.send_message(id, "Your bio must not include double quotes.\n\n")
        return

    if params.startswith(':'):
        params = params.replace(':', '').strip()

    players[id]['lookDescription'] = params
    mud.send_message(id, "Your bio has been set.\n\n")


def eat(params,mud,playersDB: {},players: {},rooms: {}, \
        npcsDB: {},npcs: {},itemsDB: {},items: {}, \
        envDB: {},env: {},eventDB: {},eventSchedule, \
        id: int,fights: {},corpses: {},blocklist, \
        mapArea: [],characterClassDB: {},spellsDB: {}, \
        sentimentDB: {},guildsDB: {},clouds: {}):
    food = params.lower()
    foodItemID = 0
    if len(list(players[id]['inv'])) > 0:
        for i in list(players[id]['inv']):
            if food in itemsDB[int(i)]['name'].lower():
                if itemsDB[int(i)]['edible'] != 0:
                    foodItemID = int(i)
                    break
                else:
                    mud.send_message(id, "That's not consumable.\n\n")
                    return

    if foodItemID == 0:
        mud.send_message(id, "Your don't have " + params + ".\n\n")
        return

    mud.send_message(id, "You consume " + itemsDB[foodItemID]['article'] +
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


def stepOver(params,mud,playersDB: {},players: {},rooms: {}, \
             npcsDB: {},npcs: {},itemsDB: {},items: {}, \
             envDB: {},env: {},eventDB: {},eventSchedule, \
             id: int,fights: {},corpses: {},blocklist, \
             mapArea: [],characterClassDB: {},spellsDB: {}, \
             sentimentDB: {},guildsDB: {},clouds: {}):
    roomID=players[id]['room']
    if not rooms[roomID]['trap'].get('trapActivation'):
        mud.send_message(
            id, randomDescription(
                "You don't notice a tripwire") + '.\n\n')
        return
    if rooms[roomID]['trap']['trapActivation']!='tripwire':
        mud.send_message(
            id, randomDescription(
                "You don't notice a tripwire|You don't see a tripwire") + '.\n\n')
        return
    if 'over ' not in params:
        mud.send_message(
            id, randomDescription(
                "Do what?|Eh?") + '.\n\n')
        return
        
    for direction,ex in rooms[roomID]['exits'].items():
        if direction in params:
            go('######step######'+direction,mud,playersDB,players, \
               rooms,npcsDB,npcs,itemsDB,items,envDB,env,eventDB, \
               eventSchedule,id,fights,corpses,blocklist,mapArea, \
               characterClassDB,spellsDB,sentimentDB,guildsDB,clouds)
            break

def climb(params,mud,playersDB: {},players: {},rooms: {}, \
          npcsDB: {},npcs: {},itemsDB: {},items: {}, \
          envDB: {},env: {},eventDB: {},eventSchedule, \
          id: int,fights: {},corpses: {},blocklist, \
          mapArea: [],characterClassDB: {},spellsDB: {},
          sentimentDB: {},guildsDB: {},clouds: {}):
    """Climbing through or into an item takes the player to a different room
    """
    if players[id]['canGo'] != 1:
        mud.send_message(id, "You try to move but find that you lack any ability to.\n\n")
        return
    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            itemId=items[item]['id']
            if not itemIsVisible(id,players,itemId,itemsDB):
                continue
            if not itemsDB[itemId].get('climbThrough'):
                continue
            if not itemsDB[itemId].get('exit'):
                continue
            if itemsDB[itemId].get('state'):
                if 'open' not in itemsDB[itemId]['state']:
                    mud.send_message(id, itemsDB[itemId]['name']+ \
                                     " is closed.\n\n")
                    continue
            targetRoom=itemsDB[itemId]['exit']
            if rooms[targetRoom]['maxPlayerSize']>-1:
                if players[id]['siz'] > rooms[targetRoom]['maxPlayerSize']:
                    mud.send_message(id, "You're too big.\n\n")
                    return
            if rooms[targetRoom]['maxPlayers']>-1:
                if playersInRoom(targetRoom,players,npcs) >= \
                   rooms[targetRoom]['maxPlayers']:
                    mud.send_message(id, "It's too crowded.\n\n")
                    return
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   randomDescription(players[id]['outDescription']) + '\n')
            # Trigger old room eventOnLeave for the player
            if rooms[players[id]['room']]['eventOnLeave'] is not "":
                addToScheduler(int(rooms[players[id]['room']]['eventOnLeave']),
                               id, eventSchedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = targetRoom
            # climbing message
            mud.send_message_wrap(id,'<f230>', \
                                  randomDescription(itemsDB[itemId]['climbThrough'])+"\n\n")
            time.sleep(3)
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] is not "":
                addToScheduler(int(rooms[players[id]['room']]['eventOnEnter']),
                               id, eventSchedule, eventDB)
            # message to other players
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   randomDescription(players[id]['inDescription']) + "\n\n")
            # look after climbing
            look('',mud,playersDB,players,rooms,npcsDB,npcs,itemsDB,items, \
                 envDB,env,eventDB,eventSchedule,id,fights,corpses,blocklist, \
                 mapArea,characterClassDB,spellsDB,sentimentDB,guildsDB,clouds)            
            return
    mud.send_message(id, "Nothing happens.\n\n")

def heave(params,mud,playersDB: {},players: {},rooms: {}, \
          npcsDB: {},npcs: {},itemsDB: {},items: {}, \
          envDB: {},env: {},eventDB: {},eventSchedule, \
          id: int,fights: {},corpses: {},blocklist, \
          mapArea: [],characterClassDB: {},spellsDB: {}, \
          sentimentDB: {},guildsDB: {},clouds: {}):
    """Roll/heave an item takes the player to a different room
    """
    if players[id]['canGo'] != 1:
        mud.send_message(id, "You try to move but find that you lack any ability to.\n\n")
        return

    target=params.lower()
    if target.startswith('the '):
        target=target.replace('the ','')

    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            itemId=items[item]['id']
            if not itemIsVisible(id,players,itemId,itemsDB):
                continue
            if not itemsDB[itemId].get('heave'):
                continue
            if not itemsDB[itemId].get('exit'):
                continue
            if target not in itemsDB[itemId]['name']:
                continue
            if itemsDB[itemId].get('state'):
                if 'open' not in itemsDB[itemId]['state']:
                    mud.send_message(id, itemsDB[itemId]['name']+ \
                                     " is closed.\n\n")
                    continue
            targetRoom=itemsDB[itemId]['exit']
            if rooms[targetRoom]['maxPlayerSize']>-1:
                if players[id]['siz'] > rooms[targetRoom]['maxPlayerSize']:
                    mud.send_message(id, "You're too big.\n\n")
                    return
            if rooms[targetRoom]['maxPlayers']>-1:
                if playersInRoom(targetRoom,players,npcs) >= rooms[targetRoom]['maxPlayers']:
                    mud.send_message(id, "It's too crowded.\n\n")
                    return
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   randomDescription(players[id]['outDescription']) + '\n')
            # Trigger old room eventOnLeave for the player
            if rooms[players[id]['room']]['eventOnLeave'] is not "":
                addToScheduler(int(rooms[players[id]['room']]['eventOnLeave']),
                               id, eventSchedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = targetRoom
            # heave message
            mud.send_message_wrap(id,'<f220>', \
                                  randomDescription(itemsDB[itemId]['heave'])+"\n\n")
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] is not "":
                addToScheduler(int(rooms[players[id]['room']]['eventOnEnter']),
                               id, eventSchedule, eventDB)
            # message to other players
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   randomDescription(players[id]['inDescription']) + "\n\n")
            time.sleep(3)
            # look after climbing
            look('',mud,playersDB,players,rooms,npcsDB,npcs,itemsDB,items, \
                 envDB,env,eventDB,eventSchedule,id,fights,corpses,blocklist, \
                 mapArea,characterClassDB,spellsDB,sentimentDB,guildsDB, \
                 clouds)            
            return
    mud.send_message(id, "Nothing happens.\n\n")

def jump(params,mud,playersDB: {},players: {},rooms: {}, \
         npcsDB: {},npcs: {},itemsDB: {},items: {}, \
         envDB: {},env: {},eventDB: {},eventSchedule, \
         id: int,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB: {}, \
         sentimentDB: {},guildsDB: {},clouds: {}):
    """Jumping onto an item takes the player to a different room
    """
    if players[id]['canGo'] != 1:
        mud.send_message(id, "You try to move but find that you lack any ability to.\n\n")
        return
    if not params:
        mud.send_message(id, randomDescription("You jump, expecting something to happen. But it doesn't.|Jumping doesn't help.|You jump. Nothing happens.|In this situation jumping only adds to the confusion.|You jump up and down on the spot.|You jump, and then feel vaguely silly.")+"\n\n")
        return
    words=params.lower().replace('.','').split(' ')
    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            itemId=items[item]['id']
            if not itemIsVisible(id,players,itemId,itemsDB):
                continue
            if not itemsDB[itemId].get('jumpTo'):
                continue
            if not itemsDB[itemId].get('exit'):
                continue
            wordMatched=False
            for w in words:
                if w in itemsDB[itemId]['name'].lower():
                    wordMatched=True
                    break
            if not wordMatched:
                continue
            if itemsDB[itemId].get('state'):
                if 'open' not in itemsDB[itemId]['state']:
                    mud.send_message(id, itemsDB[itemId]['name']+ \
                                     " is closed.\n\n")
                    continue
            targetRoom=itemsDB[itemId]['exit']
            if rooms[targetRoom]['maxPlayerSize']>-1:
                if players[id]['siz'] > rooms[targetRoom]['maxPlayerSize']:
                    mud.send_message(id, "You're too big.\n\n")
                    return
            if rooms[targetRoom]['maxPlayers']>-1:
                if playersInRoom(targetRoom,players,npcs) >= rooms[targetRoom]['maxPlayers']:
                    mud.send_message(id, "It's too crowded.\n\n")
                    return
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   randomDescription(players[id]['outDescription']) + '\n')
            # Trigger old room eventOnLeave for the player
            if rooms[players[id]['room']]['eventOnLeave'] is not "":
                addToScheduler(int(rooms[players[id]['room']]['eventOnLeave']),
                               id, eventSchedule, eventDB)
            # update the player's current room to the one the exit leads to
            players[id]['room'] = targetRoom
            # climbing message
            mud.send_message_wrap(id,'<f230>', \
                                  randomDescription(itemsDB[itemId]['jumpTo'])+"\n\n")
            time.sleep(3)
            # trigger new room eventOnEnter for the player
            if rooms[players[id]['room']]['eventOnEnter'] is not "":
                addToScheduler(int(rooms[players[id]['room']]['eventOnEnter']),
                               id, eventSchedule, eventDB)
            # message to other players
            messageToPlayersInRoom(mud, players, id, '<f32>' +
                                   players[id]['name'] + '<r> ' +
                                   randomDescription(players[id]['inDescription']) + "\n\n")
            # look after climbing
            look('',mud,playersDB,players,rooms,npcsDB,npcs,itemsDB,items, \
                 envDB,env,eventDB,eventSchedule,id,fights,corpses,blocklist, \
                 mapArea,characterClassDB,spellsDB,sentimentDB,guildsDB,clouds)            
            return
    mud.send_message(id, randomDescription("You jump, expecting something to happen. But it doesn't.|Jumping doesn't help.|You jump. Nothing happens.|In this situation jumping only adds to the confusion.|You jump up and down on the spot.|You jump, and then feel vaguely silly.")+"\n\n")

def chessBoardInRoom(players: {},id,rooms: {},items: {},itemsDB: {}):
    """Returns the item ID if there is a chess board in the room
    """
    rid=players[id]['room']
    for i in items:
        if items[i]['room'] != rid:
            continue
        if 'chess' in itemsDB[items[i]['id']]['game'].lower():
            return i
    return None

def deal(params,mud,playersDB: {},players: {},rooms: {}, \
         npcsDB: {},npcs: {},itemsDB: {},items: {}, \
         envDB: {},env: {},eventDB: {},eventSchedule, \
         id: int,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB: {},
         sentimentDB: {},guildsDB: {},clouds: {}):
    """Deal cards to other players
    """
    dealToPlayers(players,id,params.lower(), \
                  mud,rooms,items,itemsDB)

def handOfCards(params,mud,playersDB: {},players: {},rooms: {}, \
                npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                envDB: {},env: {},eventDB: {},eventSchedule, \
                id: int,fights: {},corpses: {},blocklist, \
                mapArea: [],characterClassDB: {},spellsDB: {}, \
                sentimentDB: {},guildsDB: {},clouds: {}):
    """Show hand of cards
    """
    showHandOfCards(players,id,mud,rooms,items,itemsDB)

def swapACard(params,mud,playersDB: {},players: {},rooms: {}, \
              npcsDB: {},npcs: {},itemsDB: {},items: {}, \
              envDB: {},env: {},eventDB: {},eventSchedule, \
              id: int,fights: {},corpses: {},blocklist, \
              mapArea: [],characterClassDB: {},spellsDB: {}, \
              sentimentDB: {},guildsDB: {},clouds: {}):
    """Swap a playing card for another from the deck
    """
    swapCard(params,players,id,mud,rooms,items,itemsDB)

def shuffle(params,mud,playersDB: {},players: {},rooms: {}, \
            npcsDB: {},npcs: {},itemsDB: {},items: {}, \
            envDB: {},env: {},eventDB: {},eventSchedule, \
            id: int,fights: {},corpses: {},blocklist, \
            mapArea: [],characterClassDB: {},spellsDB: {}, \
            sentimentDB: {},guildsDB: {},clouds: {}):
    """Shuffle a deck of cards
    """
    shuffleCards(players,id,mud,rooms,items,itemsDB)

def callCardGame(params,mud,playersDB: {},players: {},rooms: {}, \
                 npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                 envDB: {},env: {},eventDB: {},eventSchedule, \
                 id: int,fights: {},corpses: {},blocklist, \
                 mapArea: [],characterClassDB: {},spellsDB: {}, \
                 sentimentDB: {},guildsDB: {},clouds: {}):
    """Players show their cards
    """
    callCards(players,id,mud,rooms,items,itemsDB)

def morrisGame(params,mud,playersDB: {},players: {},rooms: {}, \
               npcsDB: {},npcs: {},itemsDB: {},items: {}, \
               envDB: {},env: {},eventDB: {},eventSchedule, \
               id: int,fights: {},corpses: {},blocklist, \
               mapArea: [],characterClassDB: {},spellsDB: {}, \
               sentimentDB: {},guildsDB: {},clouds: {}):
    """Show the nine men's morris board
    """
    params=params.lower()
    if params.startswith('reset') or \
       params.startswith('clear'):
        resetMorrisBoard(players,id,mud,rooms,items,itemsDB)
        return

    if params.startswith('take') or \
       params.startswith('remove') or \
       params.startswith('capture'):
        takeMorrisCounter(params,players,id,mud,rooms,items,itemsDB)
        return

    if params.startswith('move ') or \
       params.startswith('play ') or \
       params.startswith('put ') or \
       params.startswith('counter ') or \
       params.startswith('place '):
        morrisMove(params,players,id,mud,rooms, \
                   items,itemsDB)
        return

    showMorrisBoard(players,id,mud,rooms,items,itemsDB)

def chess(params,mud,playersDB: {},players: {},rooms: {}, \
          npcsDB: {},npcs: {},itemsDB: {},items: {}, \
          envDB: {},env: {},eventDB: {},eventSchedule, \
          id: int,fights: {},corpses: {},blocklist, \
          mapArea: [],characterClassDB: {},spellsDB: {}, \
          sentimentDB: {},guildsDB: {},clouds: {}):
    """Jumping onto an item takes the player to a different room
    """
    # check if board exists in room
    boardItemID=chessBoardInRoom(players,id,rooms,items,itemsDB)
    if not boardItemID:
        mud.send_message(id, "\nThere isn't a chess board here.\n\n")
        return
    rid=players[id]['room']
    # create the game state
    if not items[boardItemID].get('gameState'):
        items[boardItemID]['gameState']={}
    if not items[boardItemID]['gameState'].get('state'):
        items[boardItemID]['gameState']['state']=initialChessBoard()
        items[boardItemID]['gameState']['turn']='white'
        items[boardItemID]['gameState']['history']=[]
    # get the game history
    gameState=items[boardItemID]['gameState']['state']
    if not params:
        showChessBoard(gameState,id,mud,items[boardItemID]['gameState']['turn'])
        return
    if players[id]['canGo'] != 1 or \
       players[id]['frozenStart'] > 0:
        mud.send_message(id, randomDescription("\nYou try to make a chess move but find that you lack any ability to|You suddenly lose all enthusiasm for chess")+".\n\n")
        return
    params=params.lower().strip()
    if 'undo' in params:
        if len(items[boardItemID]['gameState']['history'])<2:
            params='reset'
        else:
            mud.send_message(id, '\nUndoing last chess move.\n')
            items[boardItemID]['gameState']['history'].pop()
            gameState=items[boardItemID]['gameState']['history'][-1]            
            items[boardItemID]['gameState']['state']=gameState
            if items[boardItemID]['gameState']['turn']=='white':
                items[boardItemID]['gameState']['turn']='black'
            else:
                items[boardItemID]['gameState']['turn']='white'
            showChessBoard(gameState,id,mud,items[boardItemID]['gameState']['turn'])
            return
    # begin a new chess game
    if 'reset' in params or \
       'restart' in params or \
       'start again' in params or \
       'begin again' in params or \
       'new game' in params:
        mud.send_message(id, '\nStarting a new game.\n')
        items[boardItemID]['gameState']['state']=initialChessBoard()
        items[boardItemID]['gameState']['turn']='white'
        items[boardItemID]['gameState']['history']=[]
        gameState=items[boardItemID]['gameState']['state']
        showChessBoard(gameState,id,mud,items[boardItemID]['gameState']['turn'])
        return            
    if 'move' in params:
        params=params.replace('move ','').replace('to ','').replace('from ','').replace('.','').replace('-','').strip()
        chessMoves=params.split(' ')

        if len(chessMoves)==1:
            if len(params)!=4:
                mud.send_message(id, "\nEnter a move such as g8f6.\n")
                return
            chessMoves=[params[:2],params[2:]]
                
        if len(chessMoves)!=2:
            mud.send_message(id, "\nThat's not a valid move.\n")
            return
        if len(chessMoves[0])!=2 or \
           len(chessMoves[1])!=2:
            mud.send_message(id, "\nEnter a move such as g8 f6.\n")
            return
        if moveChessPiece(chessMoves[0]+chessMoves[1], \
                          items[boardItemID]['gameState']['state'], \
                          items[boardItemID]['gameState']['turn'],id,mud):
            mud.send_message(id, "\n"+items[boardItemID]['gameState']['turn']+ \
                             " moves from "+chessMoves[0]+" to "+chessMoves[1]+".\n")
            gameState=items[boardItemID]['gameState']['state']
            currTurn=items[boardItemID]['gameState']['turn']
            if currTurn=='white':
                items[boardItemID]['gameState']['player1']=players[id]['name']
                items[boardItemID]['gameState']['turn']='black'
                # send a notification to the other player
                if items[boardItemID]['gameState'].get('player2'):
                    for p in players:
                        if p==id:
                            continue
                        if players[p]['name'] == items[boardItemID]['gameState']['player2']:
                            if players[p]['room'] == players[id]['room']:
                                showChessBoard(gameState,p,mud, \
                                               items[boardItemID]['gameState']['turn'])
            else:
                items[boardItemID]['gameState']['player2']=players[id]['name']
                items[boardItemID]['gameState']['turn']='white'
                # send a notification to the other player
                if items[boardItemID]['gameState'].get('player1'):
                    for p in players:
                        if p==id:
                            continue
                        if players[p]['name'] == items[boardItemID]['gameState']['player1']:
                            if players[p]['room'] == players[id]['room']:
                                showChessBoard(gameState,p,mud,items[boardItemID]['gameState']['turn'])
            items[boardItemID]['gameState']['history'].append(gameState.copy())
            showChessBoard(gameState,id,mud,currTurn)
            return
        else:
            mud.send_message(id, "\nThat's not a valid move.\n")
            return
    showChessBoard(gameState,id,mud,items[boardItemID]['gameState']['turn'])

def graphics(params,mud,playersDB: {},players: {},rooms: {}, \
             npcsDB: {},npcs: {},itemsDB: {},items: {}, \
             envDB: {},env: {},eventDB: {},eventSchedule, \
             id: int,fights: {},corpses: {},blocklist, \
             mapArea: [],characterClassDB: {},spellsDB: {}, \
             sentimentDB: {},guildsDB: {},clouds: {}):
    """Turn graphical output on or off
    """
    graphicsState=params.lower().strip()
    if graphicsState=='off' or \
       graphicsState=='false' or \
       graphicsState=='no':
        players[id]['graphics']='off'
        mud.send_message(id, "Graphics have been turned off.\n\n")
    else:
        players[id]['graphics']='on'
        mud.send_message(id, "Graphics have been activated.\n\n")

def go(params,mud,playersDB: {},players: {},rooms: {}, \
       npcsDB: {},npcs: {},itemsDB: {},items: {}, \
       envDB: {},env: {},eventDB: {},eventSchedule, \
       id: int,fights: {},corpses: {},blocklist, \
       mapArea: [],characterClassDB: {},spellsDB: {}, \
       sentimentDB: {},guildsDB: {},clouds: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if playerIsTrapped(id,players,rooms):
        describeTrappedPlayer(mud,id,players,rooms)
        return

    if players[id]['canGo'] == 1:
        # store the exit name
        ex = params.lower()

        stepping=False
        if '######step######' in ex:
            if rooms[players[id]['room']]['trap'].get('trapActivation'):
                if rooms[players[id]['room']]['trap']['trapActivation']=='tripwire':
                    ex=ex.replace('######step######','')
                    stepping=True

        # store the player's current room
        rm = rooms[players[id]['room']]

        # if the specified exit is found in the room's exits list
        rmExits=getRoomExits(rooms,players,id)
        if ex in rmExits:
            # check if there is enough room
            targetRoom=None
            if ex in rm['exits']:
                targetRoom=rm['exits'][ex]
            elif rm.get('tideOutExits'):
                targetRoom=rm['tideOutExits'][ex]
            elif rm.get('exitsWhenWearing'):
                targetRoom=rm['exitsWhenWearing'][ex]
            if targetRoom:
                if rooms[targetRoom]['maxPlayers']>-1:
                    if playersInRoom(targetRoom,players,npcs) >= \
                       rooms[targetRoom]['maxPlayers']:
                        mud.send_message(id, 'The room is full.\n\n')
                        return

                #Check that the player is not too tall
                if rooms[targetRoom]['maxPlayerSize']>-1:
                    if players[id]['siz'] > \
                       rooms[targetRoom]['maxPlayerSize']:
                        mud.send_message(id, "The entrance is too small for you to enter.\n\n")
                        return

                if not stepping:
                    if trapActivation(mud,id,players,rooms,ex):
                        return

                if rooms[players[id]['room']]['onWater']==0:
                    messageToPlayersInRoom(mud, players, id, '<f32>' +
                                           players[id]['name'] + '<r> ' +
                                           randomDescription(players[id]['outDescription']) +
                                           " via exit " + ex + '\n')

                # Trigger old room eventOnLeave for the player
                if rooms[players[id]['room']]['eventOnLeave'] is not "":
                    addToScheduler(int(rooms[players[id]['room']]['eventOnLeave']),
                                   id, eventSchedule, eventDB)

                # Does the player have any follower NPCs or familiars?
                followersMsg = ""
                for (nid, pl) in list(npcs.items()):
                    if npcs[nid]['follow'] == players[id]['name'] or \
                       (npcs[nid]['familiarOf'] == players[id]['name'] and \
                        npcs[nid]['familiarMode'] == 'follow'):
                        # is the npc in the same room as the player?
                        if npcs[nid]['room'] == players[id]['room']:
                            # is the player within the permitted npc path?
                            if rm['exits'][ex] in list(npcs[nid]['path']) or \
                               npcs[nid]['familiarOf'] == players[id]['name']:
                                followerRoomID=rm['exits'][ex]
                                if npcs[nid]['siz'] <= rooms[followerRoomID]['maxPlayerSize']:
                                    npcs[nid]['room'] = followerRoomID
                                    followersMsg = followersMsg + '<f32>' + \
                                        npcs[nid]['name'] + '<r> ' + \
                                        randomDescription(npcs[nid]['inDescription']) + '.\n\n'
                                    messageToPlayersInRoom(mud,players,id, \
                                                           '<f32>'+ \
                                                           npcs[nid]['name']+ \
                                                           '<r> '+ \
                                                           randomDescription(npcs[nid]['outDescription'])+ \
                                                           " via exit "+ex+'\n')
                                else:
                                    # The room height is too small for the follower
                                    npcs[nid]['follow'] = ""                                
                            else:
                                # not within the npc path, stop following
                                #print(npcs[nid]['name'] + ' stops following (out of path)\n')
                                npcs[nid]['follow'] = ""
                        else:
                            # stop following
                            #print(npcs[nid]['name'] + ' stops following\n')
                            npcs[nid]['follow'] = ""

                # update the player's current room to the one the exit leads to
                if rooms[players[id]['room']]['onWater']==1:
                    playersMoveTogether(id,rm['exits'][ex],mud, \
                                        playersDB,players,rooms,npcsDB,npcs, \
                                        itemsDB,items,envDB,env,eventDB,eventSchedule, \
                                        fights,corpses,blocklist,mapArea, \
                                        characterClassDB,spellsDB,sentimentDB,guildsDB)
                players[id]['room'] = rm['exits'][ex]
                rm = rooms[players[id]['room']]

                # trigger new room eventOnEnter for the player
                if rooms[players[id]['room']]['eventOnEnter'] is not "":
                    addToScheduler(int(rooms[players[id]['room']]['eventOnEnter']),
                                   id, eventSchedule, eventDB)

                if rooms[players[id]['room']]['onWater']==0:
                    messageToPlayersInRoom(mud, players, id, '<f32>' +
                                           players[id]['name'] + '<r> ' +
                                           randomDescription(players[id]['inDescription']) + "\n\n")
                    # send the player a message telling them where they are now
                    mud.send_message(id, \
                                     'You arrive at <f106>{}'.format(rooms[players[id]['room']]['name']) + "\n\n")
                else:
                    # send the player a message telling them where they are now
                    mud.send_message(id, \
                                     'You row to <f106>{}'.format(rooms[players[id]['room']]['name']) + "\n\n")

                look('',mud,playersDB,players,rooms,npcsDB,npcs, \
                     itemsDB,items,envDB,env,eventDB,eventSchedule, \
                     id,fights,corpses,blocklist,mapArea, \
                     characterClassDB,spellsDB,sentimentDB,guildsDB,clouds)            
                # report any followers
                if len(followersMsg) > 0:
                    messageToPlayersInRoom(mud, players, id, followersMsg)
                    mud.send_message(id, followersMsg)
        else:
            # the specified exit wasn't found in the current room
            # send back an 'unknown exit' message
            mud.send_message(id, "Unknown exit <f226>'{}'".format(ex) + "\n\n")
    else:
        mud.send_message(id, 'Somehow, your legs refuse to obey your will.\n')


def goNorth(params,mud,playersDB,players,rooms, \
            npcsDB,npcs,itemsDB,items,envDB, \
            env,eventDB,eventSchedule,id,fights, \
            corpses,blocklist,mapArea,characterClassDB, \
            spellsDB,sentimentDB,guildsDB,clouds) -> None:
    go('north',mud,playersDB,players,rooms,npcsDB, \
       npcs,itemsDB,items,envDB,env,eventDB,eventSchedule, \
       id,fights,corpses,blocklist,mapArea,characterClassDB, \
       spellsDB,sentimentDB,guildsDB,clouds)

def goSouth(params,mud,playersDB,players,rooms, \
            npcsDB,npcs,itemsDB,items,envDB, \
            env,eventDB,eventSchedule,id,fights, \
            corpses,blocklist,mapArea,characterClassDB, \
            spellsDB,sentimentDB,guildsDB,clouds) -> None:
    go('south',mud,playersDB,players,rooms,npcsDB, \
       npcs,itemsDB,items,envDB,env,eventDB,eventSchedule, \
       id,fights,corpses,blocklist,mapArea,characterClassDB, \
       spellsDB,sentimentDB,guildsDB,clouds)

def goEast(params,mud,playersDB,players,rooms, \
           npcsDB,npcs,itemsDB,items,envDB, \
           env,eventDB,eventSchedule,id,fights, \
           corpses,blocklist,mapArea,characterClassDB, \
           spellsDB,sentimentDB,guildsDB,clouds) -> None:
    go('east',mud,playersDB,players,rooms,npcsDB, \
       npcs,itemsDB,items,envDB,env,eventDB,eventSchedule, \
       id,fights,corpses,blocklist,mapArea,characterClassDB, \
       spellsDB,sentimentDB,guildsDB,clouds)

def goWest(params,mud,playersDB,players,rooms, \
           npcsDB,npcs,itemsDB,items,envDB, \
           env,eventDB,eventSchedule,id,fights, \
           corpses,blocklist,mapArea,characterClassDB, \
           spellsDB,sentimentDB,guildsDB,clouds) -> None:
    go('west',mud,playersDB,players,rooms,npcsDB, \
       npcs,itemsDB,items,envDB,env,eventDB,eventSchedule, \
       id,fights,corpses,blocklist,mapArea,characterClassDB, \
       spellsDB,sentimentDB,guildsDB,clouds)

def goUp(params,mud,playersDB,players,rooms, \
         npcsDB,npcs,itemsDB,items,envDB, \
         env,eventDB,eventSchedule,id,fights, \
         corpses,blocklist,mapArea,characterClassDB, \
         spellsDB,sentimentDB,guildsDB,clouds) -> None:
    go('up',mud,playersDB,players,rooms,npcsDB, \
       npcs,itemsDB,items,envDB,env,eventDB,eventSchedule, \
       id,fights,corpses,blocklist,mapArea,characterClassDB, \
       spellsDB,sentimentDB,guildsDB,clouds)

def goDown(params,mud,playersDB,players,rooms, \
           npcsDB,npcs,itemsDB,items,envDB, \
           env,eventDB,eventSchedule,id,fights, \
           corpses,blocklist,mapArea,characterClassDB, \
           spellsDB,sentimentDB,guildsDB,clouds) -> None:
    go('down',mud,playersDB,players,rooms,npcsDB, \
       npcs,itemsDB,items,envDB,env,eventDB,eventSchedule, \
       id,fights,corpses,blocklist,mapArea,characterClassDB, \
       spellsDB,sentimentDB,guildsDB,clouds)

def goIn(params,mud,playersDB,players,rooms, \
         npcsDB,npcs,itemsDB,items,envDB, \
         env,eventDB,eventSchedule,id,fights, \
         corpses,blocklist,mapArea,characterClassDB, \
         spellsDB,sentimentDB,guildsDB,clouds) -> None:
    go('in',mud,playersDB,players,rooms,npcsDB, \
       npcs,itemsDB,items,envDB,env,eventDB,eventSchedule, \
       id,fights,corpses,blocklist,mapArea,characterClassDB, \
       spellsDB,sentimentDB,guildsDB,clouds)

def goOut(params,mud,playersDB,players,rooms, \
          npcsDB,npcs,itemsDB,items,envDB, \
          env,eventDB,eventSchedule,id,fights, \
          corpses,blocklist,mapArea,characterClassDB, \
          spellsDB,sentimentDB,guildsDB,clouds) -> None:
    go('out',mud,playersDB,players,rooms,npcsDB, \
       npcs,itemsDB,items,envDB,env,eventDB,eventSchedule, \
       id,fights,corpses,blocklist,mapArea,characterClassDB, \
       spellsDB,sentimentDB,guildsDB,clouds)

def conjureRoom(params,mud,playersDB: {},players: {},rooms: {}, \
                npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                envDB: {},env: {},eventDB: {},eventSchedule, \
                id: int,fights: {},corpses: {},blocklist: {}, \
                mapArea: [],characterClassDB: {},spellsDB: {}, \
                sentimentDB: {},guildsDB: {},clouds: {}):
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
        'north': 'south',
        'south': 'north',
        'east': 'west',
        'west': 'east',
        'up': 'down',
        'down': 'up',
        'in': 'out',
        'out': 'in'}
    if roomDirection not in possibleDirections:
        mud.send_message(id, 'Specify a room direction.\n\n')
        return False

    # Is there already a room in that direction?
    playerRoomID = players[id]['room']
    roomExits = getRoomExits(rooms,players,id)
    if roomExits.get(roomDirection):
        mud.send_message(id, 'A room already exists in that direction.\n\n')
        return False

    roomID = getFreeRoomKey(rooms)
    if len(roomID) == 0:
        roomID = '$rid=1$'

    newrm = {
        'name': 'Empty room',
        'description': "You are in an empty room. There is a triangular symbol carved into the wall depicting a peasant digging with a spade. Underneath it is an inscription which reads 'aedificium'.",
        'roomTeleport': "",
        'conditional': [],
        'trap': {},
        'eventOnEnter': "",
        'eventOnLeave': "",
        "maxPlayerSize": -1,
        "maxPlayers": -1,
        'weather': 0,
        'tideOutDescription': "",
        'terrainDifficulty': 0,
        'coords': [],
        'exits': {
            oppositeDirection[roomDirection]: playerRoomID}}
    rooms[roomID] = newrm
    roomExits[roomDirection] = roomID

    # update the room coordinates
    for rm in rooms:
        rooms[rm]['coords'] = []
    mapArea = assignCoordinates(rooms)

    log("New room: " + roomID, 'info')
    saveUniverse(rooms, npcsDB, npcs, itemsDB, items, envDB, env, guildsDB)
    mud.send_message(id, 'Room created.\n\n')


def conjureItem(params,mud,playersDB: {},players: {},rooms: {}, \
                npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                envDB: {},env: {},eventDB: {},eventSchedule, \
                id: int,fights: {},corpses: {},blocklist, \
                mapArea: [],characterClassDB: {},spellsDB: {}, \
                sentimentDB: {},guildsDB: {},clouds: {}):
    itemName = params.lower()
    if len(itemName) == 0:
        mud.send_message(id, "Specify the name of an item to conjure.\n\n")
        return False

    # Check if item is in player's inventory
    for item in players[id]['inv']:
        for (iid, pl) in list(itemsDB.items()):
            if str(iid) == item:
                if itemName in itemsDB[iid]['name'].lower():
                    mud.send_message(id, "You have " +
                                     itemsDB[iid]['article'] + " " +
                                     itemsDB[iid]['name'] +
                                     " in your inventory already.\n\n")
                    return False
    # Check if it is in the room
    for (item, pl) in list(items.items()):
        if items[item]['room'] == players[id]['room']:
            if itemName in itemsDB[items[item]['id']]['name'].lower():
                mud.send_message(id, "It's already here.\n\n")
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
        items[itemKey] = {'id': itemID, 'room': players[id]['room'],
                          'whenDropped': int(time.time()),
                          'lifespan': 900000000, 'owner': id}

        mud.send_message(id, itemsDB[itemID]['article'] + ' ' +
                         itemsDB[itemID]['name'] +
                         ' spontaneously materializes in front of you.\n\n')
        saveUniverse(rooms, npcsDB, npcs, itemsDB, items, envDB, env, guildsDB)
        return True
    return False


def randomFamiliar(npcsDB):
    """Picks a familiar at random and returns its index
    """
    possibleFamiliars = []
    for index, details in npcsDB.items():
        if len(details['familiarType']) > 0:
            if len(details['familiarOf']) == 0:
                possibleFamiliars.append(int(index))
    if len(possibleFamiliars) > 0:
        randIndex=len(possibleFamiliars)-1
        return possibleFamiliars[randint(0, randIndex)]
    return -1

def conjureNPC(params,mud,playersDB: {},players: {},rooms: {}, \
               npcsDB: {},npcs: {},itemsDB: {},items: {}, \
               envDB: {},env: {},eventDB: {},eventSchedule, \
               id: int,fights: {},corpses: {},blocklist, \
               mapArea: [],characterClassDB: {},spellsDB: {}, \
               sentimentDB: {},guildsDB: {},clouds: {}):
    if not params.startswith('npc '):
        if not params.startswith('familiar'):
            return False

    npcHitPoints = 100
    isFamiliar = False
    npcType = 'NPC'
    if params.startswith('familiar'):
        isFamiliar = True
        npcType = 'Familiar'
        npcIndex = randomFamiliar(npcsDB)
        if npcIndex < 0:
            mud.send_message(id, "No familiars known.\n\n")
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
        mud.send_message(id, "Specify the name of an NPC to conjure.\n\n")
        return False

    # Check if NPC is in the room
    for (nid, pl) in list(npcs.items()):
        if npcs[nid]['room'] == players[id]['room']:
            if npcName.lower() in npcs[nid]['name'].lower():
                mud.send_message(id, npcs[nid]['name'] +
                                 " is already here.\n\n")
                return False

    # default medium size
    newNPC = {"name": npcName,
              "whenDied": None,
              "inv": [],
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
              "visibleWhenWearing": [],
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
              "clo_head": 0,
              "clo_neck": 0,
              "clo_larm": 0,
              "clo_rarm": 0,
              "clo_lhand": 0,
              "clo_rhand": 0,
              "clo_lfinger": 0,
              "clo_rfinger": 0,
              "clo_rwrist": 0,
              "clo_lwrist": 0,
              "clo_chest": 0,
              "clo_lleg": 0,
              "clo_rleg": 0,
              "clo_feet": 0,
              "imp_head": 0,
              "imp_larm": 0,
              "imp_rarm": 0,
              "imp_lhand": 0,
              "imp_rhand": 0,
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
    log(npcType + ' ' + npcName + ' generated in ' +
        players[id]['room'] + ' with key ' + str(npcsKey), 'info')
    if isFamiliar:
        mud.send_message(
            id,
            'Your familiar, ' +
            npcName +
            ', spontaneously appears.\n\n')
    else:
        mud.send_message(id, npcName + ' spontaneously appears.\n\n')
    saveUniverse(rooms, npcsDB, npcs, itemsDB, items, envDB, env, guildsDB)
    return True


def dismiss(params,mud,playersDB: {},players: {},rooms: {}, \
            npcsDB: {},npcs: {},itemsDB: {},items: {}, \
            envDB: {},env: {},eventDB: {},eventSchedule, \
            id: int,fights: {},corpses: {},blocklist, \
            mapArea: [],characterClassDB: {},spellsDB: {}, \
            sentimentDB: {},guildsDB: {},clouds: {}):
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
            mud.send_message(id, "Your familiar vanishes.\n\n")
        else:
            mud.send_message(id, "\n\n")


def conjure(params,mud,playersDB: {},players: {},rooms: {}, \
            npcsDB: {},npcs: {},itemsDB: {},items: {}, \
            envDB: {},env: {},eventDB: {},eventSchedule, \
            id: int,fights: {},corpses: {},blocklist, \
            mapArea: [],characterClassDB: {},spellsDB: {}, \
            sentimentDB: {},guildsDB: {},clouds: {}):
    if not isWitch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return

    if params.startswith('familiar'):
        conjureNPC(params,mud,playersDB,players,rooms,
                   npcsDB,npcs,itemsDB,items,envDB,env,
                   eventDB,eventSchedule,id,fights,corpses,
                   blocklist,mapArea,characterClassDB,
                   spellsDB,sentimentDB,guildsDB,clouds)
        return

    if params.startswith('room '):
        conjureRoom(params,mud,playersDB,players,rooms,npcsDB, \
                    npcs,itemsDB,items,envDB,env,eventDB, \
                    eventSchedule,id,fights,corpses,blocklist, \
                    mapArea,characterClassDB,spellsDB, \
                    sentimentDB,guildsDB,clouds)
        return

    if params.startswith('npc '):
        conjureNPC(params,mud,playersDB,players,rooms,
                   npcsDB,npcs,itemsDB,items,envDB,env,
                   eventDB,eventSchedule,id,fights,corpses,
                   blocklist,mapArea,characterClassDB,
                   spellsDB,sentimentDB,guildsDB,clouds)
        return

    conjureItem(params,mud,playersDB,players,rooms,npcsDB,npcs, \
                itemsDB,items,envDB,env,eventDB,eventSchedule, \
                id,fights,corpses,blocklist,mapArea, \
                characterClassDB,spellsDB,sentimentDB,guildsDB, \
                clouds)


def destroyItem(params,mud,playersDB: {},players: {},rooms: {}, \
                npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                envDB: {},env: {},eventDB: {},eventSchedule, \
                id: int,fights: {},corpses: {},blocklist, \
                mapArea: [],characterClassDB: {},spellsDB: {}, \
                sentimentDB: {},guildsDB: {},clouds: {}):
    itemName = params.lower()
    if len(itemName) == 0:
        mud.send_message(id, "Specify the name of an item to destroy.\n\n")
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
        mud.send_message(id, "It's not here.\n\n")
        return False

    mud.send_message(id, 'It suddenly vanishes.\n\n')
    del items[item]
    log("Item destroyed: " + destroyedName +
        ' in ' + players[id]['room'], 'info')
    saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env,guildsDB)
    return True


def destroyNPC(params,mud,playersDB: {},players: {},rooms: {}, \
               npcsDB: {},npcs: {},itemsDB: {},items: {}, \
               envDB: {},env: {},eventDB: {},eventSchedule, \
               id: int,fights: {},corpses: {},blocklist, \
               mapArea: [],characterClassDB: {},spellsDB: {}, \
               sentimentDB: {},guildsDB: {},clouds: {}):
    npcName = params.lower().replace('npc ', '').strip().replace('"', '')
    if len(npcName) == 0:
        mud.send_message(id, "Specify the name of an NPC to destroy.\n\n")
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
        mud.send_message(id, "They're not here.\n\n")
        return False

    mud.send_message(id, 'They suddenly vanish.\n\n')
    del npcs[npcID]
    del npcsDB[npcID]
    log("NPC destroyed: " + destroyedName +
        ' in ' + players[id]['room'], 'info')
    saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env,guildsDB)
    return True


def destroyRoom(params,mud,playersDB: {},players: {},rooms: {}, \
                npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                envDB: {},env: {},eventDB: {},eventSchedule, \
                id: int,fights: {},corpses: {},blocklist, \
                mapArea: [],characterClassDB: {},spellsDB: {}, \
                sentimentDB: {},guildsDB: {},clouds: {}):
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
        mud.send_message(id, 'Specify a room direction.\n\n')
        return False

    # Is there already a room in that direction?
    playerRoomID = players[id]['room']
    roomExits = getRoomExits(rooms,players,id)
    if not roomExits.get(roomDirection):
        mud.send_message(id, 'There is no room in that direction.\n\n')
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
    mapArea = assignCoordinates(rooms)

    log("Room destroyed: " + roomToDestroyID, 'info')
    saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env,guildsDB)
    mud.send_message(id, "Room destroyed.\n\n")
    return True


def destroy(params,mud,playersDB: {},players: {},rooms: {}, \
            npcsDB: {},npcs: {},itemsDB: {},items: {}, \
            envDB: {},env: {},eventDB: {},eventSchedule, \
            id: int,fights: {},corpses: {},blocklist, \
            mapArea: [],characterClassDB: {},spellsDB: {},
            sentimentDB: {},guildsDB: {},clouds):
    if not isWitch(id, players):
        mud.send_message(id, "You don't have enough powers.\n\n")
        return

    if params.startswith('room '):
        destroyRoom(params,mud,playersDB,players,rooms,npcsDB, \
                    npcs,itemsDB,items,envDB,env,eventDB, \
                    eventSchedule,id,fights,corpses,blocklist, \
                    mapArea,characterClassDB,spellsDB, \
                    sentimentDB,guildsDB,clouds)
    else:
        if params.startswith('npc '):
            destroyNPC(params,mud,playersDB,players,rooms,npcsDB, \
                       npcs,itemsDB,items,envDB,env,eventDB, \
                       eventSchedule,id,fights,corpses,blocklist, \
                       mapArea,characterClassDB,spellsDB, \
                       sentimentDB,guildsDB,clouds)
        else:
            destroyItem(params,mud,playersDB,players,rooms,npcsDB, \
                        npcs,itemsDB,items,envDB,env,eventDB, \
                        eventSchedule,id,fights,corpses,blocklist, \
                        mapArea,characterClassDB,spellsDB, \
                        sentimentDB,guildsDB,clouds)


def drop(params,mud,playersDB: {},players: {},rooms: {}, \
         npcsDB: {},npcs: {},itemsDB: {},items: {}, \
         envDB: {},env: {},eventDB: {},eventSchedule, \
         id: int,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB: {},
         sentimentDB: {},guildsDB: {},clouds: {}):
    # Check if inventory is empty
    if len(list(players[id]['inv'])) == 0:
        mud.send_message(id, 'You don`t have that!\n\n')
        return

    itemInDB = False
    itemInInventory = False
    itemID = None
    itemName = None
    target = str(params).lower()
    if target.startswith('the '):
        target = params.replace('the ', '')

    # Check if item is in player's inventory
    for item in players[id]['inv']:
        for (iid, pl) in list(itemsDB.items()):
            if str(iid) == str(item):
                if itemsDB[iid]['name'].lower() == target:
                    itemID = iid
                    itemName = itemsDB[iid]['name']
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
                        itemName = itemsDB[iid]['name']
                        itemInInventory = True
                        itemInDB = True
                        break

    if itemInDB and itemInInventory:
        if playerIsTrapped(id,players,rooms):
            mud.send_message(
                id, randomDescription(
                    "You're trapped|The trap restricts your ability to drop anything|The trap restricts your movement") + '.\n\n')
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
        removeItemFromClothing(players, id, int(i))

        # Create item on the floor in the same room as the player
        items[getFreeKey(items)] = {'id': itemID,
                                    'room': players[id]['room'],
                                    'whenDropped': int(time.time()),
                                    'lifespan': 900000000,
                                    'owner': id}

        # Print itemsInWorld to console for debugging purposes
        # for x in itemsInWorld:
        # print (x)
        # for y in itemsInWorld[x]:
        # print(y,':',itemsInWorld[x][y])

        mud.send_message(id, 'You drop ' +
                         itemsDB[int(i)]['article'] +
                         ' ' +
                         itemsDB[int(i)]['name'] +
                         ' on the floor.\n\n')

    else:
        mud.send_message(id, 'You don`t have that!\n\n')


def openItemUnlock(items: {},itemsDB: {},id,iid,players: {},mud):
    unlockItemID = itemsDB[items[iid]['id']]['lockedWithItem']
    if unlockItemID > 0:
        keyFound = False
        for i in list(players[id]['inv']):
            if int(i) == unlockItemID:
                keyFound = True
                break
        if keyFound:
            mud.send_message(
                id,
                'You use ' +
                itemsDB[unlockItemID]['article'] +
                ' ' +
                itemsDB[unlockItemID]['name'])
        else:
            if len(itemsDB[unlockItemID]['open_failed_description']) > 0:
                mud.send_message(
                    id, itemsDB[unlockItemID]['open_failed_description'] + ".\n\n")
            else:
                if itemsDB[unlockItemID]['state'].startswith('lever '):
                    mud.send_message(id, "It's operated with a lever.\n\n")
                else:                    
                    if randint(0, 1) == 1:
                        mud.send_message(
                            id,
                            "You don't have " +
                            itemsDB[unlockItemID]['article'] +
                            " " +
                            itemsDB[unlockItemID]['name'] +
                            ".\n\n")
                    else:
                        mud.send_message(
                            id,
                            "Looks like you need " +
                            itemsDB[unlockItemID]['article'] +
                            " " +
                            itemsDB[unlockItemID]['name'] +
                            " for this.\n\n")
            return False
    return True


def describeContainerContents(mud,id,itemsDB: {},itemID: {},returnMsg):
    if not itemsDB[itemID]['state'].startswith('container open'):
        if returnMsg:
            return ''
        else:
            return
    containsList=itemsDB[itemID]['contains']
    noOfItems = len(containsList)
    containerMsg = '<f15>You see '

    if noOfItems == 0:
        if 'open always' not in itemsDB[itemID]['state']:
            mud.send_message(id, containerMsg + 'nothing.\n')
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
            ' <b234><f220>' + itemsDB[int(contentsID)]['name'] + '<r>'
        itemCtr += 1

    containerMsg = containerMsg + '.\n'
    if returnMsg:
        containerMsg = '\n' + containerMsg
        return containerMsg
    else:
        mud.send_message_wrap(id,'<f220>',containerMsg + '\n')


def openItemContainer(params,mud,playersDB: {},players: {},rooms: {}, \
                      npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                      envDB: {},env: {},eventDB: {},eventSchedule, \
                      id: int,fights: {},corpses: {},target,
                      itemsInWorldCopy: {},iid):
    if not openItemUnlock(items,itemsDB,id,iid,players,mud):
        return

    itemID = items[iid]['id']
    if itemsDB[itemID]['state'].startswith('container open'):
        mud.send_message(id, "It's already open\n\n")
        return

    itemsDB[itemID]['state'] = itemsDB[itemID]['state'].replace('closed', 'open')
    itemsDB[itemID]['short_description'] = \
        itemsDB[itemID]['short_description'].replace('closed', 'open')
    itemsDB[itemID]['long_description'] = \
        itemsDB[itemID]['long_description'].replace('closed', 'open')
    itemsDB[itemID]['long_description'] = \
        itemsDB[itemID]['long_description'].replace('shut', 'open')

    if len(itemsDB[itemID]['open_description']) > 0:
        mud.send_message(id, itemsDB[itemID]['open_description'] + '\n\n')
    else:
        itemArticle=itemsDB[itemID]['article']
        if itemArticle=='a':
            itemArticle='the'
        mud.send_message(id, 'You open '+itemArticle+ \
                         ' '+itemsDB[itemID]['name'] + '.\n\n')
    describeContainerContents(mud,id,itemsDB,itemID,False)

def leverUp(params,mud,playersDB: {},players: {},rooms: {}, \
            npcsDB: {},npcs: {},itemsDB: {},items: {}, \
            envDB: {},env: {},eventDB: {},eventSchedule, \
            id: int,fights: {},corpses: {},target, \
            itemsInWorldCopy: {},iid):
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
            itemsDB[linkedItemID]['short_description'] = \
                itemsDB[linkedItemID]['short_description'].replace('open', 'closed')
            itemsDB[linkedItemID]['long_description'] = \
                itemsDB[linkedItemID]['long_description'].replace('open', 'closed')
            itemsDB[linkedItemID]['state'] = 'closed'
            linkedItemID2 = int(itemsDB[linkedItemID]['linkedItem'])
            if linkedItemID2 > 0:
                itemsDB[linkedItemID2]['short_description'] = \
                    itemsDB[linkedItemID2]['short_description'].replace('open', 'closed')
                itemsDB[linkedItemID2]['long_description'] = \
                    itemsDB[linkedItemID2]['long_description'].replace('open', 'closed')
                itemsDB[linkedItemID2]['state'] = 'closed'

        if len(roomID) > 0:
            rm = players[id]['room']
            if exitName[0] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[0]]

            rm = roomID
            if exitName[1] in rooms[rm]['exits']:
                del rooms[rm]['exits'][exitName[1]]

    if len(itemsDB[itemID]['close_description']) > 0:
        mud.send_message_wrap(id,'<f220>', \
                              itemsDB[itemID]['close_description'] + '\n\n')
    else:
        mud.send_message(
            id,
            'You push ' +
            itemsDB[itemID]['article'] +
            ' ' +
            itemsDB[itemID]['name'] +
            '\n\n')
    
def leverDown(params,mud,playersDB: {},players: {},rooms: {}, \
              npcsDB: {},npcs: {},itemsDB: {},items: {}, \
              envDB: {},env: {},eventDB: {},eventSchedule, \
              id: int,fights: {},corpses: {},target, \
              itemsInWorldCopy: {},iid):
    if not openItemUnlock(items,itemsDB,id,iid,players,mud):
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
            itemsDB[linkedItemID]['short_description'] = \
                itemsDB[linkedItemID]['short_description'].replace('closed', 'open')
            itemsDB[linkedItemID]['long_description'] = \
                itemsDB[linkedItemID]['long_description'].replace('closed', 'open')
            itemsDB[linkedItemID]['state'] = 'open'
            linkedItemID2 = int(itemsDB[linkedItemID]['linkedItem'])
            if linkedItemID2 > 0:
                itemsDB[linkedItemID2]['short_description'] = \
                    itemsDB[linkedItemID2]['short_description'].replace('closed', 'open')
                itemsDB[linkedItemID2]['long_description'] = \
                    itemsDB[linkedItemID2]['long_description'].replace('closed', 'open')
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
        mud.send_message_wrap(id,'<f220>', \
                              itemsDB[itemID]['open_description'] + '\n\n')
    else:
        mud.send_message(
            id,
            'You pull ' +
            itemsDB[itemID]['article'] +
            ' ' +
            itemsDB[itemID]['name'] +
            '\n\n')

def openItemDoor(params,mud,playersDB: {},players: {},rooms: {}, \
                 npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                 envDB: {},env: {},eventDB: {},eventSchedule, \
                 id: int,fights: {},corpses: {},target, \
                 itemsInWorldCopy: {},iid):
    if not openItemUnlock(items, itemsDB, id, iid, players, mud):
        return

    itemID = items[iid]['id']
    linkedItemID = int(itemsDB[itemID]['linkedItem'])
    roomID = itemsDB[itemID]['exit']
    if '|' in itemsDB[itemID]['exitName']:
        exitName = itemsDB[itemID]['exitName'].split('|')

        itemsDB[itemID]['state'] = 'open'
        itemsDB[itemID]['short_description'] = \
            itemsDB[itemID]['short_description'].replace('closed', 'open').replace('drawn up', 'drawn down')
        itemsDB[itemID]['long_description'] = \
            itemsDB[itemID]['long_description'].replace('closed', 'open').replace('drawn up', 'drawn down')

        if linkedItemID > 0:
            itemsDB[linkedItemID]['short_description'] = \
                itemsDB[linkedItemID]['short_description'].replace('closed', 'open').replace('drawn up', 'drawn down')
            itemsDB[linkedItemID]['long_description'] = \
                itemsDB[linkedItemID]['long_description'].replace('closed', 'open').replace('drawn up', 'drawn down')
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
        mud.send_message(id, itemsDB[itemID]['open_description'] + '\n\n')
    else:
        mud.send_message(
            id,
            'You open ' +
            itemsDB[itemID]['article'] +
            ' ' +
            itemsDB[itemID]['name'] +
            '\n\n')

def openItem(params,mud,playersDB: {},players: {},rooms: {}, \
             npcsDB: {},npcs: {},itemsDB: {},items: {}, \
             envDB: {},env: {},eventDB: {},eventSchedule, \
             id: int,fights: {},corpses: {},blocklist, \
             mapArea: [],characterClassDB: {},spellsDB: {}, \
             sentimentDB: {},guildsDB: {},clouds: {}):
    target = params.lower()

    if target.startswith('registration'):
        enableRegistrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if itemsDB[items[iid]['id']]['state'] == 'closed':
                    openItemDoor(params,mud,playersDB,players,rooms, \
                                 npcsDB,npcs,itemsDB,items,envDB,env, \
                                 eventDB,eventSchedule,id,fights, \
                                 corpses,target,itemsInWorldCopy, \
                                 iid)
                    return
                if itemsDB[items[iid]['id']]['state'].startswith('container closed'):
                    openItemContainer(params,mud,playersDB,players, \
                                      rooms,npcsDB,npcs,itemsDB, \
                                      items,envDB,env,eventDB, \
                                      eventSchedule,id,fights,corpses, \
                                      target,itemsInWorldCopy,iid)
                    return
    mud.send_message(id, "You can't open it.\n\n")

def pullLever(params,mud,playersDB: {},players: {},rooms: {}, \
              npcsDB: {},npcs: {},itemsDB: {},items: {}, \
              envDB: {},env: {},eventDB: {},eventSchedule, \
              id: int,fights: {},corpses: {},blocklist: {}, \
              mapArea: [],characterClassDB: {},spellsDB: {}, \
              sentimentDB: {},guildsDB: {},clouds: {}):
    target = params.lower()

    if target.startswith('registration'):
        enableRegistrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if itemsDB[items[iid]['id']]['state'] == 'lever up':
                    leverDown(params,mud,playersDB,players,rooms, \
                              npcsDB,npcs,itemsDB,items,envDB, \
                              env,eventDB,eventSchedule,id,fights, \
                              corpses,target,itemsInWorldCopy,iid)
                    return
                else:
                    mud.send_message(id, 'Nothing happens.\n\n')
                    return
    mud.send_message(id, "There's nothing to pull.\n\n")

def pushLever(params,mud,playersDB: {},players: {},rooms: {}, \
              npcsDB: {},npcs: {},itemsDB: {},items: {}, \
              envDB: {},env: {},eventDB: {},eventSchedule, \
              id: int,fights: {},corpses: {},blocklist, \
              mapArea: [],characterClassDB: {},spellsDB: {}, \
              sentimentDB: {},guildsDB: {},clouds: {}):
    target = params.lower()
    if target.startswith('the '):
        target=target.replace('the ','')

    if target.startswith('registration'):
        enableRegistrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if not itemsDB[items[iid]['id']]['state']:
                    heave(params,mud,playersDB,players,rooms, \
                          npcsDB,npcs,itemsDB,items,envDB,env, \
                          eventDB,eventSchedule,id,fights, \
                          corpses,blocklist,mapArea,characterClassDB, \
                          spellsDB,sentimentDB,guildsDB,clouds)
                    return
                elif itemsDB[items[iid]['id']]['state'] == 'lever down':
                    leverUp(params,mud,playersDB,players,rooms,npcsDB, \
                            npcs,itemsDB,items,envDB,env,eventDB, \
                            eventSchedule,id,fights,corpses,target, \
                            itemsInWorldCopy,iid)
                    return
    mud.send_message(id, 'Nothing happens.\n\n')

def windLever(params,mud,playersDB: {},players: {},rooms: {}, \
              npcsDB: {},npcs: {},itemsDB: {},items: {}, \
              envDB: {},env: {},eventDB: {},eventSchedule, \
              id: int,fights: {},corpses: {},blocklist, \
              mapArea: [],characterClassDB: {},spellsDB: {}, \
              sentimentDB: {},guildsDB: {},clouds: {}):
    target = params.lower()

    if target.startswith('registration'):
        enableRegistrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if itemsDB[items[iid]['id']]['state'] == 'lever up':
                    leverDown(params,mud,playersDB,players,rooms, \
                              npcsDB,npcs,itemsDB,items,envDB, \
                              env,eventDB,eventSchedule,id, \
                              fights,corpses,target, \
                              itemsInWorldCopy,iid)
                    return
                else:
                    mud.send_message(id, "It's wound all the way.\n\n")
                    return
    mud.send_message(id, "There's nothing to wind.\n\n")

def unwindLever(params,mud,playersDB: {},players: {},rooms: {}, \
                npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                envDB: {},env: {},eventDB: {},eventSchedule, \
                id: int,fights: {},corpses: {},blocklist, \
                mapArea: [],characterClassDB: {},spellsDB: {}, \
                sentimentDB: {},guildsDB: {},clouds: {}):
    target = params.lower()

    if target.startswith('registration'):
        enableRegistrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if itemsDB[items[iid]['id']]['state'] == 'lever down':
                    leverUp(params,mud,playersDB,players,rooms, \
                            npcsDB,npcs,itemsDB,items,envDB,env, \
                            eventDB,eventSchedule,id,fights, \
                            corpses,target,itemsInWorldCopy,iid)
                    return
                else:
                    mud.send_message(id, "It's unwound all the way.\n\n")
                    return
    mud.send_message(id, "There's nothing to unwind.\n\n")

def closeItemContainer(params,mud,playersDB: {},players: {},rooms: {}, \
                       npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                       envDB: {},env: {},eventDB: {},eventSchedule, \
                       id: int,fights: {},corpses: {},target, \
                       itemsInWorldCopy: {},iid):
    itemID = items[iid]['id']
    if itemsDB[itemID]['state'].startswith('container closed'):
        mud.send_message(id, "It's already closed\n\n")
        return

    if itemsDB[itemID]['state'].startswith('container open '):
        mud.send_message(id, "That's not possible.\n\n")
        return

    itemsDB[itemID]['state'] = itemsDB[itemID]['state'].replace(
        'open', 'closed')
    itemsDB[itemID]['short_description'] = itemsDB[itemID]['short_description'].replace(
        'open', 'closed')
    itemsDB[itemID]['long_description'] = itemsDB[itemID]['long_description'].replace(
        'open', 'closed')

    if len(itemsDB[itemID]['close_description']) > 0:
        mud.send_message(id, itemsDB[itemID]['close_description'] + '\n\n')
    else:
        itemArticle=itemsDB[itemID]['article']
        if itemArticle=='a':
            itemArticle='the'
        mud.send_message(id,'You close '+itemArticle+ \
                         ' '+itemsDB[itemID]['name']+'.\n\n')

def closeItemDoor(params,mud,playersDB: {},players: {},rooms: {}, \
                  npcsDB: {},npcs: {},itemsDB: {},items: {}, \
                  envDB: {},env: {},eventDB: {},eventSchedule, \
                  id: int,fights: {},corpses: {},target, \
                  itemsInWorldCopy: {},iid):
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
        itemsDB[linkedItemID]['short_description'] = \
            itemsDB[linkedItemID]['short_description'].replace('open', 'closed').replace('drawn down', 'drawn up')
        itemsDB[linkedItemID]['long_description'] = \
            itemsDB[linkedItemID]['long_description'].replace('open', 'closed').replace('drawn down', 'drawn up')
        itemsDB[linkedItemID]['state'] = 'closed'

    if len(roomID) > 0:
        rm = players[id]['room']
        if exitName[0] in rooms[rm]['exits']:
            del rooms[rm]['exits'][exitName[0]]

        rm = roomID
        if exitName[1] in rooms[rm]['exits']:
            del rooms[rm]['exits'][exitName[1]]

    if len(itemsDB[itemID]['close_description']) > 0:
        mud.send_message(id, itemsDB[itemID]['close_description'] + '\n\n')
    else:
        mud.send_message(id,'You close '+ \
                         itemsDB[itemID]['article']+' '+ \
                         itemsDB[itemID]['name']+'\n\n')


def closeItem(params,mud,playersDB: {},players: {},rooms: {}, \
              npcsDB: {},npcs: {},itemsDB: {},items: {}, \
              envDB: {},env: {},eventDB: {},eventSchedule, \
              id: int,fights: {},corpses: {},blocklist, \
              mapArea: [],characterClassDB: {},spellsDB: {}, \
              sentimentDB: {},guildsDB: {},clouds: {}):
    target = params.lower()

    if target.startswith('registration'):
        disableRegistrations(mud, id, players)
        return

    itemsInWorldCopy = deepcopy(items)
    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if target in itemsDB[items[iid]['id']]['name'].lower():
                if itemsDB[items[iid]['id']]['state'] == 'open':
                    closeItemDoor(params,mud,playersDB,players, \
                                  rooms,npcsDB,npcs,itemsDB, \
                                  items,envDB,env,eventDB, \
                                  eventSchedule,id,fights, \
                                  corpses,target,itemsInWorldCopy, \
                                  iid)
                    return
                if itemsDB[items[iid]['id']]['state'].startswith(
                        'container open'):
                    closeItemContainer(params,mud,playersDB,players, \
                                       rooms,npcsDB,npcs,itemsDB, \
                                       items,envDB,env,eventDB, \
                                       eventSchedule,id,fights, \
                                       corpses,target,itemsInWorldCopy, \
                                       iid)
                    return
    mud.send_message(id, "You can't close it.\n\n")

def putItem(params,mud,playersDB: {},players: {},rooms: {}, \
            npcsDB: {},npcs: {},itemsDB: {},items: {}, \
            envDB: {},env: {},eventDB: {},eventSchedule, \
            id: int,fights: {},corpses: {},blocklist, \
            mapArea: {},characterClassDB: {},spellsDB: {}, \
            sentimentDB: {},guildsDB: {},clouds: {}):
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
        mud.send_message(id, "You don't have " + itemName + ".\n\n")
        return

    itemsInWorldCopy = deepcopy(items)

    for (iid, pl) in list(itemsInWorldCopy.items()):
        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
            if containerName.lower(
            ) in itemsDB[items[iid]['id']]['name'].lower():
                if itemsDB[items[iid]['id']]['state'].startswith(
                        'container open'):
                    if ' noput' not in itemsDB[items[iid]['id']]['state']:
                        maxItemsInContainer=itemsDB[items[iid]['id']]['useTimes']
                        if maxItemsInContainer==0 or \
                           len(itemsDB[items[iid]['id']]['contains'])<maxItemsInContainer:
                            players[id]['inv'].remove(str(itemID))
                            removeItemFromClothing(players, id, itemID)
                            itemsDB[items[iid]['id']]['contains'].append(str(itemID))
                            mud.send_message(id, 'You put ' +
                                             itemsDB[itemID]['article'] +
                                             ' ' +
                                             itemsDB[itemID]['name'] +
                                             inon +
                                             itemsDB[items[iid]['id']]['article'] +
                                             ' ' +
                                             itemsDB[items[iid]['id']]['name'] +
                                             '.\n\n')
                        else:
                            mud.send_message(
                                id, 'No more items can be put ' + inon + ' ' + \
                                itemsDB[items[iid]['id']]['article'] + ' ' + \
                                itemsDB[items[iid]['id']]['name'] + ".\n\n")                            
                    else:
                        if 'on' in inon:
                            mud.send_message(
                                id, "You can't put anything on that.\n\n")
                        else:
                            mud.send_message(
                                id, "You can't put anything in that.\n\n")
                    return
                else:
                    if itemsDB[items[iid]['id']]['state'].startswith(
                            'container closed'):
                        if 'on' in inon:
                            mud.send_message(id, "You can't.\n\n")
                        else:
                            mud.send_message(id, "It's closed.\n\n")
                        return
                    else:
                        if 'on' in inon:
                            mud.send_message(
                                id, "You can't put anything on that.\n\n")
                        else:
                            mud.send_message(
                                id, "It can't contain anything.\n\n")
                        return

    mud.send_message(id, "You don't see " + containerName + ".\n\n")


def take(params,mud,playersDB: {},players: {},rooms: {}, \
         npcsDB: {},npcs: {},itemsDB: {},items: {}, \
         envDB: {},env: {},eventDB: {},eventSchedule, \
         id: int,fights: {},corpses: {},blocklist, \
         mapArea: [],characterClassDB: {},spellsDB: {}, \
         sentimentDB: {},guildsDB: {},clouds: {}):
    if players[id]['frozenStart'] != 0:
        mud.send_message(
            id, randomDescription(
                players[id]['frozenDescription']) + '\n\n')
        return

    if params:
        # get into, get through
        if params.startswith('into') or params.startswith('through'):
            climb(params,mud,playersDB,players,rooms,npcsDB,npcs, \
                  itemsDB,items,envDB,env,eventDB,eventSchedule, \
                  id,fights,corpses,blocklist,mapArea,characterClassDB, \
                  spellsDB,sentimentDB,guildsDB,clouds)
            return

    if len(str(params)) < 3:
        return

    if itemInInventory(players, id, str(params), itemsDB):
        mud.send_message(id, 'You are already carring ' + str(params) + '\n\n')
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
                mud.send_message_wrap(id,'<f220>', \
                                      randomDescription(itemsDB[iid2]['takeFail'])+ \
                                      "\n\n")
            else:
                mud.send_message(id,"You can't pick that up.\n\n")
            return
        if itemIsVisible(id,players,iid2,itemsDB):                
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
            itemIndex=itemsInWorldCopy[iid]['id']
            if target not in itemsDB[itemIndex]['name'].lower():
                continue
            if int(itemsDB[itemIndex]['weight']) == 0:
                if itemsDB[itemIndex].get('takeFail'):
                    mud.send_message_wrap(id,'<f220>', \
                                          randomDescription(itemsDB[itemIndex]['takeFail'])+ \
                                          "\n\n")
                else:
                    mud.send_message(id, "You can't pick that up.\n\n")
                return

            itemName = itemsDB[itemIndex]['name']
            if itemInInventory(players,id,itemName,itemsDB):
                mud.send_message(
                    id, 'You are already carring ' + itemName + '\n\n')
                return
            if itemIsVisible(id,players,itemIndex,itemsDB):
                # ID of the item to be picked up
                itemInDB = True
            break

    if itemInDB and itemIndex:
        for (iid, pl) in list(itemsInWorldCopy.items()):
            # item in same room as player
            if itemsInWorldCopy[iid]['room'] != players[id]['room']:
                continue
            itemIndex=itemsInWorldCopy[iid]['id']
            # item has the expected name
            if itemsDB[itemIndex]['name'] != itemName:
                continue
            # player can move
            if players[id]['canGo'] != 0:
                # is the item too heavy?
                players[id]['wei'] = \
                    playerInventoryWeight(id, players, itemsDB)

                if players[id]['wei'] + \
                    itemsDB[itemIndex]['weight'] > maxWeight:
                    mud.send_message(id, "You can't carry any more.\n\n")
                    return

                # is the player restricted by a trap
                if playerIsTrapped(id,players,rooms):
                    mud.send_message(
                        id, randomDescription("You're trapped|" + \
                            "The trap restricts your ability to take anything|" + \
                            "The trap restricts your movement") + '.\n\n')
                    return

                # add the item to the player's inventory
                players[id]['inv'].append(str(itemIndex))
                # update the weight of the player
                players[id]['wei'] = playerInventoryWeight(id,players,itemsDB)
                updatePlayerAttributes(id,players,itemsDB,itemIndex,1)
                # remove the item from the dict
                del items[iid]
                itemPickedUp = True
                break
            else:
                mud.send_message(id,'You try to pick up ' + itemName + \
                                 " but find that your arms won't move.\n\n")
                return

    if itemPickedUp:
        mud.send_message(id,'You pick up and place ' + \
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
            itemIndex=itemsInWorldCopy[iid]['id']
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
                        mud.send_message_wrap(id,'<f220>', \
                                              randomDescription(itemsDB[int(containerItemID)]['takeFail'])+ \
                                              "\n\n")
                    else:
                        mud.send_message(id,"You can't pick that up.\n\n")
                    return
                else:
                    # can the player move?
                    if players[id]['canGo'] != 0:
                        # is the item too heavy?
                        carryingWeight = \
                            playerInventoryWeight(id,players,itemsDB)
                        if carryingWeight + \
                                itemsDB[int(containerItemID)]['weight'] > maxWeight:
                            mud.send_message(id,"You can't carry any more.\n\n")
                            return

                        # add the item to the player's inventory
                        players[id]['inv'].append(containerItemID)
                        # remove the item from the container
                        itemsDB[itemIndex]['contains'].remove(containerItemID)
                        mud.send_message(id, 'You take ' + \
                                         itemsDB[int(containerItemID)]['article'] + \
                                         ' ' + \
                                         itemsDB[int(containerItemID)]['name'] + \
                                         ' from ' + \
                                         itemsDB[itemIndex]['article'] + \
                                         ' ' + \
                                         itemsDB[itemIndex]['name'] + \
                                         '.\n\n')
                    else:
                        mud.send_message(id, 'You try to pick up ' + \
                                         itemsDB[int(containerItemID)]['article'] + \
                                         ' ' + \
                                         itemsDB[int(containerItemID)]['name'] + \
                                         " but find that your arms won't move.\n\n")
                    return

        mud.send_message(id,'You cannot see '+target+' anywhere.\n\n')
        itemPickedUp = False


def runCommand(command,params,mud,playersDB: {},players: {},rooms: {}, \
               npcsDB: {},npcs: {},itemsDB: {},items: {}, \
               envDB: {},env: {},eventDB: {},eventSchedule, \
               id: int,fights: {},corpses: {},blocklist, \
               mapArea: [],characterClassDB: {},spellsDB: {}, \
               sentimentDB: {},guildsDB: {},clouds: {}):
    switcher = {
        "sendCommandError": sendCommandError,
        "go": go,
        "north": goNorth,
        "n": goNorth,
        "south": goSouth,
        "s": goSouth,
        "east": goEast,
        "e": goEast,
        "west": goWest,
        "w": goWest,
        "up": goUp,
        "u": goUp,
        "down": goDown,
        "d": goDown,
        "in": goIn,
        "out": goOut,
        "o": goOut,
        "bio": bio,
        "who": who,
        "quit": quit,
        "exit": quit,
        "look": look,
        "read": look,
        "l": look,
        "examine": look,
        "ex": look,
        "help": help,
        "say": say,
        "attack": attack,
        "shoot": attack,
        "take": take,
        "get": take,
        "put": putItem,
        "drop": drop,
        "check": check,
        "wear": wear,
        "don": wear,
        "unwear": unwear,
        "remove": unwear,
        "use": wield,
        "hold": wield,
        "pick": wield,
        "wield": wield,
        "brandish": wield,
        "stow": stow,
        "step": stepOver,
        "whisper": whisper,
        "teleport": teleport,
        "summon": summon,
        "mute": mute,
        "silence": mute,
        "unmute": unmute,
        "unsilence": unmute,
        "freeze": freeze,
        "unfreeze": unfreeze,
        "tell": tell,
        "command": tell,
        "instruct": tell,
        "order": tell,
        "ask": tell,
        "open": openItem,
        "close": closeItem,
        "wind": windLever,
        "unwind": unwindLever,
        "pull": pullLever,
        "yank": pullLever,
        "push": pushLever,
        "write": writeOnItem,
        "tag": writeOnItem,
        "eat": eat,
        "drink": eat,
        "kick": kick,
        "remove": kick,
        "change": changeSetting,
        "blocklist": showBlocklist,
        "block": block,
        "unblock": unblock,
        "describe": describe,
        "desc": describe,
        "description": describe,
        "conjure": conjure,
        "make": conjure,
        "cancel": destroy,
        "banish": destroy,
        "speak": speak,
        "talk": speak,
        "learn": prepareSpell,
        "prepare": prepareSpell,
        "destroy": destroy,
        "cast": castSpell,
        "spell": castSpell,
        "spells": spells,
        "dismiss": dismiss,
        "clear": clearSpells,
        "spellbook": spells,
        "affinity": affinity,
        "escape": escapeTrap,
        "cut": escapeTrap,
        "slash": escapeTrap,
        "resetuniverse": resetUniverse,
        "shutdown": shutdown,
        "inv": checkInventory,
        "i": checkInventory,
        "inventory": checkInventory,
        "squeeze": climb,
        "clamber": climb,
        "board": climb,
        "roll": heave,
        "heave": heave,
        "move": heave,
        "haul": heave,
        "heave": heave,
        "displace": heave,
        "disembark": climb,
        "climb": climb,
        "cross": climb,
        "traverse": climb,
        "jump": jump,
        "images": graphics,
        "pictures": graphics,
        "graphics": graphics,
        "chess": chess,
        "cards": helpCards,
        "deal": deal,
        "hand": handOfCards,
        "swap": swapACard,
        "shuffle": shuffle,
        "call": callCardGame,
        "morris": morrisGame
    }

    try:
        switcher[command](params,mud,playersDB,players,rooms,npcsDB, \
                          npcs,itemsDB,items,envDB,env,eventDB, \
                          eventSchedule,id,fights,corpses,blocklist, \
                          mapArea,characterClassDB,spellsDB, \
                          sentimentDB,guildsDB,clouds)
    except Exception as e:
        # print(str(e))
        switcher["sendCommandError"](e,mud,playersDB,players,rooms, \
                                     npcsDB,npcs,itemsDB,items, \
                                     envDB,env,eventDB,eventSchedule, \
                                     id,fights,corpses,blocklist, \
                                     mapArea,characterClassDB,spellsDB, \
                                     sentimentDB,guildsDB,clouds)
