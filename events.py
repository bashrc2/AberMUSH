__filename__ = "events.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"
__module_group__ = "Core"

from functions import str2bool
from functions import getFreeKey
from functions import sizeFromDescription

import time


def _setPlayerCanGo(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    if etarget in players:
        players[etarget]['canGo'] = int(ebody)


def _setPlayerCanLook(etarget, ebody, players, npcs, items,
                      env, npcsDB, envDB):
    if etarget in players:
        players[etarget]['canLook'] = int(ebody)


def _setPlayerCanSay(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    if etarget in players:
        players[etarget]['canSay'] = int(ebody)


def _setPlayerCanAttack(etarget, ebody, players, npcs, items, env,
                        npcsDB, envDB):
    if etarget in players:
        players[etarget]['canAttack'] = int(ebody)


def _setPlayerCanDirectMessage(etarget, ebody, players, npcs, items,
                               env, npcsDB, envDB):
    if etarget in players:
        players[etarget]['canDirectMessage'] = int(ebody)


def _setPlayerPrefix(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    if etarget in players:
        players[etarget]['prefix'] = str(ebody)


def _setPlayerName(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['name'] = str(ebody)


def _setPlayerRoom(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['room'] = str(ebody)


def _setPlayerLvl(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['lvl'] = int(ebody)


def _modPlayerLvl(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['lvl'] += int(ebody)


def _setPlayerExp(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['exp'] = int(ebody)


def _modPlayerExp(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['exp'] += int(ebody)


def _setPlayerStr(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['str'] = int(ebody)


def _modPlayerStr(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['str'] += int(ebody)


def _setPlayerSiz(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['siz'] = int(ebody)


def _modPlayerSiz(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['siz'] += int(ebody)


def _setPlayerWei(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['wei'] = int(ebody)


def _modPlayerWei(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['wei'] += int(ebody)


def _setPlayerPer(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['per'] = int(ebody)


def _modPlayerPer(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['per'] += int(ebody)


def _setPlayerCool(etarget, ebody, players, npcs, items,
                   env, npcsDB, envDB):
    players[etarget]['cool'] = int(ebody)


def _modPlayerCool(etarget, ebody, players, npcs, items,
                   env, npcsDB, envDB):
    players[etarget]['cool'] += int(ebody)


def _setPlayerEndu(etarget, ebody, players, npcs, items,
                   env, npcsDB, envDB):
    players[etarget]['endu'] = int(ebody)


def _modPlayerEndu(etarget, ebody, players, npcs, items,
                   env, npcsDB, envDB):
    players[etarget]['endu'] += int(ebody)


def _setPlayerCha(etarget, ebody, players, npcs, items,
                  env, npcsDB, envDB):
    players[etarget]['cha'] = int(ebody)


def _modPlayerCha(etarget, ebody, players, npcs, items,
                  env, npcsDB, envDB):
    players[etarget]['cha'] += int(ebody)


def _setPlayerInt(etarget, ebody, players, npcs, items,
                  env, npcsDB, envDB):
    players[etarget]['inte'] = int(ebody)


def _modPlayerInt(etarget, ebody, players, npcs, items,
                  env, npcsDB, envDB):
    players[etarget]['inte'] += int(ebody)


def _setPlayerAgi(etarget, ebody, players, npcs, items,
                  env, npcsDB, envDB):
    players[etarget]['agi'] = int(ebody)


def _modPlayerAgi(etarget, ebody, players, npcs, items,
                  env, npcsDB, envDB):
    players[etarget]['agi'] += int(ebody)


def _setPlayerLuc(etarget, ebody, players, npcs, items,
                  env, npcsDB, envDB):
    players[etarget]['luc'] = int(ebody)


def _modPlayerLuc(etarget, ebody, players, npcs, items,
                  env, npcsDB, envDB):
    players[etarget]['luc'] += int(ebody)


def _setPlayerCred(etarget, ebody, players, npcs, items,
                   env, npcsDB, envDB):
    players[etarget]['cred'] = int(ebody)


def _modPlayerCred(etarget, ebody, players, npcs, items,
                   env, npcsDB, envDB):
    players[etarget]['cred'] += int(ebody)


def _setPlayerGoldPieces(etarget, ebody, players, npcs, items,
                         env, npcsDB, envDB):
    players[etarget]['gp'] = int(ebody)


def _modPlayerGoldPieces(etarget, ebody, players, npcs, items,
                         env, npcsDB, envDB):
    players[etarget]['gp'] += int(ebody)


def _setPlayerSilverPieces(etarget, ebody, players, npcs, items,
                           env, npcsDB, envDB):
    players[etarget]['sp'] = int(ebody)


def _modPlayerSilverPieces(etarget, ebody, players, npcs, items,
                           env, npcsDB, envDB):
    players[etarget]['sp'] += int(ebody)


def _setPlayerCopperPieces(etarget, ebody, players, npcs, items,
                           env, npcsDB, envDB):
    players[etarget]['cp'] = int(ebody)


def _modPlayerCopperPieces(etarget, ebody, players, npcs, items,
                           env, npcsDB, envDB):
    players[etarget]['cp'] += int(ebody)


def _setPlayerElectrumPieces(etarget, ebody, players, npcs, items,
                             env, npcsDB, envDB):
    players[etarget]['ep'] = int(ebody)


def _modPlayerElectrumPieces(etarget, ebody, players, npcs, items,
                             env, npcsDB, envDB):
    players[etarget]['ep'] += int(ebody)


def _setPlayerPlatinumPieces(etarget, ebody, players, npcs, items,
                             env, npcsDB, envDB):
    players[etarget]['pp'] = int(ebody)


def _modPlayerPlatinumPieces(etarget, ebody, players, npcs, items,
                             env, npcsDB, envDB):
    players[etarget]['pp'] += int(ebody)


def _setPlayerInv(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['inv'] = str(ebody)


def _setAuthenticated(etarget, ebody, players, npcs, items,
                      env, npcsDB, envDB):
    players[etarget]['authenticated'] = str2bool(ebody)


def _setPlayerClo_head(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerClo_neck(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerClo_lwrist(etarget, ebody, players, npcs,
                         items, env, npcsDB, envDB):
    return


def _setPlayerClo_rwrist(etarget, ebody, players, npcs,
                         items, env, npcsDB, envDB):
    return


def _setPlayerClo_larm(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerClo_rarm(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerClo_lhand(etarget, ebody, players, npcs,
                        items, env, npcsDB, envDB):
    return


def _setPlayerClo_rhand(etarget, ebody, players, npcs,
                        items, env, npcsDB, envDB):
    return


def _setPlayerClo_lfinger(etarget, ebody, players, npcs,
                          items, env, npcsDB, envDB):
    return


def _setPlayerClo_gloves(etarget, ebody, players, npcs,
                         items, env, npcsDB, envDB):
    return


def _setPlayerClo_rfinger(etarget, ebody, players, npcs,
                          items, env, npcsDB, envDB):
    return


def _setPlayerClo_chest(etarget, ebody, players, npcs,
                        items, env, npcsDB, envDB):
    return


def _setPlayerClo_lleg(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerClo_rleg(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerClo_feet(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerImp_head(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerImp_larm(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerImp_rarm(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerImp_lhand(etarget, ebody, players, npcs,
                        items, env, npcsDB, envDB):
    return


def _setPlayerImp_rhand(etarget, ebody, players, npcs,
                        items, env, npcsDB, envDB):
    return


def _setPlayerImp_chest(etarget, ebody, players, npcs,
                        items, env, npcsDB, envDB):
    return


def _setPlayerImp_lleg(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerImp_rleg(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerImp_feet(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    return


def _setPlayerHp(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['hp'] = int(ebody)


def _modPlayerHp(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['hp'] += int(ebody)


def _setPlayerCharge(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['charge'] = int(ebody)


def _modPlayerCharge(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    players[etarget]['charge'] += int(ebody)


def _setPlayerIsInCombat(etarget, ebody, players, npcs,
                         items, env, npcsDB, envDB):
    players[etarget]['isInCombat'] += int(ebody)


def _setPlayerLastCombatAction(etarget, ebody, players, npcs, items,
                               env, npcsDB, envDB):
    players[etarget]['lastCombatAction'] = int(ebody)


def _modPlayerLastCombatAction(etarget, ebody, players, npcs,
                               items, env, npcsDB, envDB):
    players[etarget]['lastCombatAction'] += int(ebody)


def _setPlayerIsAttackable(etarget, ebody, players, npcs,
                           items, env, npcsDB, envDB):
    players[etarget]['isAttackable'] = int(ebody)


def _setPlayerLastRoom(etarget, ebody, players, npcs,
                       items, env, npcsDB, envDB):
    players[etarget]['lastRoom'] = str(ebody)


def _setPlayerCorpseTTL(etarget, ebody, players, npcs,
                        items, env, npcsDB, envDB):
    players[etarget]['corpseTTL'] = int(ebody)


def _modPlayerCorpseTTL(etarget, ebody, players, npcs,
                        items, env, npcsDB, envDB):
    players[etarget]['corpseTTL'] += int(ebody)


def _itemInRoom(items, id, room):
    for i in items.items():
        if i[1]['room'] == room:
            if id == i[1]['id']:
                return True
    return False


def _spawnItem(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    body = ebody.split(';')
    bodyInt = int(body[0])
    if not _itemInRoom(items, bodyInt, body[1]):
        items[getFreeKey(items, 200000)] = {
            'id': bodyInt,
            'room': body[1],
            'whenDropped': int(time.time()),
            'lifespan': int(body[2]),
            'owner': int(body[3])
        }


def _spawnNPC(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    body = ebody.split(';')

    # if the size is unknown then estimate it
    if npcsDB[int(body[0])]['siz'] == 0:
        npcsDB[int(body[0])]['siz'] = sizeFromDescription(
            npcsDB[int(body[0])]['name'] + ' ' +
            npcsDB[int(body[0])]['lookDescription'])

    npcs[getFreeKey(npcs, 90000)] = {
        'name': npcsDB[int(body[0])]['name'],
        'room': body[1],
        'lvl': npcsDB[int(body[0])]['lvl'],
        'exp': npcsDB[int(body[0])]['exp'],
        'str': npcsDB[int(body[0])]['str'],
        'siz': npcsDB[int(body[0])]['siz'],
        'wei': npcsDB[int(body[0])]['wei'],
        'per': npcsDB[int(body[0])]['per'],
        'endu': npcsDB[int(body[0])]['endu'],
        'cha': npcsDB[int(body[0])]['cha'],
        'int': npcsDB[int(body[0])]['int'],
        'agi': npcsDB[int(body[0])]['agi'],
        'follow': npcsDB[int(body[0])]['follow'],
        'bodyType': npcsDB[int(body[0])]['bodyType'],
        'canWear': npcsDB[int(body[0])]['canWear'],
        'visibleWhenWearing': npcsDB[int(body[0])]['visibleWhenWearing'],
        'canWield': npcsDB[int(body[0])]['canWield'],
        'luc': npcsDB[int(body[0])]['luc'],
        'cool': npcsDB[int(body[0])]['cool'],
        'ref': npcsDB[int(body[0])]['ref'],
        'cred': npcsDB[int(body[0])]['cred'],
        'pp': npcsDB[int(body[0])]['pp'],
        'ep': npcsDB[int(body[0])]['ep'],
        'cp': npcsDB[int(body[0])]['cp'],
        'sp': npcsDB[int(body[0])]['sp'],
        'gp': npcsDB[int(body[0])]['gp'],
        'inv': npcsDB[int(body[0])]['inv'],
        'speakLanguage': npcsDB[int(body[0])]['speakLanguage'],
        'language': npcsDB[int(body[0])]['language'],
        'conv': npcsDB[int(body[0])]['conv'],
        'path': npcsDB[int(body[0])]['path'],
        'moveDelay': npcsDB[int(body[0])]['moveDelay'],
        'moveType': npcsDB[int(body[0])]['moveType'],
        'moveTimes': npcsDB[int(body[0])]['moveTimes'],
        'isAttackable': int(body[2]),
        'isStealable': int(body[3]),
        'isKillable': int(body[4]),
        'isAggressive': int(body[5]),
        'clo_head': npcsDB[int(body[0])]['clo_head'],
        'clo_neck': npcsDB[int(body[0])]['clo_neck'],
        'clo_lwrist': npcsDB[int(body[0])]['clo_lwrist'],
        'clo_rwrist': npcsDB[int(body[0])]['clo_rwrist'],
        'clo_larm': npcsDB[int(body[0])]['clo_larm'],
        'clo_rarm': npcsDB[int(body[0])]['clo_rarm'],
        'clo_lhand': npcsDB[int(body[0])]['clo_lhand'],
        'clo_rhand': npcsDB[int(body[0])]['clo_rhand'],
        'clo_gloves': npcsDB[int(body[0])]['clo_gloves'],
        'clo_lfinger': npcsDB[int(body[0])]['clo_lfinger'],
        'clo_rfinger': npcsDB[int(body[0])]['clo_rfinger'],
        'clo_waist': npcsDB[int(body[0])]['clo_waist'],
        'clo_lear': npcsDB[int(body[0])]['clo_lear'],
        'clo_rear': npcsDB[int(body[0])]['clo_rear'],
        'clo_chest': npcsDB[int(body[0])]['clo_chest'],
        'clo_back': npcsDB[int(body[0])]['clo_back'],
        'clo_lleg': npcsDB[int(body[0])]['clo_lleg'],
        'clo_rleg': npcsDB[int(body[0])]['clo_rleg'],
        'clo_feet': npcsDB[int(body[0])]['clo_feet'],
        'imp_head': npcsDB[int(body[0])]['imp_head'],
        'imp_neck': npcsDB[int(body[0])]['imp_neck'],
        'imp_larm': npcsDB[int(body[0])]['imp_larm'],
        'imp_rarm': npcsDB[int(body[0])]['imp_rarm'],
        'imp_lhand': npcsDB[int(body[0])]['imp_lhand'],
        'imp_gloves': npcsDB[int(body[0])]['imp_gloves'],
        'imp_lfinger': npcsDB[int(body[0])]['imp_lfinger'],
        'imp_rhand': npcsDB[int(body[0])]['imp_rhand'],
        'imp_rfinger': npcsDB[int(body[0])]['imp_rfinger'],
        'imp_waist': npcsDB[int(body[0])]['imp_waist'],
        'imp_lear': npcsDB[int(body[0])]['imp_lear'],
        'imp_rear': npcsDB[int(body[0])]['imp_rear'],
        'imp_chest': npcsDB[int(body[0])]['imp_chest'],
        'imp_back': npcsDB[int(body[0])]['imp_back'],
        'imp_lleg': npcsDB[int(body[0])]['imp_lleg'],
        'imp_rleg': npcsDB[int(body[0])]['imp_rleg'],
        'imp_feet': npcsDB[int(body[0])]['imp_feet'],
        'hp': npcsDB[int(body[0])]['hp'],
        'hpMax': npcsDB[int(body[0])]['hpMax'],
        'charge': npcsDB[int(body[0])]['charge'],
        'corpseTTL': int(body[6]),
        'respawn': int(body[7]),
        'vocabulary': npcsDB[int(body[0])]['vocabulary'],
        'talkDelay': npcsDB[int(body[0])]['talkDelay'],
        'inDescription': npcsDB[int(body[0])]['inDescription'],
        'outDescription': npcsDB[int(body[0])]['outDescription'],
        'lookDescription': npcsDB[int(body[0])]['lookDescription'],
        'timeTalked': 0,
        'isInCombat': 0,
        'lastCombatAction': 0,
        'lastRoom': None,
        'whenDied': None,
        'randomizer': 0,
        'randomFactor': npcsDB[int(body[0])]['randomFactor'],
        'lastSaid': 0,
        'lastMoved': 0,
        'race': npcsDB[int(body[0])]['race'],
        'characterClass': npcsDB[int(body[0])]['characterClass'],
        'proficiencies': npcsDB[int(body[0])]['proficiencies'],
        'fightingStyle': npcsDB[int(body[0])]['fightingStyle'],
        'restRequired': npcsDB[int(body[0])]['restRequired'],
        'enemy': npcsDB[int(body[0])]['enemy'],
        'tempCharm': npcsDB[int(body[0])]['tempCharm'],
        'tempCharmTarget': npcsDB[int(body[0])]['tempCharmTarget'],
        'tempCharmDuration': npcsDB[int(body[0])]['tempCharmDuration'],
        'tempCharmStart': npcsDB[int(body[0])]['tempCharmStart'],
        'guild': npcsDB[int(body[0])]['guild'],
        'guildRole': npcsDB[int(body[0])]['guildRole'],
        'archetype': npcsDB[int(body[0])]['archetype'],
        'preparedSpells': npcsDB[int(body[0])]['preparedSpells'],
        'spellSlots': npcsDB[int(body[0])]['spellSlots'],
        'tempHitPoints': npcsDB[int(body[0])]['tempHitPoints'],
        'tempHitPointsStart': npcsDB[int(body[0])]['tempHitPointsStart'],
        'tempHitPointsDuration': npcsDB[int(body[0])]['tempHitPointsDuration'],
        'frozenDuration': npcsDB[int(body[0])]['frozenDuration'],
        'frozenStart': npcsDB[int(body[0])]['frozenStart'],
        'frozenDescription': npcsDB[int(body[0])]['frozenDescription'],
        'affinity': npcsDB[int(body[0])]['affinity'],
        'familiar': npcsDB[int(body[0])]['familiar'],
        'familiarOf': npcsDB[int(body[0])]['familiarOf'],
        'familiarTarget': npcsDB[int(body[0])]['familiarTarget'],
        'familiarType': npcsDB[int(body[0])]['familiarType'],
        'familiarMode': npcsDB[int(body[0])]['familiarMode'],
        'animalType': npcsDB[int(body[0])]['animalType']
    }


def _actorInRoom(env, name, room):
    for e in env.items():
        if room == e[1]['room']:
            if name in e[1]['name']:
                return True
    return False


def _spawnActor(etarget, ebody, players, npcs, items, env, npcsDB, envDB):
    body = ebody.split(';')
    bodyInt = int(body[0])
    if not _actorInRoom(env, envDB[bodyInt]['name'], body[1]):
        env[bodyInt] = {
            'name': envDB[bodyInt]['name'],
            'vocabulary': envDB[bodyInt]['vocabulary'],
            'talkDelay': envDB[bodyInt]['talkDelay'],
            'randomFactor': envDB[bodyInt]['randomFactor'],
            'room': body[1],
            'randomizer': envDB[bodyInt]['randomizer'],
            'timeTalked': envDB[bodyInt]['timeTalked'],
            'lastSaid': envDB[bodyInt]['lastSaid']
        }

# Function for evaluating an Event


def evaluateEvent(
        etarget,
        etype,
        ebody,
        players,
        npcs,
        items,
        env,
        npcsDB,
        envDB):
    switcher = {
        "setPlayerCanGo": _setPlayerCanGo,
        "setPlayerCanLook": _setPlayerCanLook,
        "setPlayerCanSay": _setPlayerCanSay,
        "setPlayerCanAttack": _setPlayerCanAttack,
        "setPlayerCanDirectMessage": _setPlayerCanDirectMessage,
        "setPlayerName": _setPlayerName,
        "setPlayerPrefix": _setPlayerPrefix,
        "setPlayerRoom": _setPlayerRoom,
        "setPlayerLvl": _setPlayerLvl,
        "modPlayerLvl": _modPlayerLvl,
        "setPlayerExp": _setPlayerExp,
        "modPlayerExp": _modPlayerExp,
        "setPlayerStr": _setPlayerStr,
        "modPlayerStr": _modPlayerStr,
        "setPlayerSiz": _setPlayerSiz,
        "modPlayerSiz": _modPlayerSiz,
        "setPlayerWei": _setPlayerWei,
        "modPlayerWei": _modPlayerWei,
        "setPlayerPer": _setPlayerPer,
        "modPlayerPer": _modPlayerPer,
        "setPlayerCool": _setPlayerCool,
        "modPlayerCool": _modPlayerCool,
        "setPlayerEndu": _setPlayerEndu,
        "modPlayerEndu": _modPlayerEndu,
        "setPlayerCha": _setPlayerCha,
        "modPlayerCha": _modPlayerCha,
        "setPlayerInt": _setPlayerInt,
        "modPlayerInt": _modPlayerInt,
        "setPlayerAgi": _setPlayerAgi,
        "modPlayerAgi": _modPlayerAgi,
        "setPlayerLuc": _setPlayerLuc,
        "modPlayerLuc": _modPlayerLuc,
        "setPlayerCred": _setPlayerCred,
        "modPlayerCred": _modPlayerCred,
        "setPlayerGoldPieces": _setPlayerGoldPieces,
        "modPlayerGoldPieces": _modPlayerGoldPieces,
        "setPlayerSilverPieces": _setPlayerSilverPieces,
        "modPlayerSilverPieces": _modPlayerSilverPieces,
        "setPlayerCopperPieces": _setPlayerCopperPieces,
        "modPlayerCopperPieces": _modPlayerCopperPieces,
        "setPlayerElectrumPieces": _setPlayerElectrumPieces,
        "modPlayerElectrumPieces": _modPlayerElectrumPieces,
        "setPlayerPlatinumPieces": _setPlayerPlatinumPieces,
        "modPlayerPlatinumPieces": _modPlayerPlatinumPieces,
        "setPlayerInv": _setPlayerInv,
        "setAuthenticated": _setAuthenticated,
        "setPlayerClo_head": _setPlayerClo_head,
        "setPlayerClo_neck": _setPlayerClo_neck,
        "setPlayerClo_larm": _setPlayerClo_larm,
        "setPlayerClo_rarm": _setPlayerClo_rarm,
        "setPlayerClo_lhand": _setPlayerClo_lhand,
        "setPlayerClo_rhand": _setPlayerClo_rhand,
        "setPlayerClo_gloves": _setPlayerClo_gloves,
        "setPlayerClo_lfinger": _setPlayerClo_lfinger,
        "setPlayerClo_rfinger": _setPlayerClo_rfinger,
        "setPlayerClo_lwrist": _setPlayerClo_lwrist,
        "setPlayerClo_rwrist": _setPlayerClo_rwrist,
        "setPlayerClo_chest": _setPlayerClo_chest,
        "setPlayerClo_lleg": _setPlayerClo_lleg,
        "setPlayerClo_rleg": _setPlayerClo_rleg,
        "setPlayerClo_feet": _setPlayerClo_feet,
        "setPlayerImp_head": _setPlayerImp_head,
        "setPlayerImp_larm": _setPlayerImp_larm,
        "setPlayerImp_rarm": _setPlayerImp_rarm,
        "setPlayerImp_lhand": _setPlayerImp_lhand,
        "setPlayerImp_rhand": _setPlayerImp_rhand,
        "setPlayerImp_chest": _setPlayerImp_chest,
        "setPlayerImp_lleg": _setPlayerImp_lleg,
        "setPlayerImp_rleg": _setPlayerImp_rleg,
        "setPlayerImp_feet": _setPlayerImp_feet,
        "setPlayerHp": _setPlayerHp,
        "modPlayerHp": _modPlayerHp,
        "setPlayerCharge": _setPlayerCharge,
        "modPlayerCharge": _modPlayerCharge,
        "setPlayerIsInCombat": _setPlayerIsInCombat,
        "setPlayerLastCombatAction": _setPlayerLastCombatAction,
        "modPlayerLastCombatAction": _modPlayerLastCombatAction,
        "setPlayerIsAttackable": _setPlayerIsAttackable,
        "setPlayerLastRoom": _setPlayerLastRoom,
        "setPlayerCorpseTTL": _setPlayerCorpseTTL,
        "modPlayerCorpseTTL": _modPlayerCorpseTTL,
        "spawnItem": _spawnItem,
        "spawnNPC": _spawnNPC,
        "spawnActor": _spawnActor,
    }
    switcher[etype](etarget, ebody, players, npcs, items, env, npcsDB, envDB)
