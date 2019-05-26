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
from functions import hash_password
from functions import log
from functions import saveState
from functions import playerInventoryWeight
from copy import deepcopy
import time
import datetime
import os.path
import commentjson
from random import randint

'''
Command function template:

def commandname(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        print("I'm in!")
'''

def removeItemFromClothing(players,id,itemID):
        if int(players[id]['clo_head']) == itemID:
                players[id]['clo_head'] = 0
        if int(players[id]['clo_neck']) == itemID:
                players[id]['clo_neck'] = 0
        if int(players[id]['clo_chest']) == itemID:
                players[id]['clo_chest'] = 0
        if int(players[id]['clo_feet']) == itemID:
                players[id]['clo_feet'] = 0
        if int(players[id]['clo_larm']) == itemID:
                players[id]['clo_larm'] = 0
        if int(players[id]['clo_rarm']) == itemID:
                players[id]['clo_rarm'] = 0
        if int(players[id]['clo_lleg']) == itemID:
                players[id]['clo_lleg'] = 0
        if int(players[id]['clo_rleg']) == itemID:
                players[id]['clo_rleg'] = 0
        if int(players[id]['clo_lhand']) == itemID:
                players[id]['clo_lhand'] = 0
        if int(players[id]['clo_rhand']) == itemID:
                players[id]['clo_rhand'] = 0
        if int(players[id]['clo_lwrist']) == itemID:
                players[id]['clo_lwrist'] = 0
        if int(players[id]['clo_rwrist']) == itemID:
                players[id]['clo_rwrist'] = 0

def sendCommandError(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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

def teleport(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        if players[id]['permissionLevel'] == 0:
            if isWitch(id,players):
                targetLocation = params[0:].strip().lower()
                if len(targetLocation) != 0:
                    currRoom=players[id]['room']
                    if rooms[currRoom]['name'].strip().lower() == targetLocation:
                        mud.send_message(id, "You are already in " + rooms[currRoom]['name'] + "\n")
                        return
                    for rm in rooms:
                        if rooms[rm]['name'].strip().lower() == targetLocation:
                            mud.send_message(id, "You teleport to " + rooms[rm]['name'] + "\n")
                            messageToPlayersInRoom(mud,players,id,'<f32>{}<r> suddenly vanishes.'.format(players[id]['name']) + "\n")
                            players[id]['room'] = rm
                            messageToPlayersInRoom(mud,players,id,'<f32>{}<r> suddenly appears.'.format(players[id]['name']) + "\n")
                            return
            else:
                mud.send_message(id, "You don't have enough powers for that.\n")

def summon(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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
                                mud.send_message(id, "You summon " + players[p]['name'] + "\n")
                                mud.send_message(p, "A mist surrounds you. When it clears you find that you are now in " + rooms[rm]['name'] + "\n")
                            else:
                                mud.send_message(id, players[p]['name'] + " is already here.\n")
                            return
            else:
                mud.send_message(id, "You don't have enough powers for that.\n")

def mute(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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
                                mud.send_message(id, "You have muted " + target + "\n")
                            else:
                                mud.send_message(id, "You try to mute " + target + " but their power is too strong.\n")
                            return

def unmute(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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
                                    mud.send_message(id, "You have unmuted " + target + "\n")
                                return

def freeze(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        if players[id]['permissionLevel'] == 0:
            if isWitch(id,players):
                target = params.partition(' ')[0]
                if len(target) != 0:
                    for p in players:
                        if players[p]['name'] == target:
                            if not isWitch(p,players):
                                players[p]['canGo'] = 0
                                players[p]['canAttack'] = 0
                                mud.send_message(id, "You have frozen " + target + "\n")
                            else:
                                mud.send_message(id, "You try to freeze " + target + " but their power is too strong.\n")
                            return

def unfreeze(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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
                                    mud.send_message(id, "You have unfrozen " + target + "\n")
                                return

def quit(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        mud._handle_disconnect(id)

def who(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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

def npcConversation(mud,npcs,players,itemsDB,rooms,id,nid,message):
        best_match=''
        best_match_action=''
        best_match_action_param0=''
        best_match_action_param1=''
        max_match_ctr=0

        puzzledStr='puzzled'
        if randint(0, 1) == 1:
                puzzledStr='confused'

        # for each entry in the conversation list
        for conv in npcs[nid]['conv']:
                # entry must contain matching words and resulting reply
                if len(conv)>=2:
                        # count the number of matches for this line
                        match_ctr=0
                        for word_match in conv[0]:
                                if word_match.lower() in message:
                                        match_ctr = match_ctr + 1
                        # store the best match
                        if match_ctr > max_match_ctr:
                                max_match_ctr = match_ctr
                                best_match=conv[1]
                                best_match_action=''
                                best_match_action_param0=''
                                best_match_action_param1=''
                                if len(conv)>=3:
                                        best_match_action=conv[2]
                                if len(conv)>=4:
                                        best_match_action_param0=conv[3]
                                if len(conv)>=5:
                                        best_match_action_param1=conv[4]
        if len(best_match)>0:
                # There were some word matches

                if len(best_match_action)>0:
                        # give
                        if best_match_action == 'give' or best_match_action == 'gift':
                                if len(best_match_action_param0)>0:
                                        itemID=int(best_match_action_param0)
                                        if itemID not in list(players[id]['inv']):
                                                players[id]['inv'].append(str(itemID))
                                                mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> says: " + best_match + ".")
                                                mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> gives you " + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name']  + ".\n\n")
                                                return
                                mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> looks " + puzzledStr + ".\n\n")
                                return

                        # transport (free taxi)
                        if best_match_action == 'transport' or best_match_action == 'ride' or best_match_action == 'teleport':
                                if len(best_match_action_param0)>0:
                                        roomID=best_match_action_param0
                                        mud.send_message(id, best_match)
                                        messageToPlayersInRoom(mud,players,id,'<f32>{}<r> leaves.'.format(players[id]['name']) + "\n")
                                        players[id]['room'] = roomID
                                        npcs[nid]['room'] = roomID
                                        messageToPlayersInRoom(mud,players,id,'<f32>{}<r> arrives.'.format(players[id]['name']) + "\n")
                                        mud.send_message(id, "You are in " + rooms[roomID]['name'] + "\n\n")
                                        return
                                mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> looks " + puzzledStr + ".\n\n")
                                return

                        # taxi (exchange for an item)
                        if best_match_action == 'taxi':
                                if len(best_match_action_param0)>0 and len(best_match_action_param1)>0:
                                        roomID=best_match_action_param0
                                        itemBuyID=int(best_match_action_param1)
                                        if str(itemBuyID) in list(players[id]['inv']):
                                                players[id]['inv'].remove(str(itemBuyID))

                                                mud.send_message(id, best_match)
                                                messageToPlayersInRoom(mud,players,id,'<f32>{}<r> leaves.'.format(players[id]['name']) + "\n")
                                                players[id]['room'] = roomID
                                                npcs[nid]['room'] = roomID
                                                messageToPlayersInRoom(mud,players,id,'<f32>{}<r> arrives.'.format(players[id]['name']) + "\n")
                                                mud.send_message(id, "You are in " + rooms[roomID]['name'] + "\n\n")
                                                return
                                        else:
                                                mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> says: Give me " + itemsDB[itemBuyID]['article'] + ' ' + itemsDB[itemBuyID]['name'] + ".\n\n")
                                                return
                                mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> looks " + puzzledStr + ".\n\n")
                                return

                        # give on a date
                        if best_match_action == 'giveondate' or best_match_action == 'giftondate':
                                if len(best_match_action_param0)>0:
                                        itemID=int(best_match_action_param0)
                                        if itemID not in list(players[id]['inv']):
                                                if '/' in best_match_action_param1:
                                                        dayNumber=int(best_match_action_param1.split('/')[0])
                                                        if dayNumber == int(datetime.date.today().strftime("%d")):
                                                                monthNumber=int(best_match_action_param1.split('/')[1])
                                                                if monthNumber == int(datetime.date.today().strftime("%m")):
                                                                        players[id]['inv'].append(str(itemID))
                                                                        mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> says: " + best_match + ".")
                                                                        mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> gives you " + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name']  + ".\n\n")
                                                                        return
                                mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> looks " + puzzledStr + ".\n\n")
                                return

                        # buy or exchange
                        if best_match_action == 'buy' or best_match_action == 'exchange' or best_match_action == 'barter' or best_match_action == 'trade':
                                if len(best_match_action_param0)>0 and len(best_match_action_param1)>0:
                                        itemBuyID=int(best_match_action_param0)
                                        itemSellID=int(best_match_action_param1)
                                        if str(itemSellID) not in list(npcs[nid]['inv']):
                                            if best_match_action == 'buy':
                                                    mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> says: I don't have any of those to sell.\n\n")
                                            else:
                                                    mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> says: I don't have any of those to trade.\n\n")
                                        else:
                                            if str(itemBuyID) in list(players[id]['inv']):
                                                if str(itemSellID) not in list(players[id]['inv']):
                                                        players[id]['inv'].remove(str(itemBuyID))
                                                        players[id]['inv'].append(str(itemSellID))
                                                        if str(itemBuyID) not in list(npcs[nid]['inv']):
                                                                npcs[nid]['inv'].append(str(itemBuyID))
                                                        mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> says: " + best_match + ".")
                                                        mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> gives you " + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name']  + ".\n\n")
                                                else:
                                                        mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> says: I see you already have " + itemsDB[itemSellID]['article'] + ' ' + itemsDB[itemSellID]['name'] + ".\n\n")
                                            else:
                                                if best_match_action == 'buy':
                                                        mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> says: " + itemsDB[itemSellID]['article'] + ' ' + itemsDB[itemSellID]['name'] + " costs " + itemsDB[itemBuyID]['article'] + ' ' + itemsDB[itemBuyID]['name'] + ".\n\n")
                                                else:
                                                        mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> says: I'll give you " + itemsDB[itemSellID]['article'] + ' ' + itemsDB[itemSellID]['name'] + " in exchange for " + itemsDB[itemBuyID]['article'] + ' ' + itemsDB[itemBuyID]['name'] + ".\n\n")
                                else:
                                        mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> looks " + puzzledStr + ".\n\n")
                                return

                mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> says: " + best_match + ".\n\n")
        else:
                # No word matches
                mud.send_message(id, "<f220>" + npcs[nid]['name'] + "<r> looks " + puzzledStr + ".\n\n")

def tell(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        told = False
        target = params.partition(' ')[0]
        message = params.replace(target, "")[1:]
        if len(target) != 0 and len(message) != 0:
                for p in players:
                        if players[p]['authenticated'] != None and players[p]['name'].lower() == target.lower():
                                #print("sending a tell")
                                if players[id]['name'].lower() == target.lower():
                                        mud.send_message(id, "It'd be pointless to send a tell message to yourself\n")
                                        told = True
                                        break
                                else:
                                        addToScheduler("0|msg|<f90>From " + players[id]['name'] + ": " + message, p, eventSchedule, eventDB)
                                        mud.send_message(id, "<f90>To " + players[p]['name'] + ": " + message + "\n")
                                        told = True
                                        break
                if told == False:
                        for (nid, pl) in list(npcs.items()):
                                if npcs[nid]['room'] == players[id]['room']:
                                        if target.lower() in npcs[nid]['name'].lower():
                                                npcConversation(mud,npcs,players,itemsDB,rooms,id,nid,message.lower())
                                                told = True
                                                break

                if told == False:
                        mud.send_message(id, "<f32>" + target + "<r> does not appear to be reachable at this moment.\n")
        else:
                mud.send_message(id, "Huh?\n")

def whisper(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        target = params.partition(' ')[0]
        message = params.replace(target, "")
        #if message[0] == " ":
                #message.replace(message[0], "")
        messageSent = False
        #print(message)
        #print(str(len(message)))
        if len(target) > 0:
                if len(message) > 0:
                        for p in players:
                                if players[p]['name'] != None and players[p]['name'].lower() == target.lower():
                                        if players[p]['room'] == players[id]['room']:
                                                if players[p]['name'].lower() != players[id]['name'].lower():
                                                        mud.send_message(id, "You whisper to <f32>" + players[p]['name'] + "<r>: " + message[1:])
                                                        mud.send_message(id, "\n")
                                                        mud.send_message(p, "<f162>" + players[id]['name'] + " whispers: " + message[1:])
                                                        mud.send_message(p, "\n")
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

def help(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        mud.send_message(id, 'Commands:')
        mud.send_message(id, '  bio [description]                       - Set a description of yourself')
        mud.send_message(id, '  change password [newpassword]           - Change your password')
        mud.send_message(id, '  who                                     - List players and where they are')
        mud.send_message(id, '  quit/exit                               - Leave the game')
        mud.send_message(id, '  eat/drink [item]                        - Eat or drink a consumable')
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
        mud.send_message(id, '')
        mud.send_message(id, 'Witch Commands:')
        mud.send_message(id, '  close registrations                     - Closes registrations of new players')
        mud.send_message(id, '  open registrations                      - Allows registrations of new players')
        mud.send_message(id, '  mute/silence [target]                   - Mutes a player and prevents them from attacking')
        mud.send_message(id, '  unmute/unsilence [target]               - Unmutes a player')
        mud.send_message(id, '  freeze [target]                         - Prevents a player from moving or attacking')
        mud.send_message(id, '  unfreeze [target]                       - Allows a player to move or attack')
        mud.send_message(id, '  teleport [room]                         - Teleport to a room')
        mud.send_message(id, '  summon [target]                         - Summons a player to your location\n\n')

def say(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        # print(channels)
        if players[id]['canSay'] == 1:
                # go through every player in the game
                for (pid, pl) in list(players.items()):
                        # if they're in the same room as the player
                        if players[pid]['room'] == players[id]['room']:
                                # send them a message telling them what the player said
                                mud.send_message(pid, '<f220>{}<r> says: <f159>{}'.format(players[id]['name'], params) + "\n")
        else:
                mud.send_message(id, 'To your horror, you realise you somehow cannot force yourself to utter a single word!\n')

def look(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        if players[id]['canLook'] == 1:
                if len(params) < 1:
                        # If no arguments are given, then look around and describe surroundings

                        # store the player's current room
                        rm = rooms[players[id]['room']]

                        # send the player back the description of their current room
                        mud.send_message(id, "\n<f230>" + rm['description'])

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
                        if param.startswith('the '):
                                param = params.lower().replace('the ', '')
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
                                                message += itemsDB[items[i]['id']]['long_description']
                                                message += describeContainerContents(mud, id, itemsDB, items[i]['id'], True)
                                                itemName = itemsDB[items[i]['id']]['article'] + " " + itemsDB[items[i]['id']]['name']
                                        itemCounter += 1

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

def attack(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        if players[id]['canAttack'] == 1:
                isAlreadyAttacking = False
                target = params #.lower()
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

def checkInventory(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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

def changeSetting(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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

def writeOnItem(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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

def check(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        if params.lower() == 'inventory' or params.lower() == 'inv':
                checkInventory(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses)
        elif params.lower() == 'stats':
                mud.send_message(id, 'You check your character sheet.\n')
        else:
                mud.send_message(id, 'Check what?\n')

def wear(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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

def wield(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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
                mud.send_message(id, 'You hold <b234>' + itemsDB[itemID]['name'] + '<r> in your left hand.\n\n')
        else:
                if int(players[id]['clo_lhand']) == itemID:
                        players[id]['clo_lhand'] = 0
                players[id]['clo_rhand'] = itemID
                mud.send_message(id, 'You hold <b234>' + itemsDB[itemID]['name'] + '<r> in your right hand.\n\n')

def stow(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        if len(list(players[id]['inv'])) == 0:
                return

        if int(players[id]['clo_rhand']) > 0:
                itemID=int(players[id]['clo_rhand'])
                mud.send_message(id, 'You stow ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_rhand'] = 0

        if int(players[id]['clo_lhand']) > 0:
                itemID=int(players[id]['clo_lhand'])
                mud.send_message(id, 'You stow ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_lhand'] = 0

        if int(itemsDB[itemID]['clo_rleg']) > 0:
                if int(players[id]['clo_rleg']) == 0:
                        if int(players[id]['clo_lleg']) != itemID:
                                players[id]['clo_rleg'] = itemID

        if int(itemsDB[itemID]['clo_lleg']) > 0:
                if int(players[id]['clo_lleg']) == 0:
                        if int(players[id]['clo_rleg']) != itemID:
                                players[id]['clo_lleg'] = itemID

def unwear(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        if len(list(players[id]['inv'])) == 0:
                return

        if int(players[id]['clo_head']) > 0:
                itemID=int(players[id]['clo_head'])
                mud.send_message(id, 'You remove ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_head'] = 0

        if int(players[id]['clo_neck']) > 0:
                itemID=int(players[id]['clo_neck'])
                mud.send_message(id, 'You take off ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_neck'] = 0

        if int(players[id]['clo_lwrist']) > 0:
                itemID=int(players[id]['clo_lwrist'])
                mud.send_message(id, 'You take off ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_lwrist'] = 0

        if int(players[id]['clo_rwrist']) > 0:
                itemID=int(players[id]['clo_rwrist'])
                mud.send_message(id, 'You take off ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_rwrist'] = 0

        if int(players[id]['clo_larm']) > 0:
                itemID=int(players[id]['clo_larm'])
                mud.send_message(id, 'You take off ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_larm'] = 0

        if int(players[id]['clo_rarm']) > 0:
                itemID=int(players[id]['clo_rarm'])
                mud.send_message(id, 'You take off ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_rarm'] = 0

        if int(players[id]['clo_chest']) > 0:
                itemID=int(players[id]['clo_chest'])
                mud.send_message(id, 'You remove ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
                players[id]['clo_chest'] = 0

        if int(players[id]['clo_feet']) > 0:
                itemID=int(players[id]['clo_feet'])
                mud.send_message(id, 'You take off ' + itemsDB[itemID]['article'] + ' <b234>' + itemsDB[itemID]['name'] + '\n\n')
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
        mud.send_message(id,players[pid]['lookDescription'] + '\n')

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
                mud.send_message(id,playerName + ' ' + playerName3 + ' ' + itemsDB[players[pid]['clo_rhand']]['article'] + ' ' + itemsDB[players[pid]['clo_rhand']]['name'] + ' in ' + playerName2 + ' right hand.\n')
        if int(players[pid]['clo_lhand'])>0:
                mud.send_message(id,playerName + ' ' + playerName3 + ' ' + itemsDB[players[pid]['clo_lhand']]['article'] + ' ' + itemsDB[players[pid]['clo_lhand']]['name'] + ' in ' + playerName2 + ' left hand.\n')

        if wearingCtr>0:
                wearingMsg=playerName + ' are wearing'
                wearingCtr2=0
                playerClothing=['clo_head','clo_neck','clo_lwrist','clo_rwrist','clo_larm','clo_rarm','clo_chest','clo_lleg','clo_rleg','clo_feet']
                for cl in playerClothing:
                        if int(players[pid][cl])>0:
                                if wearingCtr2>0:
                                        if wearingCtr2 == wearingCtr-1:
                                                wearingMsg=wearingMsg+' and '
                                        else:
                                                wearingMsg=wearingMsg+', '
                                else:
                                        wearingMsg=wearingMsg+' '
                                wearingMsg=wearingMsg+itemsDB[players[pid][cl]]['article'] + ' ' + itemsDB[players[pid][cl]]['name']
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

def bio(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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

        if '"' in params:
                mud.send_message(id,"Your bio must not include double quotes.\n\n")
                return
        if params.startswith(':'):
                params = params.replace(':','').strip()
        players[id]['lookDescription'] = params
        mud.send_message(id,"Your bio has been set.\n\n")

def eat(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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

        mud.send_message(id,"You consume " + itemsDB[foodItemID]['article'] + " " + itemsDB[foodItemID]['name'] + ".\n\n")

        # Alter hp
        players[id]['hp'] = players[id]['hp'] + itemsDB[foodItemID]['edible']
        if players[id]['hp']>100:
                players[id]['hp']=100

        # Consumed
        players[id]['inv'].remove(str(foodItemID))

        # Remove from hands
        if int(players[id]['clo_rhand']) == foodItemID:
                players[id]['clo_rhand'] = 0
        if int(players[id]['clo_lhand']) == foodItemID:
                players[id]['clo_lhand'] = 0

def go(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        if players[id]['canGo'] == 1:
                # store the exit name
                ex = params.lower()

                # store the player's current room
                rm = rooms[players[id]['room']]

                # if the specified exit is found in the room's exits list
                if ex in rm['exits']:
                        messageToPlayersInRoom(mud,players,id,'<f32>' + players[id]['name'] + '<r> ' + players[id]['outDescription'] + " via exit " + ex + '\n')

                        # Trigger old room eventOnLeave for the player
                        if rooms[players[id]['room']]['eventOnLeave'] is not "":
                                addToScheduler(int(rooms[players[id]['room']]['eventOnLeave']), id, eventSchedule, eventDB)

                        # Does the player have any follower NPCs?
                        followersMsg=""
                        for (nid, pl) in list(npcs.items()):
                                if npcs[nid]['follow'] == players[id]['name']:
                                        # is the npc in the same room as the player?
                                        if npcs[nid]['room'] == players[id]['room']:
                                                # is the player within the permitted npc path?
                                                if rm['exits'][ex] in list(npcs[nid]['path']):
                                                        npcs[nid]['room'] = rm['exits'][ex]
                                                        followersMsg=followersMsg+'<f32>'+npcs[nid]['name'] + '<r> ' + npcs[nid]['inDescription'] + '.\n'
                                                        messageToPlayersInRoom(mud,players,id,'<f32>' + npcs[nid]['name'] + '<r> ' + npcs[nid]['outDescription'] + " via exit " + ex + '\n')
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
                                addToScheduler(int(rooms[players[id]['room']]['eventOnEnter']), id, eventSchedule, eventDB)

                        messageToPlayersInRoom(mud,players,id,'<f32>' + players[id]['name'] + '<r> ' + players[id]['inDescription'] + "\n")

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

def drop(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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
                                break

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

        itemsDB[itemID]['state']='container open'
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

def openItem(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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

        itemsDB[itemID]['state']='container closed'
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

def closeItem(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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

def putItem(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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
                                        players[id]['inv'].remove(str(itemID))
                                        removeItemFromClothing(players,id,itemID)
                                        itemsDB[items[iid]['id']]['contains'].append(str(itemID))
                                        mud.send_message(id, 'You put ' + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name'] + inon + itemsDB[items[iid]['id']]['article'] + ' ' + itemsDB[items[iid]['id']]['name'] + '.\n\n')
                                        return
                                else:
                                        if itemsDB[items[iid]['id']]['state'] == 'container closed':
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

def take(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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

        for (iid, pl) in list(itemsDB.items()):
                if itemsDB[iid]['name'].lower() == target:
                        # ID of the item to be picked up
                        itemID = iid
                        itemName = itemsDB[iid]['name']
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
                                        carryingWeight = playerInventoryWeight(id, players, itemsDB)
                                        if carryingWeight + itemsDB[items[iid]['id']]['weight'] > 100:
                                                mud.send_message(id, "You can't carry any more.\n\n")
                                                return

                                        players[id]['inv'].append(str(items[iid]['id']))
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
                                                                        players[id]['inv'].append(containerItemID)
                                                                        itemsDB[items[iid]['id']]['contains'].remove(containerItemID)
                                                                        mud.send_message(id, 'You take ' + itemsDB[int(containerItemID)]['article'] + ' ' + itemsDB[int(containerItemID)]['name'] + ' from ' + itemsDB[items[iid]['id']]['article'] + ' ' + itemsDB[items[iid]['id']]['name'] + '.\n\n')
                                                                else:
                                                                        mud.send_message(id, 'You try to pick up ' + itemsDB[int(containerItemID)]['article'] + ' ' + itemsDB[int(containerItemID)]['name'] + " but find that your arms won't move.\n\n")
                                                                return

                mud.send_message(id, 'You cannot see ' + target + ' anywhere.\n\n')
                itemPickedUp = False

def runCommand(command, params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
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
                "change": changeSetting
        }

        try:
                switcher[command](params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses)
        except Exception as e:
                # print(str(e))
                switcher["sendCommandError"](e, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses)
