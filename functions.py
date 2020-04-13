__filename__ = "functions.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

import time
import os
import json
import errno
from copy import deepcopy
import configparser
import hashlib
import binascii
from random import randint

# example of config file usage
# print(str(Config.get('Database', 'Hostname')))
Config = configparser.ConfigParser()
Config.read('config.ini')

wearLocation = ('head', 'neck', 'lwrist', 'rwrist', 'larm', 'rarm',
                'chest', 'feet', 'lfinger', 'rfinger', 'back',
                'lleg', 'rleg')


def TimeStringToSec(durationStr: str) -> int:
    """Converts a description of a duration such as '1 hour'
       into a number of seconds
    """
    if ' ' not in durationStr:
        return 1
    dur = durationStr.lower().split(' ')
    if dur[1].startswith('s'):
        return int(dur[0])
    if dur[1].startswith('min'):
        return int(dur[0]) * 60
    if dur[1].startswith('hour') or dur[1].startswith('hr'):
        return int(dur[0]) * 60 * 60
    if dur[1].startswith('day'):
        return int(dur[0]) * 60 * 60 * 24
    return 1


def getSentiment(text: str, sentimentDB: {}) -> int:
    """Returns a sentiment score for the given text
       which can be positive or negative
    """
    textLower = text.lower()
    sentiment = 0
    for word, value in sentimentDB.items():
        if word in textLower:
            sentiment = sentiment + value
    return sentiment


def getGuildSentiment(players: {}, id, npcs: {}, p, guilds: {}) -> int:
    """Returns the sentiment of the guild of the first player
    towards the second
    """
    if not players[id].get('guild'):
        return 0
    if not players[id].get('guildRole'):
        return 0
    guildName = players[id]['guild']
    if not guilds.get(guildName):
        return 0
    otherPlayerName = npcs[p]['name']
    if not guilds[guildName]['affinity'].get(otherPlayerName):
        return 0
    # NOTE: this could be adjusted by the strength of affinity
    # between the player and the guild, but for now it's just hardcoded
    return int(guilds[guildName]['affinity'][otherPlayerName] / 2)


def baselineAffinity(players, id):
    """Returns the average affinity value for the player
    """
    averageAffinity = 0
    ctr = 0
    for name, value in players[id]['affinity'].items():
        averageAffinity = averageAffinity + value
        ctr += 1

    if ctr > 0:
        averageAffinity = int(averageAffinity / ctr)

    if averageAffinity == 0:
        averageAffinity = 1
    return averageAffinity


def increaseAffinityBetweenPlayers(players: {}, id, npcs: {},
                                   p, guilds: {}) -> None:
    """Increases the affinity level between two players
    """
    # You can't gain affinity with low intelligence creatures
    # by talking to them
    if players[id]['int'] < 2:
        return
    # Animals you can't gain affinity with by talking
    if players[id].get('animalType'):
        if len(players[id]['animalType']) > 0:
            return

    max_affinity = 10

    recipientName = npcs[p]['name']
    if players[id]['affinity'].get(recipientName):
        if players[id]['affinity'][recipientName] < max_affinity:
            players[id]['affinity'][recipientName] += 1
    else:
        # set the affinity to an assumed average
        players[id]['affinity'][recipientName] = baselineAffinity(players, id)

    # adjust guild affinity
    if players[id].get('guild') and players[id].get('guildRole'):
        guildName = players[id]['guild']
        if guilds.get(guildName):
            guild = guilds[guildName]
            if guild['affinity'].get(recipientName):
                if guild['affinity'][recipientName] < max_affinity:
                    guild['affinity'][recipientName] += 1
            else:
                guild['affinity'][recipientName] = \
                    baselineAffinity(players, id)


def decreaseAffinityBetweenPlayers(players: {}, id, npcs: {},
                                   p, guilds: {}) -> None:
    """Decreases the affinity level between two players
    """
    # You can't gain affinity with low intelligence creatures
    # by talking to them
    if players[id]['int'] < 2:
        return
    # Animals you can't gain affinity with by talking
    if players[id].get('animalType'):
        if len(players[id]['animalType']) > 0:
            return

    min_affinity = -10

    recipientName = npcs[p]['name']
    if players[id]['affinity'].get(recipientName):
        if players[id]['affinity'][recipientName] > min_affinity:
            players[id]['affinity'][recipientName] -= 1

        # Avoid zero values
        if players[id]['affinity'][recipientName] == 0:
            players[id]['affinity'][recipientName] = -1
    else:
        # set the affinity to an assumed average
        players[id]['affinity'][recipientName] = baselineAffinity(players, id)

    # adjust guild affinity
    if players[id].get('guild') and players[id].get('guildRole'):
        guildName = players[id]['guild']
        if guilds.get(guildName):
            guild = guilds[guildName]
            if guild['affinity'].get(recipientName):
                if guild['affinity'][recipientName] > min_affinity:
                    guild['affinity'][recipientName] -= 1
                # Avoid zero values
                if guild['affinity'][recipientName] == 0:
                    guild['affinity'][recipientName] = -1
            else:
                guild['affinity'][recipientName] = \
                    baselineAffinity(players, id)


def randomDescription(descriptionList):
    if '|' in descriptionList:
        descList = descriptionList.split('|')
        return descList[randint(0, len(descList) - 1)]
    return descriptionList


def levelUp(id, players, characterClassDB, increment):
    level = players[id]['lvl']
    if level < 20:
        players[id]['exp'] = players[id]['exp'] + increment
        if players[id]['exp'] > (level + 1) * 1000:
            players[id]['hpMax'] = players[id]['hpMax'] + randint(1, 9)
            players[id]['lvl'] = level + 1
            # remove any existing spell lists
            for prof in players[id]['proficiencies']:
                if isinstance(prof, list):
                    players[id]['proficiencies'].remove(prof)
            # update proficiencies
            idx = players[id]['characterClass']
            for prof in characterClassDB[idx][str(players[id]['lvl'])]:
                if prof not in players[id]['proficiencies']:
                    players[id]['proficiencies'].append(prof)


def stowHands(id, players: {}, itemsDB: {}, mud):
    if int(players[id]['clo_rhand']) > 0:
        itemID = int(players[id]['clo_rhand'])
        mud.send_message(
            id, 'You stow <b234>' +
            itemsDB[itemID]['article'] +
            ' ' +
            itemsDB[itemID]['name'] +
            '<r>\n\n')
        players[id]['clo_rhand'] = 0

    if int(players[id]['clo_lhand']) > 0:
        itemID = int(players[id]['clo_lhand'])
        mud.send_message(
            id, 'You stow <b234>' +
            itemsDB[itemID]['article'] +
            ' ' +
            itemsDB[itemID]['name'] +
            '<r>\n\n')
        players[id]['clo_lhand'] = 0


def sizeFromDescription(description: str):
    tinyEntity = ('tiny', 'moth', 'butterfly', 'insect', 'beetle', 'ant',
                  'bee', 'wasp', 'hornet', 'mosquito', 'lizard', 'mouse',
                  'rat', 'crab', 'roach', 'snail', 'slug', 'hamster',
                  'gerbil')
    smallEntity = ('small', 'dog', 'cat', 'weasel', 'otter', 'owl', 'hawk',
                   'crow', 'rook', 'robin', 'penguin', 'bird', 'pidgeon',
                   'wolf', 'badger', 'fox', 'rat', 'dwarf', 'mini', 'fish',
                   'lobster', 'koala', 'goblin')
    largeEntity = ('large', 'tiger', 'lion', 'tiger', 'wolf', 'leopard',
                   'bear', 'elk', 'deer', 'horse', 'bison', 'moose',
                   'kanga', 'zebra', 'oxe', 'beest', 'troll', 'taur')
    hugeEntity = ('huge', 'ogre', 'elephant', 'mastodon', 'giraffe', 'titan')
    gargantuanEntity = ('gargantuan', 'dragon', 'whale')
    smallerEntity = ('young', 'child', 'cub', 'kitten', 'puppy', 'juvenile',
                     'kid')
    description2 = description.lower()
    size = 2
    for e in tinyEntity:
        if e in description2:
            size = 0
            break
    for e in smallEntity:
        if e in description2:
            size = 1
            break
    for e in largeEntity:
        if e in description2:
            size = 3
            break
    for e in hugeEntity:
        if e in description2:
            size = 4
            break
    for e in gargantuanEntity:
        if e in description2:
            size = 5
            break
    if size > 0:
        for e in smallerEntity:
            if e in description2:
                size = size - 1
                break

    return size


def updatePlayerAttributes(id, players, itemsDB, itemID, mult):
    playerAttributes = ('luc', 'per', 'cha', 'int', 'cool', 'exp')
    for attr in playerAttributes:
        players[id][attr] = \
            players[id][attr] + \
            (mult * itemsDB[itemID]['mod_' + attr])
    # experience returns to zero
    itemsDB[itemID]['mod_exp'] = 0


def playerInventoryWeight(id, players, itemsDB):
    """Returns the total weight of a player's inventory
    """
    if len(list(players[id]['inv'])) == 0:
        return 0

    weight = 0
    for i in list(players[id]['inv']):
        weight = weight + itemsDB[int(i)]['weight']

    return weight


def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = \
        hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                            salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')


def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = \
        hashlib.pbkdf2_hmac('sha512',
                            provided_password.encode('utf-8'),
                            salt.encode('ascii'), 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


def silentRemove(filename: str):
    """Function to silently remove file
    """
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def loadPlayersDB(location=str(Config.get('Players', 'Location')),
                  forceLowercase=True):
    """Function to load all registered players from JSON files
    """
    DB = {}
    playerFiles = [i for i in os.listdir(
        location) if os.path.splitext(i)[1] == ".player"]
    for f in playerFiles:
        with open(os.path.join(location, f)) as file_object:
            DB[f] = json.loads(file_object.read())

    if forceLowercase is True:
        out = {}
        for key, value in DB.items():
            out[key.lower()] = value

        return(out)
    else:
        return(DB)

    # for i in playersDB:
        # print(i, playersDB[i])


def log(content, type):
    """Function used for logging messages to stdout and a disk file
    """
    # logfile = './dum.log'
    logfile = str(Config.get('Logs', 'ServerLog'))
    print(str(time.strftime("%d/%m/%Y") + " " +
              time.strftime("%I:%M:%S") + " [" + type + "] " + content))
    if os.path.exists(logfile):
        log = open(logfile, 'a')
    else:
        log = open(logfile, 'w')
    log.write(str(time.strftime("%d/%m/%Y") + " " +
              time.strftime("%I:%M:%S") + " [" + type + "] " + content) + '\n')
    log.close()


def getFreeKey(itemsDict, start=None):
    """Function for returning a first available key value for appending a new
    element to a dictionary
    """
    if start is None:
        try:
            for x in range(0, len(itemsDict) + 1):
                if len(itemsDict[x]) > 0:
                    pass
        except Exception:
            pass
        return(x)
    else:
        found = False
        while found is False:
            if start in itemsDict:
                start += 1
            else:
                found = True
        return(start)


def getFreeRoomKey(rooms):
    """Function for returning a first available room key value for appending a
    room element to a dictionary
    """
    maxRoomID = -1
    for rmkey in rooms.keys():
        roomIDStr = rmkey.replace('$', '').replace('rid=', '')
        if len(roomIDStr) == 0:
            continue

        roomID = int(roomIDStr)
        if roomID > maxRoomID:
            maxRoomID = roomID

    if maxRoomID > -1:
        return '$rid=' + str(maxRoomID + 1) + '$'
    return ''


def addToScheduler(eventID, targetID, scheduler, database):
    """Function for adding events to event scheduler
    """
    if isinstance(eventID, int):
        for item in database:
            if int(item[0]) == eventID:
                scheduler[getFreeKey(scheduler)] = {
                    'time': int(time.time() + int(item[1])),
                    'target': int(targetID),
                    'type': item[2],
                    'body': item[3]
                }
    elif isinstance(eventID, str):
        item = eventID.split('|')
        scheduler[getFreeKey(scheduler)] = {
            'time': int(time.time() + int(item[0])),
            'target': int(targetID),
            'type': item[1],
            'body': item[2]
        }


def loadPlayer(name, db):
    try:
        # with open(path + name + ".player", "r") as read_file:
        #     dict = json.loads(read_file.read())
        #     return(dict)
        # print(str(db[name.lower() + ".player"]))
        return(db[name.lower() + ".player"])
    except Exception:
        pass


def savePlayer(player, masterDB, savePassword,
               path=str(Config.get('Players', 'Location')) + "/"):
    DB = loadPlayersDB(forceLowercase=False)
    for p in DB:
        if (player['name'] + ".player").lower() == p.lower():
            with open(path + p, "r") as read_file:
                temp = json.loads(read_file.read())
            silentRemove(path + player['name'] + ".player")
            newPlayer = deepcopy(temp)
            newPlayer['pwd'] = temp['pwd']
            for key in newPlayer:
                if key != "pwd" or savePassword:
                    newPlayer[key] = player[key]

            with open(path + player['name'] + ".player", 'w') as fp:
                fp.write(json.dumps(newPlayer))
            loadPlayersDB()


def saveState(player, masterDB, savePassword):
    savePlayer(player, masterDB, savePassword)
    # masterDB = loadPlayersDB()


def saveUniverse(rooms: {}, npcsDB: {}, npcs: {},
                 itemsDB: {}, items: {},
                 envDB: {}, env: {}, guildsDB: {}):
    # save rooms
    if os.path.isfile('universe.json'):
        os.rename('universe.json', 'universe2.json')
    with open("universe.json", 'w') as fp:
        fp.write(json.dumps(rooms))

    # save items
    if os.path.isfile('universe_items.json'):
        os.rename('universe_items.json', 'universe_items2.json')
    with open("universe_items.json", 'w') as fp:
        fp.write(json.dumps(items))

    # save itemsDB
    if os.path.isfile('universe_itemsdb.json'):
        os.rename('universe_itemsdb.json', 'universe_itemsdb2.json')
    with open("universe_itemsdb.json", 'w') as fp:
        fp.write(json.dumps(itemsDB))

    # save environment actors
    if os.path.isfile('universe_actorsdb.json'):
        os.rename('universe_actorsdb.json', 'universe_actorsdb2.json')
    with open("universe_actorsdb.json", 'w') as fp:
        fp.write(json.dumps(envDB))

    # save environment actors
    if os.path.isfile('universe_actors.json'):
        os.rename('universe_actors.json', 'universe_actors2.json')
    with open("universe_actors.json", 'w') as fp:
        fp.write(json.dumps(env))

    # save npcs
    if os.path.isfile('universe_npcs.json'):
        os.rename('universe_npcs.json', 'universe_npcs2.json')
    with open("universe_npcs.json", 'w') as fp:
        fp.write(json.dumps(npcs))

    # save npcsDB
    if os.path.isfile('universe_npcsdb.json'):
        os.rename('universe_npcsdb.json', 'universe_npcsdb2.json')
    with open("universe_npcsdb.json", 'w') as fp:
        fp.write(json.dumps(npcsDB))


def str2bool(v):
    return v.lower() in ("yes", "true", "True", "t", "1")


def sendToChannel(sender, channel, message, channels):
    # print("Im in!")
    channels[getFreeKey(channels)] = {
        "channel": str(channel),
        "message": str(message),
        "sender": str(sender)}
    # print(channels)


def loadBlocklist(filename, blocklist):
    if not os.path.isfile(filename):
        return False

    blocklist.clear()

    blockfile = open(filename, "r")

    for line in blockfile:
        blockedstr = line.lower().strip()
        if ',' in blockedstr:
            blockedlst = blockedstr.lower().strip().split(',')
            for blockedstr2 in blockedlst:
                blockedstr2 = blockedstr2.lower().strip()
                if blockedstr2 not in blocklist:
                    blocklist.append(blockedstr2)
        else:
            if blockedstr not in blocklist:
                blocklist.append(blockedstr)

    blockfile.close()
    return True


def saveBlocklist(filename, blocklist):
    blockfile = open(filename, "w")
    for blockedstr in blocklist:
        blockfile.write(blockedstr + '\n')
    blockfile.close()


def setRace(template, racesDB, name):
    """Set the player race
    """
    template['speakLanguage'] = racesDB[name]['language'][0]
    template['language'].clear()
    template['language'].append(racesDB[name]['language'][0])
    template['race'] = name
    template['str'] = racesDB[name]['str']
    template['siz'] = racesDB[name]['siz']
    template['per'] = racesDB[name]['per']
    template['endu'] = racesDB[name]['endu']
    template['cha'] = racesDB[name]['cha']
    template['int'] = racesDB[name]['int']
    template['agi'] = racesDB[name]['agi']
    template['luc'] = racesDB[name]['luc']
    template['cool'] = racesDB[name]['cool']
    template['ref'] = racesDB[name]['ref']


def prepareSpells(mud, id, players):
    """Player prepares spells, called once per second
    """
    if len(players[id]['prepareSpell']) == 0:
        return

    if players[id]['prepareSpellTime'] > 0:
        if players[id]['prepareSpellProgress'] >= \
           players[id]['prepareSpellTime']:
            spellName = players[id]['prepareSpell']
            players[id]['preparedSpells'][spellName] = 1
            players[id]['spellSlots'][spellName] = 1
            players[id]['prepareSpell'] = ""
            players[id]['prepareSpellProgress'] = 0
            players[id]['prepareSpellTime'] = 0
            mud.send_message(
                id, "You prepared the spell <f220>" +
                spellName + "<r>\n\n")
        else:
            players[id]['prepareSpellProgress'] = \
                players[id]['prepareSpellProgress'] + 1


def isWearing(id, players: {}, itemList: []) -> bool:
    """Given a list of possible item IDs is the player wearing any of them?
    """
    if not itemList:
        return False

    for itemID in itemList:
        if not str(itemID).isdigit():
            print('isWearing: ' + str(itemID) + ' is not a digit')
            continue
        itemID = int(itemID)
        for locn in wearLocation:
            if int(players[id]['clo_'+locn]) == itemID:
                return True
        if int(players[id]['clo_lhand']) == itemID or \
           int(players[id]['clo_rhand']) == itemID:
            return True
    return False


def playerIsVisible(mud, observerId: int, observers: {},
                    otherPlayerId: int, others: {}) -> bool:
    """Is the other player visible to the observer?
    """
    observerId = int(observerId)
    otherPlayerId = int(otherPlayerId)
    if not others[otherPlayerId].get('visibleWhenWearing'):
        return True
    if others[otherPlayerId].get('visibleWhenWearing'):
        if isWearing(observerId, observers,
                     others[otherPlayerId]['visibleWhenWearing']):
            return True
    return False


def messageToPlayersInRoom(mud, players, id, msg):
    # go through all the players in the game
    for (pid, pl) in list(players.items()):
        # if player is in the same room and isn't the player
        # sending the command
        if players[pid]['room'] == players[id]['room'] and \
           pid != id:
            if playerIsVisible(mud, pid, players, id, players):
                mud.send_message(pid, msg)
