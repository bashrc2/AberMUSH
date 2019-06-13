__filename__ = "proficiencies.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

import types
from random import randint


def proficiencyName(prof):
    if '(' not in prof:
        return prof

    return prof.split('(')[0].strip()


def proficiencyParam(prof):
    if '(' not in prof:
        return 0

    return int(prof.split('(')[1].replace(')', '').strip())


def profFightingStyleDamage(id, players, weaponType, value):
    if not players[id].get('fightingStyle'):
        return 0
    fightStyle = players[id]['fightingStyle'].lower()
    if fightStyle == 'archery':
        if 'bow' in weaponType:
            return 2
    if fightStyle.startswith('duel'):
        if 'ranged' not in weaponType:
            if 'fist' not in weaponType:
                if players[id]['clo_lhand'] == 0 or players[id]['clo_rhand'] == 0:
                    return 2


def damageProficiencyItem(prof, id, players, weaponType):
    if isinstance(prof, list):
        return 0

    profName = proficiencyName(prof)
    profValue = proficiencyParam(prof)

    switcher = {
        "Fighting Style": profFightingStyleDamage,
        #        "Second Wind": profSecondWind,
        #        "Action Surge": profActionSurge,
        "Martial Archetype": profMartialArchetype,
        "Ability Score Improvement": profAbilityScore,
        "Extra Attack": profExtraAttack,
        "Martial Archetype feature": profMartialArchetypeFeature,
        #        "Indomitable": profIndomitable,
        "Spellcasting": profSpellcasting,
        #        "Arcane Recovery": profArcaneRecovery,
        "Cantrips": profCantrips,
        "Arcane Tradition": profArcaneTradition,
        "Arcane Tradition feature": profArcaneTraditionFeature,
        "Spell Mastery": profSpellMastery,
        "Signature Spell": profSignatureSpell
    }

    if not switcher.get(profName):
        return 0

    try:
        return switcher[profName](id, players, weaponType, profValue)
    except Exception as e:
        print("damageProficiencyItem error " + prof)

    return 0


def damageProficiency(id, players, weaponType, characterClassDB):
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
                    damageProficiencyItem(p, id, players, weaponType)
    return damage


def profSecondWind(id, players, profValue):
    if players[id]['restRequired'] != 0:
        return 0
    players[id]['restRequired'] = 1
    return randint(1, 10)


def profIndomitable(id, players, profValue):
    if players[id]['restRequired'] != 0:
        return 0
    players[id]['restRequired'] = 1
    return randint(1, 10)


def defenseProficiencyItem(prof, id, players):
    if isinstance(prof, list):
        return 0

    profName = proficiencyName(prof)
    profValue = proficiencyParam(prof)

    switcher = {
        "Second Wind": profSecondWind,
        "Indomitable": profIndomitable,
        "Arcane Recovery": profArcaneRecovery
    }

    if not switcher.get(profName):
        return 0

    try:
        return switcher[profName](id, players, profValue)
    except Exception as e:
        print("defenseProficiencyItem error " + prof)

    return 0


def defenseProficiency(id, players, characterClassDB):
    if not players[id].get('race'):
        return 0

    playerRace = players[id]['race']

    if not characterClassDB.get(playerRace):
        return 0

    defense = 0
    for lvl in range(1, players[id]['lvl']):
        if characterClassDB[playerRace].get(str(lvl)):
            profList = characterClassDB[playerRace][str(lvl)]
            for p in profList:
                defense = defense + \
                    defenseProficiencyItem(p, id, players)
    return damage


def weaponProficiencyItem(prof, id, players, weaponType):
    if isinstance(prof, list):
        return 0

    profName = proficiencyName(prof)
    profValue = proficiencyParam(prof)

    switcher = {
        # "Second Wind": profSecondWind
    }

    if not switcher.get(profName):
        return 0

    try:
        return switcher[profName](id, players, profValue)
    except Exception as e:
        print("defenseProficiencyItem error " + prof)

    return 0


def weaponProficiency(id, players, weaponType, characterClassDB):
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
                    weaponProficiencyItem(p, id, players, weaponType)

    if competence > 4:
        competence = 4

    return competence


def thievesCantCountChars(txt):
    result = 0
    for char in txt.lower():
        if char == 'a' or char == 'e' or char == 'i' or char == 'o' or char == 'u':
            result += 1
    return result


def thievesCant(spokenText):
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
        "Will I see you at the harvest festival (or any other hometown gathering) this year?",
        "Yes, I’ll be there",
        "No, I am otherwise engaged",
        "Give my regards to your Granny",
        "…and have your pets spayed")
    index = (thievesCantCountChars(spokenText) +
             len(spokenText.split(' '))) % len(cantCode)
    return cantCode[index]
