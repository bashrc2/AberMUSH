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
from copy import deepcopy
import time
import os.path

'''
Command function template:

def commandname(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        print("I'm in!")
'''

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
                            messageToPlayersInRoom(players,id,'<f32>{}<r> suddenly vanishes.'.format(players[id]['name']) + "\n")
                            players[id]['room'] = rm
                            messageToPlayersInRoom(players,id,'<f32>{}<r> suddenly appears.'.format(players[id]['name']) + "\n")
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
                                messageToPlayersInRoom(players,p,'<f32>{}<r> suddenly vanishes.'.format(players[p]['name']) + "\n")
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
        mud.send_message(id, '  who                                    - List players and where they are')
        mud.send_message(id, '  quit/exit                              - Leave the game')
        mud.send_message(id, '  say [message]                          - Says something out loud, '  + "e.g. 'say Hello'")
        mud.send_message(id, '  look/examine                           - Examines the ' + "surroundings, items in the room, NPCs or other players e.g. 'examine tin can' or 'look cleaning robot'")
        mud.send_message(id, '  go [exit]                              - Moves through the exit ' + "specified, e.g. 'go outside'")
        mud.send_message(id, '  attack [target]                        - Attack target ' + "specified, e.g. 'attack knight'")
        mud.send_message(id, '  check inventory                        - Check the contents of ' + "your inventory")
        mud.send_message(id, '  take/get [item]                        - Pick up an item lying ' + "on the floor")
        mud.send_message(id, '  drop [item]                            - Drop an item from your inventory ' + "on the floor")
        mud.send_message(id, '  use/wield/brandish [item] [left|right] - Transfer an item to your hands')
        mud.send_message(id, '  stow                                   - Free your hands of items')
        mud.send_message(id, '  whisper [target] [message]             - Whisper to a player in the same room')
        mud.send_message(id, '  tell [target] [message]                - Send a tell message to another player')
        mud.send_message(id, '')
        mud.send_message(id, 'Witch Commands:')
        mud.send_message(id, '  mute/silence [target]                  - Mutes a player and prevents them from attacking')
        mud.send_message(id, '  unmute/unsilence [target]              - Unmutes a player')
        mud.send_message(id, '  teleport [room]                        - Teleport to a room')
        mud.send_message(id, '  summon [target]                        - Summons a player to your location\n\n')

def say(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        # print(channels)
        if players[id]['canSay'] == 1:
                # go through every player in the game
                for (pid, pl) in list(players.items()):
                        # if they're in the same room as the player
                        if players[pid]['room'] == players[id]['room']:
                                # send them a message telling them what the player said
                                mud.send_message(pid, '<f32>{}<r> says: <f159>{}'.format(players[id]['name'], params) + "\n")
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

                        message = ""

                        ## Go through all players in game
                        for p in players:
                                if players[p]['authenticated'] != None:
                                        if players[p]['name'].lower() == param and players[p]['room'] == players[id]['room']:
                                                message += players[p]['lookDescription']

                        if len(message) > 0:
                                mud.send_message(id, message)
                                messageSent = True

                        message = ""

                        ## Go through all NPCs in game
                        for n in npcs:
                                if param in npcs[n]['name'].lower() and npcs[n]['room'] == players[id]['room']:
                                        message += npcs[n]['lookDescription']

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

def check(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        if params.lower() == 'inventory' or params.lower() == 'inv':
                mud.send_message(id, 'You check your inventory.')
                if len(list(players[id]['inv'])) > 0:
                        mud.send_message(id, 'You are currently in possession of: ')
                        for i in list(players[id]['inv']):
                                if int(players[id]['clo_lhand']) > 0:
                                        mud.send_message(id, '<b234>' + itemsDB[int(i)]['name'] + '<r> (left hand)')
                                else:
                                        if int(players[id]['clo_rhand']) > 0:
                                                mud.send_message(id, '<b234>' + itemsDB[int(i)]['name'] + '<r> (right hand)')
                                        else:
                                                mud.send_message(id, '<b234>' + itemsDB[int(i)]['name'])
                        mud.send_message(id, "\n")
                else:
                        mud.send_message(id, 'You haven`t got any items on you.\n')
        elif params.lower() == 'stats':
                mud.send_message(id, 'You check your character sheet.\n')
        else:
                mud.send_message(id, 'Check what?\n')

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
        if itemName.endswith(' left'):
                itemName = itemName.replace(' left','')
                itemHand = 0
        if itemName.endswith(' in left'):
                itemName = itemName.replace(' in left','')
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
        if itemName.endswith(' right'):
                itemName = itemName.replace(' right','')
                itemHand = 1
        if itemName.endswith(' in right'):
                itemName = itemName.replace(' in right','')
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
                mud.send_message(id, 'You stow the <b234>' + itemsDB[int(players[id]['clo_rhand'])]['name'] + '\n\n')
                players[id]['clo_rhand'] = 0

        if int(players[id]['clo_lhand']) > 0:
                mud.send_message(id, 'You stow the <b234>' + itemsDB[int(players[id]['clo_lhand'])]['name'] + '\n\n')
                players[id]['clo_lhand'] = 0

def messageToPlayersInRoom(players,id,msg):
        # go through all the players in the game
        for (pid, pl) in list(players.items()):
                # if player is in the same room and isn't the player
                # sending the command
                if players[pid]['room'] == players[id]['room'] \
                         and pid != id:
                        mud.send_message(pid,msg)


def go(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        if players[id]['canGo'] == 1:
                # store the exit name
                ex = params.lower()

                # store the player's current room
                rm = rooms[players[id]['room']]

                # if the specified exit is found in the room's exits list
                if ex in rm['exits']:
                        messageToPlayersInRoom(players,id,'<f32>{}<r> left via exit {}'.format(players[id]['name'], ex) + "\n")

                        # Trigger old room eventOnLeave for the player
                        if rooms[players[id]['room']]['eventOnLeave'] is not "":
                                addToScheduler(int(rooms[players[id]['room']]['eventOnLeave']), id, eventSchedule, eventDB)

                        # update the player's current room to the one the exit leads to
                        players[id]['room'] = rm['exits'][ex]
                        rm = rooms[players[id]['room']]

                        # trigger new room eventOnEnter for the player
                        if rooms[players[id]['room']]['eventOnEnter'] is not "":
                                addToScheduler(int(rooms[players[id]['room']]['eventOnEnter']), id, eventSchedule, eventDB)

                        # go through all the players in the game
                        for (pid, pl) in list(players.items()):
                                # if player is in the same (new) room and isn't the player
                                # sending the command
                                if players[pid]['room'] == players[id]['room'] \
                                        and pid != id:
                                        # send them a message telling them that the player
                                        # entered the room
                                        # mud.send_message(pid, '{} arrived via exit {}|'.format(players[id]['name'], ex))
                                        mud.send_message(pid, '<f32>{}<r> has arrived.'.format(players[id]['name'], ex) + "\n")

                        # send the player a message telling them where they are now
                        #mud.send_message(id, 'You arrive at {}'.format(players[id]['room']))
                        mud.send_message(id, 'You arrive at <f106>{}'.format(rooms[players[id]['room']]['name']) + "\n\n")
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
            for (iid, pl) in list(itemsInWorldCopy.items()):
                if itemsInWorldCopy[iid]['room'] == players[id]['room']:
                        if itemsDB[items[iid]['id']]['name'] == itemName:
                                players[id]['inv'].append(str(items[iid]['id']))
                                del items[iid]
                                itemPickedUp = True
                                break

        if itemPickedUp:
                mud.send_message(id, 'You pick up and place ' + itemName + ' in your inventory.\n\n')
                itemPickedUp = False
        else:
                mud.send_message(id, 'You cannot see ' + target + ' anywhere.\n\n')
                itemPickedUp = False

def runCommand(command, params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses):
        switcher = {
                "sendCommandError": sendCommandError,
                "go": go,
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
                "drop": drop,
                "check": check,
                "use": wield,
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
                "tell": tell,
        }

        try:
                switcher[command](params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses)
        except Exception as e:
                # print(str(e))
                switcher["sendCommandError"](e, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses)
