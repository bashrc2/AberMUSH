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
from functions import playerInventoryWeight
from random import randint
from copy import deepcopy
from environment import getTemperatureAtCoords

import time

defenseClothing=['clo_chest','clo_head','clo_larm','clo_rarm','clo_lleg','clo_rleg','clo_lwrist','clo_rwrist']

attack_types_pre=["strike","lunge","bludgeon","thrust","swipe","swing","stab","cut","slash"]
attack_types_pre2=["struck","lunged","bludgeoned","thrusted","swiped","swung","stabbed","cut","slashed"]
attack_types_post=["viciously at","savagely at","daringly at","a crushing blow on","a glancing blow on","a blow on","heavily at","clumsily at","crudely at"]

def playersRest(players):
    # rest restores hit points
    for p in players:
        if players[p]['name'] != None and players[p]['authenticated'] != None:
            if players[p]['hp'] < 100:
                if randint(0,100)>97:
                    players[p]['hp'] = players[p]['hp'] + 1

def itemInNPCInventory(npcs,id,itemName,itemsDB):
        if len(list(npcs[id]['inv'])) > 0:
                itemNameLower=itemName.lower()
                for i in list(npcs[id]['inv']):
                        if itemsDB[int(i)]['name'].lower() == itemNameLower:
                                return True
        return False

def npcUpdateLuck(nid,npcs,items,itemsDB):
    luck=0
    for i in npcs[nid]['inv']:
        luck = luck + itemsDB[int(i)]['mod_luc']
    npcs[nid]['luc'] = luck

def npcWieldsWeapon(mud,id,nid,npcs,items,itemsDB):
    # what is the best weapon which the NPC is carrying?
    itemID=0
    max_protection=0
    max_damage=0
    if int(npcs[nid]['canWield'])!=0:
        for i in npcs[nid]['inv']:
            if itemsDB[int(i)]['clo_rhand']>0:
                if itemsDB[int(i)]['mod_str']>max_damage:
                    max_damage=itemsDB[int(i)]['mod_str']
                    itemID=int(i)

    putOnArmor=False
    if int(npcs[nid]['canWear'])!=0:
        for i in npcs[nid]['inv']:
            if itemsDB[int(i)]['clo_chest']>0:
                if itemsDB[int(i)]['mod_endu']>max_protection:
                    max_protection=itemsDB[int(i)]['mod_endu']
                    itemID=int(i)
                    putOnArmor=True

    # search for any weapons on the floor
    pickedUpWeapon=False
    itemWeaponIndex=0
    if int(npcs[nid]['canWield'])!=0:
        itemsInWorldCopy = deepcopy(items)
        for (iid, pl) in list(itemsInWorldCopy.items()):
            if itemsInWorldCopy[iid]['room'] == npcs[nid]['room']:
                if itemsDB[items[iid]['id']]['weight']>0:
                    if itemsDB[items[iid]['id']]['clo_rhand']>0:
                        if itemsDB[items[iid]['id']]['mod_str']>max_damage:
                            itemName = itemsDB[items[iid]['id']]['name']
                            if not itemInNPCInventory(npcs,nid,itemName,itemsDB):
                                max_damage = itemsDB[items[iid]['id']]['mod_str']
                                itemID = int(items[iid]['id'])
                                itemWeaponIndex = iid
                                pickedUpWeapon = True

    # Search for any armor on the floor
    pickedUpArmor=False
    itemArmorIndex=0
    if int(npcs[nid]['canWear'])!=0:
        for (iid, pl) in list(itemsInWorldCopy.items()):
            if itemsInWorldCopy[iid]['room'] == npcs[nid]['room']:
                if itemsDB[items[iid]['id']]['weight']>0:
                    if itemsDB[items[iid]['id']]['clo_chest']>0:
                        if itemsDB[items[iid]['id']]['mod_endu']>max_protection:
                            itemName = itemsDB[items[iid]['id']]['name']
                            if not itemInNPCInventory(npcs,nid,itemName,itemsDB):
                                max_protection = itemsDB[items[iid]['id']]['mod_endu']
                                itemID = int(items[iid]['id'])
                                itemArmorIndex = iid
                                pickedUpArmor = True

    if itemID>0:
        if putOnArmor:
            if npcs[nid]['clo_chest'] != itemID:
                npcs[nid]['clo_chest'] = itemID
                mud.send_message(id, '<f220>' + npcs[nid]['name'] + '<r> puts on ' + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name'] + '\n')
                return True
            return False

        if pickedUpArmor:
            if npcs[nid]['clo_chest'] != itemID:
                npcs[nid]['inv'].append(str(itemID))
                npcs[nid]['clo_chest'] = itemID
                del items[itemArmorIndex]
                mud.send_message(id, '<f220>' + npcs[nid]['name'] + '<r> picks up and wears ' + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name'] + '\n')
                return True
            return False

        if npcs[nid]['clo_rhand'] != itemID:
            # Transfer weapon to hand
            npcs[nid]['clo_rhand'] = itemID
            npcs[nid]['clo_lhand'] = 0
            if pickedUpWeapon:
                npcs[nid]['inv'].append(str(itemID))
                del items[itemWeaponIndex]
                mud.send_message(id, '<f220>' + npcs[nid]['name'] + '<r> picks up ' + itemsDB[itemID]['article'] + ' ' + itemsDB[itemID]['name'] + '\n')
            else:
                mud.send_message(id, '<f220>' + npcs[nid]['name'] + '<r> has drawn their ' + itemsDB[itemID]['name'] + '\n')
            return True

    return False

def npcWearsArmor(id,npcs,itemsDB):
    if len(npcs[id]['inv'])==0:
        return

    for c in defenseClothing:
        itemID=0
        # what is the best defense which the NPC is carrying?
        max_defense=0
        for i in npcs[id]['inv']:
            if itemsDB[int(i)][c]>0:
                if itemsDB[int(i)]['mod_str'] == 0:
                    if itemsDB[int(i)]['mod_endu']>max_defense:
                        max_defense=itemsDB[int(i)]['mod_endu']
                        itemID=int(i)
        if itemID>0:
            # Wear the armor
            npcs[id][c]=itemID

def weaponDamage(id,players,itemsDB):
    damage=0

    itemID=players[id]['clo_lhand']
    if itemID>0:
        damage = damage + itemsDB[itemID]['mod_str']

    itemID=players[id]['clo_rhand']
    if itemID>0:
        damage = damage + itemsDB[itemID]['mod_str']

    # Total damage inflicted by weapons
    return damage

def weaponDefense(id,players,itemsDB):
    defense=0

    for c in defenseClothing:
        itemID=int(players[id][c])
        if itemID>0:
            defense = defense + int(itemsDB[itemID]['mod_endu'])

    # Total defense by shields or clothing
    return defense

def armorAgility(id,players,itemsDB):
    agility=0

    for c in defenseClothing:
        itemID=int(players[id][c])
        if itemID>0:
            agility = agility + int(itemsDB[itemID]['mod_agi'])

    # Total agility for clothing
    return agility

def getAttackDescription():
    attackDescriptionIndex1=randint(0,len(attack_types_pre)-1)
    attackDescriptionIndex2=randint(0,len(attack_types_post)-1)
    attackDescription=attack_types_pre[attackDescriptionIndex1] + ' ' + attack_types_post[attackDescriptionIndex2]
    return attackDescriptionIndex1,attackDescriptionIndex2,attackDescription

def getTemperatureDifficulty(rm, rooms, mapArea, clouds):
    temperature = getTemperatureAtCoords(rooms[rm]['coords'],rooms,mapArea,clouds)

    if temperature>5:
        # Things get difficult when hotter
        return int(temperature/4)
    # Things get difficult in snow/ice
    return -(temperature-5)

def runFightsBetweenPlayers(mud,players,npcs,fights,fid,itemsDB,rooms,maxTerrainDifficulty,mapArea,clouds):
        s1id = fights[fid]['s1id']
        s2id = fights[fid]['s2id']

        # In the same room?
        if players[s1id]['room'] != players[s2id]['room']:
            return

        currRoom=players[s1id]['room']
        weightDifficulty = int(playerInventoryWeight(s1id, players, itemsDB)/20)
        temperatureDifficulty = getTemperatureDifficulty(currRoom,rooms,mapArea,clouds)
        terrainDifficulty=rooms[players[s1id]['room']]['terrainDifficulty']*10/maxTerrainDifficulty

        # Agility of player
        if int(time.time()) < players[s1id]['lastCombatAction'] + 10 - players[s1id]['agi'] - armorAgility(s1id,players,itemsDB) + terrainDifficulty + temperatureDifficulty + weightDifficulty:
            return

        if players[s2id]['isAttackable'] == 1:
                players[s1id]['isInCombat'] = 1
                players[s2id]['isInCombat'] = 1
                # Do damage to the PC here
                luckValue=players[s1id]['luc']
                if luckValue>6:
                    luckValue=6
                if randint(1+luckValue, 10) > 5:
                        damageDescription='damage'
                        damageValue=weaponDamage(s1id,players,itemsDB)
                        armorValue=weaponDefense(s2id,players,itemsDB)
                        if randint(1, 20)==20:
                            damageDescription='critical damage'
                            damageValue = damageValue*2
                        modifier = randint(0, 10) + damageValue - armorValue
                        #if players[s1id]['luc']>0:
                        #    modifier = modifier + randint(0,players[s1id]['luc'])
                        attackDescriptionIndex1,attackDescriptionIndex2,attackDescription = getAttackDescription()
                        if armorValue<damageValue:
                            if players[s1id]['hp'] > 0:
                                players[s2id]['hp'] = players[s2id]['hp'] - (players[s1id]['str'] + modifier)
                                mud.send_message(s1id, 'You ' + attackDescription + ' <f32><u>' + players[s2id]['name'] + '<r> for <f15><b2> * ' + str(players[s1id]['str'] + modifier) + ' *<r> points of ' + damageDescription + '.\n')
                                attackDescription=attack_types_pre2[attackDescriptionIndex1] + ' ' + attack_types_post[attackDescriptionIndex2]
                                mud.send_message(s2id, '<f32>' + players[s1id]['name'] + '<r> has ' + attackDescription + ' you for <f15><b88> * ' + str(players[s1id]['str'] + modifier) + ' *<r> points of ' + damageDescription + '.\n')
                        else:
                            if players[s1id]['hp'] > 0:
                                # Attack deflected by armor
                                mud.send_message(s1id, 'You ' + attackDescription + ' <f32><u>' + players[s2id]['name'] + '<r> but their armor deflects it.\n')
                                attackDescription=attack_types_pre2[attackDescriptionIndex1] + ' ' + attack_types_post[attackDescriptionIndex2]
                                mud.send_message(s2id, '<f32>' + players[s1id]['name'] + '<r> has ' + attackDescription + ' you but it is deflected by your armor.\n')
                else:
                        players[s1id]['lastCombatAction'] = int(time.time())
                        mud.send_message(s1id, 'You miss trying to hit <f32><u>' + players[s2id]['name'] + '\n')
                        mud.send_message(s2id, '<f32><u>' + players[s1id]['name'] + '<r> missed while trying to hit you!\n')
                players[s1id]['lastCombatAction'] = int(time.time())
        else:
                mud.send_message(s1id, '<f225>Suddenly you stop. It wouldn`t be a good idea to attack <f32>' + players[s2id]['name'] + ' at this time.\n')
                fightsCopy = deepcopy(fights)
                for (fight, pl) in fightsCopy.items():
                        if fightsCopy[fight]['s1id'] == s1id and fightsCopy[fight]['s2id'] == s2id:
                                del fights[fight]

def runFightsBetweenPlayerAndNPC(mud,players,npcs,fights,fid,itemsDB,rooms,maxTerrainDifficulty,mapArea,clouds):
        s1id = fights[fid]['s1id']
        s2id = fights[fid]['s2id']

        # In the same room?
        if players[s1id]['room'] != npcs[s2id]['room']:
            return

        currRoom=players[s1id]['room']
        weightDifficulty = int(playerInventoryWeight(s1id, players, itemsDB)/20)
        temperatureDifficulty = getTemperatureDifficulty(currRoom,rooms,mapArea,clouds)
        terrainDifficulty=rooms[players[s1id]['room']]['terrainDifficulty']*10/maxTerrainDifficulty

        # Agility of player
        if int(time.time()) < players[s1id]['lastCombatAction'] + 10 - players[s1id]['agi'] - armorAgility(s1id,players,itemsDB) + terrainDifficulty + temperatureDifficulty + weightDifficulty:
            return

        if npcs[s2id]['isAttackable'] == 1:
                players[s1id]['isInCombat'] = 1
                npcs[s2id]['isInCombat'] = 1
                # Do damage to the NPC here
                luckValue=players[s1id]['luc']
                if luckValue>6:
                    luckValue=6
                if randint(1+luckValue, 10) > 5:
                        damageDescription='damage'
                        damageValue=weaponDamage(s1id,players,itemsDB)
                        armorValue=weaponDefense(s2id,npcs,itemsDB)
                        if randint(1, 20)==20:
                            damageDescription='critical damage'
                            damageValue = damageValue*2
                        npcWearsArmor(s2id,npcs,itemsDB)
                        modifier = randint(0, 10) + damageValue - armorValue
                        attackDescriptionIndex1,attackDescriptionIndex2,attackDescription = getAttackDescription()
                        if armorValue<damageValue:
                            if players[s1id]['hp'] > 0:
                                npcs[s2id]['hp'] = npcs[s2id]['hp'] - (players[s1id]['str'] + modifier)

                                mud.send_message(s1id, 'You '+ attackDescription + ' <f220>' + npcs[s2id]['name'] + '<r> for <b2><f15> * ' + str(players[s1id]['str'] + modifier)  + ' * <r> points of ' + damageDescription + '\n')
                        else:
                            if players[s1id]['hp'] > 0:
                                # Attack deflected by armor
                                mud.send_message(s1id, 'You ' + attackDescription + ' <f32><u>' + npcs[s2id]['name'] + '<r> but their armor deflects it.\n')
                else:
                        players[s1id]['lastCombatAction'] = int(time.time())
                        mud.send_message(s1id, 'You miss <f220>' + npcs[s2id]['name'] + '<r> completely!\n')
                players[s1id]['lastCombatAction'] = int(time.time())
        else:
                mud.send_message(s1id, '<f225>Suddenly you stop. It wouldn`t be a good idea to attack <u><f21>' + npcs[s2id]['name'] + '<r> at this time.\n')
                fightsCopy = deepcopy(fights)
                for (fight, pl) in fightsCopy.items():
                        if fightsCopy[fight]['s1id'] == s1id and fightsCopy[fight]['s2id'] == s2id:
                                del fights[fight]

def runFightsBetweenNPCAndPlayer(mud,players,npcs,fights,fid,items,itemsDB,rooms,maxTerrainDifficulty,mapArea,clouds):
        s1id = fights[fid]['s1id']
        s2id = fights[fid]['s2id']

        # In the same room?
        if npcs[s1id]['room'] != players[s2id]['room']:
            return

        currRoom=npcs[s1id]['room']
        weightDifficulty = int(playerInventoryWeight(s1id, npcs, itemsDB)/20)
        temperatureDifficulty = getTemperatureDifficulty(currRoom,rooms,mapArea,clouds)
        terrainDifficulty=rooms[players[s2id]['room']]['terrainDifficulty']*10/maxTerrainDifficulty

        # Agility of NPC
        if int(time.time()) < npcs[s1id]['lastCombatAction'] + 10 - npcs[s1id]['agi'] - armorAgility(s1id,npcs,itemsDB) + terrainDifficulty + temperatureDifficulty + weightDifficulty:
            return

        npcs[s1id]['isInCombat'] = 1
        players[s2id]['isInCombat'] = 1

        npcUpdateLuck(s1id, npcs, items, itemsDB)
        if npcWieldsWeapon(mud, s2id, s1id, npcs, items, itemsDB):
            return

        # Do the damage to PC here
        luckValue=npcs[s1id]['luc']
        if luckValue>6:
            luckValue=6
        if randint(1+luckValue, 10) > 5:
                damageDescription='damage'
                damageValue=weaponDamage(s1id,npcs,itemsDB)
                armorValue=weaponDefense(s2id,players,itemsDB)
                if randint(1, 20)==20:
                    damageDescription='critical damage'
                    damageValue = damageValue*2
                modifier = randint(0, 10) + damageValue - armorValue
                attackDescriptionIndex1,attackDescriptionIndex2,attackDescription = getAttackDescription()
                attackDescription=attack_types_pre2[attackDescriptionIndex1] + ' ' + attack_types_post[attackDescriptionIndex2]
                if armorValue<damageValue:
                    if npcs[s1id]['hp'] > 0:
                        players[s2id]['hp'] = players[s2id]['hp'] - (npcs[s1id]['str'] + modifier)
                        mud.send_message(s2id, '<f220>' + npcs[s1id]['name'] + '<r> has ' + attackDescription + ' you for <f15><b88> * ' + str(npcs[s1id]['str'] + modifier) + ' * <r> points of ' + damageDescription + '.\n')
                else:
                    mud.send_message(s2id, '<f220>' + npcs[s1id]['name'] + '<r> has ' + attackDescription + ' you but it is deflected by your armor.\n')
        else:
                npcs[s1id]['lastCombatAction'] = int(time.time())
                mud.send_message(s2id, '<f220>' + npcs[s1id]['name'] + '<r> has missed you completely!\n')
        npcs[s1id]['lastCombatAction'] = int(time.time())

def runFights(mud,players,npcs,fights,items,itemsDB,rooms,maxTerrainDifficulty,mapArea,clouds):
        for (fid, pl) in list(fights.items()):
                # PC -> PC
                if fights[fid]['s1type'] == 'pc' and fights[fid]['s2type'] == 'pc':
                    runFightsBetweenPlayers(mud,players,npcs,fights,fid,itemsDB,rooms,maxTerrainDifficulty,mapArea,clouds)
                # PC -> NPC
                elif fights[fid]['s1type'] == 'pc' and fights[fid]['s2type'] == 'npc':
                    runFightsBetweenPlayerAndNPC(mud,players,npcs,fights,fid,itemsDB,rooms,maxTerrainDifficulty,mapArea,clouds)
                # NPC -> PC
                elif fights[fid]['s1type'] == 'npc' and fights[fid]['s2type'] == 'pc':
                    runFightsBetweenNPCAndPlayer(mud,players,npcs,fights,fid,items,itemsDB,rooms,maxTerrainDifficulty,mapArea,clouds)
                # NPC -> NPC
                elif fights[fid]['s1type'] == 'npc' and fights[fid]['s2type'] == 'npc':
                        test = 1
