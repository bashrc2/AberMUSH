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
import commentjson
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


def getSentiment(text, sentimentDB):
    """Returns a sentiment score for the given text
       which can be positive or negative
    """
    textLower = text.lower()
    sentiment = 0
    for word, value in sentimentDB.items():
        if word in textLower:
            sentiment = sentiment + value
    return sentiment


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


def increaseAffinityBetweenPlayers(players, id, npcs, p):
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
    recipientName = npcs[p]['name']
    if players[id]['affinity'].get(recipientName):
        players[id]['affinity'][recipientName] = \
            players[id]['affinity'][recipientName] + 1
    else:
        # set the affinity to an assumed average
        players[id]['affinity'][recipientName] = baselineAffinity(players, id)


def decreaseAffinityBetweenPlayers(players, id, npcs, p):
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
    recipientName = npcs[p]['name']
    if players[id]['affinity'].get(recipientName):
        players[id]['affinity'][recipientName] = \
            players[id]['affinity'][recipientName] - 1

        # Avoid zero values
        if players[id]['affinity'][recipientName] == 0:
            players[id]['affinity'][recipientName] = -1
    else:
        # set the affinity to an assumed average
        players[id]['affinity'][recipientName] = baselineAffinity(players, id)


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
            for prof in characterClassDB[template['characterClass']][str(
                    players[id]['lvl'])]:
                if prof not in players[id]['proficiencies']:
                    players[id]['proficiencies'].append(prof)


def stowHands(id, players, itemsDB, mud):
    if int(players[id]['clo_rhand']) > 0:
        itemID = int(players[id]['clo_rhand'])
        mud.send_message(
            id,
            'You stow <b234>' +
            itemsDB[itemID]['article'] +
            ' ' +
            itemsDB[itemID]['name'] +
            '<r>\n\n')
        players[id]['clo_rhand'] = 0

    if int(players[id]['clo_lhand']) > 0:
        itemID = int(players[id]['clo_lhand'])
        mud.send_message(
            id,
            'You stow <b234>' +
            itemsDB[itemID]['article'] +
            ' ' +
            itemsDB[itemID]['name'] +
            '<r>\n\n')
        players[id]['clo_lhand'] = 0


def sizeFromDescription(description):
    tinyEntity = (
        'tiny',
        'moth',
        'butterfly',
        'insect',
        'beetle',
        'ant',
        'bee',
        'wasp',
        'hornet',
        'mosquito',
        'lizard',
        'mouse',
        'rat',
        'crab',
        'roach',
        'snail',
        'slug',
        'hamster',
        'gerbil')
    smallEntity = (
        'small',
        'dog',
        'cat',
        'weasel',
        'owl',
        'hawk',
        'crow',
        'rook',
        'robbin',
        'penguin',
        'bird',
        'pidgeon',
        'wolf',
        'badger',
        'fox',
        'rat',
        'dwarf',
        'mini',
        'fish',
        'lobster',
        'koala',
        'goblin')
    largeEntity = (
        'large',
        'tiger',
        'lion',
        'tiger',
        'wolf',
        'leopard',
        'bear',
        'elk',
        'deer',
        'horse',
        'bison',
        'moose',
        'kanga',
        'zebra',
        'oxe',
        'beest',
        'troll',
        'taur')
    hugeEntity = ('huge', 'ogre', 'elephant', 'mastodon', 'giraffe', 'titan')
    gargantuanEntity = ('gargantuan', 'dragon', 'whale')
    smallerEntity = (
        'young',
        'child',
        'cub',
        'kitten',
        'puppy',
        'juvenile',
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
        players[id][attr] = players[id][attr] + \
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


def moveNPCs(npcs, players, mud, now, nid):
    """If movement is defined for an NPC this moves it around
    """
    if now > npcs[nid]['lastMoved'] + \
            int(npcs[nid]['moveDelay']) + npcs[nid]['randomizer']:
        # Move types:
        #   random, cycle, inverse cycle, patrol, follow

        moveTypeLower = npcs[nid]['moveType'].lower()

        followCycle = False
        if moveTypeLower.startswith('f'):
            if len(npcs[nid]['follow']) == 0:
                followCycle = True
                # Look for a player to follow
                for (pid, pl) in list(players.items()):
                    if npcs[nid]['room'] == players[pid]['room']:
                        # follow by name
                        #print(npcs[nid]['name'] + ' starts following ' + players[pid]['name'] + '\n')
                        npcs[nid]['follow'] = players[pid]['name']
                        followCycle = False
            if not followCycle:
                return

        if moveTypeLower.startswith(
                'c') or moveTypeLower.startswith('p') or followCycle:
            npcRoomIndex = 0
            npcRoomCurr = npcs[nid]['room']
            for npcRoom in npcs[nid]['path']:
                if npcRoom == npcRoomCurr:
                    npcRoomIndex = npcRoomIndex + 1
                    break
                npcRoomIndex = npcRoomIndex + 1
            if npcRoomIndex >= len(npcs[nid]['path']):
                if moveTypeLower.startswith('p'):
                    npcs[nid]['moveType'] = 'back'
                    npcRoomIndex = len(npcs[nid]['path']) - 1
                    if npcRoomIndex > 0:
                        npcRoomIndex = npcRoomIndex - 1
                else:
                    npcRoomIndex = 0
        else:
            if moveTypeLower.startswith('i') or moveTypeLower.startswith('b'):
                npcRoomIndex = 0
                npcRoomCurr = npcs[nid]['room']
                for npcRoom in npcs[nid]['path']:
                    if npcRoom == npcRoomCurr:
                        npcRoomIndex = npcRoomIndex - 1
                        break
                    npcRoomIndex = npcRoomIndex + 1
                if npcRoomIndex >= len(npcs[nid]['path']):
                    npcRoomIndex = len(npcs[nid]['path']) - 1
                if npcRoomIndex < 0:
                    if moveTypeLower.startswith('b'):
                        npcs[nid]['moveType'] = 'patrol'
                        npcRoomIndex = 0
                        if npcRoomIndex < len(npcs[nid]['path']) - 1:
                            npcRoomIndex = npcRoomIndex + 1
                    else:
                        npcRoomIndex = len(npcs[nid]['path']) - 1
            else:
                npcRoomIndex = randint(0, len(npcs[nid]['path']) - 1)

        for (pid, pl) in list(players.items()):
            if npcs[nid]['room'] == players[pid]['room']:
                mud.send_message(
                    pid,
                    '<f220>' +
                    npcs[nid]['name'] +
                    "<r> " +
                    randomDescription(npcs[nid]['outDescription']) +
                    "\n\n")
        rm = npcs[nid]['path'][npcRoomIndex]
        npcs[nid]['room'] = rm
        npcs[nid]['lastRoom'] = rm
        for (pid, pl) in list(players.items()):
            if npcs[nid]['room'] == players[pid]['room']:
                mud.send_message(
                    pid,
                    '<f220>' +
                    npcs[nid]['name'] +
                    "<r> " +
                    randomDescription(npcs[nid]['inDescription']) +
                    "\n\n")
        npcs[nid]['randomizer'] = randint(0, npcs[nid]['randomFactor'])
        npcs[nid]['lastMoved'] = now


def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')


def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

# Function to silently remove file


def silentRemove(filename):
    try:
        os.remove(filename)
    except OSError as e:  # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred

# Function to load all registered players from JSON files
# def loadPlayersDB(location = "./players", forceLowercase = True):


def loadPlayersDB(
        location=str(
            Config.get(
                'Players',
                'Location')),
        forceLowercase=True):
    DB = {}
    playerFiles = [i for i in os.listdir(
        location) if os.path.splitext(i)[1] == ".player"]
    for f in playerFiles:
        with open(os.path.join(location, f)) as file_object:
                #playersDB[f] = file_object.read()
            DB[f] = commentjson.load(file_object)

    if forceLowercase is True:
        out = {}
        for key, value in DB.items():
            out[key.lower()] = value

        return(out)
    else:
        return(DB)

    # for i in playersDB:
        #print(i, playersDB[i])

# Function used for loggin messages to stdout and a disk file


def log(content, type):
    #logfile = './dum.log'
    logfile = str(Config.get('Logs', 'ServerLog'))
    print(str(time.strftime("%d/%m/%Y") + " " +
              time.strftime("%I:%M:%S") + " [" + type + "] " + content))
    if os.path.exists(logfile):
        log = open(logfile, 'a')
    else:
        log = open(logfile, 'w')
    log.write(str(time.strftime("%d/%m/%Y") + " " + \
              time.strftime("%I:%M:%S") + " [" + type + "] " + content) + '\n')
    log.close()

# Function for returning a first available key value for appending a new
# element to a dictionary


def getFreeKey(itemsDict, start=None):
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

# Function for returning a first available room key value for appending a
# room element to a dictionary


def getFreeRoomKey(rooms):
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

# Function for adding events to event scheduler


def addToScheduler(eventID, targetID, scheduler, database):
    if isinstance(eventID, int):
        for item in database:
            if int(item[0]) == eventID:
                scheduler[getFreeKey(scheduler)] = {'time': int(time.time(
                ) + int(item[1])), 'target': int(targetID), 'type': item[2], 'body': item[3]}
    elif isinstance(eventID, str):
        item = eventID.split('|')
        scheduler[getFreeKey(scheduler)] = {'time': int(time.time(
        ) + int(item[0])), 'target': int(targetID), 'type': item[1], 'body': item[2]}


def loadPlayer(name, db):
    try:
        # with open(path + name + ".player", "r") as read_file:
            #dict = commentjson.load(read_file)
            # return(dict)
        #print(str(db[name.lower() + ".player"]))
        return(db[name.lower() + ".player"])
    except Exception:
        pass


def savePlayer(
        player,
        masterDB,
        savePassword,
        path=str(
            Config.get(
                'Players',
                'Location')) +
        "/"):
    # print(path)
    DB = loadPlayersDB(forceLowercase=False)
    for p in DB:
        if (player['name'] + ".player").lower() == p.lower():
            #print("found the file")
            # print(p)
            with open(path + p, "r") as read_file:
                temp = commentjson.load(read_file)
            # print(temp)
            silentRemove(path + player['name'] + ".player")
            #print("removed file")
            newPlayer = deepcopy(temp)
            # print(newPlayer)
            newPlayer['pwd'] = temp['pwd']
            for key in newPlayer:
                if key != "pwd" or savePassword:
                    # print(key)
                    newPlayer[key] = player[key]

            # print(newPlayer)
            #print("Saving player state")
            with open(path + player['name'] + ".player", 'w') as fp:
                commentjson.dump(newPlayer, fp)
            #print("Updating playerd DB")
            masterDB = loadPlayersDB()
            # print(masterDB)

# State Save Function


def saveState(player, masterDB, savePassword):
    tempVar = 0
    savePlayer(player, masterDB, savePassword)
    #masterDB = loadPlayersDB()


def saveUniverse(rooms, npcsDB, npcs, itemsDB, items, envDB, env):
    # save rooms
    with open("universe.json", 'w') as fp:
        commentjson.dump(rooms, fp, indent=4, sort_keys=True)

    # save items
    with open("universe_items.json", 'w') as fp:
        commentjson.dump(items, fp, indent=4, sort_keys=True)

    # save itemsDB
    with open("universe_itemsdb.json", 'w') as fp:
        commentjson.dump(itemsDB, fp, indent=4, sort_keys=True)

    # save environment actors
    with open("universe_actorsdb.json", 'w') as fp:
        commentjson.dump(envDB, fp, indent=4, sort_keys=True)

    # save environment actors
    with open("universe_actors.json", 'w') as fp:
        commentjson.dump(env, fp, indent=4, sort_keys=True)

    # save npcs
    with open("universe_npcs.json", 'w') as fp:
        commentjson.dump(npcs, fp, indent=4, sort_keys=True)

    # save npcsDB
    with open("universe_npcsdb.json", 'w') as fp:
        commentjson.dump(npcsDB, fp, indent=4, sort_keys=True)


def str2bool(v):
    return v.lower() in ("yes", "true", "True", "t", "1")


def sendToChannel(sender, channel, message, channels):
        #print("Im in!")
    channels[getFreeKey(channels)] = {"channel": str(
        channel), "message": str(message), "sender": str(sender)}
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
        if players[id]['prepareSpellProgress'] >= players[id]['prepareSpellTime']:
            spellName = players[id]['prepareSpell']
            players[id]['preparedSpells'][spellName] = 1
            players[id]['spellSlots'][spellName] = 1
            players[id]['prepareSpell'] = ""
            players[id]['prepareSpellProgress'] = 0
            players[id]['prepareSpellTime'] = 0
            mud.send_message(
                id,
                "You prepared the spell <f220>" +
                spellName +
                "<r>\n\n")
        else:
            players[id]['prepareSpellProgress'] = players[id]['prepareSpellProgress'] + 1
