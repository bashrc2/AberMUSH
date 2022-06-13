__filename__ = "events.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Core"

from functions import str2bool
from functions import get_free_key
from functions import size_from_description
from functions import item_in_room

import time


def _setPlayerCulture(etarget, ebody, players, npcs, items,
                      env, npcs_db, env_db):
    if etarget in players:
        players[etarget]['culture'] = str(ebody)


def _setPlayerCanGo(etarget, ebody, players, npcs, items,
                    env, npcs_db, env_db):
    if etarget in players:
        players[etarget]['canGo'] = int(ebody)


def _setPlayerCanLook(etarget, ebody, players, npcs, items,
                      env, npcs_db, env_db):
    if etarget in players:
        players[etarget]['canLook'] = int(ebody)


def _setPlayerCanSay(etarget, ebody, players, npcs, items,
                     env, npcs_db, env_db):
    if etarget in players:
        players[etarget]['canSay'] = int(ebody)


def _setPlayerCanAttack(etarget, ebody, players, npcs, items, env,
                        npcs_db, env_db):
    if etarget in players:
        players[etarget]['canAttack'] = int(ebody)


def _setPlayerCanDirectMessage(etarget, ebody, players, npcs, items,
                               env, npcs_db, env_db):
    if etarget in players:
        players[etarget]['canDirectMessage'] = int(ebody)


def _setPlayerPrefix(etarget, ebody, players, npcs, items,
                     env, npcs_db, env_db):
    if etarget in players:
        players[etarget]['prefix'] = str(ebody)


def _setPlayerName(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['name'] = str(ebody)


def _setPlayerRoom(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['room'] = str(ebody)


def _setPlayerLvl(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['lvl'] = int(ebody)


def _modPlayerLvl(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['lvl'] += int(ebody)


def _setPlayerExp(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['exp'] = int(ebody)


def _modPlayerExp(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['exp'] += int(ebody)


def _setPlayerStr(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['str'] = int(ebody)


def _modPlayerStr(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['str'] += int(ebody)


def _setPlayerSiz(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['siz'] = int(ebody)


def _modPlayerSiz(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['siz'] += int(ebody)


def _setPlayerWei(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['wei'] = int(ebody)


def _modPlayerWei(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['wei'] += int(ebody)


def _setPlayerPer(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['per'] = int(ebody)


def _modPlayerPer(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['per'] += int(ebody)


def _setPlayerCool(etarget, ebody, players, npcs, items,
                   env, npcs_db, env_db):
    players[etarget]['cool'] = int(ebody)


def _modPlayerCool(etarget, ebody, players, npcs, items,
                   env, npcs_db, env_db):
    players[etarget]['cool'] += int(ebody)


def _setPlayerEndu(etarget, ebody, players, npcs, items,
                   env, npcs_db, env_db):
    players[etarget]['endu'] = int(ebody)


def _modPlayerEndu(etarget, ebody, players, npcs, items,
                   env, npcs_db, env_db):
    players[etarget]['endu'] += int(ebody)


def _setPlayerCha(etarget, ebody, players, npcs, items,
                  env, npcs_db, env_db):
    players[etarget]['cha'] = int(ebody)


def _modPlayerCha(etarget, ebody, players, npcs, items,
                  env, npcs_db, env_db):
    players[etarget]['cha'] += int(ebody)


def _setPlayerInt(etarget, ebody, players, npcs, items,
                  env, npcs_db, env_db):
    players[etarget]['inte'] = int(ebody)


def _modPlayerInt(etarget, ebody, players, npcs, items,
                  env, npcs_db, env_db):
    players[etarget]['inte'] += int(ebody)


def _setPlayerAgi(etarget, ebody, players, npcs, items,
                  env, npcs_db, env_db):
    players[etarget]['agi'] = int(ebody)


def _modPlayerAgi(etarget, ebody, players, npcs, items,
                  env, npcs_db, env_db):
    players[etarget]['agi'] += int(ebody)


def _setPlayerLuc(etarget, ebody, players, npcs, items,
                  env, npcs_db, env_db):
    players[etarget]['luc'] = int(ebody)


def _modPlayerLuc(etarget, ebody, players, npcs, items,
                  env, npcs_db, env_db):
    players[etarget]['luc'] += int(ebody)


def _setPlayerCred(etarget, ebody, players, npcs, items,
                   env, npcs_db, env_db):
    players[etarget]['cred'] = int(ebody)


def _modPlayerCred(etarget, ebody, players, npcs, items,
                   env, npcs_db, env_db):
    players[etarget]['cred'] += int(ebody)


def _setPlayerGoldPieces(etarget, ebody, players, npcs, items,
                         env, npcs_db, env_db):
    players[etarget]['gp'] = int(ebody)


def _modPlayerGoldPieces(etarget, ebody, players, npcs, items,
                         env, npcs_db, env_db):
    players[etarget]['gp'] += int(ebody)


def _setPlayerSilverPieces(etarget, ebody, players, npcs, items,
                           env, npcs_db, env_db):
    players[etarget]['sp'] = int(ebody)


def _modPlayerSilverPieces(etarget, ebody, players, npcs, items,
                           env, npcs_db, env_db):
    players[etarget]['sp'] += int(ebody)


def _setPlayerCopperPieces(etarget, ebody, players, npcs, items,
                           env, npcs_db, env_db):
    players[etarget]['cp'] = int(ebody)


def _modPlayerCopperPieces(etarget, ebody, players, npcs, items,
                           env, npcs_db, env_db):
    players[etarget]['cp'] += int(ebody)


def _setPlayerElectrumPieces(etarget, ebody, players, npcs, items,
                             env, npcs_db, env_db):
    players[etarget]['ep'] = int(ebody)


def _modPlayerElectrumPieces(etarget, ebody, players, npcs, items,
                             env, npcs_db, env_db):
    players[etarget]['ep'] += int(ebody)


def _setPlayerPlatinumPieces(etarget, ebody, players, npcs, items,
                             env, npcs_db, env_db):
    players[etarget]['pp'] = int(ebody)


def _modPlayerPlatinumPieces(etarget, ebody, players, npcs, items,
                             env, npcs_db, env_db):
    players[etarget]['pp'] += int(ebody)


def _setPlayerInv(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['inv'] = str(ebody)


def _setAuthenticated(etarget, ebody, players, npcs, items,
                      env, npcs_db, env_db):
    players[etarget]['authenticated'] = str2bool(ebody)


def _setPlayerClo_head(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerClo_neck(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerClo_lwrist(etarget, ebody, players, npcs,
                         items, env, npcs_db, env_db):
    return


def _setPlayerClo_rwrist(etarget, ebody, players, npcs,
                         items, env, npcs_db, env_db):
    return


def _setPlayerClo_larm(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerClo_rarm(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerClo_lhand(etarget, ebody, players, npcs,
                        items, env, npcs_db, env_db):
    return


def _setPlayerClo_rhand(etarget, ebody, players, npcs,
                        items, env, npcs_db, env_db):
    return


def _setPlayerClo_lfinger(etarget, ebody, players, npcs,
                          items, env, npcs_db, env_db):
    return


def _setPlayerClo_gloves(etarget, ebody, players, npcs,
                         items, env, npcs_db, env_db):
    return


def _setPlayerClo_rfinger(etarget, ebody, players, npcs,
                          items, env, npcs_db, env_db):
    return


def _setPlayerClo_chest(etarget, ebody, players, npcs,
                        items, env, npcs_db, env_db):
    return


def _setPlayerClo_lleg(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerClo_rleg(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerClo_feet(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerImp_head(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerImp_larm(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerImp_rarm(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerImp_lhand(etarget, ebody, players, npcs,
                        items, env, npcs_db, env_db):
    return


def _setPlayerImp_rhand(etarget, ebody, players, npcs,
                        items, env, npcs_db, env_db):
    return


def _setPlayerImp_chest(etarget, ebody, players, npcs,
                        items, env, npcs_db, env_db):
    return


def _setPlayerImp_lleg(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerImp_rleg(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerImp_feet(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    return


def _setPlayerHp(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['hp'] = int(ebody)


def _modPlayerHp(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    players[etarget]['hp'] += int(ebody)


def _setPlayerCharge(etarget, ebody, players, npcs, items,
                     env, npcs_db, env_db):
    players[etarget]['charge'] = int(ebody)


def _modPlayerCharge(etarget, ebody, players, npcs, items,
                     env, npcs_db, env_db):
    players[etarget]['charge'] += int(ebody)


def _setPlayerIsInCombat(etarget, ebody, players, npcs,
                         items, env, npcs_db, env_db):
    players[etarget]['isInCombat'] += int(ebody)


def _setPlayerLastCombatAction(etarget, ebody, players, npcs, items,
                               env, npcs_db, env_db):
    players[etarget]['lastCombatAction'] = int(ebody)


def _modPlayerLastCombatAction(etarget, ebody, players, npcs,
                               items, env, npcs_db, env_db):
    players[etarget]['lastCombatAction'] += int(ebody)


def _setPlayerIsAttackable(etarget, ebody, players, npcs,
                           items, env, npcs_db, env_db):
    players[etarget]['isAttackable'] = int(ebody)


def _setPlayerLastRoom(etarget, ebody, players, npcs,
                       items, env, npcs_db, env_db):
    players[etarget]['lastRoom'] = str(ebody)


def _setPlayerCorpseTTL(etarget, ebody, players, npcs,
                        items, env, npcs_db, env_db):
    players[etarget]['corpseTTL'] = int(ebody)


def _modPlayerCorpseTTL(etarget, ebody, players, npcs,
                        items, env, npcs_db, env_db):
    players[etarget]['corpseTTL'] += int(ebody)


def _spawnItem(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    body = ebody.split(';')
    body_int = int(body[0])
    if not item_in_room(items, body_int, body[1]):
        items[get_free_key(items, 200000)] = {
            'id': body_int,
            'room': body[1],
            'whenDropped': int(time.time()),
            'lifespan': int(body[2]),
            'owner': int(body[3])
        }


def _spawnNPC(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    body = ebody.split(';')

    # if the size is unknown then estimate it
    if npcs_db[int(body[0])]['siz'] == 0:
        npcs_db[int(body[0])]['siz'] = size_from_description(
            npcs_db[int(body[0])]['name'] + ' ' +
            npcs_db[int(body[0])]['lookDescription'])

    npcs_body = npcs_db[int(body[0])]
    npcs[get_free_key(npcs, 90000)] = {
        'name': npcs_body['name'],
        'room': body[1],
        'lvl': npcs_body['lvl'],
        'exp': npcs_body['exp'],
        'str': npcs_body['str'],
        'siz': npcs_body['siz'],
        'wei': npcs_body['wei'],
        'per': npcs_body['per'],
        'endu': npcs_body['endu'],
        'cha': npcs_body['cha'],
        'int': npcs_body['int'],
        'agi': npcs_body['agi'],
        'follow': npcs_body['follow'],
        'bodyType': npcs_body['bodyType'],
        'canWear': npcs_body['canWear'],
        'visibleWhenWearing': npcs_body['visibleWhenWearing'],
        'canWield': npcs_body['canWield'],
        'luc': npcs_body['luc'],
        'cool': npcs_body['cool'],
        'ref': npcs_body['ref'],
        'cred': npcs_body['cred'],
        'pp': npcs_body['pp'],
        'ep': npcs_body['ep'],
        'cp': npcs_body['cp'],
        'sp': npcs_body['sp'],
        'gp': npcs_body['gp'],
        'inv': npcs_body['inv'],
        'speakLanguage': npcs_body['speakLanguage'],
        'language': npcs_body['language'],
        'culture': npcs_body['culture'],
        'conv': npcs_body['conv'],
        'path': npcs_body['path'],
        'moveDelay': npcs_body['moveDelay'],
        'moveType': npcs_body['moveType'],
        'moveTimes': npcs_body['moveTimes'],
        'isAttackable': int(body[2]),
        'isStealable': int(body[3]),
        'isKillable': int(body[4]),
        'isAggressive': int(body[5]),
        'clo_head': npcs_body['clo_head'],
        'clo_neck': npcs_body['clo_neck'],
        'clo_lwrist': npcs_body['clo_lwrist'],
        'clo_rwrist': npcs_body['clo_rwrist'],
        'clo_larm': npcs_body['clo_larm'],
        'clo_rarm': npcs_body['clo_rarm'],
        'clo_lhand': npcs_body['clo_lhand'],
        'clo_rhand': npcs_body['clo_rhand'],
        'clo_gloves': npcs_body['clo_gloves'],
        'clo_lfinger': npcs_body['clo_lfinger'],
        'clo_rfinger': npcs_body['clo_rfinger'],
        'clo_waist': npcs_body['clo_waist'],
        'clo_lear': npcs_body['clo_lear'],
        'clo_rear': npcs_body['clo_rear'],
        'clo_chest': npcs_body['clo_chest'],
        'clo_back': npcs_body['clo_back'],
        'clo_lleg': npcs_body['clo_lleg'],
        'clo_rleg': npcs_body['clo_rleg'],
        'clo_feet': npcs_body['clo_feet'],
        'imp_head': npcs_body['imp_head'],
        'imp_neck': npcs_body['imp_neck'],
        'imp_larm': npcs_body['imp_larm'],
        'imp_rarm': npcs_body['imp_rarm'],
        'imp_lhand': npcs_body['imp_lhand'],
        'imp_gloves': npcs_body['imp_gloves'],
        'imp_lfinger': npcs_body['imp_lfinger'],
        'imp_rhand': npcs_body['imp_rhand'],
        'imp_rfinger': npcs_body['imp_rfinger'],
        'imp_waist': npcs_body['imp_waist'],
        'imp_lear': npcs_body['imp_lear'],
        'imp_rear': npcs_body['imp_rear'],
        'imp_chest': npcs_body['imp_chest'],
        'imp_back': npcs_body['imp_back'],
        'imp_lleg': npcs_body['imp_lleg'],
        'imp_rleg': npcs_body['imp_rleg'],
        'imp_feet': npcs_body['imp_feet'],
        'hp': npcs_body['hp'],
        'hpMax': npcs_body['hpMax'],
        'charge': npcs_body['charge'],
        'corpseTTL': int(body[6]),
        'respawn': int(body[7]),
        'vocabulary': npcs_body['vocabulary'],
        'talkDelay': npcs_body['talkDelay'],
        'inDescription': npcs_body['inDescription'],
        'outDescription': npcs_body['outDescription'],
        'lookDescription': npcs_body['lookDescription'],
        'timeTalked': 0,
        'isInCombat': 0,
        'lastCombatAction': 0,
        'lastRoom': None,
        'whenDied': None,
        'randomizer': 0,
        'randomFactor': npcs_body['randomFactor'],
        'lastSaid': 0,
        'lastMoved': 0,
        'race': npcs_body['race'],
        'characterClass': npcs_body['characterClass'],
        'proficiencies': npcs_body['proficiencies'],
        'fightingStyle': npcs_body['fightingStyle'],
        'restRequired': npcs_body['restRequired'],
        'enemy': npcs_body['enemy'],
        'magicShield': npcs_body['magicShield'],
        'magicShieldStart': npcs_body['magicShieldStart'],
        'magicShieldDuration': npcs_body['magicShieldDuration'],
        'tempCharm': npcs_body['tempCharm'],
        'tempCharmTarget': npcs_body['tempCharmTarget'],
        'tempCharmDuration': npcs_body['tempCharmDuration'],
        'tempCharmStart': npcs_body['tempCharmStart'],
        'guild': npcs_body['guild'],
        'guildRole': npcs_body['guildRole'],
        'archetype': npcs_body['archetype'],
        'preparedSpells': npcs_body['preparedSpells'],
        'spellSlots': npcs_body['spellSlots'],
        'tempHitPoints': npcs_body['tempHitPoints'],
        'tempHitPointsStart': npcs_body['tempHitPointsStart'],
        'tempHitPointsDuration': npcs_body['tempHitPointsDuration'],
        'frozenDuration': npcs_body['frozenDuration'],
        'frozenStart': npcs_body['frozenStart'],
        'frozenDescription': npcs_body['frozenDescription'],
        'affinity': npcs_body['affinity'],
        'familiar': npcs_body['familiar'],
        'familiarOf': npcs_body['familiarOf'],
        'familiarTarget': npcs_body['familiarTarget'],
        'familiarType': npcs_body['familiarType'],
        'familiarMode': npcs_body['familiarMode'],
        'animalType': npcs_body['animalType']
    }


def _actor_in_room(env, name, room):
    for e_co in env.items():
        if room == e_co[1]['room']:
            if name in e_co[1]['name']:
                return True
    return False


def _spawnActor(etarget, ebody, players, npcs, items, env, npcs_db, env_db):
    body = ebody.split(';')
    body_int = int(body[0])
    if not _actor_in_room(env, env_db[body_int]['name'], body[1]):
        env[body_int] = {
            'name': env_db[body_int]['name'],
            'vocabulary': env_db[body_int]['vocabulary'],
            'talkDelay': env_db[body_int]['talkDelay'],
            'randomFactor': env_db[body_int]['randomFactor'],
            'room': body[1],
            'randomizer': env_db[body_int]['randomizer'],
            'timeTalked': env_db[body_int]['timeTalked'],
            'lastSaid': env_db[body_int]['lastSaid']
        }

# Function for evaluating an Event


def evaluate_event(
        etarget,
        etype,
        ebody,
        players,
        npcs,
        items,
        env,
        npcs_db,
        env_db):
    switcher = {
        "setPlayerCulture": _setPlayerCulture,
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
    switcher[etype](etarget, ebody, players, npcs, items, env, npcs_db, env_db)
