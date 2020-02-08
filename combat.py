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
from functions import stowHands
from functions import prepareSpells
from functions import randomDescription
from functions import decreaseAffinityBetweenPlayers
from random import randint
from copy import deepcopy
from environment import getTemperatureAtCoords
from proficiencies import damageProficiency
from proficiencies import defenseProficiency
from proficiencies import weaponProficiency
from traps import playerIsTrapped
import time

defenseClothing = (
    'clo_chest',
    'clo_head',
    'clo_larm',
    'clo_rarm',
    'clo_lleg',
    'clo_rleg',
    'clo_lwrist',
    'clo_rwrist')


def updateTemporaryIncapacitation(mud, players: {}, isNPC: bool) -> None:
    """Checks if players are incapacitated by spells and removes them
       after the duration has elapsed
    """
    now = int(time.time())
    for p in players:
        if players[p]['name'] is None:
            continue
        if players[p]['frozenStart'] != 0:
            if now >= players[p]['frozenStart'] + players[p]['frozenDuration']:
                players[p]['frozenStart'] = 0
                players[p]['frozenDuration'] = 0
                players[p]['frozenDescription'] = ""
                if not isNPC:
                    mud.send_message(
                        p, "<f220>You find that you can move again.<r>\n\n")


def updateTemporaryHitPoints(mud, players: {}, isNPC: bool) -> None:
    """Updates any hit points added for a temporary period
       as the result of a spell
    """
    now = int(time.time())
    for p in players:
        if players[p]['name'] is None:
            continue
        if players[p]['tempHitPoints'] == 0:
            continue
        if players[p]['tempHitPointsStart'] == 0 and \
           players[p]['tempHitPointsDuration'] > 0:
            players[p]['tempHitPointsStart'] = now
        else:
            if now > players[p]['tempHitPointsStart'] + \
                    players[p]['tempHitPointsDuration']:
                players[p]['tempHitPoints'] = 0
                players[p]['tempHitPointsStart'] = 0
                players[p]['tempHitPointsDuration'] = 0
                if not isNPC:
                    mud.send_message(
                        p, "<f220>Your magical protection expires.<r>\n\n")

def updateTemporaryCharm(mud, players: {}, isNPC: bool) -> None:
    """Updates any charm added for a temporary period
       as the result of a spell
    """
    now = int(time.time())
    for p in players:
        if players[p]['name'] is None:
            continue
        if players[p]['tempCharm'] == 0:
            continue
        if players[p]['tempCharmStart'] == 0 and \
           players[p]['tempCharmDuration'] > 0:
            players[p]['tempCharmStart'] = now
        else:
            if not players[p].get('tempCharmDuration'):
                return
            if now > players[p]['tempCharmStart'] + \
                    players[p]['tempCharmDuration']:
                players[p]['tempCharmStart'] = 0
                players[p]['tempCharmDuration'] = 0
                if players[p]['affinity'].get(players[p]['tempCharmTarget']):
                    players[p]['affinity'][players[p]['tempCharmTarget']]-=players[p]['tempCharm']
                players[p]['tempCharm'] = 0
                if not isNPC:
                    mud.send_message(
                        p, "<f220>A charm spell wears off.<r>\n\n")

def playersRest(mud, players: {}) -> None:
    """Rest restores hit points
    """
    for p in players:
        if players[p]['name'] is not None and players[p]['authenticated'] is not None:
            if players[p]['hp'] < players[p]['hpMax'] + \
                    players[p]['tempHitPoints']:
                if randint(0, 100) > 90:
                    players[p]['hp'] += 1
            else:
                players[p]['hp'] = players[p]['hpMax'] + \
                    players[p]['tempHitPoints']
                players[p]['restRequired'] = 0
                prepareSpells(mud, p, players)


def itemInNPCInventory(npcs, id: int, itemName: str, itemsDB: {}) -> bool:
    if len(list(npcs[id]['inv'])) > 0:
        itemNameLower = itemName.lower()
        for i in list(npcs[id]['inv']):
            if itemsDB[int(i)]['name'].lower() == itemNameLower:
                return True
    return False


def npcUpdateLuck(nid, npcs: {}, items: {}, itemsDB: {}) -> None:
    """Calculate the luck of an NPC based on what items they are carrying
    """
    luck = 0
    for i in npcs[nid]['inv']:
        luck = luck + itemsDB[int(i)]['mod_luc']
    npcs[nid]['luc'] = luck


def npcWieldsWeapon(mud, id: int, nid, npcs: {}, items: {}, itemsDB: {}) -> bool:
    """what is the best weapon which the NPC is carrying?
    """
    itemID = 0
    max_protection = 0
    max_damage = 0
    if int(npcs[nid]['canWield']) != 0:
        for i in npcs[nid]['inv']:
            if itemsDB[int(i)]['clo_rhand'] > 0:
                if itemsDB[int(i)]['mod_str'] > max_damage:
                    max_damage = itemsDB[int(i)]['mod_str']
                    itemID = int(i)

    putOnArmor = False
    if int(npcs[nid]['canWear']) != 0:
        for i in npcs[nid]['inv']:
            if itemsDB[int(i)]['clo_chest'] > 0:
                if itemsDB[int(i)]['mod_endu'] > max_protection:
                    max_protection = itemsDB[int(i)]['mod_endu']
                    itemID = int(i)
                    putOnArmor = True

    # search for any weapons on the floor
    pickedUpWeapon = False
    itemWeaponIndex = 0
    if int(npcs[nid]['canWield']) != 0:
        itemsInWorldCopy = deepcopy(items)
        for (iid, pl) in list(itemsInWorldCopy.items()):
            if itemsInWorldCopy[iid]['room'] == npcs[nid]['room']:
                if itemsDB[items[iid]['id']]['weight'] > 0:
                    if itemsDB[items[iid]['id']]['clo_rhand'] > 0:
                        if itemsDB[items[iid]['id']]['mod_str'] > max_damage:
                            itemName = itemsDB[items[iid]['id']]['name']
                            if not itemInNPCInventory(
                                    npcs, nid, itemName, itemsDB):
                                max_damage = itemsDB[items[iid]
                                                     ['id']]['mod_str']
                                itemID = int(items[iid]['id'])
                                itemWeaponIndex = iid
                                pickedUpWeapon = True

    # Search for any armor on the floor
    pickedUpArmor = False
    itemArmorIndex = 0
    if int(npcs[nid]['canWear']) != 0:
        for (iid, pl) in list(itemsInWorldCopy.items()):
            if itemsInWorldCopy[iid]['room'] == npcs[nid]['room']:
                if itemsDB[items[iid]['id']]['weight'] > 0:
                    if itemsDB[items[iid]['id']]['clo_chest'] > 0:
                        if itemsDB[items[iid]['id']
                                   ]['mod_endu'] > max_protection:
                            itemName = itemsDB[items[iid]['id']]['name']
                            if not itemInNPCInventory(
                                    npcs, nid, itemName, itemsDB):
                                max_protection = itemsDB[items[iid]
                                                         ['id']]['mod_endu']
                                itemID = int(items[iid]['id'])
                                itemArmorIndex = iid
                                pickedUpArmor = True

    if itemID > 0:
        if putOnArmor:
            if npcs[nid]['clo_chest'] != itemID:
                npcs[nid]['clo_chest'] = itemID
                mud.send_message(
                    id,
                    '<f220>' +
                    npcs[nid]['name'] +
                    '<r> puts on ' +
                    itemsDB[itemID]['article'] +
                    ' ' +
                    itemsDB[itemID]['name'] +
                    '\n')
                return True
            return False

        if pickedUpArmor:
            if npcs[nid]['clo_chest'] != itemID:
                npcs[nid]['inv'].append(str(itemID))
                npcs[nid]['clo_chest'] = itemID
                del items[itemArmorIndex]
                mud.send_message(
                    id,
                    '<f220>' +
                    npcs[nid]['name'] +
                    '<r> picks up and wears ' +
                    itemsDB[itemID]['article'] +
                    ' ' +
                    itemsDB[itemID]['name'] +
                    '\n')
                return True
            return False

        if npcs[nid]['clo_rhand'] != itemID:
            # Transfer weapon to hand
            npcs[nid]['clo_rhand'] = itemID
            npcs[nid]['clo_lhand'] = 0
            if pickedUpWeapon:
                npcs[nid]['inv'].append(str(itemID))
                del items[itemWeaponIndex]
                mud.send_message(
                    id,
                    '<f220>' +
                    npcs[nid]['name'] +
                    '<r> picks up ' +
                    itemsDB[itemID]['article'] +
                    ' ' +
                    itemsDB[itemID]['name'] +
                    '\n')
            else:
                mud.send_message(
                    id,
                    '<f220>' +
                    npcs[nid]['name'] +
                    '<r> has drawn their ' +
                    itemsDB[itemID]['name'] +
                    '\n')
            return True

    return False


def npcWearsArmor(id: int, npcs: {}, itemsDB: {}) -> None:
    """An NPC puts on armor
    """
    if len(npcs[id]['inv']) == 0:
        return

    for c in defenseClothing:
        itemID = 0
        # what is the best defense which the NPC is carrying?
        max_defense = 0
        for i in npcs[id]['inv']:
            if itemsDB[int(i)][c] > 0:
                if itemsDB[int(i)]['mod_str'] == 0:
                    if itemsDB[int(i)]['mod_endu'] > max_defense:
                        max_defense = itemsDB[int(i)]['mod_endu']
                        itemID = int(i)
        if itemID > 0:
            # Wear the armor
            npcs[id][c] = itemID


def weaponDamage(id: int, players: {}, itemsDB: {}, weaponType: str, characterClassDB: {}) -> int:
    """Calculates the amount of damage which a player can do
       with weapons held
    """
    damage = 0

    itemID = players[id]['clo_lhand']
    if itemID > 0:
        damage = damage + itemsDB[itemID]['mod_str']

    itemID = players[id]['clo_rhand']
    if itemID > 0:
        damage = damage + itemsDB[itemID]['mod_str']

    # Extra damage based on proficiencies
    if damage > 0:
        damageProficiency(id, players, weaponType, characterClassDB)

    # Total damage inflicted by weapons
    return damage


def raceResistance(id: int, players: {}, racesDB: {}, weaponType: str) -> int:
    """How much resistance does the player have to the weapon type
       based upon their race
    """
    resistance = 0
    resistParam = 'resist_' + weaponType.lower()

    if weaponType.endswith('bow'):
        resistParam = 'resist_piercing'

    if weaponType.endswith('sling'):
        resistParam = 'resist_bludgeoning'

    if players[id].get('race'):
        race = players[id]['race'].lower()
        if racesDB.get(race):
            if racesDB[race].get(resistParam):
                resistance = racesDB[race][resistParam]

    return resistance


def weaponDefense(id: int, players: {}, itemsDB: {}, racesDB: {}, weaponType: str, characterClassDB: {}) -> int:
    """How much defense does a player have due to armor worn?
    """
    defense = raceResistance(id, players, racesDB, weaponType)

    for c in defenseClothing:
        itemID = int(players[id][c])
        if itemID > 0:
            defense = defense + int(itemsDB[itemID]['mod_endu'])

    if defense > 0:
        defenseProficiency(id, players, characterClassDB)

    # Total defense by shields or clothing
    return defense


def armorAgility(id: int, players: {}, itemsDB: {}) -> int:
    """Modify agility based on armor worn
    """
    agility = 0

    for c in defenseClothing:
        itemID = int(players[id][c])
        if itemID > 0:
            agility = agility + int(itemsDB[itemID]['mod_agi'])

    # Total agility for clothing
    return agility


def canUseWeapon(id: int, players: {}, itemsDB: {}, itemID: int) -> bool:
    if itemID == 0:
        return True
    lockItemID = itemsDB[itemID]['lockedWithItem']
    if lockItemID > 0:
        itemName = itemsDB[lockItemID]['name']
        for i in list(players[id]['inv']):
            if itemsDB[int(i)]['name'] == itemName:
                return True
        return False
    return True


def getWeaponHeld(id: int, players: {}, itemsDB: {}) -> (int,str,int):
    """Returns the type of weapon held, or fists if none is held and the rounds of fire
    """
    if players[id]['clo_rhand'] > 0 and players[id]['clo_lhand'] == 0:
        # something in right hand
        itemID = int(players[id]['clo_rhand'])
        if itemsDB[itemID]['mod_str'] > 0:
            if len(itemsDB[itemID]['type']) > 0:
                return itemID, itemsDB[itemID]['type'], itemsDB[itemID]['rof']

    if players[id]['clo_lhand'] > 0 and players[id]['clo_rhand'] == 0:
        # something in left hand
        itemID = int(players[id]['clo_lhand'])
        if itemsDB[itemID]['mod_str'] > 0:
            if len(itemsDB[itemID]['type']) > 0:
                return itemID, itemsDB[itemID]['type'], itemsDB[itemID]['rof']

    if players[id]['clo_lhand'] > 0 and players[id]['clo_rhand'] > 0:
        # something in both hands
        itemRightID = int(players[id]['clo_rhand'])
        itemLeftID = int(players[id]['clo_lhand'])
        if randint(0, 1) == 1:
            if itemsDB[itemRightID]['mod_str'] > 0:
                if len(itemsDB[itemRightID]['type']) > 0:
                    return itemRightID, itemsDB[itemRightID]['type'], itemsDB[itemRightID]['rof']
            if itemsDB[itemLeftID]['mod_str'] > 0:
                if len(itemsDB[itemLeftID]['type']) > 0:
                    return itemLeftID, itemsDB[itemLeftID]['type'], itemsDB[itemLeftID]['rof']
        else:
            if itemsDB[itemLeftID]['mod_str'] > 0:
                if len(itemsDB[itemLeftID]['type']) > 0:
                    return itemLeftID, itemsDB[itemLeftID]['type'], itemsDB[itemLeftID]['rof']
            if itemsDB[itemRightID]['mod_str'] > 0:
                if len(itemsDB[itemRightID]['type']) > 0:
                    return itemRightID, itemsDB[itemRightID]['type'], itemsDB[itemRightID]['rof']
    return 0, "fists", 1


def getAttackDescription(animalType: str,weaponType: str) -> (str,str):
    """Describes an attack with a given type of weapon. This
       Returns both the first person and second person
       perspective descriptions
    """
    weaponType = weaponType.lower()

    if not animalType:
        attackStrings = [
            "swing a fist at",
            "punch",
            "crudely swing a fist at",
            "ineptly punch"
        ]
    else:
        if animalType is not 'bird':
            attackStrings = [
                "savage",
                "maul",
                "bite",
                "viciously bite",
                "savagely gnaw"
            ]
        else:
            attackStrings = [
                "claw",
                "peck",
                "viciously peck",
                "savagely peck"
            ]

    attackDescriptionFirst = \
        attackStrings[randint(0, len(attackStrings) - 1)]

    if not animalType:
        attackStrings = [
            "swung a fist at",
            "punched",
            "crudely swung a fist at",
            "ineptly punched"
        ]
    else:
        if animalType is not 'bird':
            attackStrings = [
                "savaged",
                "mauled",
                "took a bite at",
                "viciously bit into",
                "savagely gnawed into"
            ]
        else:
            attackStrings = [
                "clawed",
                "pecked",
                "viciously pecked",
                "savagely pecked"
            ]

    attackDescriptionSecond = \
        attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("acid"):
        attackStrings = ["corrode", "spray", "splash"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["corroded", "sprayed", "splashed"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("bludg"):
        attackStrings = [
            "deliver a crushing blow on",
            "strike at",
            "swing at",
            "swing clumsily at",
            "strike a blow on"
        ]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = [
            "delivered a crushing blow on",
            "struck at",
            "swung at",
            "swung clumsily at",
            "struck a blow on"
        ]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("cold"):
        attackStrings = ["freeze", "chill"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["froze", "chilled"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("fire"):
        attackStrings = [
            "cast a ball a of flame at",
            "cast a fireball at",
            "cast a burning sphere at"
        ]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = [
            "casted a ball a of flame at",
            "casted a fireball at",
            "casted a burning sphere at"
        ]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("force"):
        attackStrings = ["point at", "wave at"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["pointed at", "waved at"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("lightning"):
        attackStrings = [
            "cast a bolt of lightning at",
            "cast a lightning bolt at"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = [
            "casted a bolt of lightning at",
            "casted a lightning bolt at"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("necro"):
        attackStrings = ["whither", "chill"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["whithered", "chilled"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("pierc"):
        attackStrings = ["stab at", "hack at"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["stabbed at", "hacked at"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("poison"):
        attackStrings = ["poison"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["poisoned"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("psy"):
        attackStrings = ["psychically blast", "psychically deplete"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["psychically blasted", "psychically depleted"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("radiant"):
        attackStrings = ["sear", "scorch"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["seared", "scorched"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("slash"):
        attackStrings = [
            "cut at",
            "cut savagely into",
            "slash at",
            "swing at",
            "swing clumsily at"
        ]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = [
            "cut at",
            "cut savagely into",
            "slashed at",
            "swung at",
            "swung clumsily at"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("thunder"):
        attackStrings = ["cast a thunderbolt at", "cast a bolt of thunder at"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = [
            "casted a thunderbolt at",
            "casted a bolt of thunder at"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("ranged bow") or \
       weaponType.startswith("ranged shortbow") or \
       weaponType.startswith("ranged longbow"):
        attackStrings = ["fire an arrow at", "release an arrow at"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["fired an arrow at", "released an arrow at"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("ranged crossbow"):
        attackStrings = ["fire a bolt at", "release a bolt at"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["fired a bolt at", "released a bolt at"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("ranged sling"):
        attackStrings = ["sling a rock at"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["slung a rock at"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    if weaponType.startswith("ranged dart"):
        attackStrings = ["blow a dart at"]
        attackDescriptionFirst = \
            attackStrings[randint(0, len(attackStrings) - 1)]
        attackStrings = ["blew a dart at"]
        attackDescriptionSecond = \
            attackStrings[randint(0, len(attackStrings) - 1)]

    return attackDescriptionFirst, attackDescriptionSecond


def getTemperatureDifficulty(rm: str, rooms: {}, mapArea: [], clouds: {}) -> int:
    """Returns a difficulty factor based on the ambient
       temperature
    """
    temperature = getTemperatureAtCoords(
        rooms[rm]['coords'], rooms, mapArea, clouds)

    if temperature > 5:
        # Things get difficult when hotter
        return int(temperature / 4)
    # Things get difficult in snow/ice
    return -(temperature - 5)


def attackRoll(luck: int) -> bool:
    """Did an attack succeed?
    """
    if luck > 6:
        luck = 6
    if randint(1 + luck, 10) > 5:
        return True
    return False


def criticalHit() -> bool:
    """Is this a critical hit (extra damage)?
    """
    if randint(1, 20) == 20:
        return True
    return False


def calculateDamage(weapons: int, defense: int) -> (int,int,str):
    """Returns the amount of damage an attack causes
    """
    damageDescription = 'damage'
    damageValue = weapons
    armorClass = defense
    if criticalHit():
        damageDescription = 'critical damage'
        damageValue = damageValue * 2
    return damageValue, armorClass, damageDescription


def runFightsBetweenPlayers(
        mud,
        players: {},
        npcs: {},
        fights,
        fid,
        itemsDB: {},
        rooms: {},
        maxTerrainDifficulty,
        mapArea: [],
        clouds: {},
        racesDB: {},
        characterClassDB: {},
        guilds: {}):
    """A fight between two players
    """
    s1id = fights[fid]['s1id']
    s2id = fights[fid]['s2id']

    # In the same room?
    if players[s1id]['room'] != players[s2id]['room']:
        return

    # is the player frozen?
    if players[s1id]['frozenStart'] > 0 or players[s1id]['canAttack'] == 0:
        mud.send_message(
            s2id, \
            randomDescription(players[s1id]['frozenDescription']) + '\n')
        return

    if playerIsTrapped(s1id,players,rooms):
        return

    currRoom = players[s1id]['room']
    weightDifficulty = \
        int(playerInventoryWeight(s1id, players, itemsDB) / 20)
    temperatureDifficulty = getTemperatureDifficulty(
        currRoom, rooms, mapArea, clouds)
    terrainDifficulty = \
        rooms[players[s1id]['room']]['terrainDifficulty'] * \
        10 / maxTerrainDifficulty

    # Agility of player
    if int(time.time()) < \
       players[s1id]['lastCombatAction'] + \
       10 - players[s1id]['agi'] - \
       armorAgility(s1id, players, itemsDB) + \
       terrainDifficulty + temperatureDifficulty + weightDifficulty:
        return

    if players[s2id]['isAttackable'] == 1:
        players[s1id]['isInCombat'] = 1
        players[s2id]['isInCombat'] = 1

        weaponID, weaponType, roundsOfFire = \
            getWeaponHeld(s1id, players, itemsDB)
        if not canUseWeapon(s1id, players, itemsDB, weaponID):
            lockItemID = itemsDB[weaponID]['lockedWithItem']
            mud.send_message(
                s1id,'You take aim, but find you have no ' +
                itemsDB[lockItemID]['name'].lower() + '.\n')
            mud.send_message(
                s2id,'<f32>' +
                players[s1id]['name'] +
                '<r> takes aim, but finds they have no ' +
                itemsDB[lockItemID]['name'].lower() + '.\n')
            stowHands(s1id, players, itemsDB, mud)
            mud.send_message(
                s2id,'<f32>' +
                players[s1id]['name'] +
                '<r> stows ' +
                itemsDB[itemID]['article'] +
                ' <b234>' +
                itemsDB[itemID]['name'] + '\n\n')
            players[s1id]['lastCombatAction'] = int(time.time())
            return

        # Do damage to the PC here
        if attackRoll(
            players[s1id]['luc'] +
            weaponProficiency(
                s1id,
                players,
                weaponType,
                characterClassDB)):
            damageValue, armorClass, damageDescription = \
                calculateDamage(weaponDamage(s1id, players, itemsDB, weaponType, characterClassDB), \
                                weaponDefense(s2id, players, itemsDB, racesDB, weaponType, characterClassDB))
            if roundsOfFire < 1:
                roundsOfFire = 1
            attackDescriptionFirst, attackDescriptionSecond = \
                getAttackDescription("",weaponType)
            if armorClass <= damageValue:
                if players[s1id]['hp'] > 0:
                    modifierStr = ''
                    for firingRound in range(roundsOfFire):
                        modifier = randint(
                            0, 10) + (damageValue * roundsOfFire) - armorClass
                        damagePoints = players[s1id]['str'] + modifier
                        if damagePoints < 0:
                            damagePoints = 0
                        players[s2id]['hp'] = \
                            players[s2id]['hp'] - damagePoints
                        if len(modifierStr) == 0:
                            modifierStr = modifierStr + str(damagePoints)
                        else:
                            modifierStr = \
                                modifierStr + \
                                ' + ' + str(damagePoints)

                    decreaseAffinityBetweenPlayers(
                        players,s2id,players,s1id,guilds)
                    decreaseAffinityBetweenPlayers(
                        players,s1id,players,s2id,guilds)
                    mud.send_message(
                        s1id,'You ' + \
                        attackDescriptionFirst + \
                        ' <f32><u>' + \
                        players[s2id]['name'] + \
                        '<r> for <f15><b2> * ' + \
                        modifierStr + \
                        ' *<r> points of ' + \
                        damageDescription + '.\n')
                    mud.send_message(
                        s2id,'<f32>' + \
                        players[s1id]['name'] + \
                        '<r> has ' + \
                        attackDescriptionSecond + \
                        ' you for <f15><b88> * ' + \
                        modifierStr + \
                        ' *<r> points of ' + \
                        damageDescription + '.\n')
            else:
                if players[s1id]['hp'] > 0:
                    # Attack deflected by armor
                    mud.send_message(
                        s1id,'You ' + \
                        attackDescriptionFirst + \
                        ' <f32><u>' + \
                        players[s2id]['name'] + \
                        '<r> but their armor deflects it.\n')
                    mud.send_message(
                        s2id,'<f32>' + \
                        players[s1id]['name'] + \
                        '<r> has ' + \
                        attackDescriptionSecond + \
                        ' you but it is deflected by your armor.\n')
        else:
            players[s1id]['lastCombatAction'] = int(time.time())
            mud.send_message(
                s1id,'You miss trying to hit <f32><u>' + \
                players[s2id]['name'] + '\n')
            mud.send_message(
                s2id,'<f32><u>' + \
                players[s1id]['name'] + \
                '<r> missed while trying to hit you!\n')
        players[s1id]['lastCombatAction'] = int(time.time())
    else:
        mud.send_message(
            s1id, \
            '<f225>Suddenly you stop. It wouldn`t be a good idea to attack <f32>' + \
            players[s2id]['name'] + \
            ' at this time.\n')
        fightsCopy = deepcopy(fights)
        for (fight, pl) in fightsCopy.items():
            if fightsCopy[fight]['s1id'] == s1id and fightsCopy[fight]['s2id'] == s2id:
                del fights[fight]


def runFightsBetweenPlayerAndNPC(
        mud,
        players: {},
        npcs: {},
        fights,
        fid,
        itemsDB: {},
        rooms: {},
        maxTerrainDifficulty,
        mapArea: [],
        clouds: {},
        racesDB: {},
        characterClassDB: {},
        guilds: {}):
    """Fight between a player and an NPC
    """
    s1id = fights[fid]['s1id']
    s2id = fights[fid]['s2id']

    # In the same room?
    if players[s1id]['room'] != npcs[s2id]['room']:
        return

    # is the player frozen?
    if players[s1id]['frozenStart'] > 0 or players[s1id]['canAttack'] == 0:
        mud.send_message(
            s2id, randomDescription(
                players[s1id]['frozenDescription']) + '\n')
        return

    if playerIsTrapped(s1id,players,rooms):
        return

    currRoom = players[s1id]['room']
    weightDifficulty = int(playerInventoryWeight(s1id, players, itemsDB) / 20)
    temperatureDifficulty = getTemperatureDifficulty(
        currRoom, rooms, mapArea, clouds)
    terrainDifficulty = rooms[players[s1id]['room']
                              ]['terrainDifficulty'] * 10 / maxTerrainDifficulty

    # Agility of player
    if int(time.time()) < players[s1id]['lastCombatAction'] + 10 - players[s1id]['agi'] - armorAgility(
            s1id, players, itemsDB) + terrainDifficulty + temperatureDifficulty + weightDifficulty:
        return

    if npcs[s2id]['isAttackable'] == 1:
        players[s1id]['isInCombat'] = 1
        npcs[s2id]['isInCombat'] = 1

        weaponID, weaponType, roundsOfFire = getWeaponHeld(
            s1id, players, itemsDB)
        if not canUseWeapon(s1id, players, itemsDB, weaponID):
            lockItemID = itemsDB[weaponID]['lockedWithItem']
            mud.send_message(
                s1id,
                'You take aim, but find you have no ' +
                itemsDB[lockItemID]['name'].lower() +
                '.\n')
            stowHands(s1id, players, itemsDB, mud)
            players[s1id]['lastCombatAction'] = int(time.time())
            return

        # Do damage to the NPC here
        if attackRoll(
            players[s1id]['luc'] +
            weaponProficiency(
                s1id,
                players,
                weaponType,
                characterClassDB)):
            damageValue, armorClass, damageDescription = calculateDamage(
                weaponDamage(
                    s1id, players, itemsDB, weaponType, characterClassDB), weaponDefense(
                    s2id, npcs, itemsDB, racesDB, weaponType, characterClassDB))

            npcWearsArmor(s2id, npcs, itemsDB)

            if roundsOfFire < 1:
                roundsOfFire = 1
            attackDescriptionFirst, attackDescriptionSecond = \
                getAttackDescription("",weaponType)
            if armorClass <= damageValue:
                if players[s1id]['hp'] > 0:
                    modifierStr = ''
                    for firingRound in range(roundsOfFire):
                        modifier = randint(0, 10) + damageValue - armorClass
                        damagePoints = players[s1id]['str'] + modifier
                        if damagePoints < 0:
                            damagePoints = 0
                        npcs[s2id]['hp'] = npcs[s2id]['hp'] - damagePoints
                        if len(modifierStr) == 0:
                            modifierStr = modifierStr + str(damagePoints)
                        else:
                            modifierStr = modifierStr + \
                                ' + ' + str(damagePoints)

                    decreaseAffinityBetweenPlayers(npcs,s2id,players,s1id,guilds)
                    decreaseAffinityBetweenPlayers(players,s1id,npcs,s2id,guilds)
                    mud.send_message(
                        s1id,
                        'You ' +
                        attackDescriptionFirst +
                        ' <f220>' +
                        npcs[s2id]['name'] +
                        '<r> for <b2><f15> * ' +
                        modifierStr +
                        ' * <r> points of ' +
                        damageDescription +
                        '\n')
            else:
                if players[s1id]['hp'] > 0:
                    # Attack deflected by armor
                    mud.send_message(
                        s1id,
                        'You ' +
                        attackDescriptionFirst +
                        ' <f32><u>' +
                        npcs[s2id]['name'] +
                        '<r> but their armor deflects it.\n')
        else:
            players[s1id]['lastCombatAction'] = int(time.time())
            mud.send_message(
                s1id,
                'You miss <f220>' +
                npcs[s2id]['name'] +
                '<r> completely!\n')
        players[s1id]['lastCombatAction'] = int(time.time())
    else:
        mud.send_message(
            s1id,
            '<f225>Suddenly you stop. It wouldn`t be a good idea to attack <u><f21>' +
            npcs[s2id]['name'] +
            '<r> at this time.\n')
        fightsCopy = deepcopy(fights)
        for (fight, pl) in fightsCopy.items():
            if fightsCopy[fight]['s1id'] == s1id and fightsCopy[fight]['s2id'] == s2id:
                del fights[fight]


def runFightsBetweenNPCAndPlayer(
        mud,
        players: {},
        npcs: {},
        fights,
        fid,
        items: {},
        itemsDB: {},
        rooms: {},
        maxTerrainDifficulty,
        mapArea,
        clouds: {},
        racesDB: {},
        characterClassDB: {},
        guilds: {}):
    """Fight between NPC and player
    """
    s1id = fights[fid]['s1id']
    s2id = fights[fid]['s2id']

    # In the same room?
    if npcs[s1id]['room'] != players[s2id]['room']:
        return

    # is the player frozen?
    if npcs[s1id]['frozenStart'] > 0:
        mud.send_message(
            s2id,
            '<f220>' +
            npcs[s1id]['name'] +
            "<r> tries to attack but can't move\n")
        return

    currRoom = npcs[s1id]['room']
    weightDifficulty = int(playerInventoryWeight(s1id, npcs, itemsDB) / 20)
    temperatureDifficulty = getTemperatureDifficulty(
        currRoom, rooms, mapArea, clouds)
    terrainDifficulty = rooms[players[s2id]['room']
                              ]['terrainDifficulty'] * 10 / maxTerrainDifficulty

    # Agility of NPC
    if int(time.time()) < npcs[s1id]['lastCombatAction'] + 10 - npcs[s1id]['agi'] - armorAgility(
            s1id, npcs, itemsDB) + terrainDifficulty + temperatureDifficulty + weightDifficulty:
        return

    npcs[s1id]['isInCombat'] = 1
    players[s2id]['isInCombat'] = 1

    npcUpdateLuck(s1id, npcs, items, itemsDB)
    if npcWieldsWeapon(mud, s2id, s1id, npcs, items, itemsDB):
        return

    weaponID, weaponType, roundsOfFire = getWeaponHeld(s1id, npcs, itemsDB)

    # Do the damage to PC here
    if attackRoll(npcs[s1id]['luc'] +
                  weaponProficiency(s1id, npcs, weaponType, characterClassDB)):
        damageValue, armorClass, damageDescription = calculateDamage(
            weaponDamage(
                s1id, npcs, itemsDB, weaponType, characterClassDB), weaponDefense(
                s2id, players, itemsDB, racesDB, weaponType, characterClassDB))
        if roundsOfFire < 1:
            roundsOfFire = 1
        attackDescriptionFirst, attackDescriptionSecond = \
            getAttackDescription(npcs[s1id]['animalType'],weaponType)
        if armorClass <= damageValue:
            if npcs[s1id]['hp'] > 0:
                modifierStr = ''
                for firingRound in range(roundsOfFire):
                    modifier = randint(
                        0, 10) + damageValue - armorClass - npcs[s1id]['tempHitPoints']
                    damagePoints = npcs[s1id]['str'] + modifier
                    if damagePoints < 0:
                        damagePoints = 0
                    players[s2id]['hp'] = players[s2id]['hp'] - damagePoints
                    if len(modifierStr) == 0:
                        modifierStr = modifierStr + str(damagePoints)
                    else:
                        modifierStr = modifierStr + ' + ' + str(damagePoints)
                decreaseAffinityBetweenPlayers(npcs,s1id,players,s2id,guilds)
                decreaseAffinityBetweenPlayers(players,s2id,npcs,s1id,guilds)
                mud.send_message(
                    s2id,
                    '<f220>' +
                    npcs[s1id]['name'] +
                    '<r> has ' +
                    attackDescriptionSecond +
                    ' you for <f15><b88> * ' +
                    modifierStr +
                    ' * <r> points of ' +
                    damageDescription +
                    '.\n')
        else:
            mud.send_message(
                s2id,
                '<f220>' +
                npcs[s1id]['name'] +
                '<r> has ' +
                attackDescriptionSecond +
                ' you but it is deflected by your armor.\n')
    else:
        npcs[s1id]['lastCombatAction'] = int(time.time())
        mud.send_message(
            s2id,
            '<f220>' +
            npcs[s1id]['name'] +
            '<r> has missed you completely!\n')
    npcs[s1id]['lastCombatAction'] = int(time.time())


def runFights(
        mud,
        players: {},
        npcs: {},
        fights,
        items: {},
        itemsDB: {},
        rooms: {},
        maxTerrainDifficulty,
        mapArea: [],
        clouds: {},
        racesDB: {},
        characterClassDB: {},
        guilds: {}):
    """Handles fights
    """
    for (fid, pl) in list(fights.items()):
        # PC -> PC
        if fights[fid]['s1type'] == 'pc' and fights[fid]['s2type'] == 'pc':
            runFightsBetweenPlayers(
                mud,
                players,
                npcs,
                fights,
                fid,
                itemsDB,
                rooms,
                maxTerrainDifficulty,
                mapArea,
                clouds,
                racesDB,
                characterClassDB,
                guilds)
        # PC -> NPC
        elif fights[fid]['s1type'] == 'pc' and fights[fid]['s2type'] == 'npc':
            runFightsBetweenPlayerAndNPC(
                mud,
                players,
                npcs,
                fights,
                fid,
                itemsDB,
                rooms,
                maxTerrainDifficulty,
                mapArea,
                clouds,
                racesDB,
                characterClassDB,
                guilds)
        # NPC -> PC
        elif fights[fid]['s1type'] == 'npc' and fights[fid]['s2type'] == 'pc':
            runFightsBetweenNPCAndPlayer(
                mud,
                players,
                npcs,
                fights,
                fid,
                items,
                itemsDB,
                rooms,
                maxTerrainDifficulty,
                mapArea,
                clouds,
                racesDB,
                characterClassDB,
                guilds)
        # NPC -> NPC
        elif fights[fid]['s1type'] == 'npc' and fights[fid]['s2type'] == 'npc':
            test = 1

            
def isAttacking(players: {},id,fights: {}) -> bool:
    """Returns true if the given player is attacking
    """
    for (fight, pl) in fights.items():
        if fights[fight]['s1'] == players[id]['name']:
            return True
    return False


def getAttackingTarget(players: {},id,fights: {}):
    """Return the player or npc which is the target of an attack
    """
    for (fight, pl) in fights.items():
        if fights[fight]['s1'] == players[id]['name']:
            return fights[fight]['s2']
    return None


def playerBeginsAttack(players: {},id,target: str,npcs: {},fights: {},mud) -> bool:
    """Player begins an attack on another player or npc
    """
    targetFound = False
    if players[id]['name'].lower() == target.lower():
        mud.send_message(
            id, \
            'You attempt hitting yourself and realise this might not be the most productive way of using your time.\n')
        return targetFound

    for (pid, pl) in players.items():
        if players[pid]['authenticated'] and \
           players[pid]['name'].lower() == target.lower():
            targetFound = True
            victimId = pid
            attackerId = id
            if players[pid]['room'] != players[id]['room']:
                targetFound = False
                continue

            fights[len(fights)] = {
                's1': players[id]['name'],
                's2': target,
                's1id': attackerId,
                's2id': victimId,
                's1type': 'pc',
                's2type': 'pc',
                'retaliated': 0
            }
            mud.send_message(
                id, '<f214>Attacking <r><f255>' + target + '!\n')
            # addToScheduler('0|msg|<b63>You are being attacked by ' + players[id]['name'] + "!", pid, eventSchedule, eventDB)

    if not targetFound:
        for (nid, pl) in list(npcs.items()):
            if target.lower() not in npcs[nid]['name'].lower():
                continue

            victimId = nid
            attackerId = id
            # found target npc
            if npcs[nid]['room'] == players[id]['room'] and \
               targetFound == False:
                targetFound = True
                # target found!
                if players[id]['room'] != npcs[nid]['room']:
                    continue

                # check for familiar
                if npcs[nid]['familiarOf'] == players[id]['name']:                        
                    mud.send_message(
                        id, \
                        randomDescription("You can't attack your own familiar|You consider attacking your own familiar, but decide against it|Your familiar looks at you disapprovingly")+"\n\n")
                    return False

                if npcs[nid]['isAttackable']==0:
                    mud.send_message(id,"You can't attack them\n\n")
                    return False

                fights[len(fights)] = {
                    's1': players[id]['name'],
                    's2': nid,
                    's1id': attackerId,
                    's2id': victimId,
                    's1type': 'pc',
                    's2type': 'npc',
                    'retaliated': 0
                }                        
                mud.send_message(
                    id, 'Attacking <u><f21>' + npcs[nid]['name'] + '<r>!\n')

    if not targetFound:
        mud.send_message(
            id, 'You cannot see ' + target + ' anywhere nearby.\n')
    return targetFound


def npcBeginsAttack(npcs: {},id,target: str,players: {},fights: {},mud) -> bool:
    """npc begins an attack on a player or another npc
    """
    targetFound = False
    if npcs[id]['name'].lower() == target.lower():
        return targetFound

    for (pid, pl) in players.items():
        if players[pid]['authenticated'] and \
           players[pid]['name'].lower() == target.lower():
            targetFound = True
            victimId = pid
            attackerId = id
            if players[pid]['room'] != npcs[id]['room']:
                targetFound = False
                continue

            fights[len(fights)] = {
                's1': id,
                's2': players[pid]['name'],
                's1id': attackerId,
                's2id': victimId,
                's1type': 'npc',
                's2type': 'pc',
                'retaliated': 0
            }
            fights[len(fights)] = {
                's1': players[pid]['name'],
                's2': id,
                's1id': victimId,
                's2id': attackerId,
                's1type': 'pc',
                's2type': 'npc',
                'retaliated': 0
            }
            players[pid]['isInCombat'] = 1
            npcs[id]['isInCombat'] = 1
            mud.send_message(
                pid, '<u><f21>'+npcs[id]['name']+'<r> attacks!\n')

            # addToScheduler('0|msg|<b63>You are being attacked by ' + players[id]['name'] + "!", pid, eventSchedule, eventDB)

    if not targetFound:
        for (nid, pl) in list(npcs.items()):
            if target.lower() not in npcs[nid]['name'].lower():
                continue
            if npcs[nid]['isAttackable']==0:
                continue

            victimId = nid
            attackerId = id
            # found target npc
            if npcs[nid]['room'] == npcs[id]['room'] and \
               targetFound == False:
                targetFound = True
                # target found!
                if npcs[id]['room'] != npcs[nid]['room']:
                    continue

                # check for familiar
                if npcs[nid]['familiarOf'] == npcs[id]['name']:                        
                    return False

                fights[len(fights)] = {
                    's1': npc[id]['name'],
                    's2': nid,
                    's1id': attackerId,
                    's2id': victimId,
                    's1type': 'npc',
                    's2type': 'npc',
                    'retaliated': 0
                }                        
                fights[len(fights)] = {
                    's1': nid,
                    's2': npc[id]['name'],
                    's1id': victimId,
                    's2id': attackerId,
                    's1type': 'npc',
                    's2type': 'npc',
                    'retaliated': 0
                }                        
                npcs[nid]['isInCombat'] = 1
                npcs[id]['isInCombat'] = 1

    return targetFound

def npcAggression(npcs: {},players: {},fights: {},mud):
    """Aggressive npcs start fights
    """
    for (nid, pl) in list(npcs.items()):
        if not npcs[nid]['isAggressive']:
            continue
        # dead npcs don't attack
        if npcs[nid]['whenDied']:
            continue
        # already attacking?
        if isAttacking(npcs,nid,fights):
            continue
        # are there players in the same room?
        for (pid, pl) in players.items():
            if players[pid]['room'] == npcs[nid]['room']:
                hasAffinity=False
                if npcs[nid].get('affinity'):
                    if npcs[nid]['affinity'].get(players[pid]['name']):
                        if npcs[nid]['affinity'][players[pid]['name']] > 0:
                            hasAffinity=True
                if not hasAffinity:
                    npcBeginsAttack(npcs,nid,players[pid]['name'],players,fights,mud)
