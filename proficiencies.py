__filename__ = "proficiencies.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "DnD Mechanics"

from random import randint


def _proficiency_name(prof: str) -> str:
    if '(' not in prof:
        return prof

    return prof.split('(')[0].strip()


def _proficiency_param(prof: str) -> int:
    if '(' not in prof:
        return 0

    return int(prof.split('(')[1].replace(')', '').strip())


def _prof_fighting_style_damage(id, players: {},
                                weapon_type: str, value: int) -> int:
    if not players[id].get('fightingStyle'):
        return 0
    fight_style = players[id]['fightingStyle'].lower()
    if fight_style == 'archery':
        if 'bow' in weapon_type:
            return 2
    if fight_style.startswith('duel'):
        if 'ranged' not in weapon_type:
            if 'fist' not in weapon_type:
                if players[id]['clo_lhand'] == 0 or \
                   players[id]['clo_rhand'] == 0:
                    return 2
    return 0


def _damage_proficiency_item(prof: str, id, players: int,
                             weapon_type: str) -> int:
    if isinstance(prof, list):
        return 0

    prof_name = _proficiency_name(prof)
    prof_value = _proficiency_param(prof)

    switcher = {
        "Second Wind": _prof_second_wind,
        # "Action Surge": _profActionSurge,
        # "Martial Archetype": _profMartialArchetype,
        # "Ability Score Improvement": _profAbilityScore,
        # "Extra Attack": _profExtraAttack,
        # "Martial Archetype feature": _profMartialArchetypeFeature,
        "Indomitable": _prof_indomitable,
        # "Spellcasting": _profSpellcasting,
        # "Arcane Recovery": _profArcaneRecovery,
        # "Arcane Tradition": _profArcaneTradition,
        # "Arcane Tradition feature": _profArcaneTraditionFeature,
        # "Spell Mastery": _profSpellMastery,
        # "Signature Spell": _profSignatureSpell,
        # "Cantrips": _profCantrips,
        "Fighting Style": _prof_fighting_style_damage
    }

    if not switcher.get(prof_name):
        return 0

    try:
        return switcher[prof_name](id, players, weapon_type, prof_value)
    except Exception as ex:
        print("_damage_proficiency_item error " + prof + ' ' + str(ex))

    return 0


def damage_proficiency(id, players: {}, weapon_type: str,
                       character_class_db: {}) -> int:
    if not players[id].get('race'):
        return 0

    player_race = players[id]['race']

    if not character_class_db.get(player_race):
        return 0

    damage = 0
    for lvl in range(1, players[id]['lvl']):
        if character_class_db[player_race].get(str(lvl)):
            prof_list = character_class_db[player_race][str(lvl)]
            for plyr in prof_list:
                damage = damage + \
                    _damage_proficiency_item(plyr, id, players, weapon_type)
    return damage


def _prof_second_wind(id, players: {}, prof_value: int) -> int:
    if players[id]['restRequired'] != 0:
        return 0
    players[id]['restRequired'] = 1
    return randint(1, 10)


def _prof_indomitable(id, players: {}, prof_value: int) -> int:
    if players[id]['restRequired'] != 0:
        return 0
    players[id]['restRequired'] = 1
    return randint(1, 10)


def _defense_proficiency_item(prof: str, id, players: {}) -> int:
    """TODO: currently unused
    """
    if isinstance(prof, list):
        return 0

    prof_name = _proficiency_name(prof)
    prof_value = _proficiency_param(prof)

    switcher = {
        "Second Wind": _prof_second_wind,
        # "Arcane Recovery": _profArcaneRecovery,
        "Indomitable": _prof_indomitable
    }

    if not switcher.get(prof_name):
        return 0

    try:
        return switcher[prof_name](id, players, prof_value)
    except BaseException as ex:
        print("_defense_proficiency_item error " + prof + ' ' + str(ex))

    return 0


def _weaponProficiencyItem(prof: str, id, players: {},
                           weapon_type: str) -> int:
    if isinstance(prof, list):
        return 0

    prof_name = _proficiency_name(prof)
    prof_value = _proficiency_param(prof)

    switcher = {
        # "Second Wind": _prof_second_wind
    }

    if not switcher.get(prof_name):
        return 0

    try:
        return switcher[prof_name](id, players, prof_value)
    except BaseException as ex:
        print("_weaponProficiencyItem error " + prof + ' ' + str(ex))

    return 0


def weaponProficiency(id, players: {}, weapon_type: str,
                      character_class_db: {}) -> int:
    """TODO: currently unused
    """
    if not players[id].get('race'):
        return 0

    player_race = players[id]['race']

    if not character_class_db.get(player_race):
        return 0

    competence = int(players[id]['lvl']) - 1
    for lvl in range(1, players[id]['lvl']):
        if character_class_db[player_race].get(str(lvl)):
            prof_list = character_class_db[player_race][str(lvl)]
            for prf in prof_list:
                competence = competence + \
                    _weaponProficiencyItem(prf, id, players, weapon_type)

    if competence > 4:
        competence = 4

    return competence


def _thieves_cant_count_chars(txt: str) -> int:
    result = 0
    for char in txt.lower():
        if char in ('a', 'e', 'i', 'o', 'u'):
            result += 1
    return result


def thieves_cant(spoken_text: str) -> str:
    cant_code = (
        "Hey, girl, hey!",
        "Look what the cat dragged in",
        "Yo ho",
        "Is that you?",
        "What do we have here?",
        "Ain’t you a sight for sore eyes",
        "My, my, don’t that beat all",
        "Well aren’t you a piece of work",
        "Howdy Pardner",
        "At your service",
        "Cheerio, old chap",
        "You got some fried potatoes to go with that Lamb Chop?",
        "You got some fried potatoes to go with that Beefcake?",
        "Hey, beautiful",
        "Hey, handsome",
        "‘Ello Guv’nor",
        "I haven’t seen you in 6 months",
        "Wow, it’s been a few years",
        "Can you believe it’s been over 10 years?",
        "Seems like you left the village a lifetime ago",
        "Gosh, it feels like forever since I’ve seen you",
        "Will I see you at the harvest festival " +
        "(or any other hometown gathering) this year?",
        "Yes, I’ll be there",
        "No, I am otherwise engaged",
        "Give my regards to your Granny",
        "…and have your pets spayed")
    index = (_thieves_cant_count_chars(spoken_text) +
             len(spoken_text.split(' '))) % len(cant_code)
    return cant_code[index]
