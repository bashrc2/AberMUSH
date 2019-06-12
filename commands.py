__filename__ = "commands.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

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
from functions import getSentiment
from environment import runTide
from environment import assignCoordinates

from proficiencies import thievesCant

from npcs import npcConversation

import os
import re
import sys
from copy import deepcopy
import time
import datetime
import os.path
import commentjson
from random import randint

'''
Command function template:

def commandname(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        print("I'm in!")
'''

# maximum weight of items which can be carried
maxWeight = 100

def removeItemFromClothing(players,id,itemID):
        clothingLocation = ('clo_head','clo_neck','clo_chest','clo_feet','clo_larm','clo_rarm','clo_lleg','clo_rleg','clo_lhand','clo_rhand','clo_lwrist','clo_rwrist')
        for c in clothingLocation:
                if int(players[id][c]) == itemID:
                        players[id][c] = 0

def sendCommandError(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        mud.send_message(id, "Unknown command " + str(params) + "!\n")

def isWitch(id, players):
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

def disableRegistrations(mud, id, players):
        if not isWitch(id,players):
                mud.send_message(id, "You don't have enough powers.\n\n")
                return
        if os.path.isfile(".disableRegistrations"):
                mud.send_message(id, "New registrations are already closed.\n\n")
                return
        with open(".disableRegistrations", 'w') as fp:
                fp.write('')
        mud.send_message(id, "New player registrations are now closed.\n\n")

def enableRegistrations(mud, id, players):
        if not isWitch(id,players):
                mud.send_message(id, "You don't have enough powers.\n\n")
                return
        if not os.path.isfile(".disableRegistrations"):
                mud.send_message(id, "New registrations are already allowed.\n\n")
                return
        os.remove(".disableRegistrations")
        mud.send_message(id, "New player registrations are now permitted.\n\n")

def teleport(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['permissionLevel'] == 0:
            if isWitch(id,players):
                targetLocation = params[0:].strip().lower().replace('to the ', '').replace('to ', '')
                if len(targetLocation) != 0:
                    currRoom=players[id]['room']
                    if rooms[currRoom]['name'].strip().lower() == targetLocation:
                        mud.send_message(id, "You are already in " + rooms[currRoom]['name'] + "\n\n")
                        return
                    for rm in rooms:
                        if rooms[rm]['name'].strip().lower() == targetLocation:
                            mud.send_message(id, "You teleport to " + rooms[rm]['name'] + "\n\n")
                            messageToPlayersInRoom(mud,players,id,'<f32>{}<r> suddenly vanishes.'.format(players[id]['name']) + "\n\n")
                            players[id]['room'] = rm
                            messageToPlayersInRoom(mud,players,id,'<f32>{}<r> suddenly appears.'.format(players[id]['name']) + "\n\n")
                            return
            else:
                mud.send_message(id, "You don't have enough powers for that.\n\n")

def summon(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['permissionLevel'] == 0:
            if isWitch(id,players):
                targetPlayer = params[0:].strip().lower()
                if len(targetPlayer) != 0:
                    for p in players:
                        if players[p]['name'].strip().lower() == targetPlayer:
                            if players[p]['room'] != players[id]['room']:
                                messageToPlayersInRoom(mud,players,p,'<f32>{}<r> suddenly vanishes.'.format(players[p]['name']) + "\n")
                                players[p]['room'] = players[id]['room']
                                rm = players[p]['room']
                                mud.send_message(id, "You summon " + players[p]['name'] + "\n\n")
                                mud.send_message(p, "A mist surrounds you. When it clears you find that you are now in " + rooms[rm]['name'] + "\n\n")
                            else:
                                mud.send_message(id, players[p]['name'] + " is already here.\n\n")
                            return
            else:
                mud.send_message(id, "You don't have enough powers for that.\n\n")

def mute(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['permissionLevel'] == 0:
            if isWitch(id,players):
                target = params.partition(' ')[0]
                if len(target) != 0:
                    for p in players:
                        if players[p]['name'] == target:
                            if not isWitch(p,players):
                                players[p]['canSay'] = 0
                                players[p]['canAttack'] = 0
                                players[p]['canDirectMessage'] = 0
                                mud.send_message(id, "You have muted " + target + "\n\n")
                            else:
                                mud.send_message(id, "You try to mute " + target + " but their power is too strong.\n\n")
                            return

def unmute(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['permissionLevel'] == 0:
            if isWitch(id,players):
                target = params.partition(' ')[0]
                if len(target) != 0:
                    if target.lower() != 'guest':
                        for p in players:
                            if players[p]['name'] == target:
                                if not isWitch(p,players):
                                    players[p]['canSay'] = 1
                                    players[p]['canAttack'] = 1
                                    players[p]['canDirectMessage'] = 1
                                    mud.send_message(id, "You have unmuted " + target + "\n\n")
                                return

def freeze(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['permissionLevel'] == 0:
            if isWitch(id,players):
                target = params.partition(' ')[0]
                if len(target) != 0:
                    for p in players:
                        if players[p]['name'] == target:
                            if not isWitch(p,players):
                                players[p]['canGo'] = 0
                                players[p]['canAttack'] = 0
                                mud.send_message(id, "You have frozen " + target + "\n\n")
                            else:
                                mud.send_message(id, "You try to freeze " + target + " but their power is too strong.\n\n")
                            return

def unfreeze(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['permissionLevel'] == 0:
            if isWitch(id,players):
                target = params.partition(' ')[0]
                if len(target) != 0:
                    if target.lower() != 'guest':
                        for p in players:
                            if players[p]['name'] == target:
                                if not isWitch(p,players):
                                    players[p]['canGo'] = 1
                                    players[p]['canAttack'] = 1
                                    mud.send_message(id, "You have unfrozen " + target + "\n\n")
                                return

def showBlocklist(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if not isWitch(id,players):
                mud.send_message(id, "You don't have sufficient powers to do that.\n")
                return

        blocklist.sort()
        
        blockStr=''
        for blockedstr in blocklist:
                blockStr = blockStr + blockedstr + '\n'
                
        mud.send_message(id, "Blocked strings are:\n\n" + blockStr + '\n')
                        
def block(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if not isWitch(id,players):
                mud.send_message(id, "You don't have sufficient powers to do that.\n")
                return

        if len(params)==0:
                showBlocklist(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)
                return

        blockedstr=params.lower().strip().replace('"','')

        if blockedstr.startswith('the word '):
                blockedstr = blockedstr.replace('the word ','')
        if blockedstr.startswith('word '):
                blockedstr = blockedstr.replace('word ','')
        if blockedstr.startswith('the phrase '):
                blockedstr = blockedstr.replace('the phrase ','')
        if blockedstr.startswith('phrase '):
                blockedstr = blockedstr.replace('phrase ','')

        if blockedstr not in blocklist:
                blocklist.append(blockedstr)
                saveBlocklist("blocked.txt",blocklist)
                mud.send_message(id, "Blocklist updated.\n\n")
        else:
                mud.send_message(id, "That's already in the blocklist.\n")

def unblock(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if not isWitch(id,players):
                mud.send_message(id, "You don't have sufficient powers to do that.\n")
                return

        if len(params)==0:
                showBlocklist(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)
                return

        unblockedstr=params.lower().strip().replace('"','')

        if unblockedstr.startswith('the word '):
                unblockedstr = unblockedstr.replace('the word ','')
        if unblockedstr.startswith('word '):
                unblockedstr = unblockedstr.replace('word ','')
        if unblockedstr.startswith('the phrase '):
                unblockedstr = unblockedstr.replace('the phrase ','')
        if unblockedstr.startswith('phrase '):
                unblockedstr = unblockedstr.replace('phrase ','')

        if unblockedstr in blocklist:
                blocklist.remove(unblockedstr)
                saveBlocklist("blocked.txt",blocklist)
                mud.send_message(id, "Blocklist updated.\n\n")
        else:
                mud.send_message(id, "That's not in the blocklist.\n")

def kick(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if not isWitch(id,players):
                return
        
        playerName=params

        if len(playerName)==0:
                return

        for (pid, pl) in list(players.items()):
                if players[pid]['name'] == playerName:
                        mud.send_message(id, "Removing player " + playerName + "\n\n")
                        mud._handle_disconnect(pid)
                        break
                
def shutdown(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if not isWitch(id,players):
                mud.send_message(id, "You don't have enough power to do that.\n\n")
                return
        
        mud.send_message(id, "\n\nShutdown commenced.\n\n")
        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
        mud.send_message(id, "\n\nUniverse saved.\n\n")
        log("Universe saved", "info")
        for (pid, pl) in list(players.items()):
                mud.send_message(pid, "Game server shutting down...\n\n")
                mud._handle_disconnect(pid)
        log("Shutting down", "info")
        sys.exit()

def resetUniverse(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if not isWitch(id,players):
                mud.send_message(id, "You don't have enough power to do that.\n\n")
                return
        os.system('rm universe*.json')
        log('Universe reset', 'info')
        for (pid, pl) in list(players.items()):
                mud.send_message(pid, "Game server shutting down...\n\n")
                mud._handle_disconnect(pid)
        log("Shutting down", "info")
        sys.exit()
        
def quit(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        mud._handle_disconnect(id)

def who(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        counter = 1
        if players[id]['permissionLevel'] == 0:
                is_witch = isWitch(id,players)
                for p in players:
                        if players[p]['name'] == None:
                                name = "None"
                        else:
                            if not is_witch:
                                name = players[p]['name']
                            else:
                                if not isWitch(p,players):
                                    if players[p]['canSay'] == 1:
                                        name = players[p]['name']
                                    else:
                                        name = players[p]['name'] + " (muted)"
                                else:
                                    name = "<f32>" + players[p]['name'] + "<r>"

                        if players[p]['room'] == None:
                                room = "None"
                        else:
                                rm = rooms[players[p]['room']]
                                room = "<f230>" + rm['name']

                        mud.send_message(id, str(counter) + ". " + name + " is in " + room)
                        counter += 1
                mud.send_message(id, "\n")
        else:
                mud.send_message(id, "You do not have permission to do this.\n")
                
def tell(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea, characterClassDB,spellsDB,sentimentDB):
        told = False
        target = params.partition(' ')[0]
        message = params.replace(target, "")[1:]
        if len(target) != 0 and len(message) != 0:
                cantStr=thievesCant(message)
                for p in players:
                        if players[p]['authenticated'] != None and players[p]['name'].lower() == target.lower():
                                #print("sending a tell")
                                if players[id]['name'].lower() == target.lower():
                                        mud.send_message(id, "It'd be pointless to send a tell message to yourself\n")
                                        told = True
                                        break
                                else:
                                        # don't tell if the string contains a blocked string
                                        selfOnly=False
                                        msglower = message.lower()
                                        for blockedstr in blocklist:
                                                if blockedstr in msglower:
                                                        selfOnly=True
                                                        break
                                        
                                        if not selfOnly:
                                                if players[id]['speakLanguage'] in players[p]['language']:
                                                        addToScheduler("0|msg|<f90>From " + players[id]['name'] + ": " + message + '\n', p, eventSchedule, eventDB)
                                                        if getSentiment(message,sentimentDB)>=0:
                                                                increaseAffinityBetweenPlayers(players,id,players,p)
                                                        else:
                                                                decreaseAffinityBetweenPlayers(players,id,players,p)
                                                else:
                                                        if players[id]['speakLanguage'] != 'cant':
                                                                addToScheduler("0|msg|<f90>From " + players[id]['name'] + ": something in " + players[id]['speakLanguage']+'\n', p, eventSchedule, eventDB)
                                                        else:
                                                                addToScheduler("0|msg|<f90>From " + players[id]['name'] + ": " + cantStr + '\n', p, eventSchedule, eventDB)
                                        mud.send_message(id, "<f90>To " + players[p]['name'] + ": " + message + "\n\n")
                                        told = True
                                        break
                if told == False:
                        for (nid, pl) in list(npcs.items()):
                                if npcs[nid]['room'] == players[id]['room']:
                                        if target.lower() in npcs[nid]['name'].lower():
                                                npcConversation(mud,npcs,players,itemsDB,rooms,id,nid,message.lower(),characterClassDB,sentimentDB)
                                                told = True
                                                break

                if told == False:
                        mud.send_message(id, "<f32>" + target + "<r> does not appear to be reachable at this moment.\n\n")
        else:
                mud.send_message(id, "Huh?\n\n")

def whisper(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        target = params.partition(' ')[0]
        message = params.replace(target, "")
        
        #if message[0] == " ":
                #message.replace(message[0], "")
        messageSent = False
        #print(message)
        #print(str(len(message)))
        if len(target) > 0:
                if len(message) > 0:
                        cantStr=thievesCant(message)
                        for p in players:
                                if players[p]['name'] != None and players[p]['name'].lower() == target.lower():
                                        if players[p]['room'] == players[id]['room']:
                                                if players[p]['name'].lower() != players[id]['name'].lower():

                                                        # don't whisper if the string contains a blocked string
                                                        selfOnly=False
                                                        msglower = message[1:].lower()
                                                        for blockedstr in blocklist:
                                                                if blockedstr in msglower:
                                                                        selfOnly=True
                                                                        break

                                                        if getSentiment(message[1:],sentimentDB)>=0:
                                                                increaseAffinityBetweenPlayers(players,id,players,p)
                                                        else:
                                                                decreaseAffinityBetweenPlayers(players,id,players,p)

                                                        mud.send_message(id, "You whisper to <f32>" + players[p]['name'] + "<r>: " + message[1:] + '\n')
                                                        if not selfOnly:
                                                                if players[id]['speakLanguage'] in players[p]['language']:
                                                                
                                                                        mud.send_message(p, "<f162>" + players[id]['name'] + " whispers: " + message[1:] + '\n')
                                                                else:
                                                                        if players[id]['speakLanguage'] != 'cant':
                                                                                mud.send_message(p, "<f162>" + players[id]['name'] + " whispers something in " + players[id]['speakLanguage'] + '\n')
                                                                        else:
                                                                                mud.send_message(p, "<f162>" + players[id]['name'] + " whispers:  " + cantStr  + '\n')
                                                        messageSent = True
                                                        break
                                                else:
                                                        mud.send_message(id, "You would probably look rather silly whispering to yourself.\n")
                                                        messageSent = True
                                                        break
                        if messageSent == False:
                                mud.send_message(id, "<f32>" + target + "<r> is not here with you.\n")
                else:
                        mud.send_message(id, "What would you like to whisper?\n")
        else:
                mud.send_message(id, "Who would you like to whisper to??\n")

def help(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        mud.send_message(id, 'Commands:')
        mud.send_message(id, '  bio [description]                       - Set a description of yourself')
        mud.send_message(id, '  change password [newpassword]           - Change your password')
        mud.send_message(id, '  who                                     - List players and where they are')
        mud.send_message(id, '  quit/exit                               - Leave the game')
        mud.send_message(id, '  eat/drink [item]                        - Eat or drink a consumable')
        mud.send_message(id, '  speak [language]                        - Switch to speaking a different language')
        mud.send_message(id, '  say [message]                           - Says something out loud, '  + "e.g. 'say Hello'")
        mud.send_message(id, '  look/examine                            - Examines the ' + "surroundings, items in the room, NPCs or other players e.g. 'examine inn-keeper'")
        mud.send_message(id, '  go [exit]                               - Moves through the exit ' + "specified, e.g. 'go outside'")
        mud.send_message(id, '  attack [target]                         - Attack target ' + "specified, e.g. 'attack knight'")
        mud.send_message(id, '  check inventory                         - Check the contents of ' + "your inventory")
        mud.send_message(id, '  take/get [item]                         - Pick up an item lying ' + "on the floor")
        mud.send_message(id, '  put [item] in/on [item]                 - Put an item into or onto another one')
        mud.send_message(id, '  drop [item]                             - Drop an item from your inventory ' + "on the floor")
        mud.send_message(id, '  use/hold/pick/wield [item] [left|right] - Transfer an item to your hands')
        mud.send_message(id, '  stow                                    - Free your hands of items')
        mud.send_message(id, '  wear [item]                             - Wear an item')
        mud.send_message(id, '  remove/unwear [item]                    - Remove a worn item')
        mud.send_message(id, '  whisper [target] [message]              - Whisper to a player in the same room')
        mud.send_message(id, '  tell/ask [target] [message]             - Send a tell message to another player or NPC')
        mud.send_message(id, '  open [item]                             - Open an item or door')
        mud.send_message(id, '  close [item]                            - Close an item or door')
        mud.send_message(id, '  affinity [player name]                  - Shows your affinity level with another player')
        mud.send_message(id, '')
        mud.send_message(id, 'Spell commands:')
        mud.send_message(id, '  prepare spells                          - List spells which can be prepared')
        mud.send_message(id, '  prepare [spell name]                    - Prepares a spell')
        mud.send_message(id, '  spells                                  - Lists your prepared spells')
        mud.send_message(id, '  clear spells                            - Clears your prepared spells list')
        mud.send_message(id, '  cast [spell name] on [target]           - Cast a spell on a player or NPC')
        
        if isWitch(id,players):
                mud.send_message(id, '')
                mud.send_message(id, 'Witch Commands:')
                mud.send_message(id, '  close registrations                     - Closes registrations of new players')
                mud.send_message(id, '  open registrations                      - Allows registrations of new players')
                mud.send_message(id, '  mute/silence [target]                   - Mutes a player and prevents them from attacking')
                mud.send_message(id, '  unmute/unsilence [target]               - Unmutes a player')
                mud.send_message(id, '  freeze [target]                         - Prevents a player from moving or attacking')
                mud.send_message(id, '  unfreeze [target]                       - Allows a player to move or attack')
                mud.send_message(id, '  teleport [room]                         - Teleport to a room')
                mud.send_message(id, '  summon [target]                         - Summons a player to your location')
                mud.send_message(id, '  kick/remove [target]                    - Remove a player from the game')
                mud.send_message(id, '  blocklist                               - Show the current blocklist')
                mud.send_message(id, '  block [word or phrase]                  - Adds a word or phrase to the blocklist')
                mud.send_message(id, '  unblock [word or phrase]                - Removes a word or phrase to the blocklist')
                mud.send_message(id, '  describe "room" "room name"             - Changes the name of the current room')
                mud.send_message(id, '  describe "room description"             - Changes the current room description')
                mud.send_message(id, '  describe "tide" "room description"      - Changes the room description when tide is out')
                mud.send_message(id, '  describe "item" "item description"      - Changes the description of an item in the room')
                mud.send_message(id, '  describe "NPC" "NPC description"        - Changes the description of an NPC in the room')
                mud.send_message(id, '  conjure room [direction]                - Creates a new room in the given direction')
                mud.send_message(id, '  conjure npc [target]                    - Creates a named NPC in the room')
                mud.send_message(id, '  conjure [item]                          - Creates a new item in the room')
                mud.send_message(id, '  destroy room [direction]                - Removes the room in the given direction')
                mud.send_message(id, '  destroy npc [target]                    - Removes a named NPC from the room')
                mud.send_message(id, '  destroy [item]                          - Removes an item from the room')
                mud.send_message(id, '  resetuniverse                           - Resets the universe, losing any changes from defaults')
                mud.send_message(id, '  shutdown                                - Shuts down the game server')
        mud.send_message(id, '\n\n')

def spellTimeToSec(durationStr):
        """Converts a description of a duration such as '1 hour'
           into a number of seconds
        """
        if ' ' not in durationStr:
                return 1
        dur = durationStr.split(' ')
        if dur[1].startswith('min'):
                return int(dur[0])*60
        if dur[1].startswith('hour') or dur[1].startswith('hr'):
                return int(dur[0])*60*60
        if dur[1].startswith('day'):
                return int(dur[0])*60*60*24
        return 1

def removePreparedSpell(players,id,spellName):
        del players[id]['preparedSpells'][spellName]
        del players[id]['spellSlots'][spellName]

def castSpellOnPlayer(mud, spellName, players, id, npcs, p, spellDetails):
        if npcs[p]['room'] != players[id]['room']:
                mud.send_message(id, "They're not here.\n\n")
                return

        if spellDetails['action'].startswith('protect'):
                npcs[p]['tempHitPoints']=spellDetails['hp']
                npcs[p]['tempHitPointsDuration']=spellTimeToSec(spellDetails['duration'])
                npcs[p]['tempHitPointsStart']=int(time.time())

        if spellDetails['action'].startswith('friend'):
                if players[id]['cha'] < npcs[p]['cha']:
                        removePreparedSpell(players,id,spellName)
                        mud.send_message(id, "You don't have enough charisma.\n\n")
                        return
                playerName=players[id]['name']
                if npcs[p]['affinity'].get(playerName):
                        npcs[p]['affinity'][playerName]=npcs[p]['affinity'][playerName]+1
                else:
                        npcs[p]['affinity'][playerName]=1

        if spellDetails['action'].startswith('attack'):
                if len(spellDetails['damageType'])==0 or spellDetails['damageType']=='str':
                        npcs[p]['hp'] = npcs[p]['hp'] - randint(1,spellDetails['damage'])
                else:
                        damageType=spellDetails['damageType']
                        if npcs[p].get(damageType):
                                npcs[p][damageType] = npcs[p][damageType] - randint(1,spellDetails['damage'])
                                if npcs[p][damageType]<0:
                                        npcs[p][damageType]=0
                
        if spellDetails['action'].startswith('frozen'):
                npcs[p]['frozenDescription']=spellDetails['actionDescription']
                npcs[p]['frozenDuration']=spellTimeToSec(spellDetails['duration'])
                npcs[p]['frozenStart']=int(time.time())

        mud.send_message(id, randomDescription(spellDetails['description']).format('<f32>'+npcs[p]['name']+'<r>') + '\n\n')
        
        secondDesc=randomDescription(spellDetails['description_second'])
        if npcs==players and len(secondDesc)>0:
                mud.send_message(p, secondDesc.format(players[id]['name'],'you') + '\n\n')

        removePreparedSpell(players,id,spellName)

def castSpell(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['frozenStart']!=0:
                mud.send_message(id, randomDescription(players[id]['frozenDescription']) + '\n\n')
                return

        if len(params.strip())==0:
                mud.send_message(id, 'You try to cast a spell but fail horribly.\n\n')
                return

        castStr=params.lower().strip()
        if castStr.startswith('the spell '):
                castStr = castStr.replace('the spell ','',1)
        if castStr.startswith('a '):
                castStr = castStr.replace('a ','',1)
        if castStr.startswith('the '):
                castStr = castStr.replace('the ','',1)
        if castStr.startswith('spell '):
                castStr = castStr.replace('spell ','',1)
        castAt=''
        spellName=''
        if ' at ' in castStr:
                spellName=castStr.split(' at ')[0].strip()
                castAt=castStr.split(' at ')[1].strip()
        else:
                if ' on ' in castStr:
                        spellName=castStr.split(' on ')[0].strip()
                        castAt=castStr.split(' on ')[1].strip()

        if len(castAt)==0:
                mud.send_message(id, 'Who to cast at?\n\n')
                return

        if not players[id]['preparedSpells'].get(spellName):
                mud.send_message(id, "That's not a prepared spell.\n\n")
                return

        spellDetails=None
        if spellsDB.get('cantrip'):
                if spellsDB['cantrip'].get(spellName):
                        spellDetails=spellsDB['cantrip'][spellName]
        if spellDetails == None:
                maxSpellLevel=getPlayerMaxSpellLevel(players,id)         
                for level in range(1,maxSpellLevel+1):
                        if spellsDB[str(level)].get(spellName):
                                spellDetails=spellsDB[str(level)][spellName]
                                break
        if spellDetails == None:
                mud.send_message(id, "No definition found for spell " + spellName + ".\n\n")
                return

        for p in players:
                if castAt not in players[p]['name'].lower():
                        continue
                if p == id:
                        mud.send_message(id, "This is not a hypnosis spell.\n\n")
                        return
                castSpellOnPlayer(mud, spellName, players, id, players, p, spellDetails)
                return

        for p in npcs:
                if castAt not in npcs[p]['name'].lower():
                        continue

                if npcs[p]['familiarOf'] == id:
                        mud.send_message(id, "You can't cast a spell on your own familiar!\n\n")
                        return

                castSpellOnPlayer(mud, spellName, players, id, npcs, p, spellDetails)
                return                

def affinity(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        otherPlayer=params.lower().strip()
        if len(otherPlayer)==0:
                mud.send_message(id, 'With which player?\n\n')
                return
        if players[id]['affinity'].get(otherPlayer):
                affinity=players[id]['affinity'][otherPlayer]
                if affinity>=0:
                        mud.send_message(id, 'Your affinity with <f32><u>' + otherPlayer + '<r> is <f15><b2>+' + str(affinity) + '<r>\n\n')
                else:
                        mud.send_message(id, 'Your affinity with <f32><u>' + otherPlayer + '<r> is <f15><b88>' + str(affinity) + '<r>\n\n')
                return
        mud.send_message(id, "You don't have any affinity with them.\n\n")

def clearSpells(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if len(players[id]['preparedSpells'])>0:
                players[id]['preparedSpells'].clear()
                players[id]['spellSlots'].clear()
                mud.send_message(id, 'Your prepared spells list has been cleared.\n\n')
                return

        mud.send_message(id, "Your don't have any spells prepared.\n\n")

def spells(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if len(players[id]['preparedSpells'])>0:
                mud.send_message(id, 'Your prepared spells:\n')
                for name,details in players[id]['preparedSpells'].items():
                        mud.send_message(id, '  <b234>'+name+'<r>')
                mud.send_message(id, '\n')
        else:
                mud.send_message(id, 'You have no spells prepared.\n\n')

def prepareSpellAtLevel(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,spellName,level):
        for name,details in spellsDB[level].items():
                if name.lower() == spellName:
                        if name.lower() not in players[id]['preparedSpells']:
                                if len(spellsDB[level][name]['items'])==0:
                                        players[id]['preparedSpells'][name]=1
                                else:
                                        for required in spellsDB[level][name]['items']:
                                                requiredItemFound=False
                                                for i in list(players[id]['inv']):
                                                        if int(i) == required:
                                                                requiredItemFound=True
                                                                break
                                                if not requiredItemFound:
                                                        mud.send_message(id, 'You need <b234>' + itemsDB[required]['article'] + ' ' + itemsDB[required]['name'] + '<r>\n\n')
                                                        return True
                                players[id]['prepareSpell'] = spellName
                                players[id]['prepareSpellProgress'] = 0
                                players[id]['prepareSpellTime'] = spellTimeToSec(details['prepareTime'])
                                if len(details['prepareTime'])>0:
                                        mud.send_message(id, 'You begin preparing the spell <b234>' + spellName + '<r>. It will take ' + details['prepareTime'] + '.\n\n')
                                else:
                                        mud.send_message(id, 'You begin preparing the spell <b234>' + spellName + '<r>.\n\n')
                                return True
        return False

def playerMaxCantrips(players,id):
        """Returns the maximum number of cantrips which the player can prepare
        """
        maxCantrips=0
        for prof in players[id]['proficiencies']:
                if type(prof)==list:
                        continue
                if prof.lower().startswith('cantrip'):
                        if '(' in prof and ')' in prof:
                                cantrips=int(prof.split('(')[1].replace(')',''))
                                if cantrips>maxCantrips:
                                        maxCantrips=cantrips
        return maxCantrips

def getPlayerMaxSpellLevel(players,id):
        """Returns the maximum spell level of the player
        """
        for prof in players[id]['proficiencies']:                
                if type(prof)==list:           
                        spellList=list(prof)
                        if len(spellList)>0:
                                if spellList[0].lower()=='spell':
                                        return len(spellList)-1
        return -1

def getPlayerSpellSlotsAtSpellLevel(players,id, spellLevel):
        """Returns the maximum spell slots at the given spell level
        """
        for prof in players[id]['proficiencies']:                
                if type(prof)==list:           
                        spellList=list(prof)
                        if len(spellList)>0:
                                if spellList[0].lower()=='spell':
                                        return spellList[spellLevel]
        return 0

def getPlayerUsedSlotsAtSpellLevel(players,id, spellLevel, spellsDB):
        """Returns the used spell slots at the given spell level
        """
        if not spellsDB.get(str(spellLevel)):
                return 0

        usedCounter=0
        for spellName,details in spellsDB[str(spellLevel)].items():
                if spellName in players[id]['preparedSpells']:
                        usedCounter = usedCounter + 1
        return usedCounter

def playerPreparedCantrips(players,id,spellsDB,sentimentDB):
        """Returns the number of cantrips which the player has prepared
        """
        preparedCounter=0
        for spellName in players[id]['preparedSpells']:
                for cantripName,details in spellsDB['cantrip'].items():
                        if cantripName == spellName:
                                preparedCounter=preparedCounter+1
                                break
        return preparedCounter

def prepareSpell(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        spellName=params.lower().strip()

        # "learn spells" or "prepare spells" shows list of spells
        if spellName=='spell' or spellName=='spells':
                spellName=''

        maxCantrips=playerMaxCantrips(players,id)
        maxSpellLevel=getPlayerMaxSpellLevel(players,id)

        if maxSpellLevel<0 and maxCantrips==0:
                mud.send_message(id, "You can't prepare spells.\n\n")
                return

        if len(spellName)==0:
                # list spells which can be prepared
                mud.send_message(id, 'Spells you can prepare are:\n')

                if maxCantrips>0 and spellsDB.get('cantrip'):
                        for name,details in spellsDB['cantrip'].items():
                                if name.lower() not in players[id]['preparedSpells']:
                                        spellClasses=spellsDB['cantrip'][name]['classes']
                                        if players[id]['characterClass'] in spellClasses or \
                                           len(spellClasses)==0:
                                                mud.send_message(id, '  <f220>-'+name+'<r>')
                
                if maxSpellLevel>0:
                        for level in range(1,maxSpellLevel+1):
                                if not spellsDB.get(str(level)):
                                        continue
                                for name,details in spellsDB[str(level)].items():
                                        if name.lower() not in players[id]['preparedSpells']:
                                                spellClasses=spellsDB[str(level)][name]['classes']
                                                if players[id]['characterClass'] in spellClasses or \
                                                   len(spellClasses)==0:
                                                        mud.send_message(id, '  <b234>'+name+'<r>')
                mud.send_message(id, '\n')
        else:
                if spellName.startswith('the spell '):
                        spellName = spellName.replace('the spell ','')
                if spellName.startswith('spell '):
                        spellName = spellName.replace('spell ','')
                if spellName == players[id]['prepareSpell']:
                        mud.send_message(id, 'You are already preparing that.\n\n')
                        return

                if maxCantrips>0 and spellsDB.get('cantrip'):
                        if playerPreparedCantrips(players,id,spellsDB) < maxCantrips:
                                if prepareSpellAtLevel(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,spellName,'cantrip'):
                                        return
                        else:
                                mud.send_message(id, "You can't prepare any more cantrips.\n\n")
                                return

                if maxSpellLevel>0:
                        for level in range(1,maxSpellLevel+1):                        
                                if not spellsDB.get(str(level)):
                                        continue
                                maxSlots=getPlayerSpellSlotsAtSpellLevel(players,id,level)
                                usedSlots=getPlayerUsedSlotsAtSpellLevel(players,id,level,spellsDB)
                                if usedSlots<maxSlots:
                                        if prepareSpellAtLevel(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,spellName,str(level)):
                                                return
                                else:
                                        mud.send_message(id, "You have prepared the maximum level" + str(level) + " spells.\n\n")
                                        return

                mud.send_message(id, "That's not a spell.\n\n")

def speak(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        lang=params.lower().strip()
        if lang not in players[id]['language']:
                mud.send_message(id, "You don't know how to speak " + lang + "\n\n")
                return
        players[id]['speakLanguage'] = lang
        mud.send_message(id, "You switch to speaking in " + lang + "\n\n")        
                
def say(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        # print(channels)
        if players[id]['canSay'] == 1:

                # don't say if the string contains a blocked string
                selfOnly=False
                params2 = params.lower()
                for blockedstr in blocklist:
                        if blockedstr in params2:
                                selfOnly=True
                                break
                        
                # go through every player in the game
                cantStr=thievesCant(params)
                for (pid, pl) in list(players.items()):
                        # if they're in the same room as the player
                        if players[pid]['room'] == players[id]['room']:
                                if selfOnly == False or pid == id:
                                        if players[id]['speakLanguage'] in players[pid]['language']:
                                                if getSentiment(params,sentimentDB)>=0:
                                                        increaseAffinityBetweenPlayers(players,id,players,pid)
                                                        increaseAffinityBetweenPlayers(players,pid,players,id)
                                                else:
                                                        decreaseAffinityBetweenPlayers(players,id,players,pid)
                                                        decreaseAffinityBetweenPlayers(players,pid,players,id)
                                                                
                                                # send them a message telling them what the player said
                                                mud.send_message(pid, '<f220>{}<r> says: <f159>{}'.format(players[id]['name'], params) + "\n\n")
                                        else:
                                                if players[id]['speakLanguage'] != 'cant':
                                                        mud.send_message(pid, '<f220>{}<r> says something in <f159>{}<r>'.format(players[id]['name'], players[id]['speakLanguage']) + "\n\n")
                                                else:
                                                        mud.send_message(pid, '<f220>{}<r> says: <f159>{}'.format(players[id]['name'], cantStr) + "\n\n")
        else:
                mud.send_message(id, 'To your horror, you realise you somehow cannot force yourself to utter a single word!\n')

def conditionalRoom(condType,cond,description,id,players):
        if condType=='hour':
                currHour = datetime.datetime.utcnow().hour
                condHour = cond.replace('>','').replace('<','').replace('=','').strip()
                if '>' in cond:
                        if currHour > int(condHour):
                                return True
                if '<' in cond:
                        if currHour < int(condHour):
                                return True
                if '=' in cond:
                        if currHour == int(condHour):
                                return True

        if condType=='skill':
                if '<=' in cond:
                        skillType=cond.split('<=')[0].strip()
                        if players[id].get(skillType):
                                skillValue=int(cond.split('<=')[1].split())
                                if players[id][skillType] <= skillValue:
                                        return True
                if '>=' in cond:
                        skillType=cond.split('>=')[0].strip()
                        if players[id].get(skillType):
                                skillValue=int(cond.split('>=')[1].split())
                                if players[id][skillType] >= skillValue:
                                        return True
                if '>' in cond:
                        skillType=cond.split('>')[0].strip()
                        if players[id].get(skillType):
                                skillValue=int(cond.split('>')[1].split())
                                if players[id][skillType] > skillValue:
                                        return True
                if '<' in cond:
                        skillType=cond.split('<')[0].strip()
                        if players[id].get(skillType):
                                skillValue=int(cond.split('<')[1].split())
                                if players[id][skillType] < skillValue:
                                        return True
                if '=' in cond:
                        cond=cond.replace('==','=')
                        skillType=cond.split('=')[0].strip()
                        if players[id].get(skillType):
                                skillValue=int(cond.split('=')[1].split())
                                if players[id][skillType] == skillValue:
                                        return True

        if condType=='date' or condType=='day':
                dayNumber=int(cond.split('/')[0])                
                if dayNumber == int(datetime.datetime.utcnow().strftime("%d")):
                        monthNumber=int(cond.split('/')[1])
                        if monthNumber == int(datetime.datetime.utcnow().strftime("%m")):
                                return True

        if condType=='held' or condType.startswith('hold'):
                if players[id]['clo_lhand'] == int(cond) or \
                   players[id]['clo_rhand'] == int(cond):
                        return True

        if condType=='wear':
                wearableLocation=('clo_head','clo_neck','clo_chest', \
                                  'clo_larm','clo_lleg','clo_rarm', \
                                  'clo_rleg','clo_lwrist', \
                                  'clo_rwrist','clo_feet')
                for w in wearableLocation:
                        if players[id][w] == int(cond):
                                return True

        return False

def conditionalRoomDescription(description,tideOutDescription,conditional,id,players):
        roomDescription = description
        if len(tideOutDescription)>0:
                if runTide() < 0:
                        roomDescription = rm['tideOutDescription']

        # Alternative descriptions triggered by conditions
        for possibleDescription in conditional:
                if len(possibleDescription)>=3:
                        condType=possibleDescription[0]
                        cond=possibleDescription[1]
                        alternativeDescription=possibleDescription[2]
                        if conditionalRoom(condType,cond,alternativeDescription,id,players):
                                roomDescription=alternativeDescription
                                break

        return roomDescription
        
def look(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['canLook'] == 1:
                if len(params) < 1:
                        # If no arguments are given, then look around and describe surroundings

                        # store the player's current room
                        rm = rooms[players[id]['room']]

                        # send the player back the description of their current room
                        roomDescription=rm['description']
                        if len(rm['conditional'])>0:
                                roomDescription = \
                                        conditionalRoomDescription(roomDescription, \
                                                                   rm['tideOutDescription'], \
                                                                   rm['conditional'], \
                                                                   id,players)

                        mud.send_message(id, "\n<f230>" + roomDescription)
                        playershere = []

                        itemshere = []

                        # go through every player in the game
                        for (pid, pl) in list(players.items()):
                                # if they're in the same room as the player
                                if players[pid]['room'] == players[id]['room']:
                                        # ... and they have a name to be shown
                                        if players[pid]['name'] is not None and players[pid]['name'] is not players[id]['name']:
                                                # add their name to the list
                                                if players[pid]['prefix'] == "None":
                                                        playershere.append(players[pid]['name'])
                                                else:
                                                        playershere.append("[" + players[pid]['prefix'] + "] " + players[pid]['name'])

                        ##### Show corpses in the room
                        for (corpse, pl) in list(corpses.items()):
                                if corpses[corpse]['room'] == players[id]['room']:
                                        playershere.append(corpses[corpse]['name'])

                        ##### Show NPCs in the room #####
                        for (nid, pl) in list(npcs.items()):
                                if npcs[nid]['room'] == players[id]['room']:
                                        playershere.append(npcs[nid]['name'])

                        ##### Show items in the room
                        for (item, pl) in list(items.items()):
                                if items[item]['room'] == players[id]['room']:
                                        itemshere.append(itemsDB[items[item]['id']]['article'] + ' ' + itemsDB[items[item]['id']]['name'])

                        # send player a message containing the list of players in the room
                        if len(playershere) > 0:
                                mud.send_message(id, '<f230>You see: <f220>{}'.format(', '.join(playershere)))

                        # send player a message containing the list of exits from this room
                        mud.send_message(id, '<f230>Exits are: <f220>{}'.format(', '.join(rm['exits'])))

                        # send player a message containing the list of items in the room
                        if len(itemshere) > 0:
                                mud.send_message(id, '<f230>You notice: <f220>{}'.format(', '.join(itemshere)))

                        mud.send_message(id, "\n")
                else:
                        # If argument is given, then evaluate it
                        param = params.lower()
                        if param.startswith('at the '):
                                param = params.lower().replace('at the ', '')
                        if param.startswith('the '):
                                param = params.lower().replace('the ', '')
                        if param.startswith('at '):
                                param = params.lower().replace('at ', '')
                        if param.startswith('a '):
                                param = params.lower().replace('a ', '')
                        messageSent = False
                        
                        ## Go through all players in game
                        for p in players:
                                if players[p]['authenticated'] != None:
                                        if players[p]['name'].lower() == param and players[p]['room'] == players[id]['room']:
                                                bioOfPlayer(mud,id,p,players,itemsDB)
                                                messageSent = True

                        message = ""

                        ## Go through all NPCs in game
                        for n in npcs:
                                if param in npcs[n]['name'].lower() and npcs[n]['room'] == players[id]['room']:
                                        bioOfPlayer(mud,id,n,npcs,itemsDB)
                                        messageSent = True

                        if len(message) > 0:
                                mud.send_message(id, message + "\n\n")
                                messageSent = True

                        message = ""

                        ## Go through all Items in game
                        itemCounter = 0
                        for i in items:
                                if items[i]['room'].lower() == players[id]['room'] and param in itemsDB[items[i]['id']]['name'].lower():
                                        if itemCounter == 0:
                                                itemLanguage=itemsDB[int(i)]['language']
                                                if len(itemLanguage)==0:                                                
                                                        message += itemsDB[items[i]['id']]['long_description']
                                                        message += describeContainerContents(mud, id, itemsDB, items[i]['id'], True)
                                                else:
                                                        if itemLanguage in players[id]['language']:
                                                                message += itemsDB[items[i]['id']]['long_description']
                                                                message += describeContainerContents(mud, id, itemsDB, items[i]['id'], True)
                                                        else:
                                                                message += "It's written in " + itemLanguage
                                                itemName = itemsDB[items[i]['id']]['article'] + " " + itemsDB[items[i]['id']]['name']
                                        itemCounter += 1

                        # Examine items in inventory
                        if len(message) == 0:
                                playerinv = list(players[id]['inv'])
                                if len(playerinv) > 0:
                                        # check for exact match of item name
                                        invItemFound=False
                                        for i in playerinv:
                                                if param == itemsDB[int(i)]['name'].lower():
                                                        itemLanguage=itemsDB[int(i)]['language']
                                                        if len(itemLanguage)==0:
                                                                message += itemsDB[int(i)]['long_description']
                                                                message += describeContainerContents(mud, id, itemsDB, int(i), True)
                                                        else:
                                                                if itemLanguage in players[id]['language']:
                                                                        message += itemsDB[int(i)]['long_description']
                                                                        message += describeContainerContents(mud, id, itemsDB, int(i), True)
                                                                else:
                                                                        message += "It's written in " + itemLanguage
                                                        itemName = itemsDB[int(i)]['article'] + " " + itemsDB[int(i)]['name']
                                                        invItemFound=True
                                                        break
                                        if not invItemFound:
                                                # check for partial match of item name
                                                for i in playerinv:
                                                        if param in itemsDB[int(i)]['name'].lower():
                                                                itemLanguage=itemsDB[int(i)]['language']
                                                                if len(itemLanguage)==0:
                                                                        message += itemsDB[int(i)]['long_description']
                                                                        message += describeContainerContents(mud, id, itemsDB, int(i), True)
                                                                else:
                                                                        if itemLanguage in players[id]['language']:
                                                                                message += itemsDB[int(i)]['long_description']
                                                                                message += describeContainerContents(mud, id, itemsDB, int(i), True)
                                                                        else:
                                                                                message += "It's written in " + itemLanguage

                                                                itemName = itemsDB[int(i)]['article'] + " " + itemsDB[int(i)]['name']
                                                                break

                        if len(message) > 0:
                                mud.send_message(id, "It's " + itemName + ".")
                                mud.send_message(id, message + "\n\n")
                                messageSent = True
                                if itemCounter > 1:
                                        mud.send_message(id, "You can see " + str(itemCounter) + " of those in the vicinity.\n")

                        ## If no message has been sent, it means no player/npc/item was found
                        if messageSent == False:
                                mud.send_message(id, "Look at what?\n")
        else:
                mud.send_message(id, 'You somehow cannot muster enough perceptive powers to perceive and describe your immediate surroundings...\n')

def attack(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['frozenStart']!=0:
                mud.send_message(id, randomDescription(players[id]['frozenDescription']) + '\n\n')
                return

        if players[id]['canAttack'] == 1:
                isAlreadyAttacking = False
                target = params #.lower()
                if target.startswith('at '):
                        target = params.replace('at ', '')
                if target.startswith('the '):
                        target = params.replace('the ', '')

                targetFound = False

                for (fight, pl) in fights.items():
                        if fights[fight]['s1'] == players[id]['name']:
                                isAlreadyAttacking = True
                                currentTarget = fights[fight]['s2']

                if isAlreadyAttacking == False:
                        if players[id]['name'].lower() != target.lower():
                                for (pid, pl) in players.items():
                                        if players[pid]['authenticated'] == True and players[pid]['name'].lower() == target.lower():
                                                targetFound = True
                                                victimId = pid
                                                attackerId = id
                                                if players[pid]['room'] == players[id]['room']:
                                                        fights[len(fights)] = { 's1': players[id]['name'], 's2': target, 's1id': attackerId, 's2id': victimId, 's1type': 'pc', 's2type': 'pc', 'retaliated': 0 }
                                                        mud.send_message(id, '<f214>Attacking <r><f255>' + target + '!\n')
                                                        # addToScheduler('0|msg|<b63>You are being attacked by ' + players[id]['name'] + "!", pid, eventSchedule, eventDB)
                                                else:
                                                        targetFound = False

                                # mud.send_message(id, 'You cannot see ' + target + ' anywhere nearby.|')
                                if(targetFound == False):
                                        for (nid, pl) in list(npcs.items()):
                                                if target.lower() in npcs[nid]['name'].lower():
                                                        victimId = nid
                                                        attackerId = id
                                                        # print('found target npc')
                                                        if npcs[nid]['room'] == players[id]['room'] and targetFound == False:
                                                                targetFound = True
                                                                # print('target found!')
                                                                if players[id]['room'] == npcs[nid]['room']:
                                                                        if npcs[nid]['familiarOf'] == id:
                                                                                mud.send_message(id, "You can't attack your own familiar!\n\n")
                                                                                return

                                                                        fights[len(fights)] = { 's1': players[id]['name'], 's2': nid, 's1id': attackerId, 's2id': victimId, 's1type': 'pc', 's2type': 'npc', 'retaliated': 0 }
                                                                        mud.send_message(id, 'Attacking <u><f21>' + npcs[nid]['name'] + '<r>!\n')
                                                                else:
                                                                        pass

                                if targetFound == False:
                                        mud.send_message(id, 'You cannot see ' + target + ' anywhere nearby.\n')
                        else:
                                mud.send_message(id, 'You attempt hitting yourself and realise this might not be the most productive way of using your time.\n')
                else:
                        if type(currentTarget) is not int:
                                mud.send_message(id, 'You are already attacking ' + currentTarget + "\n")
                        else:
                                mud.send_message(id, 'You are already attacking ' + npcs[currentTarget]['name'] + "\n")

                # List fights for debugging purposes
                # for x in fights:
                        # print (x)
                        # for y in fights[x]:
                                # print (y,':',fights[x][y])
        else:
                mud.send_message(id, 'Right now, you do not feel like you can force yourself to attack anyone or anything.\n')

def itemInInventory(players,id,itemName,itemsDB):
        if len(list(players[id]['inv'])) > 0:
                itemNameLower=itemName.lower()
                for i in list(players[id]['inv']):
                        if itemsDB[int(i)]['name'].lower() == itemNameLower:
                                return True
        return False

def describe(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if not isWitch(id,players):
                mud.send_message(id, "You don't have enough powers.\n\n")
                return

        if '"' not in params:
                mud.send_message(id, 'Descriptions need to be within double quotes.\n\n')
                return

        descriptionStrings=re.findall('"([^"]*)"', params)
        if len(descriptionStrings)==0:
                mud.send_message(id, 'Descriptions need to be within double quotes.\n\n')
                return

        if len(descriptionStrings[0].strip()) < 3:
                mud.send_message(id, 'Description is too short.\n\n')
                return
        
        rm = players[id]['room']
        if len(descriptionStrings)==1:
                rooms[rm]['description'] = descriptionStrings[0]
                mud.send_message(id, 'Room description set.\n\n')
                saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
                return

        if len(descriptionStrings)==2:
                thingDescribed = descriptionStrings[0].lower()
                thingDescription = descriptionStrings[1]

                if len(thingDescription)<3:
                        mud.send_message(id, 'Description of ' + descriptionStrings[0] + ' is too short.\n\n')
                        return                        
                
                if thingDescribed == 'name':
                        rooms[rm]['name'] = thingDescription
                        mud.send_message(id, 'Room name changed to ' + thingDescription + '.\n\n')
                        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
                        return
                
                if thingDescribed == 'tide':
                        rooms[rm]['tideOutDescription'] = thingDescription
                        mud.send_message(id, 'Tide out description set.\n\n')
                        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
                        return

                # change the description of an item in the room
                for (item, pl) in list(items.items()):
                        if items[item]['room'] == players[id]['room']:
                                if thingDescribed in itemsDB[items[item]['id']]['name'].lower():
                                        itemsDB[items[item]['id']]['long_description'] = thingDescription
                                        mud.send_message(id, 'New description set for ' + itemsDB[items[item]['id']]['article'] + ' ' + itemsDB[items[item]['id']]['name'] + '.\n\n')
                                        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
                                        return

                # Change the description of an NPC in the room
                for (nid, pl) in list(npcs.items()):
                        if npcs[nid]['room'] == players[id]['room']:
                                if thingDescribed in npcs[nid]['name'].lower():
                                        npcs[nid]['lookDescription'] = thingDescription
                                        mud.send_message(id, 'New description set for ' + npcs[nid]['name'] + '.\n\n')
                                        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
                                        return

        if len(descriptionStrings)==3:
                if descriptionStrings[0].lower() != 'name':
                        mud.send_message(id, "I don't understand.\n\n")
                        return
                thingDescribed = descriptionStrings[1].lower()
                thingName = descriptionStrings[2]
                if len(thingName)<3:
                        mud.send_message(id, 'Description of ' + descriptionStrings[1] + ' is too short.\n\n')
                        return

                # change the name of an item in the room
                for (item, pl) in list(items.items()):
                        if items[item]['room'] == players[id]['room']:
                                if thingDescribed in itemsDB[items[item]['id']]['name'].lower():
                                        itemsDB[items[item]['id']]['name'] = thingName
                                        mud.send_message(id, 'New description set for ' + itemsDB[items[item]['id']]['article'] + ' ' + itemsDB[items[item]['id']]['name'] + '.\n\n')
                                        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
                                        return

                # Change the name of an NPC in the room
                for (nid, pl) in list(npcs.items()):
                        if npcs[nid]['room'] == players[id]['room']:
                                if thingDescribed in npcs[nid]['name'].lower():
                                        npcs[nid]['name'] = thingName
                                        mud.send_message(id, 'New description set for ' + npcs[nid]['name'] + '.\n\n')
                                        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
                                        return
                                
def checkInventory(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        mud.send_message(id, 'You check your inventory.')
        if len(list(players[id]['inv'])) > 0:
                mud.send_message(id, 'You are currently in possession of:\n')
                for i in list(players[id]['inv']):
                        if int(players[id]['clo_lhand']) == int(i):
                                mud.send_message(id, ' * ' + itemsDB[int(i)]['article'] + ' <b234>' + itemsDB[int(i)]['name'] + '<r> (left hand)')
                        else:
                                if int(players[id]['clo_lleg']) == int(i):
                                        mud.send_message(id, ' * ' + itemsDB[int(i)]['article'] + ' <b234>' + itemsDB[int(i)]['name'] + '<r> (left leg)')
                                else:
                                        if int(players[id]['clo_rleg']) == int(i):
                                                mud.send_message(id, ' * ' + itemsDB[int(i)]['article'] + ' <b234>' + itemsDB[int(i)]['name'] + '<r> (right leg)')
                                        else:
                                                if int(players[id]['clo_rhand']) == int(i):
                                                        mud.send_message(id, ' * ' + itemsDB[int(i)]['article'] + ' <b234>' + itemsDB[int(i)]['name'] + '<r> (right hand)')
                                                else:
                                                        if int(players[id]['clo_head']) ==int(i) or int(players[id]['clo_lwrist']) ==int(i) or int(players[id]['clo_rwrist']) ==int(i) or int(players[id]['clo_larm']) ==int(i) or int(players[id]['clo_rarm']) ==int(i) or int(players[id]['clo_neck']) ==int(i) or int(players[id]['clo_chest']) == int(i) or int(players[id]['clo_feet']) == int(i):
                                                                mud.send_message(id, ' * ' + itemsDB[int(i)]['article'] + ' <b234>' + itemsDB[int(i)]['name'] + '<r> (worn)')
                                                        else:
                                                                mud.send_message(id, ' * ' + itemsDB[int(i)]['article'] + ' <b234>' + itemsDB[int(i)]['name'])
                mud.send_message(id, "\n\n")
        else:
                mud.send_message(id, 'You haven`t got any items on you.\n\n')

def changeSetting(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        newPassword=''
        if params.startswith('password '):
                newPassword=params.replace('password ','')
        if params.startswith('pass '):
                newPassword=params.replace('pass ','')
        if len(newPassword)>0:
            if len(newPassword)<6:
                mud.send_message(id, "That password is too short.\n\n")
                return
            players[id]['pwd'] = hash_password(newPassword)
            log("Player " + players[id]['name'] + " changed their password", "info")
            saveState(players[id],playersDB,True)
            mud.send_message(id, "Your password has been changed.\n\n")

def writeOnItem(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if ' on ' not in params:
                if ' onto ' not in params:
                        if ' in ' not in params:
                                if ' using ' not in params:
                                        if ' with ' not in params:
                                                mud.send_message(id, 'What?\n\n')
                                                return
        writeItemName=''
        msg=''
        if ' using ' not in params:
                msg=params.split(' using ')[0].remove('"')
                writeItemName=params.split(' using ')[1].lower()
        if ' with ' not in params:
                msg=params.split(' with ')[0].remove('"')
                writeItemName=params.split(' with ')[1].lower()

        if len(msg)==0:
                return
        if len(msg)>64:
                mud.send_message(id, 'That message is too long.\n\n')

def check(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if params.lower() == 'inventory' or params.lower() == 'inv':
                checkInventory(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)
        elif params.lower() == 'stats':
                mud.send_message(id, 'You check your character sheet.\n')
        else:
                mud.send_message(id, 'Check what?\n')

def wear(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['frozenStart']!=0:
                mud.send_message(id, randomDescription(players[id]['frozenDescription']) + '\n\n')
                return

        if len(params) < 1:
                mud.send_message(id, 'Specify an item from your inventory.\n\n')
                return

        if len(list(players[id]['inv'])) == 0:
                mud.send_message(id, 'You are not carrying that.\n\n')
                return

        itemName = params.lower()
        if itemName.startswith('the '):
                itemName = itemName.replace('the ','')
        if itemName.startswith('my '):
                itemName = itemName.replace('my ','')
        if itemName.startswith('your '):
                itemName = itemName.replace('your ','')

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

        if itemsDB[itemID]['clo_head'] > 0:
                players[id]['clo_head'] = itemID
                mud.send_message(id, 'You don ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                return
        if itemsDB[itemID]['clo_neck'] > 0:
                players[id]['clo_neck'] = itemID
                mud.send_message(id, 'You wear ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '<r> around your neck\n\n')
                return
        if itemsDB[itemID]['clo_rarm'] > 0:
                players[id]['clo_rarm'] = itemID
                mud.send_message(id, 'You wear ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '<r> on your right arm\n\n')
                return
        if itemsDB[itemID]['clo_larm'] > 0:
                players[id]['clo_larm'] = itemID
                mud.send_message(id, 'You wear ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '<r> on your left arm\n\n')
                return
        if itemsDB[itemID]['clo_rwrist'] > 0:
                players[id]['clo_rwrist'] = itemID
                mud.send_message(id, 'You wear ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '<r> on your right wrist\n\n')
                return
        if itemsDB[itemID]['clo_lwrist'] > 0:
                players[id]['clo_lwrist'] = itemID
                mud.send_message(id, 'You wear ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '<r> on your left wrist\n\n')
                return
        if itemsDB[itemID]['clo_chest'] > 0:
                players[id]['clo_chest'] = itemID
                mud.send_message(id, 'You wear ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                return
        if itemsDB[itemID]['clo_feet'] > 0:
                players[id]['clo_feet'] = itemID
                mud.send_message(id, 'You put on ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                return

        mud.send_message(id, "You can't wear that\n\n")

def wield(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['frozenStart']!=0:
                mud.send_message(id, randomDescription(players[id]['frozenDescription']) + '\n\n')
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
                itemName = itemName.replace('the ','')
        if itemName.startswith('my '):
                itemName = itemName.replace('my ','')
        if itemName.startswith('your '):
                itemName = itemName.replace('your ','')
        if itemName.endswith(' on left hand'):
                itemName = itemName.replace(' on left hand','')
                itemHand = 0
        if itemName.endswith(' in left hand'):
                itemName = itemName.replace(' in left hand','')
                itemHand = 0
        if itemName.endswith(' in my left hand'):
                itemName = itemName.replace(' in my left hand','')
                itemHand = 0
        if itemName.endswith(' in your left hand'):
                itemName = itemName.replace(' in your left hand','')
                itemHand = 0
        if itemName.endswith(' left'):
                itemName = itemName.replace(' left','')
                itemHand = 0
        if itemName.endswith(' in left'):
                itemName = itemName.replace(' in left','')
                itemHand = 0
        if itemName.endswith(' on left'):
                itemName = itemName.replace(' on left','')
                itemHand = 0
        if itemName.endswith(' on right hand'):
                itemName = itemName.replace(' on right hand','')
                itemHand = 1
        if itemName.endswith(' in right hand'):
                itemName = itemName.replace(' in right hand','')
                itemHand = 1
        if itemName.endswith(' in my right hand'):
                itemName = itemName.replace(' in my right hand','')
                itemHand = 1
        if itemName.endswith(' in your right hand'):
                itemName = itemName.replace(' in your right hand','')
                itemHand = 1
        if itemName.endswith(' right'):
                itemName = itemName.replace(' right','')
                itemHand = 1
        if itemName.endswith(' in right'):
                itemName = itemName.replace(' in right','')
                itemHand = 1
        if itemName.endswith(' on right'):
                itemName = itemName.replace(' on right','')
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

        if itemsDB[itemID]['clo_lhand'] == 0 and itemsDB[itemID]['clo_rhand'] == 0:
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
                mud.send_message(id, 'You hold <b234>' + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name'] + '<r> in your left hand.\n\n')
        else:
                if int(players[id]['clo_lhand']) == itemID:
                        players[id]['clo_lhand'] = 0
                players[id]['clo_rhand'] = itemID
                mud.send_message(id, 'You hold <b234>' + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name'] + '<r> in your right hand.\n\n')
                
def stow(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if len(list(players[id]['inv'])) == 0:
                return

        stowHands(id,players,itemsDB,mud)

        if int(itemsDB[itemID]['clo_rleg']) > 0:
                if int(players[id]['clo_rleg']) == 0:
                        if int(players[id]['clo_lleg']) != itemID:
                                players[id]['clo_rleg'] = itemID

        if int(itemsDB[itemID]['clo_lleg']) > 0:
                if int(players[id]['clo_lleg']) == 0:
                        if int(players[id]['clo_rleg']) != itemID:
                                players[id]['clo_lleg'] = itemID

def unwear(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if len(list(players[id]['inv'])) == 0:
                return

        if int(players[id]['clo_head']) > 0:
                itemID=int(players[id]['clo_head'])
                mud.send_message(id, 'You remove ' + \
                                 itemsDB[itemID]['article'] + ' <b234>' + \
                                 itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_head'] = 0

        if int(players[id]['clo_neck']) > 0:
                itemID=int(players[id]['clo_neck'])
                mud.send_message(id, 'You take off ' + \
                                 itemsDB[itemID]['article'] + ' <b234>' + \
                                 itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_neck'] = 0

        if int(players[id]['clo_lwrist']) > 0:
                itemID=int(players[id]['clo_lwrist'])
                mud.send_message(id, 'You take off ' + \
                                 itemsDB[itemID]['article'] + ' <b234>' + \
                                 itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_lwrist'] = 0

        if int(players[id]['clo_rwrist']) > 0:
                itemID=int(players[id]['clo_rwrist'])
                mud.send_message(id, 'You take off ' + \
                                 itemsDB[itemID]['article'] + ' <b234>' + \
                                 itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_rwrist'] = 0

        if int(players[id]['clo_larm']) > 0:
                itemID=int(players[id]['clo_larm'])
                mud.send_message(id, 'You take off ' + \
                                 itemsDB[itemID]['article'] + ' <b234>' + \
                                 itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_larm'] = 0

        if int(players[id]['clo_rarm']) > 0:
                itemID=int(players[id]['clo_rarm'])
                mud.send_message(id, 'You take off ' + \
                                 itemsDB[itemID]['article'] + ' <b234>' + \
                                 itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_rarm'] = 0

        if int(players[id]['clo_chest']) > 0:
                itemID=int(players[id]['clo_chest'])
                mud.send_message(id, 'You remove ' + \
                                 itemsDB[itemID]['article'] + ' <b234>' + \
                                 itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_chest'] = 0

        if int(players[id]['clo_feet']) > 0:
                itemID=int(players[id]['clo_feet'])
                mud.send_message(id, 'You take off ' + \
                                 itemsDB[itemID]['article'] + ' <b234>' + \
                                 itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_feet'] = 0

def messageToPlayersInRoom(mud,players,id,msg):
        # go through all the players in the game
        for (pid, pl) in list(players.items()):
                # if player is in the same room and isn't the player
                # sending the command
                if players[pid]['room'] == players[id]['room'] \
                         and pid != id:
                        mud.send_message(pid,msg)

def bioOfPlayer(mud,id,pid,players,itemsDB):
        if players[pid].get('race'):
                if len(players[pid]['race'])>0:
                        mud.send_message(id,'<f32>' + players[pid]['name'] + '<r> (' + \
                                         players[pid]['race'] + ' ' + \
                                         players[pid]['characterClass'] + ')\n')

        if players[pid].get('speakLanguage'):
                mud.send_message(id,'<f15>Speaks:<r> ' + players[pid]['speakLanguage'] + '\n')
        if pid == id:
                if players[id].get('language'):
                        if len(players[id]['language'])>1:
                                languagesStr=''
                                langCtr=0
                                for lang in players[id]['language']:
                                        if langCtr>0:
                                                languagesStr = languagesStr + ', ' + lang
                                        else:
                                                languagesStr = languagesStr + lang
                                        langCtr=langCtr+1
                                mud.send_message(id,'Languages: ' + languagesStr + '\n')
        
        mud.send_message(id,players[pid]['lookDescription'] + '\n')

        if players[pid].get('canGo'):
                if players[pid]['canGo'] == 0:
                        mud.send_message(id,'They are frozen.\n')

        # count items of clothing
        wearingCtr=0
        if int(players[pid]['clo_head'])>0:
                wearingCtr=wearingCtr+1
        if int(players[pid]['clo_neck'])>0:
                wearingCtr=wearingCtr+1
        if int(players[pid]['clo_chest'])>0:
                wearingCtr=wearingCtr+1
        if int(players[pid]['clo_feet'])>0:
                wearingCtr=wearingCtr+1
        if int(players[pid]['clo_lleg'])>0:
                wearingCtr=wearingCtr+1
        if int(players[pid]['clo_rleg'])>0:
                wearingCtr=wearingCtr+1
        if int(players[pid]['clo_larm'])>0:
                wearingCtr=wearingCtr+1
        if int(players[pid]['clo_rarm'])>0:
                wearingCtr=wearingCtr+1

        playerName='You'
        playerName2='your'
        playerName3='have'
        if id != pid:
                playerName='They'
                playerName2='their'
                playerName3='have'

        if int(players[pid]['clo_rhand'])>0:
                mud.send_message(id,playerName + ' ' + playerName3 + ' ' + \
                                 itemsDB[players[pid]['clo_rhand']]['article'] + \
                                 ' ' + itemsDB[players[pid]['clo_rhand']]['name'] + \
                                 ' in ' + playerName2 + ' right hand.\n')
        if int(players[pid]['clo_lhand'])>0:
                mud.send_message(id,playerName + ' ' + playerName3 + ' ' + \
                                 itemsDB[players[pid]['clo_lhand']]['article'] + \
                                 ' ' + itemsDB[players[pid]['clo_lhand']]['name'] + \
                                 ' in ' + playerName2 + ' left hand.\n')

        if wearingCtr>0:
                wearingMsg=playerName + ' are wearing'
                wearingCtr2=0
                playerClothing=('clo_head','clo_neck','clo_lwrist','clo_rwrist',\
                                'clo_larm','clo_rarm','clo_chest','clo_lleg',\
                                'clo_rleg','clo_feet')
                for cl in playerClothing:
                        if int(players[pid][cl])>0:
                                if wearingCtr2>0:
                                        if wearingCtr2 == wearingCtr-1:
                                                wearingMsg=wearingMsg+' and '
                                        else:
                                                wearingMsg=wearingMsg+', '
                                else:
                                        wearingMsg=wearingMsg+' '
                                wearingMsg=wearingMsg+itemsDB[players[pid][cl]]['article'] + \
                                        ' ' + itemsDB[players[pid][cl]]['name']
                                if cl.endswith('neck'):
                                        wearingMsg=wearingMsg+' around ' + playerName2 + ' neck'
                                if cl.endswith('lwrist'):
                                        wearingMsg=wearingMsg+' on ' + playerName2 + ' left wrist'
                                if cl.endswith('rwrist'):
                                        wearingMsg=wearingMsg+' on ' + playerName2 + ' right wrist'
                                if cl.endswith('lleg'):
                                        wearingMsg=wearingMsg+' on ' + playerName2 + ' left leg'
                                if cl.endswith('rleg'):
                                        wearingMsg=wearingMsg+' on ' + playerName2 + ' right leg'
                                wearingCtr2=wearingCtr2+1
                mud.send_message(id,wearingMsg + '.\n')
        mud.send_message(id,'\n')

def bio(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if len(params) == 0:
                bioOfPlayer(mud,id,id,players,itemsDB)
                return

        if params == players[id]['name']:
                bioOfPlayer(mud,id,id,players,itemsDB)
                return

        # go through all the players in the game
        if players[id]['authenticated'] != None:
            for (pid, pl) in list(players.items()):
                if players[pid]['name'] == params:
                        bioOfPlayer(mud,id,pid,players,itemsDB)
                        return

        if players[id]['name'].lower() == 'guest':
                mud.send_message(id,"Guest players cannot set a bio.\n\n")
                return

        if players[id]['canSay'] == 0:
                mud.send_message(id,"You try to describe yourself, but find you have nothing to say.\n\n")
                return

        if '"' in params:
                mud.send_message(id,"Your bio must not include double quotes.\n\n")
                return

        if params.startswith(':'):
                params = params.replace(':','').strip()

        players[id]['lookDescription'] = params
        mud.send_message(id,"Your bio has been set.\n\n")

def eat(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        food = params.lower()
        foodItemID=0
        if len(list(players[id]['inv'])) > 0:
                for i in list(players[id]['inv']):
                        if food in itemsDB[int(i)]['name'].lower():
                                if itemsDB[int(i)]['edible']!=0:
                                        foodItemID=int(i)
                                        break
                                else:
                                        mud.send_message(id,"That's not consumable.\n\n")
                                        return

        if foodItemID == 0:
                mud.send_message(id,"Your don't have " + params + ".\n\n")
                return

        mud.send_message(id,"You consume " + itemsDB[foodItemID]['article'] + \
                         " " + itemsDB[foodItemID]['name'] + ".\n\n")

        # Alter hp
        players[id]['hp'] = players[id]['hp'] + itemsDB[foodItemID]['edible']
        if players[id]['hp']>100:
                players[id]['hp']=100

        # Consumed
        players[id]['inv'].remove(str(foodItemID))

        # decrement any attributes associated with the food
        updatePlayerAttributes(id,players,itemsDB,foodItemID,-1)

        # Remove from hands
        if int(players[id]['clo_rhand']) == foodItemID:
                players[id]['clo_rhand'] = 0
        if int(players[id]['clo_lhand']) == foodItemID:
                players[id]['clo_lhand'] = 0

def go(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['frozenStart']!=0:
                mud.send_message(id, randomDescription(players[id]['frozenDescription']) + '\n\n')
                return
                
        if players[id]['canGo'] == 1:
                # store the exit name
                ex = params.lower()

                # store the player's current room
                rm = rooms[players[id]['room']]

                # if the specified exit is found in the room's exits list
                if ex in rm['exits']:
                        messageToPlayersInRoom(mud,players,id,'<f32>' + \
                                               players[id]['name'] + '<r> ' + \
                                               players[id]['outDescription'] + \
                                               " via exit " + ex + '\n')

                        # Trigger old room eventOnLeave for the player
                        if rooms[players[id]['room']]['eventOnLeave'] is not "":
                                addToScheduler(int(rooms[players[id]['room']]['eventOnLeave']), \
                                               id, eventSchedule, eventDB)

                        # Does the player have any follower NPCs or familiars?
                        followersMsg=""
                        for (nid, pl) in list(npcs.items()):
                                if npcs[nid]['follow'] == players[id]['name'] or \
                                   (npcs[nid]['familiarOf'] == id and npcs[nid]['familiarMode'] == 'follow'):
                                        # is the npc in the same room as the player?
                                        if npcs[nid]['room'] == players[id]['room']:
                                                # is the player within the permitted npc path?
                                                if rm['exits'][ex] in list(npcs[nid]['path']) or \
                                                   npcs[nid]['familiarOf'] == id:
                                                        npcs[nid]['room'] = rm['exits'][ex]
                                                        followersMsg=followersMsg+'<f32>' + \
                                                                npcs[nid]['name'] + '<r> ' + \
                                                                npcs[nid]['inDescription'] + '.\n'
                                                        messageToPlayersInRoom(mud,players,id,'<f32>' + \
                                                                               npcs[nid]['name'] + '<r> ' + \
                                                                               npcs[nid]['outDescription'] + \
                                                                               " via exit " + ex + '\n')
                                                else:
                                                        # not within the npc path, stop following
                                                        #print(npcs[nid]['name'] + ' stops following (out of path)\n')
                                                        npcs[nid]['follow'] = ""
                                        else:
                                                # stop following
                                                #print(npcs[nid]['name'] + ' stops following\n')
                                                npcs[nid]['follow'] = ""

                        # update the player's current room to the one the exit leads to
                        players[id]['room'] = rm['exits'][ex]
                        rm = rooms[players[id]['room']]

                        # trigger new room eventOnEnter for the player
                        if rooms[players[id]['room']]['eventOnEnter'] is not "":
                                addToScheduler(int(rooms[players[id]['room']]['eventOnEnter']), \
                                               id, eventSchedule, eventDB)

                        messageToPlayersInRoom(mud,players,id,'<f32>' + \
                                               players[id]['name'] + '<r> ' + \
                                               players[id]['inDescription'] + "\n")

                        # send the player a message telling them where they are now
                        #mud.send_message(id, 'You arrive at {}'.format(players[id]['room']))
                        mud.send_message(id, 'You arrive at <f106>{}'.format(rooms[players[id]['room']]['name']) + "\n\n")
                        # report any followers
                        if len(followersMsg)>0:
                                messageToPlayersInRoom(mud,players,id,followersMsg)
                                mud.send_message(id, followersMsg);
                else:
                        # the specified exit wasn't found in the current room
                        # send back an 'unknown exit' message
                        mud.send_message(id, "Unknown exit <f226>'{}'".format(ex) + "\n\n")
        else:
                mud.send_message(id, 'Somehow, your legs refuse to obey your will.\n')

def conjureRoom(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        params = params.replace('room ','')
        roomDirection = params.lower().strip()
        possibleDirections=('north','south','east','west','up','down','in','out')
        oppositeDirection={'north':'south','south':'north','east':'west','west':'east','up':'down','down':'up','in':'out','out':'in'}
        if roomDirection not in possibleDirections:
                mud.send_message(id, 'Specify a room direction.\n\n')
                return False

        # Is there already a room in that direction?
        playerRoomID=players[id]['room']
        roomExits=rooms[playerRoomID]['exits']
        if roomExits.get(roomDirection):
                mud.send_message(id, 'A room already exists in that direction.\n\n')
                return False

        roomID = getFreeRoomKey(rooms)
        if len(roomID)==0:
                roomID='$rid=1$'

        newrm = { 'name': 'Empty room', \
               'description': "You are in an empty room. There is a triangular symbol carved into the wall depicting a peasant digging with a spade. Underneath it is an inscription which reads 'aedificium'.", \
               'conditional': [], \
               'eventOnEnter': "", \
               'eventOnLeave': "", \
               'weather': 0, \
               'tideOutDescription': "", \
               'terrainDifficulty': 0, \
               'coords': [], \
               'exits': { oppositeDirection[roomDirection]: playerRoomID } \
        }
        rooms[roomID]=newrm
        roomExits[roomDirection]=roomID

        # update the room coordinates
        for rm in rooms:
                rooms[rm]['coords']=[]
        mapArea = assignCoordinates(rooms)
        
        log("New room: " + roomID, 'info')
        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
        mud.send_message(id, 'Room created.\n\n')
                
def conjureItem(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        itemName = params.lower()
        if len(itemName)==0:
                mud.send_message(id, "Specify the name of an item to conjure.\n\n")
                return False

        # Check if item is in player's inventory
        for item in players[id]['inv']:
                for (iid, pl) in list(itemsDB.items()):
                        if str(iid) == item:
                                if itemName in itemsDB[iid]['name'].lower():
                                        mud.send_message(id, "You have " + \
                                                         itemsDB[iid]['article'] + " " + \
                                                         itemsDB[iid]['name'] + \
                                                         " in your inventory already.\n\n")
                                        return False
        # Check if it is in the room
        for (item, pl) in list(items.items()):
                if items[item]['room'] == players[id]['room']:
                        if itemName in itemsDB[items[item]['id']]['name'].lower():
                                mud.send_message(id, "It's already here.\n\n")
                                return False

        itemID=-1
        for (item, pl) in list(items.items()):
                if itemName == itemsDB[items[item]['id']]['name'].lower():
                        itemID=items[item]['id']
                        break

        if itemID == -1:
                for (item, pl) in list(items.items()):
                        if itemName in itemsDB[items[item]['id']]['name'].lower():
                                itemID=items[item]['id']
                                break

        if itemID != -1:
                # Generate item
                itemKey=getFreeKey(items)
                items[itemKey] = { 'id': itemID, 'room': players[id]['room'], \
                                   'whenDropped': int(time.time()), \
                                   'lifespan': 900000000, 'owner': id }

                mud.send_message(id, itemsDB[itemID]['article'] + ' ' + \
                                 itemsDB[itemID]['name'] + \
                                 ' spontaneously materializes in front of you.\n\n')
                saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
                return True
        return False

def randomFamiliar(npcsDB):
        """Picks a familiar at random and returns its index
        """
        possibleFamiliars=[]
        for index,details in npcsDB.items():
                if len(details['familiarType'])>0:
                        if details['familiarOf']==-1:
                                possibleFamiliars.append(int(index))
        if len(possibleFamiliars)>0:
                return possibleFamiliars[randint(0,len(possibleFamiliars)+1)]
        return -1

def conjureNPC(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if not params.startswith('npc '):
                if not params.startswith('familiar'):
                        return False

        npcHitPoints=100
        isFamiliar=False
        npcType='NPC'
        if params.startswith('familiar'):
                isFamiliar=True
                npcType='Familiar'
                npcIndex=randomFamiliar(npcsDB)
                if npcIndex<0:
                        mud.send_message(id, "No familiars known.\n\n")
                        return
                npcName=npcsDB[npcIndex]['name']
                npcHitPoints=5
                npcSize=1
                npcStrength=5
                npcFamiliarOf=id
                npcAnimalType=npcsDB[npcIndex]['animalType']
                npcFamiliarType=npcsDB[npcIndex]['familiarType']
                npcFamiliarMode="follow"
                npcConv=deepcopy(npcsDB[npcIndex]['conv'])
                npcVocabulary=deepcopy(npcsDB[npcIndex]['vocabulary'])
                npcTalkDelay=npcsDB[npcIndex]['talkDelay']
                npcRandomFactor=npcsDB[npcIndex]['randomFactor']
                npcLookDescription=npcsDB[npcIndex]['lookDescription']
                npcInDescription=npcsDB[npcIndex]['inDescription']
                npcOutDescription=npcsDB[npcIndex]['outDescription']
                npcMoveDelay=npcsDB[npcIndex]['moveDelay']
        else:
                npcName = params.replace('npc ','',1).strip().replace('"','')
                npcSize=sizeFromDescription(npcName)
                npcStrength=80
                npcFamiliarOf=-1
                npcAnimalType=""
                npcFamiliarType=""
                npcFamiliarMode=""
                npcConv=[]
                npcVocabulary=[""]
                npcTalkDelay=300
                npcRandomFactor=100
                npcLookDescription="A new NPC, not yet described"
                npcInDescription="arrives"
                npcOutDescription="goes"
                npcMoveDelay=300

        if len(npcName) == 0:
                mud.send_message(id, "Specify the name of an NPC to conjure.\n\n")
                return False

        # Check if NPC is in the room
        for (nid, pl) in list(npcs.items()):
                if npcs[nid]['room'] == players[id]['room']:
                        if npcName.lower() in npcs[nid]['name'].lower():
                                mud.send_message(id, npcs[nid]['name'] + \
                                                 " is already here.\n\n")
                                return False

        # default medium size
        newNPC = { "name": npcName, \
                   "whenDied": None, \
                   "inv" : [], \
                   "conv" : npcConv, \
                   "room" : players[id]['room'], \
                   "path" : [], \
                   "bodyType": "", \
                   "moveDelay" : npcMoveDelay, \
                   "moveType" : "", \
                   "vocabulary" : npcVocabulary, \
                   "talkDelay" : npcTalkDelay, \
                   "timeTalked": 0, \
                   "lastSaid": 0, \
                   "randomizer": 0, \
                   "randomFactor" : npcRandomFactor, \
                   "follow" : "", \
                   "canWield" : 0, \
                   "canWear" : 0, \
                   "race": "", \
                   "characterClass": "", \
                   "archetype": "", \
                   "proficiencies": [], \
                   "fightingStyle": "", \
                   "restRequired": 0, \
                   "enemy": "", \
                   "tempHitPointsDuration": 0, \
                   "tempHitPointsStart": 0, \
                   "tempHitPoints": 0, \
                   "spellSlots": {}, \
                   "preparedSpells": {}, \
                   "hpMax" : npcHitPoints, \
                   "hp" : npcHitPoints, \
                   "charge" : 1233, \
                   "lvl" : 5, \
                   "exp" : 32, \
                   "str" : npcStrength, \
                   "siz" : npcSize, \
                   "wei" : 100, \
                   "per" : 3, \
                   "endu" : 1, \
                   "cha" : 4, \
                   "int" : 2, \
                   "agi" : 6, \
                   "luc" : 1, \
                   "cool" : 0, \
                   "ref": 1, \
                   "cred" : 122, \
                   "clo_head" : 0, \
                   "clo_neck" : 0, \
                   "clo_larm" : 0, \
                   "clo_rarm" : 0, \
                   "clo_lhand" : 0, \
                   "clo_rhand" : 0, \
                   "clo_rwrist" : 0, \
                   "clo_lwrist" : 0, \
                   "clo_chest" : 0, \
                   "clo_lleg" : 0, \
                   "clo_rleg" : 0, \
                   "clo_feet" : 0, \
                   "imp_head" : 0, \
                   "imp_larm" : 0, \
                   "imp_rarm" : 0, \
                   "imp_lhand" : 0, \
                   "imp_rhand" : 0, \
                   "imp_chest" : 0, \
                   "imp_lleg" : 0, \
                   "imp_rleg" : 0, \
                   "imp_feet" : 0, \
                   "inDescription": npcInDescription, \
                   "outDescription": npcOutDescription, \
                   "lookDescription": npcLookDescription, \
                   "canGo": 0, \
                   "canLook": 1, \
                   "canWield": 0, \
                   "canWear": 0, \
                   "frozenStart": 0, \
                   "frozenDuration": 0, \
                   "frozenDescription": "", \
                   "affinity": {}, \
                   "familiar": -1, \
                   "familiarOf": npcFamiliarOf, \
                   "familiarType": npcFamiliarType, \
                   "familiarMode": npcFamiliarMode, \
                   "animalType": npcAnimalType
        }

        if isFamiliar:
                if players[id]['familiar'] != -1:
                        npcsKey=players[id]['familiar']
                else:
                        npcsKey=getFreeKey(npcs)
                        players[id]['familiar']=npcsKey
        else:
                npcsKey=getFreeKey(npcs)
                
        npcs[npcsKey]=newNPC
        npcsDB[npcsKey]=newNPC
        log(npcType + ' ' + npcName + ' generated in ' + players[id]['room'] + ' with key ' + str(npcsKey), 'info')
        if isFamiliar:
                mud.send_message(id, 'Your familiar, ' + npcName + ', spontaneously appears.\n\n')
        else:
                mud.send_message(id, npcName + ' spontaneously appears.\n\n')
        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
        return True

def conjure(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if not isWitch(id,players):
                mud.send_message(id, "You don't have enough powers.\n\n")
                return

        if params.startswith('familiar'):
                conjureNPC(params, mud, playersDB, players, rooms, \
                           npcsDB, npcs, itemsDB, items, envDB, env, \
                           eventDB, eventSchedule, id, fights, corpses, \
                           blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)
                return
        
        if params.startswith('room '):
                conjureRoom(params, mud, playersDB, players, rooms, npcsDB, \
                            npcs, itemsDB, items, envDB, env, eventDB, \
                            eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)
                return

        if params.startswith('npc '):
                conjureNPC(params, mud, playersDB, players, rooms, \
                           npcsDB, npcs, itemsDB, items, envDB, env, \
                           eventDB, eventSchedule, id, fights, corpses, \
                           blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)
                return
        
        conjureItem(params, mud, playersDB, players, rooms, \
                    npcsDB, npcs, itemsDB, items, envDB, env, \
                    eventDB, eventSchedule, id, fights, \
                    corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)

def destroyItem(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        itemName = params.lower()
        if len(itemName)==0:
                mud.send_message(id, "Specify the name of an item to destroy.\n\n")
                return False
        
        # Check if it is in the room
        itemID=-1
        destroyedName=''
        for (item, pl) in list(items.items()):
                if items[item]['room'] == players[id]['room']:
                        if itemName in itemsDB[items[item]['id']]['name']:
                                destroyedName=itemsDB[items[item]['id']]['name']
                                itemID=items[item]['id']
                                break
        if itemID==-1:
                mud.send_message(id, "It's not here.\n\n")
                return False

        mud.send_message(id, 'It suddenly vanishes.\n\n')
        del items[item]
        log("Item destroyed: " + destroyedName + ' in ' + players[id]['room'], 'info')
        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
        return True

def destroyNPC(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        npcName = params.lower().replace('npc ','').strip().replace('"','')
        if len(npcName)==0:
                mud.send_message(id, "Specify the name of an NPC to destroy.\n\n")
                return False
        
        # Check if NPC is in the room
        npcID=-1
        destroyedName=''
        for (nid, pl) in list(npcs.items()):
                if npcs[nid]['room'] == players[id]['room']:
                        if npcName.lower() in npcs[nid]['name'].lower():
                                destroyedName=npcs[nid]['name']
                                npcID=nid
                                break

        if npcID == -1:
                mud.send_message(id, "They're not here.\n\n")
                return False

        mud.send_message(id, 'They suddenly vanish.\n\n')
        del npcs[npcID]
        del npcsDB[npcID]
        log("NPC destroyed: " + destroyedName + ' in ' + players[id]['room'], 'info')
        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
        return True

def destroyRoom(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        params = params.replace('room ','')
        roomDirection = params.lower().strip()
        possibleDirections=('north','south','east','west','up','down','in','out')
        oppositeDirection={'north':'south','south':'north','east':'west', \
                           'west':'east','up':'down','down':'up', \
                           'in':'out','out':'in'}
        if roomDirection not in possibleDirections:
                mud.send_message(id, 'Specify a room direction.\n\n')
                return False

        # Is there already a room in that direction?
        playerRoomID=players[id]['room']
        roomExits=rooms[playerRoomID]['exits']
        if not roomExits.get(roomDirection):
                mud.send_message(id, 'There is no room in that direction.\n\n')
                return False

        roomToDestroyID=roomExits.get(roomDirection)
        roomToDestroy = rooms[roomToDestroyID]
        roomExitsToDestroy=roomToDestroy['exits']
        for direction,roomID in roomExitsToDestroy.items():
                # Remove the exit from the other room to this one
                otherRoom=rooms[roomID]
                if otherRoom['exits'].get(oppositeDirection[direction]):
                        del otherRoom['exits'][oppositeDirection[direction]]
        del rooms[roomToDestroyID]

        # update the map area
        for rm in rooms:
                rooms[rm]['coords']=[]
        mapArea = assignCoordinates(rooms)
        
        log("Room destroyed: " + roomToDestroyID, 'info')
        saveUniverse(rooms,npcsDB,npcs,itemsDB,items,envDB,env)
        mud.send_message(id, "Room destroyed.\n\n")
        return True

def destroy(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if not isWitch(id,players):
                mud.send_message(id, "You don't have enough powers.\n\n")
                return

        if params.startswith('room '):
                destroyRoom(params, mud, playersDB, players, rooms, npcsDB, \
                            npcs, itemsDB, items, envDB, env, eventDB, \
                            eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)
        else:
                if params.startswith('npc '):
                        destroyNPC(params, mud, playersDB, players, rooms, \
                                   npcsDB, npcs, itemsDB, items, envDB, env, \
                                   eventDB, eventSchedule, id, fights, \
                                   corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)
                else:
                        destroyItem(params, mud, playersDB, players, rooms, \
                                    npcsDB, npcs, itemsDB, items, envDB, env, \
                                    eventDB, eventSchedule, id, fights, \
                                    corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)

def drop(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
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
                        if str(iid) == item:
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
                        if str(iid) == item:
                                if target in itemsDB[iid]['name'].lower():
                                        itemID = iid
                                        itemName = itemsDB[iid]['name']
                                        itemInInventory = True
                                        itemInDB = True
                                        break

        if itemInDB and itemInInventory:
                inventoryCopy = deepcopy(players[id]['inv'])
                for i in inventoryCopy:
                        if int(i) == itemID:
                                # Remove first matching item from inventory
                                players[id]['inv'].remove(i)
                                updatePlayerAttributes(id,players,itemsDB,itemID,-1)
                                break

                players[id]['wei'] = playerInventoryWeight(id, players, itemsDB)

                # remove from clothing
                removeItemFromClothing(players,id,int(i))

                # Create item on the floor in the same room as the player
                items[getFreeKey(items)] = { 'id': itemID, 'room': players[id]['room'], 'whenDropped': int(time.time()), 'lifespan': 900000000, 'owner': id }

                # Print itemsInWorld to console for debugging purposes
                # for x in itemsInWorld:
                        # print (x)
                        # for y in itemsInWorld[x]:
                                        # print(y,':',itemsInWorld[x][y])

                mud.send_message(id, 'You drop ' + itemsDB[int(i)]['article'] + ' ' + itemsDB[int(i)]['name'] + ' on the floor.\n\n')

        else:
                mud.send_message(id, 'You don`t have that!\n\n')

def openItemUnlock(items,itemsDB,id,iid,players,mud):
        unlockItemID=itemsDB[items[iid]['id']]['lockedWithItem']
        if unlockItemID>0:
                    keyFound=False
                    for i in list(players[id]['inv']):
                            if int(i) == unlockItemID:
                                    keyFound=True
                                    break
                    if keyFound:
                            mud.send_message(id, 'You use ' + itemsDB[unlockItemID]['article'] + ' ' + itemsDB[unlockItemID]['name'])
                    else:
                            if len(itemsDB[unlockItemID]['open_failed_description'])>0:
                                    mud.send_message(id, itemsDB[unlockItemID]['open_failed_description'] + ".\n\n")
                            else:
                                    if randint(0, 1) == 1:
                                            mud.send_message(id, "You don't have " + itemsDB[unlockItemID]['article'] + " " + itemsDB[unlockItemID]['name'] + ".\n\n")
                                    else:
                                            mud.send_message(id, "Looks like you need " + itemsDB[unlockItemID]['article'] + " " + itemsDB[unlockItemID]['name'] + " for this.\n\n")
                            return False
        return True

def describeContainerContents(mud, id, itemsDB, itemID, returnMsg):
        if not itemsDB[itemID]['state'].startswith('container open'):
                if returnMsg:
                        return ''
                else:
                        return
        noOfItems=len(itemsDB[itemID]['contains'])
        containerMsg='You see '

        if noOfItems == 0:
                mud.send_message(id, containerMsg + ' nothing.\n\n')
                return

        itemCtr=0
        for contentsID in itemsDB[itemID]['contains']:
                if itemCtr > 0:
                        if itemCtr < noOfItems-1:
                                containerMsg = containerMsg + ', '
                        else:
                                containerMsg = containerMsg + ' and '

                containerMsg = containerMsg + itemsDB[int(contentsID)]['article'] + ' <b234>' + itemsDB[int(contentsID)]['name'] + '<r>'
                itemCtr = itemCtr + 1

        containerMsg = containerMsg + '.\n'
        if returnMsg:
                containerMsg = '\n' + containerMsg
                return containerMsg
        else:
                mud.send_message(id, containerMsg + '\n')

def openItemContainer(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, target, itemsInWorldCopy, iid):
        if not openItemUnlock(items, itemsDB, id, iid, players, mud):
                return

        itemID=items[iid]['id']
        if itemsDB[itemID]['state'].startswith('container open'):
                mud.send_message(id, "It's already open\n\n")
                return

        itemsDB[itemID]['state']=itemsDB[itemID]['state'].replace('closed','open')
        itemsDB[itemID]['short_description']=itemsDB[itemID]['short_description'].replace('closed','open')
        itemsDB[itemID]['long_description']=itemsDB[itemID]['long_description'].replace('closed','open')
        itemsDB[itemID]['long_description']=itemsDB[itemID]['long_description'].replace('shut','open')

        if len(itemsDB[itemID]['open_description'])>0:
                mud.send_message(id, itemsDB[itemID]['open_description'] + '\n')
        describeContainerContents(mud, id, itemsDB, itemID, False)

def openItemDoor(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, target, itemsInWorldCopy, iid):
        if not openItemUnlock(items,itemsDB,id,iid,players,mud):
                return

        itemID=items[iid]['id']
        linkedItemID=int(itemsDB[itemID]['linkedItem'])
        roomID=itemsDB[itemID]['exit']
        if '|' in itemsDB[itemID]['exitName']:
                exitName=itemsDB[itemID]['exitName'].split('|')

                itemsDB[itemID]['state']='open'
                itemsDB[itemID]['short_description']=itemsDB[itemID]['short_description'].replace('closed','open')
                itemsDB[itemID]['long_description']=itemsDB[itemID]['long_description'].replace('closed','open')

                if linkedItemID>0:
                        itemsDB[linkedItemID]['short_description']=itemsDB[linkedItemID]['short_description'].replace('closed','open')
                        itemsDB[linkedItemID]['long_description']=itemsDB[linkedItemID]['long_description'].replace('closed','open')
                        itemsDB[linkedItemID]['state']='open'

                if len(roomID)>0:
                        rm = players[id]['room']
                        if exitName[0] in rooms[rm]['exits']:
                                del rooms[rm]['exits'][exitName[0]]
                        rooms[rm]['exits'][exitName[0]] = roomID

                        rm = roomID
                        if exitName[1] in rooms[rm]['exits']:
                                del rooms[rm]['exits'][exitName[1]]
                        rooms[rm]['exits'][exitName[1]] = players[id]['room']

        if len(itemsDB[itemID]['open_description'])>0:
                mud.send_message(id, itemsDB[itemID]['open_description'] + '\n\n')
        else:
                mud.send_message(id, 'You open ' + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name'] + '\n\n')

def openItem(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        target=params.lower()

        if target.startswith('registration'):
                enableRegistrations(mud, id, players)
                return

        itemsInWorldCopy = deepcopy(items)
        for (iid, pl) in list(itemsInWorldCopy.items()):
                if itemsInWorldCopy[iid]['room'] == players[id]['room']:
                    if target in itemsDB[items[iid]['id']]['name'].lower():
                            if itemsDB[items[iid]['id']]['state'] == 'closed':
                                    openItemDoor(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, target, itemsInWorldCopy, iid)
                                    break
                            if itemsDB[items[iid]['id']]['state'] == 'container closed':
                                    openItemContainer(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, target, itemsInWorldCopy, iid)
                                    break

def closeItemContainer(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, target, itemsInWorldCopy, iid):
        itemID=items[iid]['id']
        if itemsDB[itemID]['state'].startswith('container closed'):
                mud.send_message(id, "It's already closed\n\n")
                return

        if itemsDB[itemID]['state'].startswith('container open '):
                mud.send_message(id, "That's not possible.\n\n")
                return

        itemsDB[itemID]['state']=itemsDB[itemID]['state'].replace('open', 'closed')
        itemsDB[itemID]['short_description']=itemsDB[itemID]['short_description'].replace('open', 'closed')
        itemsDB[itemID]['long_description']=itemsDB[itemID]['long_description'].replace('open','closed')

        if len(itemsDB[itemID]['close_description'])>0:
                mud.send_message(id, itemsDB[itemID]['close_description'] + '\n\n')
        else:
                mud.send_message(id, 'You close ' + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name'] + '.\n\n')

def closeItemDoor(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, target, itemsInWorldCopy, iid):
        itemID=items[iid]['id']
        linkedItemID=int(itemsDB[itemID]['linkedItem'])
        roomID=itemsDB[itemID]['exit']
        if '|' not in itemsDB[itemID]['exitName']:
                return

        exitName=itemsDB[itemID]['exitName'].split('|')

        itemsDB[itemID]['state']='closed'
        itemsDB[itemID]['short_description']=itemsDB[itemID]['short_description'].replace('open','closed')
        itemsDB[itemID]['long_description']=itemsDB[itemID]['long_description'].replace('open','closed')

        if linkedItemID>0:
                itemsDB[linkedItemID]['short_description']=itemsDB[linkedItemID]['short_description'].replace('open','closed')
                itemsDB[linkedItemID]['long_description']=itemsDB[linkedItemID]['long_description'].replace('open','closed')
                itemsDB[linkedItemID]['state']='closed'

        if len(roomID)>0:
                rm = players[id]['room']
                if exitName[0] in rooms[rm]['exits']:
                        del rooms[rm]['exits'][exitName[0]]

                rm = roomID
                if exitName[1] in rooms[rm]['exits']:
                        del rooms[rm]['exits'][exitName[1]]

        if len(itemsDB[itemID]['close_description'])>0:
                mud.send_message(id, itemsDB[itemID]['close_description'] + '\n\n')
        else:
                mud.send_message(id, 'You close ' + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name'] + '\n\n')

def closeItem(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        target=params.lower()

        if target.startswith('registration'):
                disableRegistrations(mud, id, players)
                return

        itemsInWorldCopy = deepcopy(items)
        for (iid, pl) in list(itemsInWorldCopy.items()):
                if itemsInWorldCopy[iid]['room'] == players[id]['room']:
                    if target in itemsDB[items[iid]['id']]['name'].lower():
                            if itemsDB[items[iid]['id']]['state'] == 'open':
                                    closeItemDoor(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, target, itemsInWorldCopy, iid)
                                    break
                            if itemsDB[items[iid]['id']]['state'].startswith('container open'):
                                    closeItemContainer(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, target, itemsInWorldCopy, iid)
                                    break

def putItem(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if ' in ' not in params:
                if ' on ' not in params:
                        if ' into ' not in params:
                                if ' onto ' not in params:
                                        if ' within ' not in params:
                                                return

        target = []
        inon=' in '
        if ' in ' in params:
                target = params.split(' in ')
        else:
                if ' into ' in params:
                        target = params.split(' into ')
                else:
                        if ' onto ' in params:
                                target = params.split(' onto ')
                                inon=' onto '
                        else:
                                if ' on ' in params:
                                        inon=' on '
                                        target = params.split(' on ')
                                else:
                                        target = params.split(' within ')

        if len(target) != 2:
                return

        itemID = 0
        itemName = target[0]
        containerName = target[1]

        if len(list(players[id]['inv'])) > 0:
                itemNameLower=itemName.lower()
                for i in list(players[id]['inv']):
                        if itemsDB[int(i)]['name'].lower() == itemNameLower:
                                itemID=int(i)
                                itemName=itemsDB[int(i)]['name']

                if itemID == 0:
                        for i in list(players[id]['inv']):
                                if itemNameLower in itemsDB[int(i)]['name'].lower():
                                        itemID=int(i)
                                        itemName=itemsDB[int(i)]['name']

        if itemID == 0:
                mud.send_message(id, "You don't have " + itemName +".\n\n")
                return

        itemsInWorldCopy = deepcopy(items)

        for (iid, pl) in list(itemsInWorldCopy.items()):
                if itemsInWorldCopy[iid]['room'] == players[id]['room']:
                        if containerName.lower() in itemsDB[items[iid]['id']]['name'].lower():
                                if itemsDB[items[iid]['id']]['state'].startswith('container open'):
                                        if ' noput' not in itemsDB[items[iid]['id']]['state']:
                                                players[id]['inv'].remove(str(itemID))
                                                removeItemFromClothing(players,id,itemID)
                                                itemsDB[items[iid]['id']]['contains'].append(str(itemID))
                                                mud.send_message(id, 'You put ' + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name'] + inon + itemsDB[items[iid]['id']]['article'] + ' ' + itemsDB[items[iid]['id']]['name'] + '.\n\n')
                                        else:
                                                if 'on' in inon:
                                                        mud.send_message(id, "You can't put anything on that.\n\n")
                                                else:
                                                        mud.send_message(id, "You can't put anything in that.\n\n")
                                        return
                                else:
                                        if itemsDB[items[iid]['id']]['state'].startswith('container closed'):
                                                if 'on' in inon:
                                                        mud.send_message(id, "You can't.\n\n")
                                                else:
                                                        mud.send_message(id, "It's closed.\n\n")
                                                return
                                        else:
                                                if 'on' in inon:
                                                        mud.send_message(id, "You can't put anything on that.\n\n")
                                                else:
                                                        mud.send_message(id, "It can't contain anything.\n\n")
                                                return

        mud.send_message(id, "You don't see " + containerName + ".\n\n")

def take(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        if players[id]['frozenStart']!=0:
                mud.send_message(id, randomDescription(players[id]['frozenDescription']) + '\n\n')
                return

        if len(str(params)) < 3:
            return

        if itemInInventory(players,id,str(params),itemsDB):
            mud.send_message(id, 'You are already carring ' + str(params) + '\n\n')
            return

        itemInDB = False
        itemID = None
        itemName = None
        itemPickedUp = False
        target = str(params).lower()
        if target.startswith('the '):
                target = params.replace('the ', '')

        for (iid, pl) in list(items.items()):
                iid2=items[iid]['id']
                if itemsDB[iid2]['name'].lower() == target:
                        # ID of the item to be picked up
                        itemID = iid
                        itemName = itemsDB[iid2]['name']
                        itemInDB = True
                        break
                else:
                        itemInDB = False
                        itemName = None
                        itemID = None

        itemsInWorldCopy = deepcopy(items)

        if not itemInDB:
            # Try fuzzy match of the item name
            for (iid, pl) in list(itemsInWorldCopy.items()):
                if itemsInWorldCopy[iid]['room'] == players[id]['room']:
                    if target in itemsDB[items[iid]['id']]['name'].lower():
                        # ID of the item to be picked up
                        itemID = itemsDB[items[iid]['id']]
                        itemName = itemsDB[items[iid]['id']]['name']
                        itemInDB = True
                        if itemInInventory(players,id,itemName,itemsDB):
                                mud.send_message(id, 'You are already carring ' + itemName + '\n\n')
                                return
                        break
                    else:
                        itemInDB = False
                        itemName = None
                        itemID = None

        if itemInDB:
            if int(itemsDB[items[iid]['id']]['weight']) == 0:
                    mud.send_message(id, "You can't pick that up.\n\n")
                    return

            for (iid, pl) in list(itemsInWorldCopy.items()):
                if itemsInWorldCopy[iid]['room'] == players[id]['room']:
                        if itemsDB[items[iid]['id']]['name'] == itemName:
                                if players[id]['canGo'] != 0:
                                        # Too heavy?
                                        players[id]['wei'] = playerInventoryWeight(id, players, itemsDB)

                                        if players[id]['wei'] + itemsDB[items[iid]['id']]['weight'] > maxWeight:
                                                mud.send_message(id, "You can't carry any more.\n\n")
                                                return

                                        players[id]['inv'].append(str(items[iid]['id']))
                                        players[id]['wei'] = playerInventoryWeight(id, players, itemsDB)
                                        updatePlayerAttributes(id,players,itemsDB,items[iid]['id'],1)
                                        del items[iid]
                                        itemPickedUp = True
                                        break
                                else:
                                        mud.send_message(id, 'You try to pick up ' + itemName + " but find that your arms won't move.\n\n")
                                        return

        if itemPickedUp:
                mud.send_message(id, 'You pick up and place ' + itemName + ' in your inventory.\n\n')
                itemPickedUp = False
        else:
                # are there any open containers with this item?
                if ' from ' in target:
                        target2 = target.split(' from ')
                        target = target2[0]

                for (iid, pl) in list(itemsInWorldCopy.items()):
                        if itemsInWorldCopy[iid]['room'] == players[id]['room']:
                                if itemsDB[items[iid]['id']]['state'].startswith('container open'):
                                        for containerItemID in itemsDB[items[iid]['id']]['contains']:
                                                itemName = itemsDB[int(containerItemID)]['name']
                                                if target in itemName.lower():
                                                        if itemsDB[int(containerItemID)]['weight']==0:
                                                                mud.send_message(id, "You can't pick that up.\n\n")
                                                                return
                                                        else:
                                                                if players[id]['canGo'] != 0:
                                                                        # Too heavy?
                                                                        carryingWeight = playerInventoryWeight(id, players, itemsDB)
                                                                        if carryingWeight + itemsDB[int(containerItemID)]['weight'] > maxWeight:
                                                                                mud.send_message(id, "You can't carry any more.\n\n")
                                                                                return

                                                                        players[id]['inv'].append(containerItemID)
                                                                        itemsDB[items[iid]['id']]['contains'].remove(containerItemID)
                                                                        mud.send_message(id, 'You take ' + itemsDB[int(containerItemID)]['article'] + ' ' + itemsDB[int(containerItemID)]['name'] + ' from ' + itemsDB[items[iid]['id']]['article'] + ' ' + itemsDB[items[iid]['id']]['name'] + '.\n\n')
                                                                else:
                                                                        mud.send_message(id, 'You try to pick up ' + itemsDB[int(containerItemID)]['article'] + ' ' + itemsDB[int(containerItemID)]['name'] + " but find that your arms won't move.\n\n")
                                                                return

                mud.send_message(id, 'You cannot see ' + target + ' anywhere.\n\n')
                itemPickedUp = False

def runCommand(command, params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB):
        switcher = {
                "sendCommandError": sendCommandError,
                "go": go,
                "bio": bio,
                "who": who,
                "quit": quit,
                "exit": quit,
                "look": look,
                "examine": look,
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
                "ask": tell,
                "open": openItem,
                "close": closeItem,
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
                "learn": prepareSpell,
                "prepare": prepareSpell,
                "destroy": destroy,
                "cast": castSpell,
                "spell": castSpell,
                "spells": spells,
                "clear": clearSpells,
                "spellbook": spells,
                "affinity": affinity,
                "resetuniverse": resetUniverse,
                "shutdown": shutdown
        }

        try:
                switcher[command](params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)
        except Exception as e:
                # print(str(e))
                switcher["sendCommandError"](e, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, blocklist, mapArea,characterClassDB,spellsDB,sentimentDB)
