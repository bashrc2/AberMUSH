__filename__ = "combat.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "DnD Mechanics"

from functions import playerInventoryWeight
from functions import stowHands
from functions import prepareSpells
from functions import randomDescription
from functions import decreaseAffinityBetweenPlayers
from functions import deepcopy
from functions import playerIsProne
from functions import setPlayerProne
from random import randint
# from copy import deepcopy
from environment import getTemperatureAtCoords
from proficiencies import damageProficiency
from traps import playerIsTrapped
import os
import time

defenseClothing = (
    'clo_chest',
    'clo_head',
    'clo_neck',
    'clo_larm',
    'clo_rarm',
    'clo_lleg',
    'clo_rleg',
    'clo_lwrist',
    'clo_rwrist',
    'clo_lhand',
    'clo_rhand',
    'clo_lfinger',
    'clo_rfinger',
    'clo_waist',
    'clo_gloves')


def removePreparedSpell(players, id, spellName):
    del players[id]['preparedSpells'][spellName]
    del players[id]['spellSlots'][spellName]


def _playerIsAvailable(id, players: {}, itemsDB: {}, rooms: {},
                       mapArea: {}, clouds: {},
                       maxTerrainDifficulty: int) -> bool:
    """Returns True if the player is available.
    Availability is encumbered by weight, temperature and terrain
    """
    currRoom = players[id]['room']
    weightDifficulty = \
        int(_getEncumberanceFromWeight(id, players, itemsDB) * 2)
    temperatureDifficulty = \
        _getTemperatureDifficulty(currRoom, rooms, mapArea, clouds)
    terrainDifficulty = \
        int(rooms[players[id]['room']]['terrainDifficulty'] * 10 /
            maxTerrainDifficulty)

    # Agility of NPC
    modifier = \
        10 - players[id]['agi'] - \
        _armorAgility(id, players, itemsDB) + terrainDifficulty + \
        temperatureDifficulty + weightDifficulty
    if modifier < 6:
        modifier = 6
    elif modifier > 25:
        modifier = 25

    if int(time.time()) < players[id]['lastCombatAction'] + modifier:
        return False
    return True


def _getEncumberanceFromWeight(id, players: {}, itemsDB: {}) -> int:
    """Returns the light medium or heavy encumberance (0,1,2)
    """
    totalWeight = playerInventoryWeight(id, players, itemsDB)

    strength = int(players[id]['str'])
    if strength < 1:
        strength = 1

    # encumberance for light, medium and heavy loads
    encumberance = {
        "1": [3, 6, 10],
        "2": [6, 13, 20],
        "3": [10, 20, 30],
        "4": [13, 26, 40],
        "5": [16, 33, 50],
        "6": [20, 40, 60],
        "7": [23, 46, 70],
        "8": [26, 53, 80],
        "9": [30, 60, 90],
        "10": [33, 66, 100],
        "11": [38, 76, 115],
        "12": [43, 86, 130],
        "13": [50, 100, 150],
        "14": [58, 116, 175],
        "15": [66, 133, 200],
        "16": [76, 153, 230],
        "17": [86, 173, 260],
        "18": [100, 200, 300],
        "19": [116, 233, 350],
        "20": [133, 266, 400],
        "21": [153, 306, 460],
        "22": [173, 346, 520],
        "23": [200, 400, 600],
        "24": [233, 466, 700],
        "25": [266, 533, 800],
        "26": [306, 613, 920],
        "27": [346, 693, 1040],
        "28": [400, 800, 1200],
        "29": [466, 933, 1400]
    }

    if strength <= 29:
        thresholds = encumberance[str(strength)]
    else:
        strIndex = 20 + (strength % 10)
        multiplier = int((strength - 20) / 10)
        thresholds = encumberance[str(strIndex)]
        for i in range(len(thresholds)):
            thresholds[i] = int(thresholds[i] * (multiplier*4))

    # multiplier for creature size
    size = int(players[id]['siz'])
    mult = 1
    if size == 3:
        mult = 2
    elif size == 4:
        mult = 4
    elif size == 5:
        mult = 8
    elif size == 6:
        mult = 16

    for i in range(len(thresholds)):
        if totalWeight < int(thresholds[i] * mult):
            return i
    return 2


def _playerShoves(mud, id, players1: {}, s2id, players2: {},
                  racesDB: {}) -> bool:
    """One player attempts to shove another
    """
    player1Size = players1[id]['siz']
    player2Size = players2[s2id]['siz']
    if players2[s2id].get('race'):
        race = players2[s2id]['race'].lower()
        if racesDB.get(race):
            if racesDB[race].get('siz'):
                player2Size = racesDB[race]['siz']
    if player2Size < player1Size or player2Size > player1Size + 1:
        if player2Size > player1Size:
            descr = randomDescription("They're too large to shove")
        else:
            descr = randomDescription("They're too small to shove")
        mud.sendMessage(id, descr + '.\n')
        players1[id]['shove'] = 0
        return False

    player1Strength = players1[id]['str']
    player2Strength = players2[s2id]['str']
    if players2[s2id].get('race'):
        race = players2[s2id]['race'].lower()
        if racesDB.get(race):
            if racesDB[race].get('str'):
                player2Strength = racesDB[race]['str']

    players1[id]['shove'] = 0

    if playerIsProne(s2id, players2):
        mud.sendMessage(
            id,
            'You attempt to shove ' + players2[s2id]['name'] +
            ', but they are already prone.\n')
        return False

    descr = randomDescription('You shove ' + players2[s2id]['name'])
    mud.sendMessage(id, descr + '.\n')

    if randint(1, player1Strength) > randint(1, player2Strength):
        players2[s2id]['prone'] = 1
        desc = (
            'They stumble and fall to the ground',
            'They come crashing to the ground',
            'They fall heavily to the ground',
            'They topple and fall to the ground',
            'They stagger and fall backwards',
            'They lose balance and fall backwards'
        )
        descr = randomDescription(desc)
        mud.sendMessage(id, descr + '.\n')
        return True
    else:
        desc = (
            'They remain standing',
            'They remain in place',
            'They stand firm',
            'They push back and remain standing',
            'They remain steady'
        )
        descr = randomDescription(desc)
        mud.sendMessage(id, descr + '.\n')
        return False


def _combatUpdateMaxHitPoints(id, players: {}, racesDB: {}) -> None:
    """Updates the hpMax value
    """
    # some npcs are invincible
    if players[id]['hpMax'] >= 999:
        return

    level = players[id]['lvl']
    hitDie = '1d10'
    if players[id].get('race'):
        race = players[id]['race'].lower()
        if racesDB.get(race):
            if racesDB[race].get('hitDie'):
                hitDie = racesDB[race]['hitDie']
    hpMax = int(hitDie.split('d')[1])
    if level > 1:
        hpMax = hpMax + (int(hpMax/2) * (level - 1))
    players[id]['hpMax'] = hpMax


def healthOfPlayer(pid: int, players: {}) -> str:
    """Returns a description of health status
    """
    hp = players[pid]['hp']
    hpMax = 11
    if players[pid].get('hpMax'):
        hpMax = players[pid]['hpMax']
    healthPercent = int(hp * 100 / hpMax)
    healthMsg = 'in full health'
    if healthPercent < 100:
        if healthPercent >= 99:
            healthMsg = 'lightly wounded'
        elif healthPercent >= 84:
            healthMsg = 'moderately wounded'
        elif healthPercent >= 70:
            healthMsg = 'considerably wounded'
        elif healthPercent >= 56:
            healthMsg = 'quite wounded'
        elif healthPercent >= 42:
            healthMsg = 'badly wounded'
        elif healthPercent >= 28:
            healthMsg = 'extremely wounded'
        elif healthPercent >= 14:
            healthMsg = 'critically wounded'
        elif healthPercent > 0:
            healthMsg = 'close to death'
        else:
            healthMsg = 'dead'
        # add color for critical health
        if healthPercent < 50:
            healthMsg = '<f15><b88>' + healthMsg + '<r>'
        elif healthPercent < 70:
            healthMsg = '<f15><b166>' + healthMsg + '<r>'
    return healthMsg


def _combatAbilityModifier(score: int) -> int:
    """Returns the ability modifier
    """
    if score > 30:
        return 10

    # min and max score and the corresponding
    # ability modifier
    abilityTable = (
        [1, 1, -5],
        [2, 3, -4],
        [4, 5, -3],
        [6, 7, -2],
        [8, 9, -1],
        [10, 11, 0],
        [12, 13, 1],
        [14, 15, 2],
        [16, 17, 3],
        [18, 19, 4],
        [20, 21, 5],
        [22, 23, 6],
        [24, 25, 7],
        [26, 27, 8],
        [28, 29, 9],
        [30, 30, 10]
    )

    for abilityRange in abilityTable:
        if score >= abilityRange[0] and \
           score <= abilityRange[1]:
            return abilityRange[2]
    return 0


def _combatRaceResistance(id: int, players: {},
                          racesDB: {}, weaponType: str) -> int:
    """How much resistance does the player have to the weapon type
       based upon their race
    """
    resistance = 0
    resistParam = 'resist_' + weaponType.lower()

    if weaponType.endswith('bow'):
        resistParam = 'resist_piercing'

    if weaponType.endswith('sling') or \
       'flail' in weaponType or \
       'whip' in weaponType:
        resistParam = 'resist_bludgeoning'

    if players[id].get('race'):
        race = players[id]['race'].lower()
        if racesDB.get(race):
            if racesDB[race].get(resistParam):
                resistance = racesDB[race][resistParam]

    return resistance


def _combatDamageFromWeapon(id, players: {},
                            itemsDB: {}, weaponType: str,
                            characterClassDB: {},
                            isCritical: bool) -> (int, str):
    """find the weapon being used and return its damage value
    """
    weaponLocations = (
        'clo_lhand',
        'clo_rhand',
        'clo_gloves'
    )

    # bare knuckle fight
    damageRollBest = '1d3'
    maxDamage = 1

    for w in weaponLocations:
        itemID = int(players[id][w])
        if itemID <= 0:
            continue
        damageRoll = itemsDB[itemID]['damage']
        if not damageRoll:
            continue
        if 'd' not in damageRoll:
            continue
        die = int(damageRoll.split('d')[1])
        noOfRolls = int(damageRoll.split('d')[0])
        if isCritical:
            # double the damage for a critical hit
            noOfRolls *= 2
        score = 0
        for roll in range(noOfRolls):
            score += randint(1, die)
        if score > maxDamage:
            maxDamage = score
            damageRollBest = damageRoll
    return maxDamage, damageRollBest


def _combatArmorClass(id, players: {},
                      racesDB: {}, attackWeaponType: str,
                      itemsDB: {}) -> int:
    """Returns the armor class for the given player
    when attacked by the given weapon type
    """
    armorClass = 0
    for c in defenseClothing:
        itemID = int(players[id][c])
        if itemID <= 0:
            continue

        armorClass += itemsDB[itemID]['armorClass']
    if armorClass < 10:
        armorClass += 10

    raceArmor = _combatRaceResistance(id, players, racesDB,
                                      attackWeaponType)
    if armorClass < raceArmor:
        armorClass = raceArmor

    if players[id].get('magicShield'):
        armorClass += players[id]['magicShield']

    return armorClass


def _combatProficiencyBonus(id, players: {}, weaponType: str,
                            characterClassDB: {}) -> int:
    """Returns the proficiency bonus with the given weapon type
    """
    return damageProficiency(id, players, weaponType,
                             characterClassDB)


def _combatAttackRoll(id, players: {}, weaponType: str,
                      targetArmorClass: int,
                      characterClassDB: {},
                      dodgeModifier: int) -> (bool, bool):
    """Returns true if an attack against a target succeeds
    """
    d20 = randint(1, 20)
    if d20 == 1:
        # miss
        return False, False
    if d20 == 20:
        # critical hit
        return True, True

    abilityModifier = 0
    if 'ranged' in weaponType:
        abilityModifier = _combatAbilityModifier(players[id]['agi'])
    else:
        abilityModifier = _combatAbilityModifier(players[id]['str'])

    proficiencyBonus = \
        _combatProficiencyBonus(id, players, weaponType,
                                characterClassDB)

    if d20 + abilityModifier + proficiencyBonus >= \
       targetArmorClass + dodgeModifier:
        return True, False
    return False, False


def _sendCombatImage(mud, id, players: {}, race: str,
                     weaponType: str) -> None:
    """Sends an image based on a character of a given race using a given weapon
    """
    if not (race and weaponType):
        return
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    combatImageFilename = 'images/combat/' + race + '_' + weaponType
    if not os.path.isfile(combatImageFilename):
        return
    with open(combatImageFilename, 'r') as imgFile:
        mud.sendImage(id, '\n' + imgFile.read())


def updateTemporaryIncapacitation(mud, players: {}, isNPC: bool) -> None:
    """Checks if players are incapacitated by spells and removes them
       after the duration has elapsed
    """
    now = int(time.time())
    for p in players:
        thisPlayer = players[p]
        if thisPlayer['name'] is None:
            continue
        if thisPlayer['frozenStart'] != 0:
            if now >= thisPlayer['frozenStart'] + thisPlayer['frozenDuration']:
                thisPlayer['frozenStart'] = 0
                thisPlayer['frozenDuration'] = 0
                thisPlayer['frozenDescription'] = ""
                if not isNPC:
                    mud.sendMessage(
                        p, "<f220>You find that you can move again.<r>\n\n")


def updateTemporaryHitPoints(mud, players: {}, isNPC: bool) -> None:
    """Updates any hit points added for a temporary period
       as the result of a spell
    """
    now = int(time.time())
    for p in players:
        thisPlayer = players[p]
        if thisPlayer['name'] is None:
            continue
        if thisPlayer['tempHitPoints'] == 0:
            continue
        if thisPlayer['tempHitPointsStart'] == 0 and \
           thisPlayer['tempHitPointsDuration'] > 0:
            thisPlayer['tempHitPointsStart'] = now
        else:
            if now > thisPlayer['tempHitPointsStart'] + \
                    thisPlayer['tempHitPointsDuration']:
                thisPlayer['tempHitPoints'] = 0
                thisPlayer['tempHitPointsStart'] = 0
                thisPlayer['tempHitPointsDuration'] = 0
                if not isNPC:
                    mud.sendMessage(
                        p, "<f220>Your magical protection expires.<r>\n\n")


def updateTemporaryCharm(mud, players: {}, isNPC: bool) -> None:
    """Updates any charm added for a temporary period
       as the result of a spell
    """
    now = int(time.time())
    for p in players:
        thisPlayer = players[p]
        if thisPlayer['name'] is None:
            continue
        if thisPlayer['tempCharm'] == 0:
            continue
        if thisPlayer['tempCharmStart'] == 0 and \
           thisPlayer['tempCharmDuration'] > 0:
            thisPlayer['tempCharmStart'] = now
        else:
            if not thisPlayer.get('tempCharmDuration'):
                return
            if now > thisPlayer['tempCharmStart'] + \
                    thisPlayer['tempCharmDuration']:
                thisPlayer['tempCharmStart'] = 0
                thisPlayer['tempCharmDuration'] = 0
                if thisPlayer['affinity'].get(thisPlayer['tempCharmTarget']):
                    thisPlayer['affinity'][thisPlayer['tempCharmTarget']] -= \
                        thisPlayer['tempCharm']
                thisPlayer['tempCharm'] = 0
                if not isNPC:
                    mud.sendMessage(
                        p, "<f220>A charm spell wears off.<r>\n\n")


def updateMagicShield(mud, players: {}, isNPC: bool) -> None:
    """Updates any magic shield for a temporary period
       as the result of a spell
    """
    now = int(time.time())
    for p in players:
        thisPlayer = players[p]
        if thisPlayer['name'] is None:
            continue
        if not thisPlayer.get('magicShield'):
            continue
        if thisPlayer['magicShieldStart'] == 0 and \
           thisPlayer['magicShieldDuration'] > 0:
            thisPlayer['magicShieldStart'] = now
        else:
            if not thisPlayer.get('magicShieldDuration'):
                return
            if now > thisPlayer['magicShieldStart'] + \
                    thisPlayer['magicShieldDuration']:
                thisPlayer['magicShieldStart'] = 0
                thisPlayer['magicShieldDuration'] = 0
                thisPlayer['magicShield'] = 0
                if not isNPC:
                    mud.sendMessage(
                        p, "<f220>Your magic shield wears off.<r>\n\n")


def playersRest(mud, players: {}) -> None:
    """Rest restores hit points
    """
    for p in players:
        thisPlayer = players[p]
        if thisPlayer['name'] is not None and \
           thisPlayer['authenticated'] is not None:
            if thisPlayer['hp'] < thisPlayer['hpMax'] + \
                    thisPlayer['tempHitPoints']:
                if randint(0, 100) > 90:
                    thisPlayer['hp'] += 1
            else:
                thisPlayer['hp'] = thisPlayer['hpMax'] + \
                    thisPlayer['tempHitPoints']
                thisPlayer['restRequired'] = 0
                prepareSpells(mud, p, players)


def _itemInNPCInventory(npcs, id: int, itemName: str, itemsDB: {}) -> bool:
    if len(list(npcs[id]['inv'])) > 0:
        itemNameLower = itemName.lower()
        for i in list(npcs[id]['inv']):
            if itemsDB[int(i)]['name'].lower() == itemNameLower:
                return True
    return False


def _npcUpdateLuck(nid, npcs: {}, items: {}, itemsDB: {}) -> None:
    """Calculate the luck of an NPC based on what items they are carrying
    """
    luck = 0
    for i in npcs[nid]['inv']:
        luck = luck + itemsDB[int(i)]['mod_luc']
    npcs[nid]['luc'] = luck


def _npcWieldsWeapon(mud, id: int, nid, npcs: {}, items: {},
                     itemsDB: {}) -> bool:
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
            elif itemsDB[int(i)]['clo_lhand'] > 0:
                if itemsDB[int(i)]['mod_str'] > max_damage:
                    max_damage = itemsDB[int(i)]['mod_str']
                    itemID = int(i)

    putOnArmor = False
    if int(npcs[nid]['canWear']) != 0:
        for i in npcs[nid]['inv']:
            if itemsDB[int(i)]['clo_chest'] < 1:
                continue
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
            if itemsInWorldCopy[iid]['room'] != npcs[nid]['room']:
                continue
            if itemsDB[items[iid]['id']]['weight'] == 0:
                continue
            if itemsDB[items[iid]['id']]['clo_rhand'] == 0:
                continue
            if itemsDB[items[iid]['id']]['mod_str'] <= max_damage:
                continue
            itemName = itemsDB[items[iid]['id']]['name']
            if _itemInNPCInventory(npcs, nid, itemName, itemsDB):
                continue
            max_damage = itemsDB[items[iid]['id']]['mod_str']
            itemID = int(items[iid]['id'])
            itemWeaponIndex = iid
            pickedUpWeapon = True

    # Search for any armor on the floor
    pickedUpArmor = False
    itemArmorIndex = 0
    if int(npcs[nid]['canWear']) != 0:
        for (iid, pl) in list(itemsInWorldCopy.items()):
            if itemsInWorldCopy[iid]['room'] != npcs[nid]['room']:
                continue
            if itemsDB[items[iid]['id']]['weight'] == 0:
                continue
            if itemsDB[items[iid]['id']]['clo_chest'] == 0:
                continue
            if itemsDB[items[iid]['id']]['mod_endu'] <= max_protection:
                continue
            itemName = itemsDB[items[iid]['id']]['name']
            if _itemInNPCInventory(npcs, nid, itemName, itemsDB):
                continue
            max_protection = \
                itemsDB[items[iid]['id']]['mod_endu']
            itemID = int(items[iid]['id'])
            itemArmorIndex = iid
            pickedUpArmor = True

    if itemID > 0:
        if putOnArmor:
            if npcs[nid]['clo_chest'] != itemID:
                npcs[nid]['clo_chest'] = itemID
                mud.sendMessage(
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
                mud.sendMessage(
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
                mud.sendMessage(
                    id,
                    '<f220>' +
                    npcs[nid]['name'] +
                    '<r> picks up ' +
                    itemsDB[itemID]['article'] +
                    ' ' +
                    itemsDB[itemID]['name'] +
                    '\n')
            else:
                mud.sendMessage(
                    id,
                    '<f220>' +
                    npcs[nid]['name'] +
                    '<r> has drawn their ' +
                    itemsDB[itemID]['name'] +
                    '\n')
            return True

    return False


def _npcWearsArmor(id: int, npcs: {}, itemsDB: {}) -> None:
    """An NPC puts on armor
    """
    if len(npcs[id]['inv']) == 0:
        return

    for c in defenseClothing:
        itemID = 0
        # what is the best defense which the NPC is carrying?
        max_defense = 0
        for i in npcs[id]['inv']:
            if itemsDB[int(i)][c] < 1:
                continue
            if itemsDB[int(i)]['mod_str'] != 0:
                continue
            if itemsDB[int(i)]['mod_endu'] > max_defense:
                max_defense = itemsDB[int(i)]['mod_endu']
                itemID = int(i)
        if itemID > 0:
            # Wear the armor
            npcs[id][c] = itemID


def _twoHandedWeapon(id: int, players: {}, itemsDB: {}) -> None:
    """ If carrying a two handed weapon then make sure
    that the other hand is empty
    """
    itemIDleft = players[id]['clo_lhand']
    itemIDright = players[id]['clo_rhand']
    # items on both hands
    if itemIDleft == 0 or itemIDright == 0:
        return
    # at least one item is two handed
    if itemsDB[itemIDleft]['bothHands'] == 0 and \
       itemsDB[itemIDright]['bothHands'] == 0:
        return
    if itemsDB[itemIDright]['bothHands'] == 1:
        players[id]['clo_lhand'] = 0
    else:
        players[id]['clo_rhand'] = 0


def _armorAgility(id: int, players: {}, itemsDB: {}) -> int:
    """Modify agility based on armor worn
    """
    agility = 0

    for c in defenseClothing:
        itemID = int(players[id][c])
        if itemID > 0:
            agility = agility + int(itemsDB[itemID]['mod_agi'])

    # Total agility for clothing
    return agility


def _canUseWeapon(id: int, players: {}, itemsDB: {}, itemID: int) -> bool:
    if itemID == 0:
        return True
    lockItemID = itemsDB[itemID]['lockedWithItem']
    if str(lockItemID).isdigit():
        if lockItemID > 0:
            itemName = itemsDB[lockItemID]['name']
            for i in list(players[id]['inv']):
                if itemsDB[int(i)]['name'] == itemName:
                    return True
            return False
    return True


def _getWeaponHeld(id: int, players: {}, itemsDB: {}) -> (int, str, int):
    """Returns the type of weapon held, or fists if none
    is held and the rounds of fire
    """
    fighter = players[id]
    if fighter['clo_rhand'] > 0 and fighter['clo_lhand'] == 0:
        # something in right hand
        itemID = int(fighter['clo_rhand'])
        if itemsDB[itemID]['mod_str'] > 0:
            if len(itemsDB[itemID]['type']) > 0:
                return itemID, itemsDB[itemID]['type'], itemsDB[itemID]['rof']

    if fighter['clo_lhand'] > 0 and fighter['clo_rhand'] == 0:
        # something in left hand
        itemID = int(fighter['clo_lhand'])
        if itemsDB[itemID]['mod_str'] > 0:
            if len(itemsDB[itemID]['type']) > 0:
                return itemID, itemsDB[itemID]['type'], itemsDB[itemID]['rof']

    if fighter['clo_lhand'] > 0 and fighter['clo_rhand'] > 0:
        # something in both hands
        itemRightID = int(fighter['clo_rhand'])
        itemRight = itemsDB[itemRightID]
        itemLeftID = int(fighter['clo_lhand'])
        itemLeft = itemsDB[itemLeftID]
        if randint(0, 1) == 1:
            if itemRight['mod_str'] > 0:
                if len(itemRight['type']) > 0:
                    return itemRightID, itemRight['type'], itemRight['rof']
            if itemLeft['mod_str'] > 0:
                if len(itemLeft['type']) > 0:
                    return itemLeftID, itemLeft['type'], itemLeft['rof']
        else:
            if itemLeft['mod_str'] > 0:
                if len(itemLeft['type']) > 0:
                    return itemLeftID, itemLeft['type'], itemLeft['rof']
            if itemRight['mod_str'] > 0:
                if len(itemRight['type']) > 0:
                    return itemRightID, itemRight['type'], itemRight['rof']
    return 0, "fists", 1


def _getAttackDescription(animalType: str, weaponType: str,
                          attackDB: {}, isCritical: bool) -> (str, str):
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
        attackDescriptionFirst = randomDescription(attackStrings)
        attackStrings = [
            "swung a fist at",
            "punched",
            "crudely swung a fist at",
            "ineptly punched"
        ]
        attackDescriptionSecond = randomDescription(attackStrings)
        for attackType, attackDesc in attackDB.items():
            if animalType.startswith('animal '):
                continue
            attackTypeList = attackType.split('|')
            for attackTypeStr in attackTypeList:
                if not weaponType.startswith(attackTypeStr):
                    continue
                if not isCritical:
                    # first person - you attack a player or npc
                    attackDescriptionFirst = \
                        randomDescription(attackDesc['first'])
                    # second person - you were attacked by a player or npc
                    attackDescriptionSecond = \
                        randomDescription(attackDesc['second'])
                else:
                    # first person critical hit
                    attackDescriptionFirst = \
                        randomDescription(attackDesc['critical first'])
                    # second person critical hit
                    attackDescriptionSecond = \
                        randomDescription(attackDesc['critical second'])
                break
    else:
        attackStrings = [
            "savage",
            "maul",
            "bite",
            "viciously bite",
            "savagely gnaw"
        ]
        attackDescriptionFirst = randomDescription(attackStrings)
        attackStrings = [
            "savaged",
            "mauled",
            "took a bite at",
            "viciously bit into",
            "savagely gnawed into"
        ]
        attackDescriptionSecond = randomDescription(attackStrings)
        for anType, attackDesc in attackDB.items():
            if not anType.startswith('animal '):
                continue
            anType = anType.replace('animal ', '')
            animalTypeList = anType.split('|')
            for animalTypeStr in animalTypeList:
                if not animalType.startswith(animalTypeStr):
                    continue
                if not isCritical:
                    # first person -  you attack a player or npc
                    attackDescriptionFirst = \
                        randomDescription(attackDesc['first'])
                    # second person -  you were attacked by a player or npc
                    attackDescriptionSecond = \
                        randomDescription(attackDesc['second'])
                else:
                    # first person critical hit
                    attackDescriptionFirst = \
                        randomDescription(attackDesc['critical first'])
                    # second person critical hit
                    attackDescriptionSecond = \
                        randomDescription(attackDesc['critical second'])
                break

    return attackDescriptionFirst, attackDescriptionSecond


def _getTemperatureDifficulty(rm: str, rooms: {}, mapArea: [],
                              clouds: {}) -> int:
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


def _runFightsBetweenPlayers(mud, players: {}, npcs: {},
                             fights, fid, itemsDB: {},
                             rooms: {}, maxTerrainDifficulty, mapArea: [],
                             clouds: {}, racesDB: {}, characterClassDB: {},
                             guilds: {}, attackDB: {}):
    """A fight between two players
    """
    s1id = fights[fid]['s1id']
    s2id = fights[fid]['s2id']

    # In the same room?
    if players[s1id]['room'] != players[s2id]['room']:
        return

    # is the player frozen?
    if players[s1id]['frozenStart'] > 0 or players[s1id]['canAttack'] == 0:
        descr = randomDescription(players[s1id]['frozenDescription'])
        mud.sendMessage(s2id, descr + '\n')
        players[s1id]['lastCombatAction'] = int(time.time())
        return

    if playerIsTrapped(s1id, players, rooms):
        players[s1id]['lastCombatAction'] = int(time.time())
        return

    if not _playerIsAvailable(s1id, players, itemsDB, rooms,
                              mapArea, clouds,
                              maxTerrainDifficulty):
        return

    # if the player is dodging then miss a turn
    if players[s1id].get('dodge'):
        if players[s1id]['dodge'] == 1:
            players[s1id]['lastCombatAction'] = int(time.time())
            return

    if players[s2id]['isAttackable'] == 1:
        players[s1id]['isInCombat'] = 1
        players[s2id]['isInCombat'] = 1

        if playerIsProne(s1id, players):
            # on the ground, so can't attack and misses the turn
            players[s1id]['lastCombatAction'] = int(time.time())
            # stand up for the next turn
            setPlayerProne(s1id, players, False)
            descr = randomDescription(
                'stands up|' +
                'gets up|' +
                'gets back on their feet|' +
                'stands back up again'
            )
            mud.sendMessage(s2id, '<f32>' + players[s1id]['name'] + ' ' +
                            descr + '<r>.\n')
            return

        # attempt to shove
        if players[s1id].get('shove'):
            if players[s1id]['shove'] == 1:
                if _playerShoves(mud, s1id, players, s2id, players, racesDB):
                    players[s2id]['lastCombatAction'] = int(time.time())
                players[s1id]['lastCombatAction'] = int(time.time())
                return

        _twoHandedWeapon(s1id, players, itemsDB)
        weaponID, weaponType, roundsOfFire = \
            _getWeaponHeld(s1id, players, itemsDB)
        if not _canUseWeapon(s1id, players, itemsDB, weaponID):
            lockItemID = itemsDB[weaponID]['lockedWithItem']
            mud.sendMessage(
                s1id, 'You take aim, but find you have no ' +
                itemsDB[lockItemID]['name'].lower() + '.\n')
            mud.sendMessage(
                s2id, '<f32>' +
                players[s1id]['name'] +
                '<r> takes aim, but finds they have no ' +
                itemsDB[lockItemID]['name'].lower() + '.\n')
            stowHands(s1id, players, itemsDB, mud)
            mud.sendMessage(
                s2id, '<f32>' +
                players[s1id]['name'] +
                '<r> stows ' +
                itemsDB[weaponID]['article'] +
                ' <b234>' +
                itemsDB[weaponID]['name'] + '\n\n')
            players[s1id]['lastCombatAction'] = int(time.time())
            return

        # A dodge value used to adjust agility of the target player
        # This is proportional to their luck, which can be modified by
        # various items
        dodgeModifier = 0
        if players[s2id].get('dodge'):
            if players[s2id]['dodge'] == 1:
                dodgeModifier = randint(0, players[s2id]['luc'])
                desc = (
                    'You dodge',
                    'You swerve to avoid being hit',
                    'You pivot',
                    'You duck'
                )
                dodgeDescription = randomDescription(desc)
                mud.sendMessage(s2id,
                                '<f32>' + dodgeDescription + '<r>.\n')
                mud.sendMessage(
                    s1id, '<f32>' + players[s2id]['name'] +
                    '<r> tries to ' +
                    dodgeDescription.replace('You ', '') + '.\n')
                players[s2id]['dodge'] = 0

        targetArmorClass = \
            _combatArmorClass(s2id, players,
                              racesDB, weaponType, itemsDB)

        # Do damage to the PC here
        hit, isCritical = _combatAttackRoll(s1id, players, weaponType,
                                            targetArmorClass, characterClassDB,
                                            dodgeModifier)
        if hit:
            attackDescriptionFirst, attackDescriptionSecond = \
                _getAttackDescription("", weaponType, attackDB, isCritical)

            if roundsOfFire < 1:
                roundsOfFire = 1

            for firingRound in range(roundsOfFire):
                if players[s1id]['hp'] <= 0:
                    break
                damageValue, damageRoll = \
                    _combatDamageFromWeapon(s1id, players,
                                            itemsDB, weaponType,
                                            characterClassDB,
                                            isCritical)
                # eg "1d8 = 5"
                damageValueDesc = damageRoll + ' = ' + str(damageValue)
                if isCritical:
                    damageValueDesc = '2 x ' + damageValueDesc

                if int(players[s2id]['hpMax']) < 999:
                    players[s2id]['hp'] = \
                        int(players[s2id]['hp']) - damageValue
                    if players[s2id]['hp'] < 0:
                        players[s2id]['hp'] = 0

                decreaseAffinityBetweenPlayers(
                    players, s2id, players, s1id, guilds)
                decreaseAffinityBetweenPlayers(
                    players, s1id, players, s2id, guilds)
                _sendCombatImage(mud, s1id, players,
                                 players[s1id]['race'], weaponType)

                attackText = 'attack'
                finalText = ''
                if isinstance(attackDescriptionFirst, str):
                    attackText = attackDescriptionFirst
                elif isinstance(attackDescriptionFirst, list):
                    attackText = attackDescriptionFirst[0]
                    if len(attackDescriptionFirst) > 1:
                        finalText = ' ' + \
                            randomDescription(attackDescriptionFirst[1]) + '\n'
                mud.sendMessage(
                    s1id, 'You ' + attackText + ' <f32><u>' +
                    players[s2id]['name'] +
                    '<r> for <f15><b2> * ' +
                    damageValueDesc +
                    ' *<r> points of damage.\n' +
                    finalText +
                    players[s2id]['name'] + ' is ' +
                    healthOfPlayer(s2id, players) + '\n')

                _sendCombatImage(mud, s2id, players,
                                 players[s1id]['race'], weaponType)

                healthDescription = healthOfPlayer(s2id, players)
                if 'dead' in healthDescription:
                    healthDescription = 'You are ' + healthDescription
                else:
                    healthDescription = \
                        'Your health status is ' + healthDescription

                attackText = 'attacked'
                finalText = ''
                if isinstance(attackDescriptionSecond, str):
                    attackText = attackDescriptionSecond
                elif isinstance(attackDescriptionSecond, list):
                    attackText = attackDescriptionSecond[0]
                    if len(attackDescriptionSecond) > 1:
                        finalText = ' ' + \
                            randomDescription(attackDescriptionSecond[1]) + \
                            '\n'
                mud.sendMessage(
                    s2id, '<f32>' +
                    players[s1id]['name'] +
                    '<r> has ' + attackText + ' you for <f15><b88> * ' +
                    damageValueDesc +
                    ' *<r> points of damage.\n' + finalText +
                    healthDescription + '\n')
        else:
            players[s1id]['lastCombatAction'] = int(time.time())
            mud.sendMessage(
                s1id, 'You miss trying to hit <f32><u>' +
                players[s2id]['name'] + '\n')
            mud.sendMessage(
                s2id, '<f32><u>' +
                players[s1id]['name'] +
                '<r> missed while trying to hit you!\n')
        players[s1id]['lastCombatAction'] = int(time.time())
    else:
        mud.sendMessage(
            s1id,
            '<f225>Suddenly you stop. It wouldn`t be a good ' +
            'idea to attack <f32>' +
            players[s2id]['name'] + ' at this time.\n')
        fightsCopy = deepcopy(fights)
        for (fight, pl) in fightsCopy.items():
            if fightsCopy[fight]['s1id'] == s1id and \
               fightsCopy[fight]['s1type'] == 'pc' and \
               fightsCopy[fight]['s2id'] == s2id and \
               fightsCopy[fight]['s2type'] == 'pc':
                del fights[fight]
                players[s1id]['isInCombat'] = 0
                players[s2id]['isInCombat'] = 0


def _runFightsBetweenPlayerAndNPC(mud, players: {}, npcs: {}, fights, fid,
                                  itemsDB: {}, rooms: {}, maxTerrainDifficulty,
                                  mapArea: [], clouds: {}, racesDB: {},
                                  characterClassDB: {}, guilds: {},
                                  attackDB: {}):
    """Fight between a player and an NPC
    """
    s1id = fights[fid]['s1id']
    s2id = fights[fid]['s2id']

    # In the same room?
    if players[s1id]['room'] != npcs[s2id]['room']:
        return

    # is the player frozen?
    if players[s1id]['frozenStart'] > 0 or \
       players[s1id]['canAttack'] == 0:
        descr = randomDescription(players[s1id]['frozenDescription'])
        mud.sendMessage(s2id, descr + '\n')
        players[s1id]['lastCombatAction'] = int(time.time())
        return

    if playerIsTrapped(s1id, players, rooms):
        players[s1id]['lastCombatAction'] = int(time.time())
        return

    if not _playerIsAvailable(s1id, players, itemsDB, rooms,
                              mapArea, clouds,
                              maxTerrainDifficulty):
        return

    # if the player is dodging then miss a turn
    if players[s1id].get('dodge'):
        if players[s1id]['dodge'] == 1:
            players[s1id]['lastCombatAction'] = int(time.time())
            return

    if npcs[s2id]['isAttackable'] == 1:
        players[s1id]['isInCombat'] = 1
        npcs[s2id]['isInCombat'] = 1

        if playerIsProne(s1id, players):
            # on the ground, so can't attack and misses the turn
            players[s1id]['lastCombatAction'] = int(time.time())
            # stand up for the next turn
            setPlayerProne(s1id, players, False)
            return

        # attempt to shove
        if players[s1id].get('shove'):
            if players[s1id]['shove'] == 1:
                if _playerShoves(mud, s1id, players, s2id, npcs, racesDB):
                    npcs[s2id]['lastCombatAction'] = int(time.time())
                players[s1id]['lastCombatAction'] = int(time.time())
                return

        _twoHandedWeapon(s1id, players, itemsDB)
        weaponID, weaponType, roundsOfFire = \
            _getWeaponHeld(s1id, players, itemsDB)
        if not _canUseWeapon(s1id, players, itemsDB, weaponID):
            lockItemID = itemsDB[weaponID]['lockedWithItem']
            mud.sendMessage(
                s1id,
                'You take aim, but find you have no ' +
                itemsDB[lockItemID]['name'].lower() +
                '.\n')
            stowHands(s1id, players, itemsDB, mud)
            players[s1id]['lastCombatAction'] = int(time.time())
            return

        # A dodge value used to adjust agility of the target player
        # This is proportional to their luck, which can be modified by
        # various items
        dodgeModifier = 0
        if npcs[s2id].get('dodge'):
            if npcs[s2id]['dodge'] == 1:
                dodgeModifier = randint(0, npcs[s2id]['luc'])
                mud.sendMessage(
                    s1id, '<f32>' + npcs[s2id]['name'] +
                    '<r> tries to dodge.\n')
                npcs[s2id]['dodge'] = 0

        targetArmorClass = \
            _combatArmorClass(s2id, npcs,
                              racesDB, weaponType, itemsDB)

        # Do damage to the PC here
        hit, isCritical = _combatAttackRoll(s1id, players, weaponType,
                                            targetArmorClass, characterClassDB,
                                            dodgeModifier)
        if hit:
            attackDescriptionFirst, attackDescriptionSecond = \
                _getAttackDescription("", weaponType, attackDB, isCritical)

            if roundsOfFire < 1:
                roundsOfFire = 1

            for firingRound in range(roundsOfFire):
                if players[s1id]['hp'] <= 0:
                    break

                damageValue, damageRoll = \
                    _combatDamageFromWeapon(s1id, players,
                                            itemsDB, weaponType,
                                            characterClassDB,
                                            isCritical)
                # eg "1d8 = 5"
                damageValueDesc = damageRoll + ' = ' + str(damageValue)
                if isCritical:
                    damageValueDesc = '2 x ' + damageValueDesc

                _npcWearsArmor(s2id, npcs, itemsDB)

                if int(npcs[s2id]['hpMax']) < 999:
                    npcs[s2id]['hp'] = int(npcs[s2id]['hp']) - damageValue
                    if int(npcs[s2id]['hp']) < 0:
                        npcs[s2id]['hp'] = 0

                decreaseAffinityBetweenPlayers(npcs, s2id, players,
                                               s1id, guilds)
                decreaseAffinityBetweenPlayers(players, s1id, npcs,
                                               s2id, guilds)
                _sendCombatImage(mud, s1id, players,
                                 players[s1id]['race'], weaponType)
                attackText = 'attack'
                finalText = ''
                if isinstance(attackDescriptionFirst, str):
                    attackText = attackDescriptionFirst
                elif isinstance(attackDescriptionFirst, list):
                    attackText = attackDescriptionFirst[0]
                    if len(attackDescriptionFirst) > 1:
                        finalText = ' ' + \
                            randomDescription(attackDescriptionFirst[1]) + '\n'
                mud.sendMessage(
                    s1id,
                    'You ' + attackText + ' <f220>' +
                    npcs[s2id]['name'] +
                    '<r> for <b2><f15> * ' +
                    damageValueDesc +
                    ' * <r> points of damage\n' + finalText +
                    npcs[s2id]['name'] + ' is ' +
                    healthOfPlayer(s2id, npcs) + '\n')
        else:
            players[s1id]['lastCombatAction'] = int(time.time())
            desc = [
                'You miss <f220>' + npcs[s2id]['name'] + '<r> completely!',
                'You hopelessly fail to hit <f220>' +
                npcs[s2id]['name'] + '<r>',
                'You fail to hit <f220>' + npcs[s2id]['name'] + '<r>',
                'You utterly fail to hit <f220>' + npcs[s2id]['name'] + '<r>',
                'You completely fail to hit <f220>' +
                npcs[s2id]['name'] + '<r>',
                'You widely miss <f220>' + npcs[s2id]['name'] + '<r>',
                'You miss <f220>' + npcs[s2id]['name'] + '<r> by miles!',
                'You miss <f220>' + npcs[s2id]['name'] +
                '<r> by a wide margin'
            ]
            descr = randomDescription(desc)
            mud.sendMessage(s1id, descr + '\n')
        players[s1id]['lastCombatAction'] = int(time.time())
    else:
        mud.sendMessage(
            s1id,
            '<f225>Suddenly you stop. It wouldn`t be a good ' +
            'idea to attack <u><f21>' +
            npcs[s2id]['name'] + '<r> at this time.\n')
        fightsCopy = deepcopy(fights)
        for (fight, pl) in fightsCopy.items():
            if fightsCopy[fight]['s1id'] == s1id and \
               fightsCopy[fight]['s1type'] == 'pc' and \
               fightsCopy[fight]['s2id'] == s2id and \
               fightsCopy[fight]['s2type'] == 'npc':
                del fights[fight]
                players[s1id]['isInCombat'] = 0
                npcs[s2id]['isInCombat'] = 0


def _runFightsBetweenNPCAndPlayer(mud, players: {}, npcs: {}, fights, fid,
                                  items: {}, itemsDB: {}, rooms: {},
                                  maxTerrainDifficulty, mapArea, clouds: {},
                                  racesDB: {}, characterClassDB: {},
                                  guilds: {}, attackDB: {}):
    """Fight between NPC and player
    """
    s1id = fights[fid]['s1id']
    s2id = fights[fid]['s2id']

    # In the same room?
    if npcs[s1id]['room'] != players[s2id]['room']:
        return

    # is the player frozen?
    if npcs[s1id]['frozenStart'] > 0:
        mud.sendMessage(
            s2id, '<f220>' +
            npcs[s1id]['name'] +
            "<r> tries to attack but can't move\n")
        npcs[s1id]['lastCombatAction'] = int(time.time())
        return

    if not _playerIsAvailable(s1id, npcs, itemsDB, rooms,
                              mapArea, clouds,
                              maxTerrainDifficulty):
        return

    # if the npc is dodging then miss a turn
    if npcs[s1id].get('dodge'):
        if npcs[s1id]['dodge'] == 1:
            npcs[s1id]['lastCombatAction'] = int(time.time())
            return

    npcs[s1id]['isInCombat'] = 1
    players[s2id]['isInCombat'] = 1

    if playerIsProne(s1id, npcs):
        # on the ground, so can't attack and misses the turn
        npcs[s1id]['lastCombatAction'] = int(time.time())
        # stand up for the next turn
        setPlayerProne(s1id, npcs, False)
        desc = (
            'stands up',
            'gets up',
            'gets back on their feet',
            'stands back up again'
        )
        descr = randomDescription(desc)
        mud.sendMessage(s2id, '<f32>' + npcs[s1id]['name'] + ' ' +
                        descr + '<r>.\n')
        return

    _npcUpdateLuck(s1id, npcs, items, itemsDB)
    if _npcWieldsWeapon(mud, s2id, s1id, npcs, items, itemsDB):
        npcs[s1id]['lastCombatAction'] = int(time.time())
        return

    _twoHandedWeapon(s1id, npcs, itemsDB)
    weaponID, weaponType, roundsOfFire = _getWeaponHeld(s1id, npcs, itemsDB)

    # A dodge value used to adjust agility of the target player
    # This is proportional to their luck, which can be modified by
    # various items
    dodgeModifier = 0
    if players[s2id].get('dodge'):
        if players[s2id]['dodge'] == 1:
            dodgeModifier = randint(0, players[s2id]['luc'])
            desc = (
                'You dodge',
                'You swerve to avoid being hit',
                'You pivot',
                'You duck'
            )
            dodgeDescription = randomDescription(desc)
            mud.sendMessage(s2id,
                            '<f32>' + dodgeDescription + '<r>.\n')
            players[s2id]['dodge'] = 0

    targetArmorClass = \
        _combatArmorClass(s2id, players,
                          racesDB, weaponType, itemsDB)

    # Do damage to the PC here
    hit, isCritical = _combatAttackRoll(s1id, npcs, weaponType,
                                        targetArmorClass, characterClassDB,
                                        dodgeModifier)
    if hit:
        attackDescriptionFirst, attackDescriptionSecond = \
            _getAttackDescription(npcs[s1id]['animalType'],
                                  weaponType, attackDB, isCritical)

        if roundsOfFire < 1:
            roundsOfFire = 1

        for firingRound in range(roundsOfFire):
            if npcs[s1id]['hp'] <= 0:
                break
            damageValue, damageRoll = \
                _combatDamageFromWeapon(s1id, npcs,
                                        itemsDB, weaponType,
                                        characterClassDB,
                                        isCritical)
            # eg "1d8 = 5"
            damageValueDesc = damageRoll + ' = ' + str(damageValue)
            if isCritical:
                damageValueDesc = '2 x ' + damageValueDesc

            if int(players[s2id]['hpMax']) < 999:
                players[s2id]['hp'] = int(players[s2id]['hp']) - damageValue
                if int(players[s2id]['hp']) < 0:
                    players[s2id]['hp'] = 0

            decreaseAffinityBetweenPlayers(npcs, s1id, players,
                                           s2id, guilds)
            decreaseAffinityBetweenPlayers(players, s2id, npcs,
                                           s1id, guilds)
            if not npcs[s1id]['animalType']:
                _sendCombatImage(mud, s2id, players,
                                 npcs[s1id]['race'], weaponType)
            else:
                _sendCombatImage(mud, s2id, players,
                                 npcs[s1id]['animalType'], weaponType)

            healthDescription = healthOfPlayer(s2id, players)
            if 'dead' in healthDescription:
                healthDescription = 'You are ' + healthDescription
            else:
                healthDescription = \
                    'Your health status is ' + healthDescription

            attackText = 'attacked'
            finalText = ''
            if isinstance(attackDescriptionSecond, str):
                attackText = attackDescriptionSecond
            elif isinstance(attackDescriptionSecond, list):
                attackText = attackDescriptionSecond[0]
                if len(attackDescriptionSecond) > 1:
                    finalText = ' ' + \
                        randomDescription(attackDescriptionSecond[1]) + \
                        '\n'
            mud.sendMessage(
                s2id, '<f220>' +
                npcs[s1id]['name'] + '<r> has ' +
                attackText +
                ' you for <f15><b88> * ' +
                damageValueDesc + ' * <r> points of ' +
                'damage.\n' + finalText +
                healthDescription + '\n')
    else:
        npcs[s1id]['lastCombatAction'] = int(time.time())
        desc = [
            '<f220>' + npcs[s1id]['name'] + '<r> missed you completely!',
            '<f220>' + npcs[s1id]['name'] + '<r> hopelessly fails to hit you',
            '<f220>' + npcs[s1id]['name'] + '<r> failed to hit you',
            '<f220>' + npcs[s1id]['name'] + '<r> utterly failed to hit you',
            '<f220>' + npcs[s1id]['name'] + '<r> completely failed to hit you',
            '<f220>' + npcs[s1id]['name'] + '<r> misses you widely',
            '<f220>' + npcs[s1id]['name'] + '<r> missed you by miles!',
            '<f220>' + npcs[s1id]['name'] + '<r> missed you by a wide margin'
        ]
        descr = randomDescription(desc)
        mud.sendMessage(s2id, descr + '\n')
    npcs[s1id]['lastCombatAction'] = int(time.time())


def isPlayerFighting(id, players: {}, fights: {}) -> bool:
    """Returns true if the player is fighting
    """
    for (fid, pl) in list(fights.items()):
        if fights[fid]['s1type'] == 'pc':
            if fights[fid]['s1'] == players[id]['name']:
                return True
        if fights[fid]['s2type'] == 'pc':
            if fights[fid]['s2'] == players[id]['name']:
                return True
    return False


def runFights(mud, players: {}, npcs: {}, fights: {}, items: {}, itemsDB: {},
              rooms: {}, maxTerrainDifficulty, mapArea: [], clouds: {},
              racesDB: {}, characterClassDB: {}, guilds: {}, attackDB: {}):
    """Handles fights
    """
    for (fid, pl) in list(fights.items()):
        # PC -> PC
        if fights[fid]['s1type'] == 'pc' and fights[fid]['s2type'] == 'pc':
            _runFightsBetweenPlayers(mud, players, npcs, fights, fid, itemsDB,
                                     rooms, maxTerrainDifficulty, mapArea,
                                     clouds, racesDB, characterClassDB, guilds,
                                     attackDB)
        # PC -> NPC
        elif fights[fid]['s1type'] == 'pc' and fights[fid]['s2type'] == 'npc':
            _runFightsBetweenPlayerAndNPC(mud, players, npcs, fights,
                                          fid, itemsDB, rooms,
                                          maxTerrainDifficulty, mapArea,
                                          clouds, racesDB, characterClassDB,
                                          guilds, attackDB)
        # NPC -> PC
        elif fights[fid]['s1type'] == 'npc' and fights[fid]['s2type'] == 'pc':
            _runFightsBetweenNPCAndPlayer(mud, players, npcs, fights,
                                          fid, items,
                                          itemsDB, rooms, maxTerrainDifficulty,
                                          mapArea, clouds, racesDB,
                                          characterClassDB, guilds, attackDB)
        # NPC -> NPC
        # elif fights[fid]['s1type'] == 'npc' and \
        #    fights[fid]['s2type'] == 'npc':
        #     test = 1


def isAttacking(players: {}, id, fights: {}) -> bool:
    """Returns true if the given player is attacking
    """
    for (fight, pl) in fights.items():
        if fights[fight]['s1'] == players[id]['name']:
            return True
    return False


def getAttackingTarget(players: {}, id, fights: {}):
    """Return the player or npc which is the target of an attack
    """
    for (fight, pl) in fights.items():
        if fights[fight]['s1'] == players[id]['name']:
            return fights[fight]['s2']
    return None


def stopAttack(players: {}, id, npcs: {}, fights: {}):
    """Stops any fights for the given player
    """
    fightsCopy = deepcopy(fights)
    for (fight, pl) in fightsCopy.items():
        s1type = fightsCopy[fight]['s1type']
        s1id = fightsCopy[fight]['s1id']
        s2type = fightsCopy[fight]['s2type']
        s2id = fightsCopy[fight]['s2id']
        if s1type == 'pc' and s1id == id:
            del fights[fight]
            players[id]['isInCombat'] = 0
            if s2type == 'pc':
                players[s2id]['isInCombat'] = 0
            else:
                npcs[s2id]['isInCombat'] = 0
        elif s2type == 'pc' and s2id == id:
            del fights[fight]
            players[id]['isInCombat'] = 0
            if s1type == 'pc':
                players[s1id]['isInCombat'] = 0
            else:
                npcs[s1id]['isInCombat'] = 0


def playerBeginsAttack(players: {}, id, target: str,
                       npcs: {}, fights: {}, mud, racesDB: {},
                       itemHistory: {}) -> bool:
    """Player begins an attack on another player or npc
    """
    targetFound = False
    if players[id]['name'].lower() == target.lower():
        mud.sendMessage(
            id,
            'You attempt hitting yourself and realise this ' +
            'might not be the most productive way of using your time.\n')
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

            _combatUpdateMaxHitPoints(id, players, racesDB)
            _combatUpdateMaxHitPoints(pid, players, racesDB)

            mud.sendMessage(
                id, '<f214>Attacking <r><f255>' + target + '!\n')

    if not targetFound:
        for (nid, pl) in list(npcs.items()):
            if target.lower() not in npcs[nid]['name'].lower():
                continue
            victimId = nid
            attackerId = id
            # found target npc
            if npcs[nid]['room'] != players[id]['room']:
                continue

            # check for familiar
            if npcs[nid]['familiarOf'] == players[id]['name']:
                desc = (
                    "You can't attack your own familiar",
                    "You consider attacking " +
                    "your own familiar, but decide against it",
                    "Your familiar looks at you disapprovingly"
                )
                descr = randomDescription(desc)
                mud.sendMessage(id, descr + "\n\n")
                return False

            if npcs[nid]['isAttackable'] == 0:
                mud.sendMessage(id, "You can't attack them\n\n")
                return False

            targetFound = True
            fights[len(fights)] = {
                's1': players[id]['name'],
                's2': nid,
                's1id': attackerId,
                's2id': victimId,
                's1type': 'pc',
                's2type': 'npc',
                'retaliated': 0
            }

            _combatUpdateMaxHitPoints(id, players, racesDB)
            _combatUpdateMaxHitPoints(nid, npcs, racesDB)

            mud.sendMessage(
                id, 'Attacking <u><f21>' + npcs[nid]['name'] + '<r>!\n')
            break

    if not targetFound:
        mud.sendMessage(
            id, 'You cannot see ' + target + ' anywhere nearby.\n')
    return targetFound


def _npcBeginsAttack(npcs: {}, id, target: str, players: {},
                     fights: {}, mud, items: {}, itemsDB: {},
                     racesDB: {}) -> bool:
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

            _combatUpdateMaxHitPoints(pid, players, racesDB)
            _combatUpdateMaxHitPoints(id, npcs, racesDB)

            _npcUpdateLuck(id, npcs, items, itemsDB)
            _npcWieldsWeapon(mud, pid, id, npcs, items, itemsDB)

            mud.sendMessage(
                pid, '<u><f21>' + npcs[id]['name'] + '<r> attacks!\n')

    if not targetFound:
        for (nid, pl) in list(npcs.items()):
            if target.lower() not in npcs[nid]['name'].lower():
                continue
            if npcs[nid]['isAttackable'] == 0:
                continue
            victimId = nid
            attackerId = id
            # found target npc
            if npcs[nid]['room'] != npcs[id]['room']:
                continue
            # target found!
            # check for familiar
            if npcs[nid]['familiarOf'] == npcs[id]['name']:
                return False

            targetFound = True
            fights[len(fights)] = {
                's1': npcs[id]['name'],
                's2': nid,
                's1id': attackerId,
                's2id': victimId,
                's1type': 'npc',
                's2type': 'npc',
                'retaliated': 0
            }
            fights[len(fights)] = {
                's1': nid,
                's2': npcs[id]['name'],
                's1id': victimId,
                's2id': attackerId,
                's1type': 'npc',
                's2type': 'npc',
                'retaliated': 0
            }
            npcs[nid]['isInCombat'] = 1
            npcs[id]['isInCombat'] = 1

            _combatUpdateMaxHitPoints(nid, npcs, racesDB)
            _combatUpdateMaxHitPoints(id, npcs, racesDB)

            _npcUpdateLuck(id, npcs, items, itemsDB)
            _npcWieldsWeapon(mud, pid, id, npcs, items, itemsDB)
            break

    return targetFound


def npcAggression(npcs: {}, players: {}, fights: {}, mud,
                  items: {}, itemsDB: {}, racesDB: {}):
    """Aggressive npcs start fights
    """
    for (nid, pl) in list(npcs.items()):
        if not npcs[nid].get('isAggressive'):
            continue
        if not npcs[nid]['isAggressive']:
            continue
        # dead npcs don't attack
        if npcs[nid]['whenDied']:
            continue
        if npcs[nid]['frozenStart'] > 0:
            continue
        # already attacking?
        if isAttacking(npcs, nid, fights):
            continue
        # are there players in the same room?
        for (pid, pl) in players.items():
            if players[pid]['room'] != npcs[nid]['room']:
                continue
            hasAffinity = False
            if npcs[nid].get('affinity'):
                if npcs[nid]['affinity'].get(players[pid]['name']):
                    if npcs[nid]['affinity'][players[pid]['name']] > 0:
                        hasAffinity = True
            if not hasAffinity:
                if randint(0, 1000) > 995:
                    _npcBeginsAttack(npcs, nid, players[pid]['name'],
                                     players, fights, mud, items,
                                     itemsDB, racesDB)
