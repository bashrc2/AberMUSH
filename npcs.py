__filename__ = "npcs.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from functions import log
from functions import moveNPCs
from random import randint
from copy import deepcopy

import time

def npcsRest(npcs):
    # rest restores hit points of NPCs
    for p in npcs:
        if npcs[p]['hp'] < 100:
            if randint(0,100)>97:
                npcs[p]['hp'] = npcs[p]['hp'] + 1

def npcRespawns(npcs):
        for (nid, pl) in list(npcs.items()):
                # print(npcs[nid])
                if npcs[nid]['whenDied'] is not None and int(time.time()) >= npcs[nid]['whenDied'] + npcs[nid]['respawn']:
                        #print("IN")
                        npcs[nid]['whenDied'] = None
                        #npcs[nid]['room'] = npcsTemplate[nid]['room']
                        npcs[nid]['room'] = npcs[nid]['lastRoom']
                        # print("respawning " + npcs[nid]['name'])
                        # print(npcs[nid]['hp'])

def runNPCs(mud,npcs,players,fights,corpses,scriptedEventsDB,itemsDB,npcsTemplate):
        for (nid, pl) in list(npcs.items()):
                # Check if any player is in the same room, then send a random message to them
                now = int(time.time())
                if npcs[nid]['vocabulary'][0]:
                    if now > npcs[nid]['timeTalked'] + npcs[nid]['talkDelay'] + npcs[nid]['randomizer']:
                        rnd = randint(0, len(npcs[nid]['vocabulary']) - 1)
                        while rnd is npcs[nid]['lastSaid']:
                                rnd = randint(0, len(npcs[nid]['vocabulary']) - 1)
                        for (pid, pl) in list(players.items()):
                                if npcs[nid]['room'] == players[pid]['room']:
                                        if len(npcs[nid]['vocabulary']) > 1:
                                                #mud.send_message(pid, npcs[nid]['vocabulary'][rnd])
                                                msg = '<f220>' + npcs[nid]['name'] + '<r> says: <f86>' + npcs[nid]['vocabulary'][rnd] + "\n"
                                                mud.send_message(pid, msg)
                                                npcs[nid]['randomizer'] = randint(0, npcs[nid]['randomFactor'])
                                                npcs[nid]['lastSaid'] = rnd
                                                npcs[nid]['timeTalked'] =  now
                                        else:
                                                #mud.send_message(pid, npcs[nid]['vocabulary'][0])
                                                msg = '<f220>' + npcs[nid]['name'] + '<r> says: <f86>' + npcs[nid]['vocabulary'][0] + "\n"
                                                mud.send_message(pid, msg)
                                                npcs[nid]['randomizer'] = randint(0, npcs[nid]['randomFactor'])
                                                npcs[nid]['timeTalked'] =  now

                # Iterate through fights and see if anyone is attacking an NPC - if so, attack him too if not in combat (TODO: and isAggressive = true)
                isInFight=False
                for (fid, pl) in list(fights.items()):
                        if fights[fid]['s2id'] == nid and npcs[fights[fid]['s2id']]['isInCombat'] == 1 and fights[fid]['s1type'] == 'pc' and fights[fid]['retaliated'] == 0:
                                # print('player is attacking npc')
                                # BETA: set las combat action to now when attacking a player
                                npcs[fights[fid]['s2id']]['lastCombatAction'] = int(time.time())
                                fights[fid]['retaliated'] = 1
                                npcs[fights[fid]['s2id']]['isInCombat'] = 1
                                fights[len(fights)] = { 's1': npcs[fights[fid]['s2id']]['name'], 's2': players[fights[fid]['s1id']]['name'], 's1id': nid, 's2id': fights[fid]['s1id'], 's1type': 'npc', 's2type': 'pc', 'retaliated': 1 }
                                isInFight=True
                        elif fights[fid]['s2id'] == nid and npcs[fights[fid]['s2id']]['isInCombat'] == 1 and fights[fid]['s1type'] == 'npc' and fights[fid]['retaliated'] == 0:
                                # print('npc is attacking npc')
                                # BETA: set las combat action to now when attacking a player
                                npcs[fights[fid]['s2id']]['lastCombatAction'] = int(time.time())
                                fights[fid]['retaliated'] = 1
                                npcs[fights[fid]['s2id']]['isInCombat'] = 1
                                fights[len(fights)] = { 's1': npcs[fights[fid]['s2id']]['name'], 's2': players[fights[fid]['s1id']]['name'], 's1id': nid, 's2id': fights[fid]['s1id'], 's1type': 'npc', 's2type': 'npc', 'retaliated': 1 }
                                isInFight=True

                # NPC moves to the next location
                now = int(time.time())
                if isInFight == False and len(npcs[nid]['path'])>0:
                        moveNPCs(npcs,players,mud,now,nid)

                # Check if NPC is still alive, if not, remove from room and create a corpse, set isInCombat to 0, set whenDied to now and remove any fights NPC was involved in
                if npcs[nid]['hp'] <= 0:
                        npcs[nid]['isInCombat'] = 0
                        npcs[nid]['lastRoom'] = npcs[nid]['room']
                        npcs[nid]['whenDied'] = int(time.time())
                        fightsCopy = deepcopy(fights)
                        for (fight, pl) in fightsCopy.items():
                                if fightsCopy[fight]['s1id'] == nid or fightsCopy[fight]['s2id'] == nid:
                                        del fights[fight]
                                        corpses[len(corpses)] = { 'room': npcs[nid]['room'], 'name': str(npcs[nid]['name'] + '`s corpse'), 'inv': npcs[nid]['inv'], 'died': int(time.time()), 'TTL': npcs[nid]['corpseTTL'], 'owner': 1 }
                        for (pid, pl) in list(players.items()):
                                if players[pid]['authenticated'] is not None:
                                        if players[pid]['authenticated'] is not None and players[pid]['room'] == npcs[nid]['room']:
                                                mud.send_message(pid, "<f220>{}<r> <f88>has been killed.".format(npcs[nid]['name']) + "\n")
                                                npcs[nid]['lastRoom'] = npcs[nid]['room']
                                                npcs[nid]['room'] = None
                                                npcs[nid]['hp'] = npcsTemplate[nid]['hp']

                        # Drop NPC loot on the floor
                        droppedItems = []
                        for i in npcs[nid]['inv']:
                                # print("Dropping item " + str(i[0]) + " likelihood of " + str(i[1]) + "%")
                                if randint(0, 100) < int(i[1]):
                                        addToScheduler("0|spawnItem|" + str(i[0]) + ";" + str(npcs[nid]['lastRoom']) + ";0;0", -1, eventSchedule, scriptedEventsDB)
                                        # print("Dropped!" + str(itemsDB[int(i[0])]['name']))
                                        droppedItems.append(str(itemsDB[int(i[0])]['name']))

                        # Inform other players in the room what items got dropped on NPC death
                        if len(droppedItems) > 0:
                                for p in players:
                                        if players[p]['room'] == npcs[nid]['lastRoom']:
                                                mud.send_message(p, "Right before <f220>" + str(npcs[nid]['name']) +"<r>'s lifeless body collapsed to the floor, it had dropped the following items: <f220>{}".format(', '.join(droppedItems)) + "\n")

def npcConversation(mud,npcs,players,itemsDB,rooms,id,nid,message):
        best_match=''
        best_match_action=''
        best_match_action_param0=''
        best_match_action_param1=''
        max_match_ctr=0

        puzzledStr='puzzled'
        if randint(0, 1) == 1:
                puzzledStr='confused'

        conversation_states=players[id]['convstate']
        conversation_new_state=''

        # for each entry in the conversation list
        for conv in npcs[nid]['conv']:
                # entry must contain matching words and resulting reply
                if len(conv)>=2:
                        # count the number of matches for this line
                        match_ctr=0
                        words_list = conv[0]
                        for word_match in words_list:
                                if word_match.lower().startswith('state:'):
                                    # is the conversations with this npc in the given state?
                                    state_value=word_match.lower().split(':')[1].strip()
                                    if npcs[nid]['name'] in conversation_states:
                                        match_ctr = match_ctr + 1
                                        if conversation_states[npcs[nid]['name']] != state_value:
                                            match_ctr=0
                                            break
                                else:
                                    if word_match.lower() in message:
                                        match_ctr = match_ctr + 1
                        # store the best match
                        if match_ctr > max_match_ctr:
                                max_match_ctr = match_ctr
                                best_match=conv[1]
                                best_match_action=''
                                best_match_action_param0=''
                                best_match_action_param1=''
                                currIndex=2
                                conversation_new_state=''
                                if len(conv)>=3:
                                        if conv[2].lower().startswith('state:'):
                                            conversation_new_state=conv[2].lower().split(':')[1].strip()
                                            if len(conv)>=4:
                                                best_match_action=conv[3]
                                            if len(conv)>=5:
                                                best_match_action_param0=conv[4]
                                            if len(conv)>=6:
                                                best_match_action_param1=conv[5]
                                        else:
                                            best_match_action=conv[2]
                                            if len(conv)>=4:
                                                best_match_action_param0=conv[3]
                                            if len(conv)>=5:
                                                best_match_action_param1=conv[4]
        if len(best_match)>0:
                # There were some word matches
            
                if len(conversation_new_state)>0:
                    # set the new conversation state with this npc
                    conversation_states[npcs[nid]['name']] = conversation_new_state

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
                                        messageToPlayersInRoom(mud,players,id,'<f32>{}<r> leaves.'.format(players[id]['name']) + "\n\n")
                                        players[id]['room'] = roomID
                                        npcs[nid]['room'] = roomID
                                        messageToPlayersInRoom(mud,players,id,'<f32>{}<r> arrives.'.format(players[id]['name']) + "\n\n")
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
                                                messageToPlayersInRoom(mud,players,id,'<f32>{}<r> leaves.'.format(players[id]['name']) + "\n\n")
                                                players[id]['room'] = roomID
                                                npcs[nid]['room'] = roomID
                                                messageToPlayersInRoom(mud,players,id,'<f32>{}<r> arrives.'.format(players[id]['name']) + "\n\n")
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

