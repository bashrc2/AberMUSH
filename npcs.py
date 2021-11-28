__filename__ = "npcs.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "NPCs"

import os
import datetime
from suntime import Sun
from functions import addToScheduler
from functions import messageToPlayersInRoom
from functions import log
from functions import playerInventoryWeight
from functions import updatePlayerAttributes
from functions import increaseAffinityBetweenPlayers
from functions import decreaseAffinityBetweenPlayers
from functions import getSentiment
from functions import randomDescription
from functions import deepcopy
from random import randint
# from copy import deepcopy
from familiar import getFamiliarModes
from familiar import familiarDefaultMode
from familiar import familiarScout
from familiar import familiarHide
from familiar import familiarSight
from environment import getRainAtCoords
from environment import getRoomCulture

import time


def corpseExists(corpses: {}, room: str, name: str) -> bool:
    """Returns true if a corpse with the given name exists in the given room
    """
    corpsesCopy = deepcopy(corpses)
    for (c, pl) in corpsesCopy.items():
        if corpsesCopy[c]['room'] == room:
            if corpsesCopy[c]['name'] == name:
                return True
    return False


def npcsRest(npcs: {}) -> None:
    """Rest restores hit points of NPCs
    """
    for p in npcs:
        thisNPC = npcs[p]
        if thisNPC['hp'] < thisNPC['hpMax'] + thisNPC['tempHitPoints']:
            if randint(0, 100) > 97:
                thisNPC['hp'] += 1
        else:
            thisNPC['hp'] = thisNPC['hpMax'] + thisNPC['tempHitPoints']
            thisNPC['restRequired'] = 0


def _getLeaderRoomIndex(npcs: {}, players: {}, mud,
                        now, nid: int, moveType: str) -> str:
    """An NPC follows another NPC or player
    This returns the index of the room where the leader is located
    """
    if moveType.startswith('leader:'):
        leaderName = moveType.split(':')[1]
        if len(leaderName) > 0:
            # is the leader an NPC
            for (lid, pl) in list(npcs.items()):
                leaderNPC = npcs[lid]
                if leaderNPC['name'] == leaderName:
                    if leaderNPC['room'] != npcs[nid]['room']:
                        # follower NPCs are in the same guild
                        npcs[nid]['guild'] = leaderNPC['guild']
                        return leaderNPC['room']
            # is the leader a player
            for (pid, pl) in list(players.items()):
                if players[pid]['name'] == leaderName:
                    if players[pid]['room'] != npcs[nid]['room']:
                        npcs[nid]['guild'] = players[pid]['guild']
                        return players[pid]['room']
    return ''


def getSolar():
    return Sun(52.414, 4.081)


def _entityIsActive(id, players: {}, rooms: {},
                    moveTimes: [], mapArea: [], clouds: {}) -> bool:
    if len(moveTimes) == 0:
        return True

    # These variables are used for matching a number of days
    # as separate time ranges, eg X or Y or Z
    matchingDays = False
    daysAreMatched = False

    for timeRange in moveTimes:
        if len(timeRange) >= 2:
            timeRangeType = timeRange[0].lower()
            if timeRangeType == 'day' or \
               timeRangeType == 'weekday' or \
               timeRangeType == 'dayofweek' or \
               timeRangeType == 'dow':
                currDayOfWeek = datetime.datetime.today().weekday()
                dowMatched = False
                for dow in range(1, len(timeRange)):
                    dayOfWeek = timeRange[dow].lower()
                    if dayOfWeek.startswith('m') and currDayOfWeek == 0:
                        dowMatched = True
                    if dayOfWeek.startswith('tu') and currDayOfWeek == 1:
                        dowMatched = True
                    if dayOfWeek.startswith('w') and currDayOfWeek == 2:
                        dowMatched = True
                    if dayOfWeek.startswith('th') and currDayOfWeek == 3:
                        dowMatched = True
                    if dayOfWeek.startswith('f') and currDayOfWeek == 4:
                        dowMatched = True
                    if dayOfWeek.startswith('sa') and currDayOfWeek == 5:
                        dowMatched = True
                    if dayOfWeek.startswith('su') and currDayOfWeek == 6:
                        dowMatched = True
                if not dowMatched:
                    return False
                continue
            elif timeRangeType == 'season':
                currMonthNumber = int(datetime.datetime.today().strftime("%m"))
                seasonMatched = False
                for seasonIndex in range(1, len(timeRange)):
                    seasonName = timeRange[seasonIndex].lower()
                    if seasonName == 'spring':
                        if currMonthNumber > 1 and currMonthNumber <= 4:
                            seasonMatched = True
                    elif seasonName == 'summer':
                        if currMonthNumber > 4 and currMonthNumber <= 9:
                            seasonMatched = True
                    elif seasonName == 'autumn':
                        if currMonthNumber > 9 and currMonthNumber <= 10:
                            seasonMatched = True
                    elif seasonName == 'winter':
                        if currMonthNumber > 10 or currMonthNumber <= 1:
                            seasonMatched = True
                if not seasonMatched:
                    return False
                continue

        if len(timeRange) != 3:
            continue
        timeRangeType = timeRange[0].lower()
        timeRangeStart = timeRange[1]
        timeRangeEnd = timeRange[2]

        # sunrise
        if timeRangeType == 'sunrise' or \
           timeRangeType == 'dawn':
            currTime = datetime.datetime.today()
            currHour = currTime.hour
            sun = getSolar()
            sunRiseTime = sun.get_local_sunrise_time(currTime).hour
            if 'true' in timeRangeStart.lower() or \
               'y' in timeRangeStart.lower():
                if not (currHour >= sunRiseTime - 1 and
                        currHour <= sunRiseTime):
                    return False
            else:
                if not (currHour < sunRiseTime - 1 or
                        currHour > sunRiseTime):
                    return False

        if timeRangeType == 'sunset' or \
           timeRangeType == 'dusk':
            currTime = datetime.datetime.today()
            currHour = currTime.hour
            sun = getSolar()
            sunSetTime = sun.get_local_sunset_time(currTime).hour
            if 'true' in timeRangeStart.lower() or \
               'y' in timeRangeStart.lower():
                if not (currHour >= sunSetTime and currHour <= sunSetTime + 1):
                    return False
            else:
                if not (currHour < sunSetTime or currHour > sunSetTime + 1):
                    return False

        if timeRangeType == 'rain':
            rm = players[id]['room']
            coords = rooms[rm]['coords']
            if 'true' in timeRangeStart.lower() or \
               'y' in timeRangeStart.lower():
                if not getRainAtCoords(coords, mapArea, clouds):
                    return False
            else:
                if getRainAtCoords(coords, mapArea, clouds):
                    return False

        if timeRangeType == 'rainday':
            currTime = datetime.datetime.today()
            currHour = currTime.hour
            sun = getSolar()
            sunRiseTime = sun.get_local_sunrise_time(currTime).hour
            sunSetTime = sun.get_local_sunset_time(currTime).hour
            if currHour < sunRiseTime or \
               currHour > sunSetTime:
                return False
            rm = players[id]['room']
            coords = rooms[rm]['coords']
            if 'true' in timeRangeStart.lower() or \
               'y' in timeRangeStart.lower():
                if not getRainAtCoords(coords, mapArea, clouds):
                    return False
            else:
                if getRainAtCoords(coords, mapArea, clouds):
                    return False

        if timeRangeType == 'rainnight':
            currTime = datetime.datetime.today()
            currHour = currTime.hour
            sun = getSolar()
            sunRiseTime = sun.get_local_sunrise_time(currTime).hour
            sunSetTime = sun.get_local_sunset_time(currTime).hour
            if currHour >= sunRiseTime and \
               currHour <= sunSetTime:
                return False
            rm = players[id]['room']
            coords = rooms[rm]['coords']
            if 'true' in timeRangeStart.lower() or \
               'y' in timeRangeStart.lower():
                if not getRainAtCoords(coords, mapArea, clouds):
                    return False
            else:
                if getRainAtCoords(coords, mapArea, clouds):
                    return False

        if timeRangeType == 'rainmorning':
            currTime = datetime.datetime.today()
            currHour = currTime.hour
            sun = getSolar()
            sunRiseTime = sun.get_local_sunrise_time(currTime).hour
            if currHour < sunRiseTime or \
               currHour > 12:
                return False
            rm = players[id]['room']
            coords = rooms[rm]['coords']
            if 'true' in timeRangeStart.lower() or \
               'y' in timeRangeStart.lower():
                if not getRainAtCoords(coords, mapArea, clouds):
                    return False
            else:
                if getRainAtCoords(coords, mapArea, clouds):
                    return False

        if timeRangeType == 'rainafternoon':
            currTime = datetime.datetime.today()
            currHour = currTime.hour
            if currHour < 12 or currHour > 17:
                return False
            rm = players[id]['room']
            coords = rooms[rm]['coords']
            if 'true' in timeRangeStart.lower() or \
               'y' in timeRangeStart.lower():
                if not getRainAtCoords(coords, mapArea, clouds):
                    return False
            else:
                if getRainAtCoords(coords, mapArea, clouds):
                    return False

        if timeRangeType == 'rainevening':
            currTime = datetime.datetime.today()
            currHour = currTime.hour
            sun = getSolar()
            sunSetTime = sun.get_local_sunset_time(currTime).hour
            if currHour < 17 or \
               currHour > sunSetTime:
                return False
            rm = players[id]['room']
            coords = rooms[rm]['coords']
            if 'true' in timeRangeStart.lower() or \
               'y' in timeRangeStart.lower():
                if not getRainAtCoords(coords, mapArea, clouds):
                    return False
            else:
                if getRainAtCoords(coords, mapArea, clouds):
                    return False

        # hour of day
        if timeRangeType.startswith('hour'):
            currHour = datetime.datetime.today().hour
            startHour = int(timeRangeStart)
            endHour = int(timeRangeEnd)
            if endHour >= startHour:
                if currHour < startHour or currHour > endHour:
                    return False
            else:
                if currHour > endHour and currHour < startHour:
                    return False

        # between months
        if timeRangeType.startswith('month'):
            currMonth = int(datetime.datetime.today().strftime("%m"))
            startMonth = int(timeRangeStart)
            endMonth = int(timeRangeEnd)
            if endMonth >= startMonth:
                if currMonth < startMonth or currMonth > endMonth:
                    return False
            else:
                if currMonth > endMonth and currMonth < startMonth:
                    return False

        # a particular day of a month
        if timeRangeType.startswith('dayofmonth'):
            currMonth = int(datetime.datetime.today().strftime("%m"))
            currDayOfMonth = int(datetime.datetime.today().strftime("%d"))
            month = int(timeRangeStart)
            monthday = int(timeRangeEnd)
            matchingDays = True
            if currMonth == month and currDayOfMonth == monthday:
                daysAreMatched = True

        # between days of year
        if timeRangeType == 'daysofyear':
            currDayOfYear = int(datetime.datetime.today().strftime("%j"))
            startDay = int(timeRangeStart)
            endDay = int(timeRangeEnd)
            if endDay >= startDay:
                if currDayOfYear < startDay or currDayOfYear > endDay:
                    return False
            else:
                if currDayOfYear > endDay and currDayOfYear < startDay:
                    return False

    # if we are matching a set of days, where any matched?
    if matchingDays:
        if not daysAreMatched:
            return False

    return True


def _moveNPCs(npcs, players, mud, now, nid) -> None:
    """If movement is defined for an NPC this moves it around
    """
    thisNPC = npcs[nid]
    if now > thisNPC['lastMoved'] + \
       int(thisNPC['moveDelay']) + thisNPC['randomizer']:
        # Move types:
        #   random, cycle, inverse cycle, patrol, follow, leader:name
        moveTypeLower = thisNPC['moveType'].lower()

        followCycle = False
        if moveTypeLower.startswith('f'):
            if len(thisNPC['follow']) == 0:
                followCycle = True
                # Look for a player to follow
                for (pid, pl) in list(players.items()):
                    if thisNPC['room'] == players[pid]['room']:
                        # follow by name
                        # print(thisNPC['name'] + ' starts following ' +
                        # players[pid]['name'] + '\n')
                        thisNPC['follow'] = players[pid]['name']
                        followCycle = False
            if not followCycle:
                return

        if moveTypeLower.startswith('c') or \
           moveTypeLower.startswith('p') or followCycle:
            npcRoomIndex = 0
            npcRoomCurr = thisNPC['room']
            for npcRoom in thisNPC['path']:
                if npcRoom == npcRoomCurr:
                    npcRoomIndex = npcRoomIndex + 1
                    break
                npcRoomIndex = npcRoomIndex + 1
            if npcRoomIndex >= len(thisNPC['path']):
                if moveTypeLower.startswith('p'):
                    thisNPC['moveType'] = 'back'
                    npcRoomIndex = len(thisNPC['path']) - 1
                    if npcRoomIndex > 0:
                        npcRoomIndex = npcRoomIndex - 1
                else:
                    npcRoomIndex = 0
        else:
            if moveTypeLower.startswith('i') or moveTypeLower.startswith('b'):
                npcRoomIndex = 0
                npcRoomCurr = thisNPC['room']
                for npcRoom in thisNPC['path']:
                    if npcRoom == npcRoomCurr:
                        npcRoomIndex = npcRoomIndex - 1
                        break
                    npcRoomIndex = npcRoomIndex + 1
                if npcRoomIndex >= len(thisNPC['path']):
                    npcRoomIndex = len(thisNPC['path']) - 1
                if npcRoomIndex < 0:
                    if moveTypeLower.startswith('b'):
                        thisNPC['moveType'] = 'patrol'
                        npcRoomIndex = 0
                        if npcRoomIndex < len(thisNPC['path']) - 1:
                            npcRoomIndex = npcRoomIndex + 1
                    else:
                        npcRoomIndex = len(thisNPC['path']) - 1
            else:
                npcRoomIndex = \
                    _getLeaderRoomIndex(npcs, players, mud, now,
                                        nid, moveTypeLower)
                if len(npcRoomIndex) == 0:
                    npcRoomIndex = randint(0, len(thisNPC['path']) - 1)

        rm = thisNPC['path'][npcRoomIndex]
        if thisNPC['room'] != rm:
            for (pid, pl) in list(players.items()):
                if thisNPC['room'] == players[pid]['room']:
                    mud.sendMessage(
                        pid, '<f220>' + thisNPC['name'] + "<r> " +
                        randomDescription(thisNPC['outDescription']) +
                        "\n\n")
            thisNPC['room'] = rm
            thisNPC['lastRoom'] = rm
            for (pid, pl) in list(players.items()):
                if thisNPC['room'] == players[pid]['room']:
                    mud.sendMessage(
                        pid, '<f220>' + thisNPC['name'] + "<r> " +
                        randomDescription(thisNPC['inDescription']) +
                        "\n\n")
        thisNPC['randomizer'] = randint(0, thisNPC['randomFactor'])
        thisNPC['lastMoved'] = now


def _removeInactiveEntity(nid, npcs: {}, nid2, npcsDB: {},
                          npcActive: bool) -> bool:
    """Moves inactive NPCs to and from purgatory
    Returns true when recovering from purgatory
    """
    # Where NPCs go when inactive by default
    purgatoryRoom = "$rid=1386$"

    for timeRange in npcsDB[nid2]['moveTimes']:
        if len(timeRange) == 2:
            if timeRange[0].startswith('inactive') or \
               timeRange[0].startswith('home'):
                purgatoryRoom = "$rid=" + str(timeRange[1]) + "$"
            break

    thisNPC = npcs[nid]
    if thisNPC['room'] == purgatoryRoom:
        if npcActive:
            if thisNPC.get('lastRoom'):
                # recover from puratory
                thisNPC['room'] = thisNPC['lastRoom']
                return True
        return False

    if not npcActive:
        # Move the NPC to purgatory
        thisNPC['lastRoom'] = thisNPC['room']
        thisNPC['room'] = purgatoryRoom
        return False


def npcRespawns(npcs: {}) -> None:
    """Respawns inactive NPCs
    """
    for (nid, pl) in list(npcs.items()):
        thisNPC = npcs[nid]
        if not thisNPC['whenDied']:
            continue
        if int(time.time()) >= thisNPC['whenDied'] + thisNPC['respawn']:
            if len(thisNPC['familiarOf']) == 0:
                thisNPC['whenDied'] = None
                # thisNPC['room'] = npcsTemplate[nid]['room']
                thisNPC['room'] = thisNPC['lastRoom']
                hpStr = str(thisNPC['hp'])
                log("respawning " + thisNPC['name'] +
                    " with " + hpStr +
                    " hit points", "info")


def runMobileItems(itemsDB: {}, items: {}, eventSchedule,
                   scriptedEventsDB,
                   rooms: {}, mapArea, clouds: {}) -> None:
    """Updates all NPCs
    """
    for (item, pl) in list(items.items()):
        itemID = items[item]['id']
        # only non-takeable items
        if itemsDB[itemID]['weight'] > 0:
            continue
        if not itemsDB[itemID].get('moveTimes'):
            continue
        # Active now?
        itemActive = \
            _entityIsActive(itemID, items, rooms,
                            itemsDB[itemID]['moveTimes'],
                            mapArea, clouds)
        # Remove if not active
        _removeInactiveEntity(item, items, itemID, itemsDB, itemActive)
        if not itemActive:
            continue


def runNPCs(mud, npcs: {}, players: {}, fights, corpses, scriptedEventsDB,
            itemsDB: {}, npcsTemplate, rooms: {}, mapArea, clouds: {},
            eventSchedule) -> None:
    """Updates all NPCs
    """

    for (nid, pl) in list(npcs.items()):
        # is the NPC a familiar?
        npcIsFamiliar = False
        thisNPC = npcs[nid]
        if len(thisNPC['familiarOf']) > 0:
            for (pid, pl) in list(players.items()):
                if thisNPC['familiarOf'] == players[pid]['name']:
                    npcIsFamiliar = True
                    break

        if not npcIsFamiliar:
            # is the NPC active according to moveTimes?
            npcActive = \
                _entityIsActive(nid, npcs, rooms,
                                thisNPC['moveTimes'],
                                mapArea, clouds)
            _removeInactiveEntity(nid, npcs, nid, npcs, npcActive)
            if not npcActive:
                continue

        # Check if any player is in the same room, then send a random
        # message to them
        now = int(time.time())
        if thisNPC['vocabulary'][0]:
            if now > \
               thisNPC['timeTalked'] + \
               thisNPC['talkDelay'] + \
               thisNPC['randomizer']:
                rnd = randint(0, len(thisNPC['vocabulary']) - 1)
                while rnd is thisNPC['lastSaid']:
                    rnd = randint(0, len(thisNPC['vocabulary']) - 1)
                for (pid, pl) in list(players.items()):
                    if thisNPC['room'] == players[pid]['room']:
                        if len(thisNPC['vocabulary']) > 1:
                            # mud.sendMessage(pid,
                            # thisNPC['vocabulary'][rnd])
                            msg = '<f220>' + thisNPC['name'] + \
                                '<r> says: <f86>' + \
                                thisNPC['vocabulary'][rnd] + "\n\n"
                            mud.sendMessage(pid, msg)
                            thisNPC['randomizer'] = \
                                randint(0, thisNPC['randomFactor'])
                            thisNPC['lastSaid'] = rnd
                            thisNPC['timeTalked'] = now
                        else:
                            # mud.sendMessage(pid, thisNPC['vocabulary'][0])
                            msg = '<f220>' + thisNPC['name'] + \
                                '<r> says: <f86>' + \
                                thisNPC['vocabulary'][0] + "\n\n"
                            mud.sendMessage(pid, msg)
                            thisNPC['randomizer'] = \
                                randint(0, thisNPC['randomFactor'])
                            thisNPC['timeTalked'] = now

        # Iterate through fights and see if anyone is attacking an NPC -
        # if so, attack him too if not in combat (TODO: and isAggressive =
        # true)
        isInFight = False
        for (fid, pl) in list(fights.items()):
            if fights[fid]['s2id'] == nid and \
               npcs[fights[fid]['s2id']]['isInCombat'] == 1 and \
               fights[fid]['s2type'] == 'npc' and \
               fights[fid]['s1type'] == 'pc' and \
               fights[fid]['retaliated'] == 0:
                # print('player is attacking npc')
                # BETA: set las combat action to now when attacking a
                # player
                npcs[fights[fid]['s2id']]['lastCombatAction'] = \
                    int(time.time())
                fights[fid]['retaliated'] = 1
                npcs[fights[fid]['s2id']]['isInCombat'] = 1
                fights[len(fights)] = {
                    's1': npcs[fights[fid]['s2id']]['name'],
                    's2': players[fights[fid]['s1id']]['name'],
                    's1id': nid,
                    's2id': fights[fid]['s1id'],
                    's1type': 'npc',
                    's2type': 'pc',
                    'retaliated': 1
                }
                isInFight = True
            elif (fights[fid]['s2id'] == nid and
                  npcs[fights[fid]['s2id']]['isInCombat'] == 1 and
                  fights[fid]['s1type'] == 'npc' and
                  fights[fid]['retaliated'] == 0):
                # print('npc is attacking npc')
                # BETA: set last combat action to now when attacking a player
                npcs[fights[fid]['s2id']]['lastCombatAction'] = \
                    int(time.time())
                fights[fid]['retaliated'] = 1
                npcs[fights[fid]['s2id']]['isInCombat'] = 1
                fights[len(fights)] = {
                    's1': npcs[fights[fid]['s2id']]['name'],
                    's2': players[fights[fid]['s1id']]['name'],
                    's1id': nid,
                    's2id': fights[fid]['s1id'],
                    's1type': 'npc',
                    's2type': 'npc',
                    'retaliated': 1
                }
                isInFight = True

        # NPC moves to the next location
        now = int(time.time())
        if isInFight is False and \
           len(thisNPC['path']) > 0:
            _moveNPCs(npcs, players, mud, now, nid)

        # Check if NPC is still alive, if not, remove from room and
        # create a corpse, set isInCombat to 0, set whenDied to now
        # and remove any fights NPC was involved in
        if thisNPC['hp'] <= 0:
            thisNPC['isInCombat'] = 0
            thisNPC['lastRoom'] = thisNPC['room']
            thisNPC['whenDied'] = int(time.time())

            # if the NPC is a familiar detach it from player
            for pl in players:
                if players[pl]['name'] is None:
                    continue
                if players[pl]['familiar'] == int(nid):
                    players[pl]['familiar'] -= 1

            fightsCopy = deepcopy(fights)
            for (fight, pl) in fightsCopy.items():
                if ((fightsCopy[fight]['s1type'] == 'npc' and
                     fightsCopy[fight]['s1id'] == nid) or
                    (fightsCopy[fight]['s2type'] == 'npc' and
                     fightsCopy[fight]['s2id'] == nid)):
                    # clear the combat flag
                    if fightsCopy[fight]['s1type'] == 'pc':
                        fid = fightsCopy[fight]['s1id']
                        players[fid]['isInCombat'] = 0
                    elif fightsCopy[fight]['s1type'] == 'npc':
                        fid = fightsCopy[fight]['s1id']
                        npcs[fid]['isInCombat'] = 0
                    if fightsCopy[fight]['s2type'] == 'pc':
                        fid = fightsCopy[fight]['s2id']
                        players[fid]['isInCombat'] = 0
                    elif fightsCopy[fight]['s2type'] == 'npc':
                        fid = fightsCopy[fight]['s2id']
                        npcs[fid]['isInCombat'] = 0
                    del fights[fight]
                    corpseName = str(thisNPC['name'] + "'s corpse")
                    if not corpseExists(corpses,
                                        thisNPC['room'],
                                        corpseName):
                        corpses[len(corpses)] = {
                            'room': thisNPC['room'],
                            'name': corpseName,
                            'inv': deepcopy(thisNPC['inv']),
                            'died': int(time.time()),
                            'TTL': thisNPC['corpseTTL'],
                            'owner': 1
                        }

            # inform players about the death of an npc
            for (pid, pl) in list(players.items()):
                if players[pid]['authenticated'] is not None:
                    if players[pid]['authenticated'] is not None and \
                       players[pid]['room'] == thisNPC['room']:
                        mud.sendMessage(
                            pid,
                            "<f220>{}<r> ".format(thisNPC['name']) +
                            "<f88>has been killed.\n")
                        thisNPC['lastRoom'] = thisNPC['room']
                        thisNPC['room'] = None
                        thisNPC['hp'] = npcsTemplate[nid]['hp']

            # Drop NPC loot on the floor
            droppedItems = []
            for i in thisNPC['inv']:
                if not str(i).isdigit():
                    for (pid, pl) in list(players.items()):
                        mud.sendMessage(
                            pid, 'NPC drops item: ' +
                            str(i) + ' is not an item number\n')
                    continue
                if randint(0, 100) < 50:
                    itemIDStr = str(i)
                    lastRoomStr = str(thisNPC['lastRoom'])
                    addToScheduler("0|spawnItem|" + itemIDStr + ";" +
                                   lastRoomStr + ";0;0",
                                   -1, eventSchedule, scriptedEventsDB)
                    print("Dropped!" + str(itemsDB[int(i)]['name']))
                    droppedItems.append(str(itemsDB[int(i)]['name']))

            # Inform other players in the room what items got dropped on NPC
            # death
            if len(droppedItems) > 0:
                for p in players:
                    if players[p]['name'] is None:
                        continue
                    if players[p]['room'] == thisNPC['lastRoom']:
                        mud.sendMessage(
                            p, "Right before <f220>" +
                            str(thisNPC['name']) +
                            "<r>'s lifeless body collapsed to the floor, " +
                            "it had dropped the following items: " +
                            "<f220>{}".format(', '.join(droppedItems)) + "\n")


def _conversationState(word: str, conversationStates: {},
                       nid, npcs: {},
                       matchCtr: int) -> (bool, bool, int):
    """Is the conversations with this npc in the given state?
       Returns True if the conversation is in the given state
       Also returns True if subsequent words can also be matched
       and the current word match counter
    """
    thisNPC = npcs[nid]
    if word.lower().startswith('state:'):
        requiredState = word.lower().split(':')[1].strip()
        if thisNPC['name'] in conversationStates:
            if conversationStates[thisNPC['name']] != requiredState:
                return False, False, matchCtr
            return True, True, matchCtr + 1
    return False, True, matchCtr


def _conversationCondition(word: str, conversationStates: {},
                           nid, npcs: {}, matchCtr: int,
                           players: {}, rooms: {},
                           id, culturesDB: {}) -> (bool, bool, int):
    conditionType = ''
    if '>' in word.lower():
        conditionType = '>'
    if '<' in word.lower():
        conditionType = '<'
    if '=' in word.lower():
        conditionType = conditionType + '='

    if len(conditionType) == 0:
        return False, True, matchCtr

    varStr = word.lower().split(conditionType)[0].strip()
    currValue = -99999
    targetValue = None

    if varStr == 'hp' or varStr == 'hitpoints':
        currValue = players[id]['hp']
    if varStr == 'hpPercent' or varStr == 'hitpointspercent':
        currValue = int(players[id]['hp'] * 100 / players[id]['hp'])
    if varStr == 'cul' or \
       varStr == 'culture':
        if players[id].get('culture'):
            currValue = players[id]['culture']
            targetValue = word.lower().split(conditionType)[1].strip()
    if varStr == 'roomcul' or \
       varStr == 'roomculture':
        currValue = getRoomCulture(culturesDB, rooms, players[id]['room'])
        targetValue = word.lower().split(conditionType)[1].strip()
    if varStr == 'str' or \
       varStr == 'strength':
        currValue = players[id]['str']
    if varStr == 'wei' or \
       varStr == 'weight':
        currValue = players[id]['wei']
    if varStr == 'per' or \
       varStr == 'perception':
        currValue = players[id]['per']
    if varStr == 'lvl' or \
       varStr == 'level':
        currValue = players[id]['lvl']
    if varStr == 'exp' or \
       varStr == 'experience':
        currValue = players[id]['exp']
    if varStr == 'endu' or \
       varStr == 'endurance':
        currValue = players[id]['endu']
    if varStr == 'cha' or \
       varStr == 'charisma':
        currValue = players[id]['cha']
    if varStr == 'int' or \
       varStr == 'intelligence':
        currValue = players[id]['int']
    if varStr == 'agi' or \
       varStr == 'agility':
        currValue = players[id]['agi']
    if varStr == 'luc' or \
       varStr == 'luck':
        currValue = players[id]['luc']
    if varStr == 'cred':
        currValue = players[id]['cred']
    if varStr == 'pp':
        currValue = players[id]['pp']
    if varStr == 'ep':
        currValue = players[id]['ep']
    if varStr == 'sp':
        currValue = players[id]['sp']
    if varStr == 'cp':
        currValue = players[id]['cp']
    if varStr == 'gp':
        currValue = players[id]['gp']
    if varStr == 'reflex':
        currValue = players[id]['ref']
    if varStr == 'cool':
        currValue = players[id]['cool']
    if varStr == 'rest':
        currValue = players[id]['restRequired']
    if varStr == 'language':
        currValue = players[id]['speakLanguage'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '='
    if varStr == 'notlanguage':
        currValue = players[id]['speakLanguage'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '!='
    if varStr == 'guild':
        currValue = players[id]['guild'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '='
    if varStr == 'region':
        rm = players[id]['room']
        currValue = rooms[rm]['region'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '='
    if varStr == 'notguild':
        currValue = players[id]['guild'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '!='
    if varStr == 'race':
        currValue = players[id]['race'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '='
    if varStr == 'notrace':
        currValue = players[id]['race'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '!='
    if varStr == 'characterclass':
        currValue = players[id]['characterClass'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '='
    if varStr == 'notcharacterclass':
        currValue = players[id]['characterClass'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '!='
    if varStr == 'enemy':
        currValue = players[id]['enemy'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '='
    if varStr == 'notenemy':
        currValue = players[id]['enemy'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '!='
    if varStr == 'affinity':
        if npcs[nid]['affinity'].get(players[id]['name']):
            currValue = npcs[nid]['affinity'][players[id]['name']]
        else:
            currValue = 0

    if targetValue is None:
        targetValue = int(word.lower().split(conditionType)[1].strip())

    if not isinstance(currValue, str):
        if currValue == -99999:
            return False, True, matchCtr

        if conditionType == '>':
            if currValue <= targetValue:
                return False, False, matchCtr

        if conditionType == '<':
            if currValue >= targetValue:
                return False, False, matchCtr

        if conditionType == '>=':
            if currValue < targetValue:
                return False, False, matchCtr

        if conditionType == '<=':
            if currValue > targetValue:
                return False, False, matchCtr

    if conditionType == '=':
        if currValue != targetValue:
            return False, False, matchCtr

    if conditionType == '!=':
        if currValue == targetValue:
            return False, False, matchCtr

    return True, True, matchCtr + 1


def _conversationWordCount(message: str, wordsList: [], npcs: {},
                           nid, conversationStates: {},
                           players: {}, rooms: {}, id,
                           culturesDB: {}) -> int:
    """Returns the number of matched words in the message.
       This is a 'bag of words/conditions' type of approach.
    """
    matchCtr = 0
    for possibleWord in wordsList:
        if possibleWord.lower().startswith('image:'):
            continue

        # Is the conversation required to be in a certain state?
        stateMatched, continueMatching, matchCtr = \
            _conversationState(possibleWord,
                               conversationStates,
                               nid, npcs, matchCtr)

        if not continueMatching:
            break

        if not stateMatched:
            # match conditions such as "strength < 10"
            wordMatched, continueMatching, matchCtr = \
                _conversationCondition(possibleWord,
                                       conversationStates,
                                       nid, npcs,
                                       matchCtr,
                                       players, rooms, id,
                                       culturesDB)

            if not continueMatching:
                break

            if not wordMatched:
                if possibleWord.lower() in message:
                    matchCtr += 1
    return matchCtr


def _conversationGive(bestMatch: str, bestMatchAction: str,
                      thingGivenIDstr: str, players: {}, id,
                      mud, npcs: {}, nid: int, itemsDB: {},
                      puzzledStr: str, guildsDB: {}) -> bool:
    """Conversation in which an NPC gives something to you
    """
    if bestMatchAction == 'give' or \
       bestMatchAction == 'gift':
        thisNPC = npcs[nid]
        if len(thingGivenIDstr) > 0:
            itemID = int(thingGivenIDstr)
            if itemID not in list(players[id]['inv']):
                players[id]['inv'].append(str(itemID))
                updatePlayerAttributes(id, players, itemsDB, itemID, 1)
                players[id]['wei'] = \
                    playerInventoryWeight(id, players, itemsDB)
                increaseAffinityBetweenPlayers(players, id, npcs, nid,
                                               guildsDB)
                increaseAffinityBetweenPlayers(npcs, nid, players, id,
                                               guildsDB)
                if '#' not in bestMatch:
                    mud.sendMessage(
                        id, "<f220>" + thisNPC['name'] + "<r> says: " +
                        bestMatch + ".")
                else:
                    mud.sendMessage(id, "<f220>" +
                                    bestMatch.replace('#', '').strip() + ".")
                mud.sendMessage(
                    id, "<f220>" + thisNPC['name'] +
                    "<r> gives you " + itemsDB[itemID]['article'] +
                    ' ' + itemsDB[itemID]['name'] + ".\n\n")
                return True
        mud.sendMessage(
            id, "<f220>" + thisNPC['name'] +
            "<r> looks " + puzzledStr + ".\n\n")
        return True
    return False


def _conversationSkill(bestMatch: str, bestMatchAction: str,
                       bestMatchActionParam0: str,
                       bestMatchActionParam1: str,
                       players: {}, id, mud, npcs: {}, nid, itemsDB: {},
                       puzzledStr: str, guildsDB: {}) -> bool:
    """Conversation in which an NPC gives or alters a skill
    """
    if bestMatchAction == 'skill' or \
       bestMatchAction == 'teach':
        thisNPC = npcs[nid]
        if len(bestMatchActionParam0) > 0 and \
           len(bestMatchActionParam1) > 0:
            newSkill = bestMatchActionParam0.lower()
            skillValueStr = bestMatchActionParam1
            if not players[id].get(newSkill):
                log(newSkill + ' skill does not exist in player instance',
                    'info')
                return False
            if '+' in skillValueStr:
                # increase skill
                players[id][newSkill] = \
                    players[id][newSkill] + \
                    int(skillValueStr.replace('+', ''))
            else:
                # decrease skill
                if '-' in skillValueStr:
                    players[id][newSkill] = \
                        players[id][newSkill] - \
                        int(skillValueStr.replace('-', ''))
                else:
                    # set skill to absolute value
                    players[id][newSkill] = \
                        players[id][newSkill] + \
                        int(skillValueStr)

            increaseAffinityBetweenPlayers(players, id, npcs, nid, guildsDB)
            increaseAffinityBetweenPlayers(npcs, nid, players, id, guildsDB)

            mud.sendMessage(
                id, "<f220>" + thisNPC['name'] + "<r> says: " + bestMatch +
                ".\n\n")
            return True
        else:
            mud.sendMessage(
                id, "<f220>" + thisNPC['name'] + "<r> looks " +
                puzzledStr + ".\n\n")
            return False
    return False


def _conversationExperience(
        bestMatch: str, bestMatchAction: str,
        bestMatchActionParam0: str,
        bestMatchActionParam1: str,
        players: {}, id, mud, npcs: {}, nid, itemsDB: {},
        puzzledStr: str, guildsDB: {}) -> bool:
    """Conversation in which an NPC increases your experience
    """
    if bestMatchAction == 'exp' or \
       bestMatchAction == 'experience':
        if len(bestMatchActionParam0) > 0:
            expValue = int(bestMatchActionParam0)
            players[id]['exp'] = players[id]['exp'] + expValue
            increaseAffinityBetweenPlayers(players, id, npcs, nid, guildsDB)
            increaseAffinityBetweenPlayers(npcs, nid, players, id, guildsDB)
            return True
        else:
            mud.sendMessage(
                id, "<f220>" + npcs[nid]['name'] + "<r> looks " +
                puzzledStr + ".\n\n")
            return False
    return False


def _conversationJoinGuild(
        bestMatch: str, bestMatchAction: str,
        bestMatchActionParam0: str,
        bestMatchActionParam1: str,
        players: {}, id, mud, npcs: {}, nid, itemsDB: {},
        puzzledStr: str, guildsDB: {}) -> bool:
    """Conversation in which an NPC adds you to a guild
    """
    if bestMatchAction == 'clan' or \
       bestMatchAction == 'guild' or \
       bestMatchAction == 'tribe' or \
       bestMatchAction == 'house':
        if len(bestMatchActionParam0) > 0:
            players[id]['guild'] = bestMatchActionParam0
            if len(bestMatchActionParam1) > 0:
                players[id]['guildRole'] = bestMatchActionParam1
            increaseAffinityBetweenPlayers(players, id, npcs, nid, guildsDB)
            increaseAffinityBetweenPlayers(npcs, nid, players, id, guildsDB)
            return True
        else:
            mud.sendMessage(
                id, "<f220>" + npcs[nid]['name'] +
                "<r> looks " + puzzledStr + ".\n\n")
            return False
    return False


def _conversationFamiliarMode(
        bestMatch: str, bestMatchAction: str,
        bestMatchActionParam0: str,
        bestMatchActionParam1: str,
        players: {}, id, mud, npcs: {}, npcsDB: {}, rooms: {},
        nid, items: {}, itemsDB: {}, puzzledStr: str) -> bool:
    """Switches the mode of a familiar
    """
    thisNPC = npcs[nid]
    if bestMatchAction == 'familiar':
        if len(bestMatchActionParam0) > 0:
            if thisNPC['familiarOf'] == players[id]['name']:
                mode = bestMatchActionParam0.lower().strip()
                if mode in getFamiliarModes():
                    if mode == 'follow':
                        familiarDefaultMode(nid, npcs, npcsDB)
                    if mode == 'hide':
                        familiarHide(nid, npcs, npcsDB)
                    mud.sendMessage(
                        id, "<f220>" + thisNPC['name'] +
                        "<r> " + bestMatch + ".\n\n")
                    if mode == 'scout':
                        familiarScout(mud, players, id, nid,
                                      npcs, npcsDB, rooms,
                                      bestMatchActionParam1)
                    if mode == 'see':
                        familiarSight(mud, nid, npcs, npcsDB,
                                      rooms, players, id, items,
                                      itemsDB)
                    return True
            else:
                mud.sendMessage(
                    id, thisNPC['name'] + " is not your familiar.\n\n")
        else:
            mud.sendMessage(
                id, "<f220>" + thisNPC['name'] +
                "<r> looks " + puzzledStr + ".\n\n")
            return False
    return False


def _conversationTransport(
        bestMatchAction: str, bestMatchActionParam0: str,
        mud, id, players: {}, bestMatch, npcs: {}, nid,
        puzzledStr, guildsDB: {}, rooms: {}) -> bool:
    """Conversation in which an NPC transports you to some location
    """
    if bestMatchAction == 'transport' or \
       bestMatchAction == 'ride' or \
       bestMatchAction == 'teleport':
        thisNPC = npcs[nid]
        if len(bestMatchActionParam0) > 0:
            roomID = bestMatchActionParam0
            mud.sendMessage(id, bestMatch)
            messageToPlayersInRoom(
                mud, players, id,
                '<f32>{}<r> leaves.'.format(players[id]['name']) + "\n\n")
            players[id]['room'] = roomID
            thisNPC['room'] = roomID
            increaseAffinityBetweenPlayers(players, id, npcs, nid, guildsDB)
            increaseAffinityBetweenPlayers(npcs, nid, players, id, guildsDB)
            messageToPlayersInRoom(
                mud, players, id,
                '<f32>{}<r> arrives.'.format(players[id]['name']) + "\n\n")
            mud.sendMessage(
                id, "You are in " + rooms[roomID]['name'] + "\n\n")
            return True
        mud.sendMessage(
            id, "<f220>" + thisNPC['name'] + "<r> looks " +
            puzzledStr + ".\n\n")
        return True
    return False


def _conversationTaxi(
        bestMatchAction: str, bestMatchActionParam0: str,
        bestMatchActionParam1: str, players: {},
        id, mud, bestMatch, npcs: {}, nid, itemsDB: {},
        puzzledStr: str, guildsDB: {}, rooms: {}) -> bool:
    """Conversation in which an NPC transports you to some
    location in exchange for payment/barter
    """
    if bestMatchAction == 'taxi':
        thisNPC = npcs[nid]
        if len(bestMatchActionParam0) > 0 and \
           len(bestMatchActionParam1) > 0:
            roomID = bestMatchActionParam0
            itemBuyID = int(bestMatchActionParam1)
            if str(itemBuyID) in list(players[id]['inv']):
                players[id]['inv'].remove(str(itemBuyID))

                increaseAffinityBetweenPlayers(players, id, npcs,
                                               nid, guildsDB)
                increaseAffinityBetweenPlayers(npcs, nid, players,
                                               id, guildsDB)
                mud.sendMessage(id, bestMatch)
                messageToPlayersInRoom(
                    mud, players, id,
                    '<f32>{}<r> leaves.'.format(players[id]['name']) + "\n\n")
                players[id]['room'] = roomID
                thisNPC['room'] = roomID
                messageToPlayersInRoom(
                    mud, players, id,
                    '<f32>{}<r> arrives.'.format(players[id]['name']) + "\n\n")
                mud.sendMessage(
                    id, "You are in " + rooms[roomID]['name'] + "\n\n")
                return True
            else:
                mud.sendMessage(
                    id, "<f220>" + thisNPC['name'] + "<r> says: Give me " +
                    itemsDB[itemBuyID]['article'] + ' ' +
                    itemsDB[itemBuyID]['name'] + ".\n\n")
                return True
        mud.sendMessage(
            id, "<f220>" + thisNPC['name'] + "<r> looks " +
            puzzledStr + ".\n\n")
        return True
    return False


def _conversationGiveOnDate(
        bestMatchAction: str, bestMatchActionParam0: str,
        bestMatchActionParam1: str, players: {},
        id, mud, npcs: {}, nid, itemsDB: {}, bestMatch,
        puzzledStr: str, guildsDB: {}) -> bool:
    """Conversation in which an NPC gives something to you on
    a particular date of the year eg. Some festival or holiday
    """
    if bestMatchAction == 'giveondate' or \
       bestMatchAction == 'giftondate':
        thisNPC = npcs[nid]
        if len(bestMatchActionParam0) > 0:
            itemID = int(bestMatchActionParam0)
            if itemID not in list(players[id]['inv']):
                if '/' in bestMatchActionParam1:
                    dayNumber = int(bestMatchActionParam1.split('/')[0])
                    if dayNumber == \
                       int(datetime.datetime.today().strftime("%d")):
                        monthNumber = \
                            int(bestMatchActionParam1.split('/')[1])
                        if monthNumber == \
                           int(datetime.datetime.today().strftime("%m")):
                            players[id]['inv'].append(str(itemID))
                            players[id]['wei'] = \
                                playerInventoryWeight(id, players, itemsDB)
                            updatePlayerAttributes(
                                id, players, itemsDB, itemID, 1)
                            increaseAffinityBetweenPlayers(
                                players, id, npcs, nid, guildsDB)
                            increaseAffinityBetweenPlayers(
                                npcs, nid, players, id, guildsDB)
                            if '#' not in bestMatch:
                                mud.sendMessage(
                                    id, "<f220>" + thisNPC['name'] +
                                    "<r> says: " + bestMatch + ".")
                            else:
                                mud.sendMessage(
                                    id, "<f220>" +
                                    bestMatch.replace('#', '').strip() + ".")
                            mud.sendMessage(
                                id, "<f220>" + thisNPC['name'] +
                                "<r> gives you " +
                                itemsDB[itemID]['article'] +
                                ' ' + itemsDB[itemID]['name'] + ".\n\n")
                            return True
        mud.sendMessage(
            id, "<f220>" + thisNPC['name'] + "<r> looks " +
            puzzledStr + ".\n\n")
        return True
    return False


def _conversationSell(
        bestMatch: str, bestMatchAction: str,
        bestMatchActionParam0: str,
        npcs: {}, nid, mud, id, players: {}, itemsDB: {},
        puzzledStr: str, guildsDB: {}) -> bool:
    """Conversation in which a player sells to an NPC
    """
    if bestMatchAction == 'sell':
        sellItemIds = bestMatchActionParam0.split('|')
        if len(bestMatchActionParam0) > 0 and sellItemIds:
            for sellIDStr in sellItemIds:
                sellIDStr = sellIDStr.strip()
                itemSellID = int(sellIDStr)
                cost = itemsDB[sellIDStr]['cost']
                if sellIDStr in players[id]['inv'] and cost:
                    # increase the player's money
                    denomination = 'gp'
                    if cost.endswith('sp'):
                        denomination = 'sp'
                    elif cost.endswith('cp'):
                        denomination = 'cp'
                    elif cost.endswith('ep'):
                        denomination = 'ep'
                    elif cost.endswith('pp'):
                        denomination = 'pp'
                    qty = int(cost.replace(denomination, ''))
                    players[id][denomination] += qty

                    # decrease the players inventory
                    players[id]['inv'].remove(sellIDStr)
                    updatePlayerAttributes(
                        id, players, itemsDB, itemSellID, -1)
                    players[id]['wei'] = \
                        playerInventoryWeight(id, players, itemsDB)
                    increaseAffinityBetweenPlayers(players, id, npcs,
                                                   nid, guildsDB)
                    increaseAffinityBetweenPlayers(npcs, nid, players,
                                                   id, guildsDB)

                    itemName = \
                        itemsDB[sellIDStr]['article'] + ' ' + \
                        itemsDB[sellIDStr]['name']
                    mud.sendMessage(
                        id, "You sell " + itemName + ".\n\n")
                    return True
    return False


def _conversationBuyOrExchange(
        bestMatch: str, bestMatchAction: str,
        bestMatchActionParam0: str,
        bestMatchActionParam1: str,
        npcs: {}, nid, mud, id, players: {}, itemsDB: {},
        puzzledStr: str, guildsDB: {}) -> bool:
    """Conversation in which an NPC exchanges/swaps some item
    with you or in which you buy some item from them
    """
    if bestMatchAction == 'buy' or \
       bestMatchAction == 'exchange' or \
       bestMatchAction == 'barter' or \
       bestMatchAction == 'trade':
        thisNPC = npcs[nid]
        if len(bestMatchActionParam0) > 0 and len(
                bestMatchActionParam1) > 0:
            itemBuyID = int(bestMatchActionParam0)
            itemSellID = int(bestMatchActionParam1)
            if str(itemSellID) not in list(thisNPC['inv']):
                if bestMatchAction == 'buy':
                    mud.sendMessage(
                        id, "<f220>" + thisNPC['name'] +
                        "<r> says: I don't have any of those to sell.\n\n")
                else:
                    mud.sendMessage(
                        id, "<f220>" + thisNPC['name'] +
                        "<r> says: I don't have any of those to trade.\n\n")
            else:
                if str(itemBuyID) in list(players[id]['inv']):
                    if str(itemSellID) not in list(players[id]['inv']):
                        players[id]['inv'].remove(str(itemBuyID))
                        updatePlayerAttributes(
                            id, players, itemsDB, itemBuyID, -1)
                        players[id]['inv'].append(str(itemSellID))
                        players[id]['wei'] = \
                            playerInventoryWeight(id, players, itemsDB)
                        updatePlayerAttributes(
                            id, players, itemsDB, itemSellID, 1)
                        if str(itemBuyID) not in list(thisNPC['inv']):
                            thisNPC['inv'].append(str(itemBuyID))
                        increaseAffinityBetweenPlayers(players, id, npcs,
                                                       nid, guildsDB)
                        increaseAffinityBetweenPlayers(npcs, nid, players,
                                                       id, guildsDB)
                        mud.sendMessage(
                            id, "<f220>" + thisNPC['name'] +
                            "<r> says: " + bestMatch + ".")
                        mud.sendMessage(
                            id, "<f220>" + thisNPC['name'] +
                            "<r> gives you " +
                            itemsDB[itemSellID]['article'] +
                            ' ' + itemsDB[itemSellID]['name'] + ".\n\n")
                    else:
                        mud.sendMessage(id, "<f220>" + thisNPC['name'] +
                                        "<r> says: I see you already have " +
                                        itemsDB[itemSellID]['article'] + ' ' +
                                        itemsDB[itemSellID]['name'] + ".\n\n")
                else:
                    if bestMatchAction == 'buy':
                        mud.sendMessage(
                            id, "<f220>" + thisNPC['name'] + "<r> says: " +
                            itemsDB[itemSellID]['article'] + ' ' +
                            itemsDB[itemSellID]['name'] + " costs " +
                            itemsDB[itemBuyID]['article'] + ' ' +
                            itemsDB[itemBuyID]['name'] + ".\n\n")
                    else:
                        mud.sendMessage(
                            id, "<f220>" + thisNPC['name'] +
                            "<r> says: I'll give you " +
                            itemsDB[itemSellID]['article'] +
                            ' ' + itemsDB[itemSellID]['name'] +
                            " in exchange for " +
                            itemsDB[itemBuyID]['article'] + ' ' +
                            itemsDB[itemBuyID]['name'] + ".\n\n")
        else:
            mud.sendMessage(
                id, "<f220>" + thisNPC['name'] + "<r> looks " +
                puzzledStr + ".\n\n")
            return True
    return False


def npcConversation(mud, npcs: {}, npcsDB: {}, players: {},
                    items: {}, itemsDB: {}, rooms: {},
                    id: int, nid: int, message,
                    characterClassDB: {}, sentimentDB: {},
                    guildsDB: {}, clouds: {}, racesDB: {},
                    itemHistory: {}, culturesDB: {}) -> None:
    """Conversation with an NPC
    This typically works by matching some words and then
    producing a corresponding response and/or action
    """
    thisNPC = npcs[nid]
    if len(thisNPC['familiarOf']) > 0:
        # is this a familiar of another player?
        if thisNPC['familiarOf'] != players[id]['name']:
            # familiar only talks to its assigned player
            mud.sendMessage(
                id, "<f220>" + thisNPC['name'] +
                "<r> ignores you.\n\n")
            return

    randValue = randint(0, 100)
    puzzledStr = 'puzzled'
    if randValue > 25:
        puzzledStr = 'confused'
    if randValue > 50:
        puzzledStr = 'baffled'
    if randValue > 75:
        puzzledStr = 'perplexed'

    if thisNPC.get('language'):
        if players[id]['speakLanguage'] not in thisNPC['language']:
            mud.sendMessage(
                id, "<f220>" + thisNPC['name'] + "<r> looks " +
                puzzledStr +
                ". They don't understand your language.\n\n")
            return

    bestMatch = ''
    bestMatchAction = ''
    bestMatchActionParam0 = ''
    bestMatchActionParam1 = ''
    imageName = None
    maxMatchCtr = 0

    conversationStates = players[id]['convstate']
    conversationNewState = ''

    # for each entry in the conversation list
    thisNPC = npcs[nid]
    for conv in thisNPC['conv']:
        # entry must contain matching words and resulting reply
        if len(conv) >= 2:
            # count the number of matches for this line
            matchCtr = \
                _conversationWordCount(message, conv[0], npcs,
                                       nid, conversationStates,
                                       players, rooms, id,
                                       culturesDB)
            # store the best match
            if matchCtr > maxMatchCtr:
                maxMatchCtr = matchCtr
                bestMatch = randomDescription(conv[1])
                bestMatchAction = ''
                bestMatchActionParam0 = ''
                bestMatchActionParam1 = ''
                conversationNewState = ''
                imageName = None
                if len(conv) >= 3:
                    idx = 2
                    ctr = 0
                    while idx < len(conv):
                        if ':' not in conv[idx]:
                            if ctr == 0:
                                bestMatchAction = conv[idx]
                            elif ctr == 1:
                                bestMatchActionParam0 = conv[idx]
                            elif ctr == 2:
                                bestMatchActionParam1 = conv[idx]
                            ctr += 1
                            idx += 1
                            continue
                        if conv[idx].lower().startswith('image:'):
                            imageName = \
                                conv[idx].lower().split(':')[1].strip()
                        elif conv[idx].lower().startswith('state:'):
                            conversationNewState = \
                                conv[idx].lower().split(':')[1].strip()
                        idx += 1

    if getSentiment(message, sentimentDB) >= 0:
        increaseAffinityBetweenPlayers(players, id, npcs, nid, guildsDB)
        increaseAffinityBetweenPlayers(npcs, nid, players, id, guildsDB)
    else:
        decreaseAffinityBetweenPlayers(players, id, npcs, nid, guildsDB)
        decreaseAffinityBetweenPlayers(npcs, nid, players, id, guildsDB)

    if len(bestMatch) > 0:
        # There were some word matches
        if imageName:
            imageFilename = 'images/events/' + imageName
            if os.path.isfile(imageFilename):
                with open(imageFilename, 'r') as imageFile:
                    mud.sendImage(id, '\n' + imageFile.read())

        if len(conversationNewState) > 0:
            # set the new conversation state with this npc
            conversationStates[thisNPC['name']] = conversationNewState

        if len(bestMatchAction) > 0:
            # give
            if _conversationGive(bestMatch, bestMatchAction,
                                 bestMatchActionParam0, players,
                                 id, mud, npcs, nid, itemsDB, puzzledStr,
                                 guildsDB):
                return

            # teach skill
            if _conversationSkill(bestMatch, bestMatchAction,
                                  bestMatchActionParam0,
                                  bestMatchActionParam1, players,
                                  id, mud, npcs, nid, itemsDB, puzzledStr,
                                  guildsDB):
                return

            # increase experience
            if _conversationExperience(bestMatch, bestMatchAction,
                                       bestMatchActionParam0,
                                       bestMatchActionParam1, players,
                                       id, mud, npcs, nid, itemsDB, puzzledStr,
                                       guildsDB):
                return

            # Join a guild
            if _conversationJoinGuild(bestMatch, bestMatchAction,
                                      bestMatchActionParam0,
                                      bestMatchActionParam1, players,
                                      id, mud, npcs, nid, itemsDB, puzzledStr,
                                      guildsDB):
                return

            # Switch familiar into different modes
            if _conversationFamiliarMode(bestMatch, bestMatchAction,
                                         bestMatchActionParam0,
                                         bestMatchActionParam1,
                                         players,
                                         id, mud, npcs, npcsDB, rooms,
                                         nid, items, itemsDB, puzzledStr):
                return

            # transport (free taxi)
            if _conversationTransport(bestMatchAction,
                                      bestMatchActionParam0, mud,
                                      id, players, bestMatch, npcs,
                                      nid, puzzledStr, guildsDB, rooms):
                return

            # taxi (exchange for an item)
            if _conversationTaxi(bestMatchAction,
                                 bestMatchActionParam0,
                                 bestMatchActionParam1, players,
                                 id, mud, bestMatch, npcs, nid,
                                 itemsDB, puzzledStr, guildsDB, rooms):
                return

            # give on a date
            if _conversationGiveOnDate(bestMatchAction,
                                       bestMatchActionParam0,
                                       bestMatchActionParam1,
                                       players, id, mud, npcs, nid,
                                       itemsDB, bestMatch, puzzledStr,
                                       guildsDB):
                return

            # sell
            if _conversationSell(bestMatch, bestMatchAction,
                                 bestMatchActionParam0,
                                 npcs, nid, mud, id, players,
                                 itemsDB, puzzledStr, guildsDB):
                return

            # buy or exchange
            if _conversationBuyOrExchange(bestMatch, bestMatchAction,
                                          bestMatchActionParam0,
                                          bestMatchActionParam1,
                                          npcs, nid, mud, id, players,
                                          itemsDB, puzzledStr, guildsDB):
                return

        if thisNPC['familiarOf'] == players[id]['name'] or \
           len(thisNPC['animalType']) > 0 or \
           '#' in bestMatch:
            # Talking with a familiar or animal can include
            # non-verbal responses so we remove 'says'
            mud.sendMessage(
                id, "<f220>" + thisNPC['name'] + "<r> " +
                bestMatch.replace('#', '').strip() + ".\n\n")
        else:
            mud.sendMessage(
                id, "<f220>" + thisNPC['name'] + "<r> says: " +
                bestMatch + ".\n\n")
    else:
        # No word matches
        mud.sendMessage(
            id, "<f220>" + thisNPC['name'] +
            "<r> looks " + puzzledStr + ".\n\n")
