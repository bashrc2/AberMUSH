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

def proficiencyName(prof):
    if '(' not in prof:
        return prof

    return prof.split('(')[0].strip()

def proficiencyParam(prof):
    if '(' not in prof:
        return 0

    return int(prof.split('(')[1].replace(')','').strip())

def profFightingStyleDamage(id,players,weaponType,value):
    if not players[id].get('fightingStyle'):
        return 0
    fightStyle=players[id]['fightingStyle'].lower()
    if fightStyle=='archery':
        if 'bow' in weaponType:
            return 2
    if fightStyle.startswith('duel'):
        if 'ranged' not in weaponType:
            if 'fist' not in weaponType:
                if players[id]['clo_lhand']==0 or players[id]['clo_rhand']==0:
                    return 2

def damageProficiencyItem(prof, id, players, weaponType):
    if prof is list:
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

    try:
        return switcher[profName](id,players,weaponType,profValue)
    except Exception as e:
        print("damageProficiencyItem error " + prof)

    return 0    

def damageProficiency(id, players, weaponType, characterClassDB):
    if not players[id].get('race'):
        return 0

    playerRace=players[id]['race']
    
    if not characterClassDB.get(playerRace):
        return 0

    damage=0
    for lvl in range(1,players[id]['lvl']):
        if characterClassDB[playerRace].get(str(lvl)):
            profList=characterClassDB[playerRace][str(lvl)]
            for p in profList:
                damage = damage + \
                    damageProficiencyItem(p, id, players, weaponType)
    return damage

def defenseProficiencyItem(prof, id, players):
    if prof is list:
        return 0

    profName = proficiencyName(prof)
    profValue = proficiencyParam(prof)

    switcher = {
        "Second Wind": profSecondWind,
        "Action Surge": profActionSurge,
        "Indomitable": profIndomitable,
        "Arcane Recovery": profArcaneRecovery
    }

    try:
        return switcher[profName](id,players,profValue)
    except Exception as e:
        print("defenseProficiencyItem error " + prof)

    return 0    

def defenseProficiency(id, players, characterClassDB):
    if not players[id].get('race'):
        return 0

    playerRace=players[id]['race']
    
    if not characterClassDB.get(playerRace):
        return 0

    defense=0
    for lvl in range(1,players[id]['lvl']):
        if characterClassDB[playerRace].get(str(lvl)):
            profList=characterClassDB[playerRace][str(lvl)]
            for p in profList:
                defense = defense + \
                    defenseProficiencyItem(p, id, players)
    return damage

    
