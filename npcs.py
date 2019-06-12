__filename__ = "npcs.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from functions import log
from functions import moveNPCs
from functions import playerInventoryWeight
from functions import updatePlayerAttributes
from functions import increaseAffinityBetweenPlayers
from functions import decreaseAffinityBetweenPlayers
from functions import getSentiment
from random import randint
from copy import deepcopy
from familiar import getFamiliarModes

import time

def npcsRest(npcs):
    """Rest restores hit points of NPCs
    """
    for p in npcs:
        if npcs[p]['hp'] < npcs[p]['hpMax'] + npcs[p]['tempHitPoints']:
            if randint(0, 100) > 97:
                npcs[p]['hp'] = npcs[p]['hp'] + 1
        else:
            npcs[p]['hp'] = npcs[p]['hpMax'] + npcs[p]['tempHitPoints']
            npcs[p]['restRequired'] = 0


def npcRespawns(npcs):
    """Respawns inactive NPCs
    """
    for (nid, pl) in list(npcs.items()):
        if npcs[nid]['whenDied'] is not None and \
           int(time.time()) >= npcs[nid]['whenDied'] + npcs[nid]['respawn']:
            if len(npcs[nid]['familiarOf']) == 0:
                npcs[nid]['whenDied'] = None
                #npcs[nid]['room'] = npcsTemplate[nid]['room']
                npcs[nid]['room'] = npcs[nid]['lastRoom']
                log("respawning " +
                    npcs[nid]['name'] +
                    " with " +
                    str(npcs[nid]['hp']) +
                    " hit points", "info")


def runNPCs(
        mud,
        npcs,
        players,
        fights,
        corpses,
        scriptedEventsDB,
        itemsDB,
        npcsTemplate):
    """Updates all NPCs
    """
    for (nid, pl) in list(npcs.items()):
                # Check if any player is in the same room, then send a random
                # message to them
        now = int(time.time())
        if npcs[nid]['vocabulary'][0]:
            if now > npcs[nid]['timeTalked'] + \
                    npcs[nid]['talkDelay'] + npcs[nid]['randomizer']:
                rnd = randint(0, len(npcs[nid]['vocabulary']) - 1)
                while rnd is npcs[nid]['lastSaid']:
                    rnd = randint(0, len(npcs[nid]['vocabulary']) - 1)
                for (pid, pl) in list(players.items()):
                    if npcs[nid]['room'] == players[pid]['room']:
                        if len(npcs[nid]['vocabulary']) > 1:
                            #mud.send_message(pid, npcs[nid]['vocabulary'][rnd])
                            msg = '<f220>' + npcs[nid]['name'] + '<r> says: <f86>' + \
                                npcs[nid]['vocabulary'][rnd] + "\n"
                            mud.send_message(pid, msg)
                            npcs[nid]['randomizer'] = randint(
                                0, npcs[nid]['randomFactor'])
                            npcs[nid]['lastSaid'] = rnd
                            npcs[nid]['timeTalked'] = now
                        else:
                            #mud.send_message(pid, npcs[nid]['vocabulary'][0])
                            msg = '<f220>' + npcs[nid]['name'] + '<r> says: <f86>' + \
                                npcs[nid]['vocabulary'][0] + "\n"
                            mud.send_message(pid, msg)
                            npcs[nid]['randomizer'] = randint(
                                0, npcs[nid]['randomFactor'])
                            npcs[nid]['timeTalked'] = now

        # Iterate through fights and see if anyone is attacking an NPC -
        # if so, attack him too if not in combat (TODO: and isAggressive =
        # true)
        isInFight = False
        for (fid, pl) in list(fights.items()):
            if fights[fid]['s2id'] == nid and \
               npcs[fights[fid]['s2id']]['isInCombat'] == 1 and \
               fights[fid]['s1type'] == 'pc' and \
               fights[fid]['retaliated'] == 0:
                    # print('player is attacking npc')
                    # BETA: set las combat action to now when attacking a
                    # player
                npcs[fights[fid]['s2id']]['lastCombatAction'] = int(
                    time.time())
                fights[fid]['retaliated'] = 1
                npcs[fights[fid]['s2id']]['isInCombat'] = 1
                fights[len(fights)] = {'s1': npcs[fights[fid]['s2id']]['name'],
                                       's2': players[fights[fid]['s1id']]['name'],
                                       's1id': nid, 's2id': fights[fid]['s1id'],
                                       's1type': 'npc', 's2type': 'pc', 'retaliated': 1}
                isInFight = True
            elif fights[fid]['s2id'] == nid and \
                    npcs[fights[fid]['s2id']]['isInCombat'] == 1 and \
                    fights[fid]['s1type'] == 'npc' and \
                    fights[fid]['retaliated'] == 0:
                # print('npc is attacking npc')
                # BETA: set las combat action to now when attacking a player
                npcs[fights[fid]['s2id']]['lastCombatAction'] = int(
                    time.time())
                fights[fid]['retaliated'] = 1
                npcs[fights[fid]['s2id']]['isInCombat'] = 1
                fights[len(fights)] = {'s1': npcs[fights[fid]['s2id']]['name'],
                                       's2': players[fights[fid]['s1id']]['name'],
                                       's1id': nid, 's2id': fights[fid]['s1id'],
                                       's1type': 'npc', 's2type': 'npc', 'retaliated': 1}
                isInFight = True

        # NPC moves to the next location
        now = int(time.time())
        if isInFight == False and len(npcs[nid]['path']) > 0:
            moveNPCs(npcs, players, mud, now, nid)

        # Check if NPC is still alive, if not, remove from room and create a corpse,
        # set isInCombat to 0, set whenDied to now and remove any fights NPC
        # was involved in
        if npcs[nid]['hp'] <= 0:
            npcs[nid]['isInCombat'] = 0
            npcs[nid]['lastRoom'] = npcs[nid]['room']
            npcs[nid]['whenDied'] = int(time.time())
            # detach familiar from player
            for pl in players:
                if players[pl]['familiar']==int(nid):
                    players[pl]['familiar']=-1
            fightsCopy = deepcopy(fights)
            for (fight, pl) in fightsCopy.items():
                if fightsCopy[fight]['s1id'] == nid or \
                   fightsCopy[fight]['s2id'] == nid:
                    del fights[fight]
                    corpses[len(corpses)] = {'room': npcs[nid]['room'],
                                             'name': str(npcs[nid]['name'] + '`s corpse'),
                                             'inv': npcs[nid]['inv'],
                                             'died': int(time.time()),
                                             'TTL': npcs[nid]['corpseTTL'], 'owner': 1}
            for (pid, pl) in list(players.items()):
                if players[pid]['authenticated'] is not None:
                    if players[pid]['authenticated'] is not None and \
                       players[pid]['room'] == npcs[nid]['room']:
                        mud.send_message(
                            pid, "<f220>{}<r> <f88>has been killed.".format(
                                npcs[nid]['name']) + "\n")
                        npcs[nid]['lastRoom'] = npcs[nid]['room']
                        npcs[nid]['room'] = None
                        npcs[nid]['hp'] = npcsTemplate[nid]['hp']

            # Drop NPC loot on the floor
            droppedItems = []
            for i in npcs[nid]['inv']:
                # print("Dropping item " + str(i[0]) + " likelihood of " + str(i[1]) + "%")
                if randint(0, 100) < int(i[1]):
                    addToScheduler("0|spawnItem|" +
                                   str(i[0]) +
                                   ";" +
                                   str(npcs[nid]['lastRoom']) +
                                   ";0;0", -
                                   1, eventSchedule, scriptedEventsDB)
                    # print("Dropped!" + str(itemsDB[int(i[0])]['name']))
                    droppedItems.append(str(itemsDB[int(i[0])]['name']))

            # Inform other players in the room what items got dropped on NPC
            # death
            if len(droppedItems) > 0:
                for p in players:
                    if players[p]['room'] == npcs[nid]['lastRoom']:
                        mud.send_message(
                            p,
                            "Right before <f220>" +
                            str(
                                npcs[nid]['name']) +
                            "<r>'s lifeless body collapsed to the floor, " +
                            "it had dropped the following items: <f220>{}".format(
                                ', '.join(droppedItems)) +
                            "\n")


def conversationState(word, conversation_states, nid, npcs, match_ctr):
    """Is the conversations with this npc in the given state?
       Returns True if the conversation is in the given state
       Also returns True if subsequent words can also be matched
       and the current word match counter
    """
    if word.lower().startswith('state:'):
        requiredState = word.lower().split(':')[1].strip()
        if npcs[nid]['name'] in conversation_states:
            if conversation_states[npcs[nid]['name']] != requiredState:
                return False, False, match_ctr
            return True, True, match_ctr + 1
    return False, True, match_ctr


def conversationCondition(
        word,
        conversation_states,
        nid,
        npcs,
        match_ctr,
        players,
        id):
    conditionType = ''
    if '>' in word.lower():
        conditionType = '>'
    if '<' in word.lower():
        conditionType = '<'
    if '=' in word.lower():
        conditionType = conditionType + '='

    if len(conditionType) == 0:
        return False, True, match_ctr

    varStr = word.lower().split(conditionType)[0].strip()
    currValue = -99999
    targetValue = None

    if varStr == 'hp' or varStr == 'hitpoints':
        currValue = players[id]['hp']
    if varStr == 'hpPercent' or varStr == 'hitpointspercent':
        currValue = int(players[id]['hp'] * 100 / players[id]['hp'])
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
    if varStr == 'race':
        currValue = players[id]['race'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '='
    if varStr == 'characterclass':
        currValue = players[id]['characterClass'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '='
    if varStr == 'enemy':
        currValue = players[id]['enemy'].lower()
        targetValue = word.lower().split(conditionType)[1].strip()
        conditionType = '='
    if varStr == 'affinity':
        if npcs[nid]['affinity'].get(players[id]['name']):
            currValue = npcs[nid]['affinity'][players[id]['name']]
        else:
            currValue = 0

    if targetValue is None:
        targetValue = int(word.lower().split(conditionType)[1].strip())

    if currValue == -99999:
        return False, True, match_ctr

    if conditionType == '>':
        if currValue <= targetValue:
            return False, False, match_ctr

    if conditionType == '<':
        if currValue >= targetValue:
            return False, False, match_ctr

    if conditionType == '=':
        if currValue != targetValue:
            return False, False, match_ctr

    if conditionType == '>=':
        if currValue < targetValue:
            return False, False, match_ctr

    if conditionType == '<=':
        if currValue > targetValue:
            return False, False, match_ctr

    return True, True, match_ctr + 1


def conversationWordCount(
        message,
        words_list,
        npcs,
        nid,
        conversation_states,
        players,
        id):
    """Returns the number of matched words in the message.
       This is a 'bag of words/conditions' type of approach.
    """
    match_ctr = 0
    for word_match in words_list:
        # Is the conversation required to be in a certain state?
        matched, continueMatching, match_ctr = conversationState(
            word_match, conversation_states, nid, npcs, match_ctr)

        if not continueMatching:
            break

        if not matched:
            # match conditions such as "strength < 10"
            matched, continueMatching, match_ctr = conversationCondition(
                word_match, conversation_states, nid, npcs, match_ctr, players, id)

            if not continueMatching:
                break

            if not matched:
                if word_match.lower() in message:
                    match_ctr = match_ctr + 1
    return match_ctr


def conversationGive(
        best_match,
        best_match_action,
        best_match_action_param0,
        players,
        id,
        mud,
        npcs,
        nid,
        itemsDB,
        puzzledStr):
    """Conversation in which an NPC gives something to you
    """
    if best_match_action == 'give' or \
       best_match_action == 'gift':
        if len(best_match_action_param0) > 0:
            itemID = int(best_match_action_param0)
            if itemID not in list(players[id]['inv']):
                players[id]['inv'].append(str(itemID))
                updatePlayerAttributes(id, players, itemsDB, itemID, 1)
                players[id]['wei'] = playerInventoryWeight(
                    id, players, itemsDB)
                increaseAffinityBetweenPlayers(players, id, npcs, nid)
                increaseAffinityBetweenPlayers(npcs, nid, players, id)
                mud.send_message(
                    id,
                    "<f220>" +
                    npcs[nid]['name'] +
                    "<r> says: " +
                    best_match +
                    ".")
                mud.send_message(
                    id,
                    "<f220>" +
                    npcs[nid]['name'] +
                    "<r> gives you " +
                    itemsDB[itemID]['article'] +
                    ' ' +
                    itemsDB[itemID]['name'] +
                    ".\n\n")
                return True
        mud.send_message(
            id,
            "<f220>" +
            npcs[nid]['name'] +
            "<r> looks " +
            puzzledStr +
            ".\n\n")
        return True
    return False


def conversationSkill(
        best_match,
        best_match_action,
        best_match_action_param0,
        best_match_action_param1,
        players,
        id,
        mud,
        npcs,
        nid,
        itemsDB,
        puzzledStr):
    """Conversation in which an NPC gives or alters a skill
    """
    if best_match_action == 'skill' or \
       best_match_action == 'teach':
        if len(best_match_action_param0) > 0 and \
           len(best_match_action_param1) > 0:
            newSkill = best_match_action_param0.lower()
            skillValueStr = best_match_action_param1
            if not players[id].get(newSkill):
                log(newSkill + ' skill does not exist in player instance', 'info')
                return False
            if '+' in skillValueStr:
                # increase skill
                players[id][newSkill] = players[id][newSkill] + \
                    int(skillValueStr.replace('+', ''))
            else:
                # decrease skill
                if '-' in skillValueStr:
                    players[id][newSkill] = players[id][newSkill] - \
                        int(skillValueStr.replace('-', ''))
                else:
                    # set skill to absolute value
                    players[id][newSkill] = players[id][newSkill] + \
                        int(skillValueStr)

            increaseAffinityBetweenPlayers(players, id, npcs, nid)
            increaseAffinityBetweenPlayers(npcs, nid, players, id)

            mud.send_message(
                id,
                "<f220>" +
                npcs[nid]['name'] +
                "<r> says: " +
                best_match +
                ".\n\n")
            return True
        else:
            mud.send_message(
                id,
                "<f220>" +
                npcs[nid]['name'] +
                "<r> looks " +
                puzzledStr +
                ".\n\n")
            return False
    return False


def conversationExperience(
        best_match,
        best_match_action,
        best_match_action_param0,
        best_match_action_param1,
        players,
        id,
        mud,
        npcs,
        nid,
        itemsDB,
        puzzledStr):
    """Conversation in which an NPC increases your experience
    """
    if best_match_action == 'exp' or \
       best_match_action == 'experience':
        if len(best_match_action_param0) > 0:
            expValue = int(best_match_action_param0)
            players[id]['exp'] = players[id]['exp'] + expValue
            increaseAffinityBetweenPlayers(players, id, npcs, nid)
            increaseAffinityBetweenPlayers(npcs, nid, players, id)
            return True
        else:
            mud.send_message(
                id,
                "<f220>" +
                npcs[nid]['name'] +
                "<r> looks " +
                puzzledStr +
                ".\n\n")
            return False
    return False

def conversationFamiliarMode(
        best_match,
        best_match_action,
        best_match_action_param0,
        players,
        id,
        mud,
        npcs,
        nid,
        itemsDB,
        puzzledStr):
    """Switches the mode of a familiar
    """
    if best_match_action == 'familiar':
        if len(best_match_action_param0) > 0:
            if npcs[nid]['familiarOf']==players[id]['name']:
                mode=best_match_action_param0.lower().strip()
                if mode in getFamiliarModes:
                    npcs[nid]['familiarMode']=mode
                    return True
            else:
                mud.send_message(
                    id,
                    npcs[nid]['name'] + " is not your familiar.\n\n")
        else:
            mud.send_message(
                id,
                "<f220>" +
                npcs[nid]['name'] +
                "<r> looks " +
                puzzledStr +
                ".\n\n")
            return False
    return False

def conversationTransport(
        best_match_action,
        best_match_action_param0,
        mud,
        id,
        players,
        best_match,
        npcs,
        nid,
        puzzledStr):
    """Conversation in which an NPC transports you to some location
    """
    if best_match_action == 'transport' or \
       best_match_action == 'ride' or \
       best_match_action == 'teleport':
        if len(best_match_action_param0) > 0:
            roomID = best_match_action_param0
            mud.send_message(id, best_match)
            messageToPlayersInRoom(
                mud, players, id, '<f32>{}<r> leaves.'.format(
                    players[id]['name']) + "\n\n")
            players[id]['room'] = roomID
            npcs[nid]['room'] = roomID
            increaseAffinityBetweenPlayers(players, id, npcs, nid)
            increaseAffinityBetweenPlayers(npcs, nid, players, id)
            messageToPlayersInRoom(
                mud, players, id, '<f32>{}<r> arrives.'.format(
                    players[id]['name']) + "\n\n")
            mud.send_message(
                id,
                "You are in " +
                rooms[roomID]['name'] +
                "\n\n")
            return True
        mud.send_message(
            id,
            "<f220>" +
            npcs[nid]['name'] +
            "<r> looks " +
            puzzledStr +
            ".\n\n")
        return True
    return False


def conversationTaxi(
        best_match_action,
        best_match_action_param0,
        best_match_action_param1,
        players,
        id,
        mud,
        best_match,
        npcs,
        nid,
        itemsDB,
        puzzledStr):
    """Conversation in which an NPC transports you to some location in exchange for payment/barter
    """
    if best_match_action == 'taxi':
        if len(best_match_action_param0) > 0 and len(
                best_match_action_param1) > 0:
            roomID = best_match_action_param0
            itemBuyID = int(best_match_action_param1)
            if str(itemBuyID) in list(players[id]['inv']):
                players[id]['inv'].remove(str(itemBuyID))

                increaseAffinityBetweenPlayers(players, id, npcs, nid)
                increaseAffinityBetweenPlayers(npcs, nid, players, id)
                mud.send_message(id, best_match)
                messageToPlayersInRoom(
                    mud, players, id, '<f32>{}<r> leaves.'.format(
                        players[id]['name']) + "\n\n")
                players[id]['room'] = roomID
                npcs[nid]['room'] = roomID
                messageToPlayersInRoom(
                    mud, players, id, '<f32>{}<r> arrives.'.format(
                        players[id]['name']) + "\n\n")
                mud.send_message(
                    id,
                    "You are in " +
                    rooms[roomID]['name'] +
                    "\n\n")
                return True
            else:
                mud.send_message(
                    id,
                    "<f220>" +
                    npcs[nid]['name'] +
                    "<r> says: Give me " +
                    itemsDB[itemBuyID]['article'] +
                    ' ' +
                    itemsDB[itemBuyID]['name'] +
                    ".\n\n")
                return True
        mud.send_message(
            id,
            "<f220>" +
            npcs[nid]['name'] +
            "<r> looks " +
            puzzledStr +
            ".\n\n")
        return True
    return False


def conversationGiveOnDate(
        best_match_action,
        best_match_action_param0,
        best_match_action_param1,
        players,
        id,
        mud,
        npcs,
        nid,
        itemsDB,
        best_match,
        puzzledStr):
    """Conversation in which an NPC gives something to you on a particular date of the year
       eg. Some festival or holiday
    """
    if best_match_action == 'giveondate' or \
       best_match_action == 'giftondate':
        if len(best_match_action_param0) > 0:
            itemID = int(best_match_action_param0)
            if itemID not in list(players[id]['inv']):
                if '/' in best_match_action_param1:
                    dayNumber = int(best_match_action_param1.split('/')[0])
                    if dayNumber == int(
                            datetime.datetime.utcnow().strftime("%d")):
                        monthNumber = int(
                            best_match_action_param1.split('/')[1])
                        if monthNumber == int(
                                datetime.datetime.utcnow().strftime("%m")):
                            players[id]['inv'].append(str(itemID))
                            players[id]['wei'] = playerInventoryWeight(
                                id, players, itemsDB)
                            updatePlayerAttributes(
                                id, players, itemsDB, itemID, 1)
                            increaseAffinityBetweenPlayers(
                                players, id, npcs, nid)
                            increaseAffinityBetweenPlayers(
                                npcs, nid, players, id)
                            mud.send_message(
                                id, "<f220>" + npcs[nid]['name'] + "<r> says: " + best_match + ".")
                            mud.send_message(
                                id,
                                "<f220>" +
                                npcs[nid]['name'] +
                                "<r> gives you " +
                                itemsDB[itemID]['article'] +
                                ' ' +
                                itemsDB[itemID]['name'] +
                                ".\n\n")
                            return True
        mud.send_message(
            id,
            "<f220>" +
            npcs[nid]['name'] +
            "<r> looks " +
            puzzledStr +
            ".\n\n")
        return True
    return False


def conversationBuyOrExchange(
        best_match,
        best_match_action,
        best_match_action_param0,
        best_match_action_param1,
        npcs,
        nid,
        mud,
        id,
        players,
        itemsDB,
        puzzledStr):
    """Conversation in which an NPC exchanges/swaps some item with you or in which you buy some item from them
    """
    if best_match_action == 'buy' or \
       best_match_action == 'exchange' or \
       best_match_action == 'barter' or \
       best_match_action == 'trade':
        if len(best_match_action_param0) > 0 and len(
                best_match_action_param1) > 0:
            itemBuyID = int(best_match_action_param0)
            itemSellID = int(best_match_action_param1)
            if str(itemSellID) not in list(npcs[nid]['inv']):
                if best_match_action == 'buy':
                    mud.send_message(
                        id,
                        "<f220>" +
                        npcs[nid]['name'] +
                        "<r> says: I don't have any of those to sell.\n\n")
                else:
                    mud.send_message(
                        id,
                        "<f220>" +
                        npcs[nid]['name'] +
                        "<r> says: I don't have any of those to trade.\n\n")
            else:
                if str(itemBuyID) in list(players[id]['inv']):
                    if str(itemSellID) not in list(players[id]['inv']):
                        players[id]['inv'].remove(str(itemBuyID))
                        updatePlayerAttributes(
                            id, players, itemsDB, itemBuyID, -1)
                        players[id]['inv'].append(str(itemSellID))
                        players[id]['wei'] = playerInventoryWeight(
                            id, players, itemsDB)
                        updatePlayerAttributes(
                            id, players, itemsDB, itemSellID, 1)
                        if str(itemBuyID) not in list(npcs[nid]['inv']):
                            npcs[nid]['inv'].append(str(itemBuyID))
                        increaseAffinityBetweenPlayers(players, id, npcs, nid)
                        increaseAffinityBetweenPlayers(npcs, nid, players, id)
                        mud.send_message(
                            id,
                            "<f220>" +
                            npcs[nid]['name'] +
                            "<r> says: " +
                            best_match +
                            ".")
                        mud.send_message(
                            id,
                            "<f220>" +
                            npcs[nid]['name'] +
                            "<r> gives you " +
                            itemsDB[itemID]['article'] +
                            ' ' +
                            itemsDB[itemID]['name'] +
                            ".\n\n")
                    else:
                        mud.send_message(id, "<f220>" + npcs[nid]['name'] +
                                         "<r> says: I see you already have " +
                                         itemsDB[itemSellID]['article'] + ' ' +
                                         itemsDB[itemSellID]['name'] + ".\n\n")
                else:
                    if best_match_action == 'buy':
                        mud.send_message(
                            id,
                            "<f220>" +
                            npcs[nid]['name'] +
                            "<r> says: " +
                            itemsDB[itemSellID]['article'] +
                            ' ' +
                            itemsDB[itemSellID]['name'] +
                            " costs " +
                            itemsDB[itemBuyID]['article'] +
                            ' ' +
                            itemsDB[itemBuyID]['name'] +
                            ".\n\n")
                    else:
                        mud.send_message(
                            id,
                            "<f220>" +
                            npcs[nid]['name'] +
                            "<r> says: I'll give you " +
                            itemsDB[itemSellID]['article'] +
                            ' ' +
                            itemsDB[itemSellID]['name'] +
                            " in exchange for " +
                            itemsDB[itemBuyID]['article'] +
                            ' ' +
                            itemsDB[itemBuyID]['name'] +
                            ".\n\n")
        else:
            mud.send_message(
                id,
                "<f220>" +
                npcs[nid]['name'] +
                "<r> looks " +
                puzzledStr +
                ".\n\n")
            return True
    return False


def npcConversation(
        mud,
        npcs,
        players,
        itemsDB,
        rooms,
        id,
        nid,
        message,
        characterClassDB,
        sentimentDB):
    """Conversation with an NPC
       This typically works by matching some words and then producing a corresponding response and/or action
    """

    if len(npcs[nid]['familiarOf'])>0:
        # is this a familiar of another player?
        if npcs[nid]['familiarOf'] != players[id]['name']:
            # familiar only talks to its assigned player
            mud.send_message(
                id,
                "<f220>" +
                npcs[nid]['name'] +
                "<r> ignores you.\n\n")
            return

    puzzledStr = 'puzzled'
    if randint(0, 1) == 1:
        puzzledStr = 'confused'

    if npcs[nid].get('language'):
        if players[id]['speakLanguage'] not in npcs[nid]['language']:
            mud.send_message(
                id,
                "<f220>" +
                npcs[nid]['name'] +
                "<r> looks " +
                puzzledStr +
                ". They don't understand your language.\n\n")
            return

    best_match = ''
    best_match_action = ''
    best_match_action_param0 = ''
    best_match_action_param1 = ''
    max_match_ctr = 0

    conversation_states = players[id]['convstate']
    conversation_new_state = ''

    # for each entry in the conversation list
    for conv in npcs[nid]['conv']:
            # entry must contain matching words and resulting reply
        if len(conv) >= 2:
                        # count the number of matches for this line
            match_ctr = conversationWordCount(
                message, conv[0], npcs, nid, conversation_states, players, id)
            # store the best match
            if match_ctr > max_match_ctr:
                max_match_ctr = match_ctr
                best_match = conv[1]
                best_match_action = ''
                best_match_action_param0 = ''
                best_match_action_param1 = ''
                currIndex = 2
                conversation_new_state = ''
                if len(conv) >= 3:
                    if conv[2].lower().startswith('state:'):
                        conversation_new_state = conv[2].lower().split(':')[
                            1].strip()
                        if len(conv) >= 4:
                            best_match_action = conv[3]
                        if len(conv) >= 5:
                            best_match_action_param0 = conv[4]
                        if len(conv) >= 6:
                            best_match_action_param1 = conv[5]
                    else:
                        best_match_action = conv[2]
                        if len(conv) >= 4:
                            best_match_action_param0 = conv[3]
                        if len(conv) >= 5:
                            best_match_action_param1 = conv[4]

    if getSentiment(message, sentimentDB) >= 0:
        increaseAffinityBetweenPlayers(players, id, npcs, nid)
        increaseAffinityBetweenPlayers(npcs, nid, players, id)
    else:
        decreaseAffinityBetweenPlayers(players, id, npcs, nid)
        decreaseAffinityBetweenPlayers(npcs, nid, players, id)

    if len(best_match) > 0:
        # There were some word matches

        if len(conversation_new_state) > 0:
                    # set the new conversation state with this npc
            conversation_states[npcs[nid]['name']] = conversation_new_state

        if len(best_match_action) > 0:
            # give
            if conversationGive(best_match, best_match_action,
                                best_match_action_param0, players,
                                id, mud, npcs, nid, itemsDB, puzzledStr):
                return

            # teach skill
            if conversationSkill(best_match, best_match_action,
                                 best_match_action_param0,
                                 best_match_action_param1, players,
                                 id, mud, npcs, nid, itemsDB, puzzledStr):
                return

            # increase experience
            if conversationExperience(best_match, best_match_action,
                                      best_match_action_param0,
                                      best_match_action_param1, players,
                                      id, mud, npcs, nid, itemsDB, puzzledStr,
                                      characterClassDB):
                return

            if conversationFamiliarMode(best_match, best_match_action,
                                        best_match_action_param0,
                                        players,
                                        id, mud, npcs, nid, itemsDB, puzzledStr,
                                        characterClassDB):
                return

            # transport (free taxi)
            if conversationTransport(best_match_action,
                                     best_match_action_param0, mud,
                                     id, players, best_match, npcs,
                                     nid, puzzledStr):
                return

            # taxi (exchange for an item)
            if conversationTaxi(best_match_action,
                                best_match_action_param0,
                                best_match_action_param1, players,
                                id, mud, best_match, npcs, nid,
                                itemsDB, puzzledStr):
                return

            # give on a date
            if conversationGiveOnDate(best_match_action,
                                      best_match_action_param0,
                                      best_match_action_param1,
                                      players, id, mud, npcs, nid,
                                      itemsDB, best_match, puzzledStr):
                return

            # buy or exchange
            if conversationBuyOrExchange(best_match, best_match_action,
                                         best_match_action_param0,
                                         best_match_action_param1,
                                         npcs, nid, mud, id, players,
                                         itemsDB, puzzledStr):
                return

        if npcs[nid]['familiarOf'] == players[id]['name'] or \
           len(npcs[nid]['animalType'])>0:
            # Talking with a familiar or animal can include
            # non-verbal responses so we remove 'says'
            mud.send_message(
                id,
                "<f220>" +
                npcs[nid]['name'] +
                "<r> " +
                best_match +
                ".\n\n")
        else:
            mud.send_message(
                id,
                "<f220>" +
                npcs[nid]['name'] +
                "<r> says: " +
                best_match +
                ".\n\n")
    else:
        # No word matches
        mud.send_message(
            id,
            "<f220>" +
            npcs[nid]['name'] +
            "<r> looks " +
            puzzledStr +
            ".\n\n")
