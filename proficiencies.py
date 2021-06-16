__filename__ = "proficiencies.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"
__module_group__ = "DnD Mechanics"

from random import randint


def _proficiencyName(prof: str) -> str:
    if '(' not in prof:
        return prof

    return prof.split('(')[0].strip()


def _proficiencyParam(prof: str) -> int:
    if '(' not in prof:
        return 0

    return int(prof.split('(')[1].replace(')', '').strip())


def _profFightingStyleDamage(id, players: {},
                             weaponType: str, value: int) -> int:
    if not players[id].get('fightingStyle'):
        return 0
    fightStyle = players[id]['fightingStyle'].lower()
    if fightStyle == 'archery':
        if 'bow' in weaponType:
            return 2
    if fightStyle.startswith('duel'):
        if 'ranged' not in weaponType:
            if 'fist' not in weaponType:
                if players[id]['clo_lhand'] == 0 or \
                   players[id]['clo_rhand'] == 0:
                    return 2
    return 0


def _damageProficiencyItem(prof: str, id, players: int,
                           weaponType: str) -> int:
    if isinstance(prof, list):
        return 0

    profName = _proficiencyName(prof)
    profValue = _proficiencyParam(prof)

    switcher = {
        "Second Wind": _profSecondWind,
        # "Action Surge": _profActionSurge,
        # "Martial Archetype": _profMartialArchetype,
        # "Ability Score Improvement": _profAbilityScore,
        # "Extra Attack": _profExtraAttack,
        # "Martial Archetype feature": _profMartialArchetypeFeature,
        "Indomitable": _profIndomitable,
        # "Spellcasting": _profSpellcasting,
        # "Arcane Recovery": _profArcaneRecovery,
        # "Arcane Tradition": _profArcaneTradition,
        # "Arcane Tradition feature": _profArcaneTraditionFeature,
        # "Spell Mastery": _profSpellMastery,
        # "Signature Spell": _profSignatureSpell,
        # "Cantrips": _profCantrips,
        "Fighting Style": _profFightingStyleDamage
    }

    if not switcher.get(profName):
        return 0

    try:
        return switcher[profName](id, players, weaponType, profValue)
    except Exception as e:
        print("_damageProficiencyItem error " + prof + ' ' + str(e))

    return 0


def damageProficiency(id, players: {}, weaponType: str,
                      characterClassDB: {}) -> int:
    if not players[id].get('race'):
        return 0

    playerRace = players[id]['race']

    if not characterClassDB.get(playerRace):
        return 0

    damage = 0
    for lvl in range(1, players[id]['lvl']):
        if characterClassDB[playerRace].get(str(lvl)):
            profList = characterClassDB[playerRace][str(lvl)]
            for p in profList:
                damage = damage + \
                    _damageProficiencyItem(p, id, players, weaponType)
    return damage


def _profSecondWind(id, players: {}, profValue: int) -> int:
    if players[id]['restRequired'] != 0:
        return 0
    players[id]['restRequired'] = 1
    return randint(1, 10)


def _profIndomitable(id, players: {}, profValue: int) -> int:
    if players[id]['restRequired'] != 0:
        return 0
    players[id]['restRequired'] = 1
    return randint(1, 10)


def _defenseProficiencyItem(prof: str, id, players: {}) -> int:
    """TODO: currently unused
    """
    if isinstance(prof, list):
        return 0

    profName = _proficiencyName(prof)
    profValue = _proficiencyParam(prof)

    switcher = {
        "Second Wind": _profSecondWind,
        # "Arcane Recovery": _profArcaneRecovery,
        "Indomitable": _profIndomitable
    }

    if not switcher.get(profName):
        return 0

    try:
        return switcher[profName](id, players, profValue)
    except Exception as e:
        print("_defenseProficiencyItem error " + prof + ' ' + str(e))

    return 0


def _weaponProficiencyItem(prof: str, id, players: {}, weaponType: str) -> int:
    if isinstance(prof, list):
        return 0

    profName = _proficiencyName(prof)
    profValue = _proficiencyParam(prof)

    switcher = {
        # "Second Wind": _profSecondWind
    }

    if not switcher.get(profName):
        return 0

    try:
        return switcher[profName](id, players, profValue)
    except Exception as e:
        print("_weaponProficiencyItem error " + prof + ' ' + str(e))

    return 0


def weaponProficiency(id, players: {}, weaponType: str,
                      characterClassDB: {}) -> int:
    """TODO: currently unused
    """
    if not players[id].get('race'):
        return 0

    playerRace = players[id]['race']

    if not characterClassDB.get(playerRace):
        return 0

    competence = int(players[id]['lvl']) - 1
    for lvl in range(1, players[id]['lvl']):
        if characterClassDB[playerRace].get(str(lvl)):
            profList = characterClassDB[playerRace][str(lvl)]
            for p in profList:
                competence = competence + \
                    _weaponProficiencyItem(p, id, players, weaponType)

    if competence > 4:
        competence = 4

    return competence


def _thievesCantCountChars(txt: str) -> int:
    result = 0
    for char in txt.lower():
        if char == 'a' or \
           char == 'e' or \
           char == 'i' or \
           char == 'o' or \
           char == 'u':
            result += 1
    return result


def thievesCant(spokenText: str) -> str:
    cantCode = (
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
    index = (_thievesCantCountChars(spokenText) +
             len(spokenText.split(' '))) % len(cantCode)
    return cantCode[index]
