__filename__ = "combat.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

from functions import log
from random import randint
from copy import deepcopy

import time

attack_types_pre=["strike","lunge","bludgeon","thrust","swipe","swing","stab","cut","slash"]
attack_types_pre2=["struck","lunged","bludgeoned","thrusted","swiped","swung","stabbed","cut","slashed"]
attack_types_post=["viciously at","savagely at","daringly at","a glancing blow on","a blow on","heavily at","clumsily at","crudely at"]

def runFightsBetweenPlayers(mud,players,npcs,fights,fid):
        s1id = fights[fid]['s1id']
        s2id = fights[fid]['s2id']

        # In the same room?
        if players[s1id]['room'] != players[s2id]['room']:
            return

        # agility
        if int(time.time()) < players[s1id]['lastCombatAction'] + 10 - players[s1id]['agi']:
            return

        if players[s2id]['isAttackable'] == 1:
                players[s1id]['isInCombat'] = 1
                players[s2id]['isInCombat'] = 1
                # Do damage to the PC here
                if randint(0, 1) == 1:
                        modifier = randint(0, 10)
                        if players[s1id]['hp'] > 0:
                                players[s2id]['hp'] = players[s2id]['hp'] - (players[s1id]['str'] + modifier)
                                players[s1id]['lastCombatAction'] = int(time.time())
                                attackDescriptionIndex1=randint(0,len(attack_types_pre)-1)
                                attackDescriptionIndex2=randint(0,len(attack_types_post)-1)
                                attackDescription=attack_types_pre[attackDescriptionIndex1] + ' ' + attack_types_post[attackDescriptionIndex2]
                                mud.send_message(s1id, 'You ' + attackDescription + ' <f32><u>' + players[s2id]['name'] + '<r> for <f15><b2> * ' + str(players[s1id]['str'] + modifier) + ' *<r> points of damage.\n')
                                attackDescription=attack_types_pre2[attackDescriptionIndex1] + ' ' + attack_types_post[attackDescriptionIndex2]
                                mud.send_message(s2id, '<f32>' + players[s1id]['name'] + '<r> has ' + attackDescription + ' you for <f15><b88> * ' + str(players[s1id]['str'] + modifier) + ' *<r> points of damage.\n')
                else:
                        players[s1id]['lastCombatAction'] = int(time.time())
                        mud.send_message(s1id, 'You miss trying to hit <f32><u>' + players[s2id]['name'] + '\n')
                        mud.send_message(s2id, '<f32><u>' + players[s1id]['name'] + '<r> missed while trying to hit you!\n')
        else:
                mud.send_message(s1id, '<f225>Suddenly you stop. It wouldn`t be a good idea to attack <f32>' + players[s2id]['name'] + ' at this time.\n')
                fightsCopy = deepcopy(fights)
                for (fight, pl) in fightsCopy.items():
                        if fightsCopy[fight]['s1id'] == s1id and fightsCopy[fight]['s2id'] == s2id:
                                del fights[fight]

def runFightsBetweenPlayerAndNPC(mud,players,npcs,fights,fid):
        s1id = fights[fid]['s1id']
        s2id = fights[fid]['s2id']

        # In the same room?
        if players[s1id]['room'] != npcs[s2id]['room']:
            return

        # Agility
        if int(time.time()) < players[s1id]['lastCombatAction'] + 10 - players[s1id]['agi']:
            return

        if npcs[s2id]['isAttackable'] == 1:
                players[s1id]['isInCombat'] = 1
                npcs[s2id]['isInCombat'] = 1
                # Do damage to the NPC here
                if randint(0, 1) == 1:
                        modifier = randint(0, 10)
                        if players[s1id]['hp'] > 0:
                                npcs[s2id]['hp'] = npcs[s2id]['hp'] - (players[s1id]['str'] + modifier)
                                players[s1id]['lastCombatAction'] = int(time.time())

                                attackDescriptionIndex1=randint(0,len(attack_types_pre)-1)
                                attackDescriptionIndex2=randint(0,len(attack_types_post)-1)
                                attackDescription=attack_types_pre[attackDescriptionIndex1] + ' ' + attack_types_post[attackDescriptionIndex2]

                                mud.send_message(s1id, 'You '+ attackDescription + ' <f220>' + npcs[s2id]['name'] + '<r> for <b2><f15> * ' + str(players[s1id]['str'] + modifier)  + ' * <r> points of damage\n')

                else:
                        players[s1id]['lastCombatAction'] = int(time.time())
                        mud.send_message(s1id, 'You miss <f220>' + npcs[s2id]['name'] + '<r> completely!\n')
        else:
                mud.send_message(s1id, '<f225>Suddenly you stop. It wouldn`t be a good idea to attack <u><f21>' + npcs[s2id]['name'] + '<r> at this time.\n')
                fightsCopy = deepcopy(fights)
                for (fight, pl) in fightsCopy.items():
                        if fightsCopy[fight]['s1id'] == s1id and fightsCopy[fight]['s2id'] == s2id:
                                del fights[fight]

def runFightsBetweenNPCAndPlayer(mud,players,npcs,fights,fid):
        s1id = fights[fid]['s1id']
        s2id = fights[fid]['s2id']

        # In the same room?
        if npcs[s1id]['room'] != players[s2id]['room']:
            return

        # Agility
        if int(time.time()) < npcs[s1id]['lastCombatAction'] + 10 - npcs[s1id]['agi']:
            return

        npcs[s1id]['isInCombat'] = 1
        players[s2id]['isInCombat'] = 1
        # Do the damage to PC here
        if randint(0, 1) == 1:
                modifier = randint(0, 10)
                if npcs[s1id]['hp'] > 0:
                        players[s2id]['hp'] = players[s2id]['hp'] - (npcs[s1id]['str'] + modifier)
                        npcs[s1id]['lastCombatAction'] = int(time.time())
                        attackDescriptionIndex1=randint(0,len(attack_types_pre)-1)
                        attackDescriptionIndex2=randint(0,len(attack_types_post)-1)
                        attackDescription=attack_types_pre2[attackDescriptionIndex1] + ' ' + attack_types_post[attackDescriptionIndex2]
                        mud.send_message(s2id, '<f220>' + npcs[s1id]['name'] + '<r> has ' + attackDescription + ' you for <f15><b88> * ' + str(npcs[s1id]['str'] + modifier) + ' * <r> points of damage.\n')
        else:
                npcs[s1id]['lastCombatAction'] = int(time.time())
                mud.send_message(s2id, '<f220>' + npcs[s1id]['name'] + '<r> has missed you completely!\n')

def runFights(mud,players,npcs,fights):
        for (fid, pl) in list(fights.items()):
                # PC -> PC
                if fights[fid]['s1type'] == 'pc' and fights[fid]['s2type'] == 'pc':
                    runFightsBetweenPlayers(mud,players,npcs,fights,fid)
                # PC -> NPC
                elif fights[fid]['s1type'] == 'pc' and fights[fid]['s2type'] == 'npc':
                    runFightsBetweenPlayerAndNPC(mud,players,npcs,fights,fid)
                # NPC -> PC
                elif fights[fid]['s1type'] == 'npc' and fights[fid]['s2type'] == 'pc':
                    runFightsBetweenNPCAndPlayer(mud,players,npcs,fights,fid)
                # NPC -> NPC
                elif fights[fid]['s1type'] == 'npc' and fights[fid]['s2type'] == 'npc':
                        test = 1
