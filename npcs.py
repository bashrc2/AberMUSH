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
