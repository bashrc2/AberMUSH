__filename__ = "combat.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "DnD Mechanics"

from functions import player_inventory_weight
from functions import stow_hands
from functions import prepare_spells
from functions import random_desc
from functions import decrease_affinity_between_players
from functions import deepcopy
from functions import player_is_prone
from functions import set_player_prone
from random import randint
# from copy import deepcopy
from environment import get_temperature_at_coords
from proficiencies import damage_proficiency
from traps import player_is_trapped
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


def remove_prepared_spell(players: {}, id, spell_name: str):
    """Remove a prepared spell
    """
    del players[id]['preparedSpells'][spell_name]
    del players[id]['spellSlots'][spell_name]


def _player_is_available(id, players: {}, items_db: {}, rooms: {},
                         map_area: {}, clouds: {},
                         max_terrain_difficulty: int) -> bool:
    """Returns True if the player is available.
    Availability is encumbered by weight, temperature and terrain
    """
    curr_room = players[id]['room']
    weight_difficulty = \
        int(_get_encumberance_from_weight(id, players, items_db) * 2)
    temperature_difficulty = \
        _get_temperature_difficulty(curr_room, rooms, map_area, clouds)
    terrain_difficulty = \
        int(rooms[players[id]['room']]['terrainDifficulty'] * 10 /
            max_terrain_difficulty)

    # Agility of NPC
    modifier = \
        10 - players[id]['agi'] - \
        _armor_agility(id, players, items_db) + terrain_difficulty + \
        temperature_difficulty + weight_difficulty
    if modifier < 6:
        modifier = 6
    elif modifier > 25:
        modifier = 25

    if int(time.time()) < players[id]['lastCombatAction'] + modifier:
        return False
    return True


def _get_encumberance_from_weight(id, players: {}, items_db: {}) -> int:
    """Returns the light medium or heavy encumberance (0,1,2)
    """
    total_weight = player_inventory_weight(id, players, items_db)

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
        str_index = 20 + (strength % 10)
        multiplier = int((strength - 20) / 10)
        thresholds = encumberance[str(str_index)]
        for idx, _ in enumerate(thresholds):
            thresholds[idx] = int(thresholds[idx] * (multiplier*4))

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

    for idx, _ in enumerate(thresholds):
        if total_weight < int(thresholds[idx] * mult):
            return idx
    return 2


def _player_shoves(mud, id, players1: {}, s2id, players2: {},
                   races_db: {}) -> bool:
    """One player attempts to shove another
    """
    player1_size = players1[id]['siz']
    player2_size = players2[s2id]['siz']
    if players2[s2id].get('race'):
        race = players2[s2id]['race'].lower()
        if races_db.get(race):
            if races_db[race].get('siz'):
                player2_size = races_db[race]['siz']
    if player2_size < player1_size or player2_size > player1_size + 1:
        if player2_size > player1_size:
            descr = random_desc("They're too large to shove")
        else:
            descr = random_desc("They're too small to shove")
        mud.send_message(id, descr + '.\n')
        players1[id]['shove'] = 0
        return False

    player1_strength = players1[id]['str']
    player2_strength = players2[s2id]['str']
    if players2[s2id].get('race'):
        race = players2[s2id]['race'].lower()
        if races_db.get(race):
            if races_db[race].get('str'):
                player2_strength = races_db[race]['str']

    players1[id]['shove'] = 0

    if player_is_prone(s2id, players2):
        mud.send_message(
            id,
            'You attempt to shove ' + players2[s2id]['name'] +
            ', but they are already prone.\n')
        return False

    descr = random_desc('You shove ' + players2[s2id]['name'])
    mud.send_message(id, descr + '.\n')

    if randint(1, player1_strength) > randint(1, player2_strength):
        players2[s2id]['prone'] = 1
        desc = (
            'They stumble and fall to the ground',
            'They come crashing to the ground',
            'They fall heavily to the ground',
            'They topple and fall to the ground',
            'They stagger and fall backwards',
            'They lose balance and fall backwards'
        )
        descr = random_desc(desc)
        mud.send_message(id, descr + '.\n')
        return True
    desc = (
        'They remain standing',
        'They remain in place',
        'They stand firm',
        'They push back and remain standing',
        'They remain steady'
    )
    descr = random_desc(desc)
    mud.send_message(id, descr + '.\n')
    return False


def _combat_update_max_hit_points(id, players: {}, races_db: {}) -> None:
    """Updates the hp_max value
    """
    # some npcs are invincible
    if players[id]['hpMax'] >= 999:
        return

    level = players[id]['lvl']
    hit_die = '1d10'
    if players[id].get('race'):
        race = players[id]['race'].lower()
        if races_db.get(race):
            if races_db[race].get('hitDie'):
                hit_die = races_db[race]['hitDie']
    hp_max = int(hit_die.split('d')[1])
    if level > 1:
        hp_max = hp_max + (int(hp_max/2) * (level - 1))
    players[id]['hpMax'] = hp_max


def health_of_player(pid: int, players: {}) -> str:
    """Returns a description of health status
    """
    hp_val = players[pid]['hp']
    hp_max = 11
    if players[pid].get('hpMax'):
        hp_max = players[pid]['hpMax']
    health_percent = int(hp_val * 100 / hp_max)
    health_msg = 'in full health'
    if health_percent < 100:
        if health_percent >= 99:
            health_msg = 'lightly wounded'
        elif health_percent >= 84:
            health_msg = 'moderately wounded'
        elif health_percent >= 70:
            health_msg = 'considerably wounded'
        elif health_percent >= 56:
            health_msg = 'quite wounded'
        elif health_percent >= 42:
            health_msg = 'badly wounded'
        elif health_percent >= 28:
            health_msg = 'extremely wounded'
        elif health_percent >= 14:
            health_msg = 'critically wounded'
        elif health_percent > 0:
            health_msg = 'close to death'
        else:
            health_msg = 'dead'
        # add color for critical health
        if health_percent < 50:
            health_msg = '<f15><b88>' + health_msg + '<r>'
        elif health_percent < 70:
            health_msg = '<f15><b166>' + health_msg + '<r>'
    return health_msg


def _combat_ability_modifier(score: int) -> int:
    """Returns the ability modifier
    """
    if score > 30:
        return 10

    # min and max score and the corresponding
    # ability modifier
    ability_table = (
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

    for ability_range in ability_table:
        if score >= ability_range[0] and \
           score <= ability_range[1]:
            return ability_range[2]
    return 0


def _combat_race_resistance(id: int, players: {},
                            races_db: {}, weapon_type: str) -> int:
    """How much resistance does the player have to the weapon type
       based upon their race
    """
    resistance = 0
    resist_param = 'resist_' + weapon_type.lower()

    if weapon_type.endswith('bow'):
        resist_param = 'resist_piercing'

    if weapon_type.endswith('sling') or \
       'flail' in weapon_type or \
       'whip' in weapon_type:
        resist_param = 'resist_bludgeoning'

    if players[id].get('race'):
        race = players[id]['race'].lower()
        if races_db.get(race):
            if races_db[race].get(resist_param):
                resistance = races_db[race][resist_param]

    return resistance


def _combatDamageFromWeapon(id, players: {},
                            items_db: {}, weapon_type: str,
                            character_class_db: {},
                            is_critical: bool) -> (int, str):
    """find the weapon being used and return its damage value
    """
    weapon_locations = (
        'clo_lhand',
        'clo_rhand',
        'clo_gloves'
    )

    # bare knuckle fight
    damage_roll_best = '1d3'
    max_damage = 1

    for wpn in weapon_locations:
        item_id = int(players[id][wpn])
        if item_id <= 0:
            continue
        damage_roll = items_db[item_id]['damage']
        if not damage_roll:
            continue
        if 'd' not in damage_roll:
            continue
        die = int(damage_roll.split('d')[1])
        no_of_rolls = int(damage_roll.split('d')[0])
        if is_critical:
            # double the damage for a critical hit
            no_of_rolls *= 2
        score = 0
        if not items_db[item_id].get('damageChart'):
            # linear damage
            for _ in range(no_of_rolls):
                score += randint(1, die + 1)
        else:
            # see https://andregarzia.com/
            # 2021/12/in-defense-of-the-damage-chart.html
            for _ in range(no_of_rolls):
                chart_index = randint(0, die)
                if chart_index < len(items_db[item_id]['damageChart']):
                    score += items_db[item_id]['damageChart'][chart_index]
                else:
                    score += items_db[item_id]['damageChart'][-1]
        if score > max_damage:
            max_damage = score
            damage_roll_best = damage_roll
    return max_damage, damage_roll_best


def _combat_armor_class(id, players: {},
                        races_db: {}, attack_weapon_type: str,
                        items_db: {}) -> int:
    """Returns the armor class for the given player
    when attacked by the given weapon type
    """
    armor_class = 0
    for clth in defenseClothing:
        item_id = int(players[id][clth])
        if item_id <= 0:
            continue

        armor_class += items_db[item_id]['armor_class']
    if armor_class < 10:
        armor_class += 10

    race_armor = _combat_race_resistance(id, players, races_db,
                                         attack_weapon_type)
    if armor_class < race_armor:
        armor_class = race_armor

    if players[id].get('magicShield'):
        armor_class += players[id]['magicShield']

    return armor_class


def _combatProficiencyBonus(id, players: {}, weapon_type: str,
                            character_class_db: {}) -> int:
    """Returns the proficiency bonus with the given weapon type
    """
    return damage_proficiency(id, players, weapon_type,
                              character_class_db)


def _combat_attack_roll(id, players: {}, weapon_type: str,
                        target_armor_class: int,
                        character_class_db: {},
                        dodge_modifier: int) -> (bool, bool):
    """Returns true if an attack against a target succeeds
    """
    d20 = randint(1, 20)
    if d20 == 1:
        # miss
        return False, False
    if d20 == 20:
        # critical hit
        return True, True

    ability_modifier = 0
    if 'ranged' in weapon_type:
        ability_modifier = _combat_ability_modifier(players[id]['agi'])
    else:
        ability_modifier = _combat_ability_modifier(players[id]['str'])

    proficiency_bonus = \
        _combatProficiencyBonus(id, players, weapon_type,
                                character_class_db)

    if d20 + ability_modifier + proficiency_bonus >= \
       target_armor_class + dodge_modifier:
        return True, False
    return False, False


def _send_combat_image(mud, id, players: {}, race: str,
                       weapon_type: str) -> None:
    """Sends an image based on a character of a given race using a given weapon
    """
    if not (race and weapon_type):
        return
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            return
    combat_image_filename = 'images/combat/' + race + '_' + weapon_type
    if not os.path.isfile(combat_image_filename):
        return
    with open(combat_image_filename, 'r') as fp_img:
        mud.send_image(id, '\n' + fp_img.read())


def update_temporary_incapacitation(mud, players: {}, is_npc: bool) -> None:
    """Checks if players are incapacitated by spells and removes them
       after the duration has elapsed
    """
    now = int(time.time())
    for plyr in players:
        this_player = players[plyr]
        if this_player['name'] is None:
            continue
        if this_player['frozenStart'] != 0:
            st_time = \
                this_player['frozenStart'] + this_player['frozenDuration']
            if now >= st_time:
                this_player['frozenStart'] = 0
                this_player['frozenDuration'] = 0
                this_player['frozenDescription'] = ""
                if not is_npc:
                    mud.send_message(
                        plyr, "<f220>You find that you can move again.<r>\n\n")


def update_temporary_hit_points(mud, players: {}, is_npc: bool) -> None:
    """Updates any hit points added for a temporary period
       as the result of a spell
    """
    now = int(time.time())
    for plyr in players:
        this_player = players[plyr]
        if this_player['name'] is None:
            continue
        if this_player['tempHitPoints'] == 0:
            continue
        if this_player['tempHitPointsStart'] == 0 and \
           this_player['tempHitPointsDuration'] > 0:
            this_player['tempHitPointsStart'] = now
        else:
            if now > this_player['tempHitPointsStart'] + \
                    this_player['tempHitPointsDuration']:
                this_player['tempHitPoints'] = 0
                this_player['tempHitPointsStart'] = 0
                this_player['tempHitPointsDuration'] = 0
                if not is_npc:
                    mud.send_message(
                        plyr, "<f220>Your magical protection expires.<r>\n\n")


def update_temporary_charm(mud, players: {}, is_npc: bool) -> None:
    """Updates any charm added for a temporary period
       as the result of a spell
    """
    now = int(time.time())
    for plyr in players:
        this_player = players[plyr]
        if this_player['name'] is None:
            continue
        if this_player['tempCharm'] == 0:
            continue
        if this_player['tempCharmStart'] == 0 and \
           this_player['tempCharmDuration'] > 0:
            this_player['tempCharmStart'] = now
        else:
            if not this_player.get('tempCharmDuration'):
                return
            if now > this_player['tempCharmStart'] + \
                    this_player['tempCharmDuration']:
                this_player['tempCharmStart'] = 0
                this_player['tempCharmDuration'] = 0
                if this_player['affinity'].get(this_player['tempCharmTarget']):
                    charm_targ = this_player['tempCharmTarget']
                    this_player['affinity'][charm_targ] -= \
                        this_player['tempCharm']
                this_player['tempCharm'] = 0
                if not is_npc:
                    mud.send_message(
                        plyr, "<f220>A charm spell wears off.<r>\n\n")


def update_magic_shield(mud, players: {}, is_npc: bool) -> None:
    """Updates any magic shield for a temporary period
       as the result of a spell
    """
    now = int(time.time())
    for plyr in players:
        this_player = players[plyr]
        if this_player['name'] is None:
            continue
        if not this_player.get('magicShield'):
            continue
        if this_player['magicShieldStart'] == 0 and \
           this_player['magicShieldDuration'] > 0:
            this_player['magicShieldStart'] = now
        else:
            if not this_player.get('magicShieldDuration'):
                return
            if now > this_player['magicShieldStart'] + \
                    this_player['magicShieldDuration']:
                this_player['magicShieldStart'] = 0
                this_player['magicShieldDuration'] = 0
                this_player['magicShield'] = 0
                if not is_npc:
                    mud.send_message(
                        plyr, "<f220>Your magic shield wears off.<r>\n\n")


def players_rest(mud, players: {}) -> None:
    """Rest restores hit points
    """
    for plyr in players:
        this_player = players[plyr]
        if this_player['name'] is not None and \
           this_player['authenticated'] is not None:
            if this_player['hp'] < this_player['hpMax'] + \
                    this_player['tempHitPoints']:
                if randint(0, 100) > 90:
                    this_player['hp'] += 1
            else:
                this_player['hp'] = this_player['hpMax'] + \
                    this_player['tempHitPoints']
                this_player['restRequired'] = 0
                prepare_spells(mud, plyr, players)


def _item_in_npc_inventory(npcs, id: int, item_name: str,
                           items_db: {}) -> bool:
    """Is an item in the NPC's inventory?
    """
    if len(list(npcs[id]['inv'])) > 0:
        item_name_lower = item_name.lower()
        for idx in list(npcs[id]['inv']):
            if items_db[int(idx)]['name'].lower() == item_name_lower:
                return True
    return False


def _npc_update_luck(nid, npcs: {}, items: {}, items_db: {}) -> None:
    """Calculate the luck of an NPC based on what items they are carrying
    """
    luck = 0
    for i in npcs[nid]['inv']:
        luck = luck + items_db[int(i)]['mod_luc']
    npcs[nid]['luc'] = luck


def _npc_wields_weapon(mud, id: int, nid: int, npcs: {},
                       items: {}, items_db: {}) -> bool:
    """what is the best weapon which the NPC is carrying?
    """
    item_id = 0
    max_protection = 0
    max_damage = 0
    if int(npcs[nid]['canWield']) != 0:
        for i in npcs[nid]['inv']:
            if items_db[int(i)]['clo_rhand'] > 0:
                if items_db[int(i)]['mod_str'] > max_damage:
                    max_damage = items_db[int(i)]['mod_str']
                    item_id = int(i)
            elif items_db[int(i)]['clo_lhand'] > 0:
                if items_db[int(i)]['mod_str'] > max_damage:
                    max_damage = items_db[int(i)]['mod_str']
                    item_id = int(i)

    put_on_armor = False
    if int(npcs[nid]['canWear']) != 0:
        for i in npcs[nid]['inv']:
            if items_db[int(i)]['clo_chest'] < 1:
                continue
            if items_db[int(i)]['mod_endu'] > max_protection:
                max_protection = items_db[int(i)]['mod_endu']
                item_id = int(i)
                put_on_armor = True

    # search for any weapons on the floor
    picked_up_weapon = False
    item_weapon_index = 0
    if int(npcs[nid]['canWield']) != 0:
        items_in_world_copy = deepcopy(items)
        for iid, _ in list(items_in_world_copy.items()):
            if items_in_world_copy[iid]['room'] != npcs[nid]['room']:
                continue
            if items_db[items[iid]['id']]['weight'] == 0:
                continue
            if items_db[items[iid]['id']]['clo_rhand'] == 0:
                continue
            if items_db[items[iid]['id']]['mod_str'] <= max_damage:
                continue
            item_name = items_db[items[iid]['id']]['name']
            if _item_in_npc_inventory(npcs, nid, item_name, items_db):
                continue
            max_damage = items_db[items[iid]['id']]['mod_str']
            item_id = int(items[iid]['id'])
            item_weapon_index = iid
            picked_up_weapon = True

    # Search for any armor on the floor
    picked_up_armor = False
    item_armor_index = 0
    if int(npcs[nid]['canWear']) != 0:
        for iid, _ in list(items_in_world_copy.items()):
            if items_in_world_copy[iid]['room'] != npcs[nid]['room']:
                continue
            if items_db[items[iid]['id']]['weight'] == 0:
                continue
            if items_db[items[iid]['id']]['clo_chest'] == 0:
                continue
            if items_db[items[iid]['id']]['mod_endu'] <= max_protection:
                continue
            item_name = items_db[items[iid]['id']]['name']
            if _item_in_npc_inventory(npcs, nid, item_name, items_db):
                continue
            max_protection = \
                items_db[items[iid]['id']]['mod_endu']
            item_id = int(items[iid]['id'])
            item_armor_index = iid
            picked_up_armor = True

    if item_id > 0:
        if put_on_armor:
            if npcs[nid]['clo_chest'] != item_id:
                npcs[nid]['clo_chest'] = item_id
                mud.send_message(
                    id,
                    '<f220>' +
                    npcs[nid]['name'] +
                    '<r> puts on ' +
                    items_db[item_id]['article'] +
                    ' ' +
                    items_db[item_id]['name'] +
                    '\n')
                return True
            return False

        if picked_up_armor:
            if npcs[nid]['clo_chest'] != item_id:
                npcs[nid]['inv'].append(str(item_id))
                npcs[nid]['clo_chest'] = item_id
                del items[item_armor_index]
                mud.send_message(
                    id,
                    '<f220>' +
                    npcs[nid]['name'] +
                    '<r> picks up and wears ' +
                    items_db[item_id]['article'] +
                    ' ' +
                    items_db[item_id]['name'] +
                    '\n')
                return True
            return False

        if npcs[nid]['clo_rhand'] != item_id:
            # Transfer weapon to hand
            npcs[nid]['clo_rhand'] = item_id
            npcs[nid]['clo_lhand'] = 0
            if picked_up_weapon:
                npcs[nid]['inv'].append(str(item_id))
                del items[item_weapon_index]
                mud.send_message(
                    id,
                    '<f220>' +
                    npcs[nid]['name'] +
                    '<r> picks up ' +
                    items_db[item_id]['article'] +
                    ' ' +
                    items_db[item_id]['name'] +
                    '\n')
            else:
                mud.send_message(
                    id,
                    '<f220>' +
                    npcs[nid]['name'] +
                    '<r> has drawn their ' +
                    items_db[item_id]['name'] +
                    '\n')
            return True

    return False


def _npc_wears_armor(id: int, npcs: {}, items_db: {}) -> None:
    """An NPC puts on armor
    """
    if len(npcs[id]['inv']) == 0:
        return

    for clth in defenseClothing:
        item_id = 0
        # what is the best defense which the NPC is carrying?
        max_defense = 0
        for idx in npcs[id]['inv']:
            if items_db[int(idx)][clth] < 1:
                continue
            if items_db[int(idx)]['mod_str'] != 0:
                continue
            if items_db[int(idx)]['mod_endu'] > max_defense:
                max_defense = items_db[int(idx)]['mod_endu']
                item_id = int(idx)
        if item_id > 0:
            # Wear the armor
            npcs[id][clth] = item_id


def _two_handed_weapon(id: int, players: {}, items_db: {}) -> None:
    """ If carrying a two handed weapon then make sure
    that the other hand is empty
    """
    item_idleft = players[id]['clo_lhand']
    item_idright = players[id]['clo_rhand']
    # items on both hands
    if item_idleft == 0 or item_idright == 0:
        return
    # at least one item is two handed
    if items_db[item_idleft]['bothHands'] == 0 and \
       items_db[item_idright]['bothHands'] == 0:
        return
    if items_db[item_idright]['bothHands'] == 1:
        players[id]['clo_lhand'] = 0
    else:
        players[id]['clo_rhand'] = 0


def _armor_agility(id: int, players: {}, items_db: {}) -> int:
    """Modify agility based on armor worn
    """
    agility = 0

    for clth in defenseClothing:
        item_id = int(players[id][clth])
        if item_id > 0:
            agility = agility + int(items_db[item_id]['mod_agi'])

    # Total agility for clothing
    return agility


def _can_use_weapon(id: int, players: {}, items_db: {}, item_id: int) -> bool:
    """Can the given player use the given weapon?
    """
    if item_id == 0:
        return True
    lock_item_id = items_db[item_id]['lockedWithItem']
    if str(lock_item_id).isdigit():
        if lock_item_id > 0:
            item_name = items_db[lock_item_id]['name']
            for i in list(players[id]['inv']):
                if items_db[int(i)]['name'] == item_name:
                    return True
            return False
    return True


def _get_weapon_held(id: int, players: {}, items_db: {}) -> (int, str, int):
    """Returns the type of weapon held, or fists if none
    is held and the rounds of fire
    """
    fighter = players[id]
    if fighter['clo_rhand'] > 0 and fighter['clo_lhand'] == 0:
        # something in right hand
        item_id = int(fighter['clo_rhand'])
        if items_db[item_id]['mod_str'] > 0:
            if len(items_db[item_id]['type']) > 0:
                return item_id, items_db[item_id]['type'], \
                    items_db[item_id]['rof']

    if fighter['clo_lhand'] > 0 and fighter['clo_rhand'] == 0:
        # something in left hand
        item_id = int(fighter['clo_lhand'])
        if items_db[item_id]['mod_str'] > 0:
            if len(items_db[item_id]['type']) > 0:
                return item_id, items_db[item_id]['type'], \
                    items_db[item_id]['rof']

    if fighter['clo_lhand'] > 0 and fighter['clo_rhand'] > 0:
        # something in both hands
        item_right_id = int(fighter['clo_rhand'])
        item_right = items_db[item_right_id]
        item_left_id = int(fighter['clo_lhand'])
        item_left = items_db[item_left_id]
        if randint(0, 1) == 1:
            if item_right['mod_str'] > 0:
                if len(item_right['type']) > 0:
                    return item_right_id, item_right['type'], item_right['rof']
            if item_left['mod_str'] > 0:
                if len(item_left['type']) > 0:
                    return item_left_id, item_left['type'], item_left['rof']
        else:
            if item_left['mod_str'] > 0:
                if len(item_left['type']) > 0:
                    return item_left_id, item_left['type'], item_left['rof']
            if item_right['mod_str'] > 0:
                if len(item_right['type']) > 0:
                    return item_right_id, item_right['type'], item_right['rof']
    return 0, "fists", 1


def _get_attack_description(animal_type: str, weapon_type: str,
                            attack_db: {}, is_critical: bool,
                            thrown: bool) -> (str, str):
    """Describes an attack with a given type of weapon. This
       Returns both the first person and second person
       perspective descriptions
    """
    weapon_type = weapon_type.lower()

    if not animal_type:
        attack_strings = [
            "swing a fist at",
            "punch",
            "crudely swing a fist at",
            "ineptly punch"
        ]
        attack_description_first = random_desc(attack_strings)
        attack_strings = [
            "swung a fist at",
            "punched",
            "crudely swung a fist at",
            "ineptly punched"
        ]
        attack_description_second = random_desc(attack_strings)
        for attack_type, attack_desc in attack_db.items():
            if animal_type.startswith('animal '):
                continue
            attack_type_list = attack_type.split('|')
            for attack_type_str in attack_type_list:
                if not weapon_type.startswith(attack_type_str):
                    continue
                if thrown and 'thrown' not in attack_type_str:
                    continue
                if not thrown and 'thrown' in attack_type_str:
                    continue
                if not is_critical:
                    # first person - you attack a player or npc
                    attack_description_first = \
                        random_desc(attack_desc['first'])
                    # second person - you were attacked by a player or npc
                    attack_description_second = \
                        random_desc(attack_desc['second'])
                else:
                    # first person critical hit
                    attack_description_first = \
                        random_desc(attack_desc['critical first'])
                    # second person critical hit
                    attack_description_second = \
                        random_desc(attack_desc['critical second'])
                break
    else:
        attack_strings = [
            "savage",
            "maul",
            "bite",
            "viciously bite",
            "savagely gnaw"
        ]
        attack_description_first = random_desc(attack_strings)
        attack_strings = [
            "savaged",
            "mauled",
            "took a bite at",
            "viciously bit into",
            "savagely gnawed into"
        ]
        attack_description_second = random_desc(attack_strings)
        for an_type, attack_desc in attack_db.items():
            if not an_type.startswith('animal '):
                continue
            an_type = an_type.replace('animal ', '')
            animal_type_list = an_type.split('|')
            for animal_type_str in animal_type_list:
                if not animal_type.startswith(animal_type_str):
                    continue
                if not is_critical:
                    # first person -  you attack a player or npc
                    attack_description_first = \
                        random_desc(attack_desc['first'])
                    # second person -  you were attacked by a player or npc
                    attack_description_second = \
                        random_desc(attack_desc['second'])
                else:
                    # first person critical hit
                    attack_description_first = \
                        random_desc(attack_desc['critical first'])
                    # second person critical hit
                    attack_description_second = \
                        random_desc(attack_desc['critical second'])
                break

    return attack_description_first, attack_description_second


def _get_temperature_difficulty(rm: str, rooms: {}, map_area: [],
                                clouds: {}) -> int:
    """Returns a difficulty factor based on the ambient
       temperature
    """
    temperature = get_temperature_at_coords(
        rooms[rm]['coords'], rooms, map_area, clouds)

    if temperature > 5:
        # Things get difficult when hotter
        return int(temperature / 4)
    # Things get difficult in snow/ice
    return -(temperature - 5)


def _run_fights_between_players(mud, players: {}, npcs: {},
                                fights, fid, items_db: {},
                                rooms: {}, max_terrain_difficulty,
                                map_area: [],
                                clouds: {}, races_db: {},
                                character_class_db: {},
                                guilds: {}, attack_db: {}):
    """A fight between two players
    """
    s1id = fights[fid]['s1id']
    s2id = fights[fid]['s2id']

    # In the same room?
    if players[s1id]['room'] != players[s2id]['room']:
        return

    # is the player frozen?
    if players[s1id]['frozenStart'] > 0 or players[s1id]['canAttack'] == 0:
        descr = random_desc(players[s1id]['frozenDescription'])
        mud.send_message(s2id, descr + '\n')
        players[s1id]['lastCombatAction'] = int(time.time())
        return

    if player_is_trapped(s1id, players, rooms):
        players[s1id]['lastCombatAction'] = int(time.time())
        return

    if not _player_is_available(s1id, players, items_db, rooms,
                                map_area, clouds,
                                max_terrain_difficulty):
        return

    # if the player is dodging then miss a turn
    if players[s1id].get('dodge'):
        if players[s1id]['dodge'] == 1:
            players[s1id]['lastCombatAction'] = int(time.time())
            return

    if players[s2id]['isAttackable'] == 1:
        players[s1id]['isInCombat'] = 1
        players[s2id]['isInCombat'] = 1

        if player_is_prone(s1id, players):
            # on the ground, so can't attack and misses the turn
            players[s1id]['lastCombatAction'] = int(time.time())
            # stand up for the next turn
            set_player_prone(s1id, players, False)
            descr = random_desc(
                'stands up|' +
                'gets up|' +
                'gets back on their feet|' +
                'stands back up again'
            )
            mud.send_message(s2id, '<f32>' + players[s1id]['name'] + ' ' +
                             descr + '<r>.\n')
            return

        # attempt to shove
        if players[s1id].get('shove'):
            if players[s1id]['shove'] == 1:
                if _player_shoves(mud, s1id, players, s2id, players, races_db):
                    players[s2id]['lastCombatAction'] = int(time.time())
                players[s1id]['lastCombatAction'] = int(time.time())
                return

        _two_handed_weapon(s1id, players, items_db)
        weapon_id, weapon_type, rounds_of_fire = \
            _get_weapon_held(s1id, players, items_db)
        if not _can_use_weapon(s1id, players, items_db, weapon_id):
            lock_item_id = items_db[weapon_id]['lockedWithItem']
            mud.send_message(
                s1id, 'You take aim, but find you have no ' +
                items_db[lock_item_id]['name'].lower() + '.\n')
            mud.send_message(
                s2id, '<f32>' +
                players[s1id]['name'] +
                '<r> takes aim, but finds they have no ' +
                items_db[lock_item_id]['name'].lower() + '.\n')
            stow_hands(s1id, players, items_db, mud)
            mud.send_message(
                s2id, '<f32>' +
                players[s1id]['name'] +
                '<r> stows ' +
                items_db[weapon_id]['article'] +
                ' <b234>' +
                items_db[weapon_id]['name'] + '\n\n')
            players[s1id]['lastCombatAction'] = int(time.time())
            return

        # A dodge value used to adjust agility of the target player
        # This is proportional to their luck, which can be modified by
        # various items
        dodge_modifier = 0
        if players[s2id].get('dodge'):
            if players[s2id]['dodge'] == 1:
                dodge_modifier = randint(0, players[s2id]['luc'])
                desc = (
                    'You dodge',
                    'You swerve to avoid being hit',
                    'You pivot',
                    'You duck'
                )
                dodge_description = random_desc(desc)
                mud.send_message(s2id,
                                 '<f32>' + dodge_description + '<r>.\n')
                mud.send_message(
                    s1id, '<f32>' + players[s2id]['name'] +
                    '<r> tries to ' +
                    dodge_description.replace('You ', '') + '.\n')
                players[s2id]['dodge'] = 0

        target_armor_class = \
            _combat_armor_class(s2id, players,
                                races_db, weapon_type, items_db)

        # Do damage to the PC here
        hit, is_critical = \
            _combat_attack_roll(s1id, players, weapon_type,
                                target_armor_class,
                                character_class_db,
                                dodge_modifier)
        if hit:
            # TODO is the weapon thrown?
            thrown = False

            attack_description_first, attack_description_second = \
                _get_attack_description("", weapon_type, attack_db,
                                        is_critical, thrown)

            if rounds_of_fire < 1:
                rounds_of_fire = 1

            for _ in range(rounds_of_fire):
                if players[s1id]['hp'] <= 0:
                    break
                damage_value, damage_roll = \
                    _combatDamageFromWeapon(s1id, players,
                                            items_db, weapon_type,
                                            character_class_db,
                                            is_critical)
                # eg "1d8 = 5"
                damage_value_desc = damage_roll + ' = ' + str(damage_value)
                if is_critical:
                    damage_value_desc = '2 x ' + damage_value_desc

                if int(players[s2id]['hpMax']) < 999:
                    players[s2id]['hp'] = \
                        int(players[s2id]['hp']) - damage_value
                    if players[s2id]['hp'] < 0:
                        players[s2id]['hp'] = 0

                decrease_affinity_between_players(
                    players, s2id, players, s1id, guilds)
                decrease_affinity_between_players(
                    players, s1id, players, s2id, guilds)
                _send_combat_image(mud, s1id, players,
                                   players[s1id]['race'], weapon_type)

                attack_text = 'attack'
                final_text = ''
                if isinstance(attack_description_first, str):
                    attack_text = attack_description_first
                elif isinstance(attack_description_first, list):
                    attack_text = attack_description_first[0]
                    if len(attack_description_first) > 1:
                        final_text = ' ' + \
                            random_desc(attack_description_first[1]) + '\n'
                mud.send_message(
                    s1id, 'You ' + attack_text + ' <f32><u>' +
                    players[s2id]['name'] +
                    '<r> for <f15><b2> * ' +
                    damage_value_desc +
                    ' *<r> points of damage.\n' +
                    final_text +
                    players[s2id]['name'] + ' is ' +
                    health_of_player(s2id, players) + '\n')

                _send_combat_image(mud, s2id, players,
                                   players[s1id]['race'], weapon_type)

                health_description = health_of_player(s2id, players)
                if 'dead' in health_description:
                    health_description = 'You are ' + health_description
                else:
                    health_description = \
                        'Your health status is ' + health_description

                attack_text = 'attacked'
                final_text = ''
                if isinstance(attack_description_second, str):
                    attack_text = attack_description_second
                elif isinstance(attack_description_second, list):
                    attack_text = attack_description_second[0]
                    if len(attack_description_second) > 1:
                        final_text = ' ' + \
                            random_desc(attack_description_second[1]) + \
                            '\n'
                mud.send_message(
                    s2id, '<f32>' +
                    players[s1id]['name'] +
                    '<r> has ' + attack_text + ' you for <f15><b88> * ' +
                    damage_value_desc +
                    ' *<r> points of damage.\n' + final_text +
                    health_description + '\n')
        else:
            players[s1id]['lastCombatAction'] = int(time.time())
            mud.send_message(
                s1id, 'You miss trying to hit <f32><u>' +
                players[s2id]['name'] + '\n')
            mud.send_message(
                s2id, '<f32><u>' +
                players[s1id]['name'] +
                '<r> missed while trying to hit you!\n')
        players[s1id]['lastCombatAction'] = int(time.time())
    else:
        mud.send_message(
            s1id,
            '<f225>Suddenly you stop. It wouldn`t be a good ' +
            'idea to attack <f32>' +
            players[s2id]['name'] + ' at this time.\n')
        fights_copy = deepcopy(fights)
        for fight, _ in fights_copy.items():
            if fights_copy[fight]['s1id'] == s1id and \
               fights_copy[fight]['s1type'] == 'pc' and \
               fights_copy[fight]['s2id'] == s2id and \
               fights_copy[fight]['s2type'] == 'pc':
                del fights[fight]
                players[s1id]['isInCombat'] = 0
                players[s2id]['isInCombat'] = 0


def _run_fights_between_player_and_npc(mud, players: {}, npcs: {}, fights, fid,
                                       items_db: {}, rooms: {},
                                       max_terrain_difficulty,
                                       map_area: [], clouds: {}, races_db: {},
                                       character_class_db: {}, guilds: {},
                                       attack_db: {}):
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
        descr = random_desc(players[s1id]['frozenDescription'])
        mud.send_message(s2id, descr + '\n')
        players[s1id]['lastCombatAction'] = int(time.time())
        return

    if player_is_trapped(s1id, players, rooms):
        players[s1id]['lastCombatAction'] = int(time.time())
        return

    if not _player_is_available(s1id, players, items_db, rooms,
                                map_area, clouds,
                                max_terrain_difficulty):
        return

    # if the player is dodging then miss a turn
    if players[s1id].get('dodge'):
        if players[s1id]['dodge'] == 1:
            players[s1id]['lastCombatAction'] = int(time.time())
            return

    if npcs[s2id]['isAttackable'] == 1:
        players[s1id]['isInCombat'] = 1
        npcs[s2id]['isInCombat'] = 1

        if player_is_prone(s1id, players):
            # on the ground, so can't attack and misses the turn
            players[s1id]['lastCombatAction'] = int(time.time())
            # stand up for the next turn
            set_player_prone(s1id, players, False)
            return

        # attempt to shove
        if players[s1id].get('shove'):
            if players[s1id]['shove'] == 1:
                if _player_shoves(mud, s1id, players, s2id, npcs, races_db):
                    npcs[s2id]['lastCombatAction'] = int(time.time())
                players[s1id]['lastCombatAction'] = int(time.time())
                return

        _two_handed_weapon(s1id, players, items_db)
        weapon_id, weapon_type, rounds_of_fire = \
            _get_weapon_held(s1id, players, items_db)
        if not _can_use_weapon(s1id, players, items_db, weapon_id):
            lock_item_id = items_db[weapon_id]['lockedWithItem']
            mud.send_message(
                s1id,
                'You take aim, but find you have no ' +
                items_db[lock_item_id]['name'].lower() +
                '.\n')
            stow_hands(s1id, players, items_db, mud)
            players[s1id]['lastCombatAction'] = int(time.time())
            return

        # A dodge value used to adjust agility of the target player
        # This is proportional to their luck, which can be modified by
        # various items
        dodge_modifier = 0
        if npcs[s2id].get('dodge'):
            if npcs[s2id]['dodge'] == 1:
                dodge_modifier = randint(0, npcs[s2id]['luc'])
                mud.send_message(
                    s1id, '<f32>' + npcs[s2id]['name'] +
                    '<r> tries to dodge.\n')
                npcs[s2id]['dodge'] = 0

        target_armor_class = \
            _combat_armor_class(s2id, npcs,
                                races_db, weapon_type, items_db)

        # Do damage to the PC here
        hit, is_critical = \
            _combat_attack_roll(s1id, players, weapon_type,
                                target_armor_class,
                                character_class_db,
                                dodge_modifier)
        if hit:
            # TODO is the weapon thrown?
            thrown = False

            attack_description_first, _ = \
                _get_attack_description("", weapon_type, attack_db,
                                        is_critical, thrown)

            if rounds_of_fire < 1:
                rounds_of_fire = 1

            for _ in range(rounds_of_fire):
                if players[s1id]['hp'] <= 0:
                    break

                damage_value, damage_roll = \
                    _combatDamageFromWeapon(s1id, players,
                                            items_db, weapon_type,
                                            character_class_db,
                                            is_critical)
                # eg "1d8 = 5"
                damage_value_desc = damage_roll + ' = ' + str(damage_value)
                if is_critical:
                    damage_value_desc = '2 x ' + damage_value_desc

                _npc_wears_armor(s2id, npcs, items_db)

                if int(npcs[s2id]['hpMax']) < 999:
                    npcs[s2id]['hp'] = int(npcs[s2id]['hp']) - damage_value
                    if int(npcs[s2id]['hp']) < 0:
                        npcs[s2id]['hp'] = 0

                decrease_affinity_between_players(npcs, s2id, players,
                                                  s1id, guilds)
                decrease_affinity_between_players(players, s1id, npcs,
                                                  s2id, guilds)
                _send_combat_image(mud, s1id, players,
                                   players[s1id]['race'], weapon_type)
                attack_text = 'attack'
                final_text = ''
                if isinstance(attack_description_first, str):
                    attack_text = attack_description_first
                elif isinstance(attack_description_first, list):
                    attack_text = attack_description_first[0]
                    if len(attack_description_first) > 1:
                        final_text = ' ' + \
                            random_desc(attack_description_first[1]) + '\n'
                mud.send_message(
                    s1id,
                    'You ' + attack_text + ' <f220>' +
                    npcs[s2id]['name'] +
                    '<r> for <b2><f15> * ' +
                    damage_value_desc +
                    ' * <r> points of damage\n' + final_text +
                    npcs[s2id]['name'] + ' is ' +
                    health_of_player(s2id, npcs) + '\n')
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
            descr = random_desc(desc)
            mud.send_message(s1id, descr + '\n')
        players[s1id]['lastCombatAction'] = int(time.time())
    else:
        mud.send_message(
            s1id,
            '<f225>Suddenly you stop. It wouldn`t be a good ' +
            'idea to attack <u><f21>' +
            npcs[s2id]['name'] + '<r> at this time.\n')
        fights_copy = deepcopy(fights)
        for fight, _ in fights_copy.items():
            if fights_copy[fight]['s1id'] == s1id and \
               fights_copy[fight]['s1type'] == 'pc' and \
               fights_copy[fight]['s2id'] == s2id and \
               fights_copy[fight]['s2type'] == 'npc':
                del fights[fight]
                players[s1id]['isInCombat'] = 0
                npcs[s2id]['isInCombat'] = 0


def _run_fights_between_npc_and_player(mud, players: {}, npcs: {}, fights, fid,
                                       items: {}, items_db: {}, rooms: {},
                                       max_terrain_difficulty, map_area,
                                       clouds: {},
                                       races_db: {}, character_class_db: {},
                                       guilds: {}, attack_db: {}):
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
            s2id, '<f220>' +
            npcs[s1id]['name'] +
            "<r> tries to attack but can't move\n")
        npcs[s1id]['lastCombatAction'] = int(time.time())
        return

    if not _player_is_available(s1id, npcs, items_db, rooms,
                                map_area, clouds,
                                max_terrain_difficulty):
        return

    # if the npc is dodging then miss a turn
    if npcs[s1id].get('dodge'):
        if npcs[s1id]['dodge'] == 1:
            npcs[s1id]['lastCombatAction'] = int(time.time())
            return

    npcs[s1id]['isInCombat'] = 1
    players[s2id]['isInCombat'] = 1

    if player_is_prone(s1id, npcs):
        # on the ground, so can't attack and misses the turn
        npcs[s1id]['lastCombatAction'] = int(time.time())
        # stand up for the next turn
        set_player_prone(s1id, npcs, False)
        desc = (
            'stands up',
            'gets up',
            'gets back on their feet',
            'stands back up again'
        )
        descr = random_desc(desc)
        mud.send_message(s2id, '<f32>' + npcs[s1id]['name'] + ' ' +
                         descr + '<r>.\n')
        return

    _npc_update_luck(s1id, npcs, items, items_db)
    if _npc_wields_weapon(mud, s2id, s1id, npcs, items, items_db):
        npcs[s1id]['lastCombatAction'] = int(time.time())
        return

    _two_handed_weapon(s1id, npcs, items_db)
    _, weapon_type, rounds_of_fire = \
        _get_weapon_held(s1id, npcs, items_db)

    # A dodge value used to adjust agility of the target player
    # This is proportional to their luck, which can be modified by
    # various items
    dodge_modifier = 0
    if players[s2id].get('dodge'):
        if players[s2id]['dodge'] == 1:
            dodge_modifier = randint(0, players[s2id]['luc'])
            desc = (
                'You dodge',
                'You swerve to avoid being hit',
                'You pivot',
                'You duck'
            )
            dodge_description = random_desc(desc)
            mud.send_message(s2id,
                             '<f32>' + dodge_description + '<r>.\n')
            players[s2id]['dodge'] = 0

    target_armor_class = \
        _combat_armor_class(s2id, players,
                            races_db, weapon_type, items_db)

    # Do damage to the PC here
    hit, is_critical = \
        _combat_attack_roll(s1id, npcs, weapon_type,
                            target_armor_class, character_class_db,
                            dodge_modifier)
    if hit:
        # TODO is the weapon thrown?
        thrown = False

        _, attack_description_second = \
            _get_attack_description(npcs[s1id]['animalType'],
                                    weapon_type, attack_db,
                                    is_critical, thrown)

        if rounds_of_fire < 1:
            rounds_of_fire = 1

        for _ in range(rounds_of_fire):
            if npcs[s1id]['hp'] <= 0:
                break
            damage_value, damage_roll = \
                _combatDamageFromWeapon(s1id, npcs,
                                        items_db, weapon_type,
                                        character_class_db,
                                        is_critical)
            # eg "1d8 = 5"
            damage_value_desc = damage_roll + ' = ' + str(damage_value)
            if is_critical:
                damage_value_desc = '2 x ' + damage_value_desc

            if int(players[s2id]['hpMax']) < 999:
                players[s2id]['hp'] = int(players[s2id]['hp']) - damage_value
                if int(players[s2id]['hp']) < 0:
                    players[s2id]['hp'] = 0

            decrease_affinity_between_players(npcs, s1id, players,
                                              s2id, guilds)
            decrease_affinity_between_players(players, s2id, npcs,
                                              s1id, guilds)
            if not npcs[s1id]['animalType']:
                _send_combat_image(mud, s2id, players,
                                   npcs[s1id]['race'], weapon_type)
            else:
                _send_combat_image(mud, s2id, players,
                                   npcs[s1id]['animalType'], weapon_type)

            health_description = health_of_player(s2id, players)
            if 'dead' in health_description:
                health_description = 'You are ' + health_description
            else:
                health_description = \
                    'Your health status is ' + health_description

            attack_text = 'attacked'
            final_text = ''
            if isinstance(attack_description_second, str):
                attack_text = attack_description_second
            elif isinstance(attack_description_second, list):
                attack_text = attack_description_second[0]
                if len(attack_description_second) > 1:
                    final_text = ' ' + \
                        random_desc(attack_description_second[1]) + \
                        '\n'
            mud.send_message(
                s2id, '<f220>' +
                npcs[s1id]['name'] + '<r> has ' +
                attack_text +
                ' you for <f15><b88> * ' +
                damage_value_desc + ' * <r> points of ' +
                'damage.\n' + final_text +
                health_description + '\n')
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
        descr = random_desc(desc)
        mud.send_message(s2id, descr + '\n')
    npcs[s1id]['lastCombatAction'] = int(time.time())


def is_player_fighting(id, players: {}, fights: {}) -> bool:
    """Returns true if the player is fighting
    """
    for (fid, _) in list(fights.items()):
        if fights[fid]['s1type'] == 'pc':
            if fights[fid]['s1'] == players[id]['name']:
                return True
        if fights[fid]['s2type'] == 'pc':
            if fights[fid]['s2'] == players[id]['name']:
                return True
    return False


def run_fights(mud, players: {}, npcs: {}, fights: {}, items: {}, items_db: {},
               rooms: {}, max_terrain_difficulty, map_area: [], clouds: {},
               races_db: {}, character_class_db: {}, guilds: {},
               attack_db: {}):
    """Handles fights
    """
    for fid, _ in list(fights.items()):
        # PC -> PC
        if fights[fid]['s1type'] == 'pc' and fights[fid]['s2type'] == 'pc':
            _run_fights_between_players(mud, players, npcs, fights, fid,
                                        items_db, rooms,
                                        max_terrain_difficulty,
                                        map_area, clouds, races_db,
                                        character_class_db,
                                        guilds, attack_db)
        # PC -> NPC
        elif fights[fid]['s1type'] == 'pc' and fights[fid]['s2type'] == 'npc':
            _run_fights_between_player_and_npc(mud, players, npcs, fights,
                                               fid, items_db, rooms,
                                               max_terrain_difficulty,
                                               map_area,
                                               clouds, races_db,
                                               character_class_db,
                                               guilds, attack_db)
        # NPC -> PC
        elif fights[fid]['s1type'] == 'npc' and fights[fid]['s2type'] == 'pc':
            _run_fights_between_npc_and_player(mud, players, npcs, fights,
                                               fid, items, items_db, rooms,
                                               max_terrain_difficulty,
                                               map_area, clouds, races_db,
                                               character_class_db, guilds,
                                               attack_db)
        # NPC -> NPC
        # elif fights[fid]['s1type'] == 'npc' and \
        #    fights[fid]['s2type'] == 'npc':
        #     test = 1


def is_attacking(players: {}, id, fights: {}) -> bool:
    """Returns true if the given player is attacking
    """
    for fight, _ in fights.items():
        if fights[fight]['s1'] == players[id]['name']:
            return True
    return False


def get_attacking_target(players: {}, id, fights: {}):
    """Return the player or npc which is the target of an attack
    """
    for fight, _ in fights.items():
        if fights[fight]['s1'] == players[id]['name']:
            return fights[fight]['s2']
    return None


def stop_attack(players: {}, id, npcs: {}, fights: {}):
    """Stops any fights for the given player
    """
    fights_copy = deepcopy(fights)
    for fight, _ in fights_copy.items():
        s1type = fights_copy[fight]['s1type']
        s1id = fights_copy[fight]['s1id']
        s2type = fights_copy[fight]['s2type']
        s2id = fights_copy[fight]['s2id']
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


def player_begins_attack(players: {}, id, target: str,
                         npcs: {}, fights: {}, mud, races_db: {},
                         item_history: {}, thrown: bool) -> bool:
    """Player begins an attack on another player or npc
    """
    target_found = False
    if players[id]['name'].lower() == target.lower():
        mud.send_message(
            id,
            'You attempt hitting yourself and realise this ' +
            'might not be the most productive way of using your time.\n')
        return target_found

    for pid, _ in players.items():
        if players[pid]['authenticated'] and \
           players[pid]['name'].lower() == target.lower():
            target_found = True
            victim_id = pid
            attacker_id = id
            if players[pid]['room'] != players[id]['room']:
                target_found = False
                continue

            fights[len(fights)] = {
                's1': players[id]['name'],
                's2': target,
                's1id': attacker_id,
                's2id': victim_id,
                's1type': 'pc',
                's2type': 'pc',
                'retaliated': 0,
                'thrown': thrown
            }

            _combat_update_max_hit_points(id, players, races_db)
            _combat_update_max_hit_points(pid, players, races_db)

            if not thrown:
                mud.send_message(
                    id, '<f214>Attacking <r><f255>' + target + '!\n')
            else:
                mud.send_message(
                    id, '<f214>Throwing at <r><f255>' + target + '!\n')

    if not target_found:
        for nid, _ in list(npcs.items()):
            if target.lower() not in npcs[nid]['name'].lower():
                continue
            victim_id = nid
            attacker_id = id
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
                descr = random_desc(desc)
                mud.send_message(id, descr + "\n\n")
                return False

            if npcs[nid]['isAttackable'] == 0:
                mud.send_message(id, "You can't attack them\n\n")
                return False

            target_found = True
            fights[len(fights)] = {
                's1': players[id]['name'],
                's2': nid,
                's1id': attacker_id,
                's2id': victim_id,
                's1type': 'pc',
                's2type': 'npc',
                'retaliated': 0,
                'thrown': thrown
            }

            _combat_update_max_hit_points(id, players, races_db)
            _combat_update_max_hit_points(nid, npcs, races_db)

            if not thrown:
                mud.send_message(
                    id, 'Attacking <u><f21>' + npcs[nid]['name'] + '<r>!\n')
            else:
                mud.send_message(
                    id, 'Throwing at <u><f21>' + npcs[nid]['name'] + '<r>!\n')
            break

    if not target_found:
        mud.send_message(
            id, 'You cannot see ' + target + ' anywhere nearby.\n')
    return target_found


def _npc_begins_attack(npcs: {}, id, target: str, players: {},
                       fights: {}, mud, items: {}, items_db: {},
                       races_db: {}, thrown: bool) -> bool:
    """npc begins an attack on a player or another npc
    """
    target_found = False
    if npcs[id]['name'].lower() == target.lower():
        return target_found

    for pid, _ in players.items():
        if players[pid]['authenticated'] and \
           players[pid]['name'].lower() == target.lower():
            target_found = True
            victim_id = pid
            attacker_id = id
            if players[pid]['room'] != npcs[id]['room']:
                target_found = False
                continue

            fights[len(fights)] = {
                's1': id,
                's2': players[pid]['name'],
                's1id': attacker_id,
                's2id': victim_id,
                's1type': 'npc',
                's2type': 'pc',
                'retaliated': 0,
                'thrown': thrown
            }
            fights[len(fights)] = {
                's1': players[pid]['name'],
                's2': id,
                's1id': victim_id,
                's2id': attacker_id,
                's1type': 'pc',
                's2type': 'npc',
                'retaliated': 0
            }
            players[pid]['isInCombat'] = 1
            npcs[id]['isInCombat'] = 1

            _combat_update_max_hit_points(pid, players, races_db)
            _combat_update_max_hit_points(id, npcs, races_db)

            _npc_update_luck(id, npcs, items, items_db)
            _npc_wields_weapon(mud, pid, id, npcs, items, items_db)

            mud.send_message(
                pid, '<u><f21>' + npcs[id]['name'] + '<r> attacks!\n')

    if not target_found:
        for nid, _ in list(npcs.items()):
            if target.lower() not in npcs[nid]['name'].lower():
                continue
            if npcs[nid]['isAttackable'] == 0:
                continue
            victim_id = nid
            attacker_id = id
            # found target npc
            if npcs[nid]['room'] != npcs[id]['room']:
                continue
            # target found!
            # check for familiar
            if npcs[nid]['familiarOf'] == npcs[id]['name']:
                return False

            target_found = True
            fights[len(fights)] = {
                's1': npcs[id]['name'],
                's2': nid,
                's1id': attacker_id,
                's2id': victim_id,
                's1type': 'npc',
                's2type': 'npc',
                'retaliated': 0
            }
            fights[len(fights)] = {
                's1': nid,
                's2': npcs[id]['name'],
                's1id': victim_id,
                's2id': attacker_id,
                's1type': 'npc',
                's2type': 'npc',
                'retaliated': 0
            }
            npcs[nid]['isInCombat'] = 1
            npcs[id]['isInCombat'] = 1

            _combat_update_max_hit_points(nid, npcs, races_db)
            _combat_update_max_hit_points(id, npcs, races_db)

            _npc_update_luck(id, npcs, items, items_db)
            _npc_wields_weapon(mud, nid, id, npcs, items, items_db)
            break

    return target_found


def npc_aggression(npcs: {}, players: {}, fights: {}, mud,
                   items: {}, items_db: {}, races_db: {}):
    """Aggressive npcs start fights
    """
    for nid, _ in list(npcs.items()):
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
        if is_attacking(npcs, nid, fights):
            continue
        # are there players in the same room?
        for pid, _ in players.items():
            if players[pid]['room'] != npcs[nid]['room']:
                continue
            has_affinity = False
            if npcs[nid].get('affinity'):
                if npcs[nid]['affinity'].get(players[pid]['name']):
                    if npcs[nid]['affinity'][players[pid]['name']] > 0:
                        has_affinity = True
            if not has_affinity:
                if randint(0, 1000) > 995:
                    # TODO does the npc have a throwable weapon?
                    thrown = False
                    _npc_begins_attack(npcs, nid, players[pid]['name'],
                                       players, fights, mud, items,
                                       items_db, races_db, thrown)
