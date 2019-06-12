__filename__ = "abermush.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski", "Mark Frimston"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from cmsg import cmsg

from functions import getFreeKey
from functions import log
from functions import saveState
from functions import saveUniverse
from functions import addToScheduler
from functions import loadPlayer
from functions import savePlayer
from functions import loadPlayersDB
from functions import sendToChannel
from functions import hash_password
from functions import verify_password
from functions import loadBlocklist
from functions import setRace

from events import evaluateEvent

from commands import runCommand
from combat import runFights
from combat import playersRest
from combat import updateTemporaryHitPoints
from combat import updateTemporaryIncapacitation
from playerconnections import runPlayerConnections
from playerconnections import disconnectIdlePlayers
from npcs import npcRespawns
from npcs import runNPCs
from npcs import npcsRest
from npcs import familiarRecall
from reaper import removeCorpses
from reaper import runDeaths
from scheduler import runSchedule
from scheduler import runEnvironment
from scheduler import runMessages
from environment import assignTerrainDifficulty
from environment import assignCoordinates
from environment import plotClouds
from environment import generateCloud
from environment import getTemperature

import datetime
import time

# import the MUD server class
from mudserver import MudServer

# import random generator library
from random import randint
import random

# import the deepcopy library
from copy import deepcopy

# import config parser
import configparser

# import the json parser
import commentjson

# import glob module
import glob

log("", "Server Boot")

log("", "Loading configuration file")

# load the configuration file
Config = configparser.ConfigParser()
Config.read('config.ini')
# example of config file usage
# print(str(Config.get('Database', 'Hostname')))

# Declare rooms dictionary
rooms = {}

# Declare NPC database dict
npcsDB = {}

# Declare NPCs dictionary
npcs = {}

# Declare NPCs master (template) dict
npcsTemplate = {}

# Declare env dict
env = {}

# Declare env database dict
envDB = {}

# Declare fights dict
fights = {}

# Declare corpses dict
corpses = {}

# Declare items dict
itemsDB = {}

# Declare itemsInWorld dict
itemsInWorld = {}

# Declare scriptedEventsDB list
scriptedEventsDB = []

# Declare eventSchedule dict
eventSchedule = {}

# Declare channels message queue dictionary
channels = {}

# Specify allowe player idle time
allowedPlayerIdle = int(Config.get('World', 'IdleTimeBeforeDisconnect'))

print("Loading sentiment...")

with open(str(Config.get('Sentiment', 'Definition')), "r") as read_file:
    sentimentDB = commentjson.load(read_file)

log("Sentiment loaded: " + str(len(sentimentDB)), "info")

print("Loading rooms...")

# Loading rooms
if os.path.isfile("universe.json"):
    with open("universe.json", "r") as read_file:
        rooms = commentjson.load(read_file)
    # Clear room coordinates
    for rm in rooms:
        rooms[rm]['coords'] = []
else:
    with open(str(Config.get('Rooms', 'Definition')), "r") as read_file:
        rooms = commentjson.load(read_file)

log("Rooms loaded: " + str(len(rooms)), "info")

maxTerrainDifficulty = assignTerrainDifficulty(rooms)

log("Terrain difficulty calculated. max=" + str(maxTerrainDifficulty), "info")

mapArea = assignCoordinates(rooms)

log("Map coordinates:" + str(mapArea), "info")

# Loading environment actors
if os.path.isfile("universe_actors.json"):
    with open("universe_actors.json", "r") as read_file:
        env = commentjson.load(read_file)
if os.path.isfile("universe_actorsdb.json"):
    with open("universe_actorsdb.json", "r") as read_file:
        envDB = commentjson.load(read_file)
else:
    with open(str(Config.get('Actors', 'Definition')), "r") as read_file:
        envDB = commentjson.load(read_file)

output_dict = {}
for key, value in envDB.items():
    output_dict[int(key)] = value

envDB = output_dict

for k in envDB:
    if not os.path.isfile("universe_actors.json"):
        envDB[k]['vocabulary'] = envDB[k]['vocabulary'].split('|')
    for v in envDB[k]:
        if not(v == "name" or
               v == "room" or
               v == "vocabulary"):
            envDB[k][v] = int(envDB[k][v])


log("Environment Actors loaded: " + str(len(envDB)), "info")

# List ENV dictionary for debugging purposes
# print(env)
# print("Test:")
# for x in env:
# print (x)
# for y in env[x]:
# print (y,':',env[x][y])

print("Loading NPCs...")
if os.path.isfile("universe_npcs.json"):
    with open("universe_npcs.json", "r") as read_file:
        npcs = commentjson.load(read_file)

if os.path.isfile("universe_npcsdb.json"):
    with open("universe_npcsdb.json", "r") as read_file:
        npcsDB = commentjson.load(read_file)
else:
    with open(str(Config.get('NPCs', 'Definition')), "r") as read_file:
        npcsDB = commentjson.load(read_file)

output_dict = {}
for key, value in npcsDB.items():
    output_dict[int(key)] = value

npcsDB = output_dict

for k in npcsDB:
    npcsDB[k]['lastRoom'] = None
    npcsDB[k]['whenDied'] = None
    if not os.path.isfile("universe_npcs.json"):
        npcsDB[k]['vocabulary'] = npcsDB[k]['vocabulary'].split('|')
    for v in npcsDB[k]:
        if not(v == "name" or
               v == "room" or
               v == "inv" or
               v == "speakLanguage" or
               v == "language" or
               v == "race" or
               v == "familiarOf" or
               v == "familiarType" or
               v == "familiarMode" or
               v == "animalType" or
               v == "archetype" or
               v == "characterClass" or
               v == "proficiencies" or
               v == "fightingStyle" or
               v == "enemy" or
               v == "affinity" or
               v == "preparedSpells" or
               v == "spellSlots" or
               v == "conv" or
               v == "path" or
               v == "follow" or
               v == "moveDelay" or
               v == "moveType" or
               v == "vocabulary" or
               v == "inDescription" or
               v == "outDescription" or
               v == "lookDescription" or
               v == "lastRoom" or
               v == "loot" or
               v == "frozenDescription" or
               v == "bodyType" or
               v == "whenDied"):
            npcsDB[k][v] = int(npcsDB[k][v])

log("NPCs loaded: " + str(len(npcsDB)), "info")

with open(str(Config.get('Races', 'Definition')), "r") as read_file:
    racesDB = commentjson.load(read_file)

log("Races loaded: " + str(len(racesDB)), "info")

with open(str(Config.get('CharacterClass', 'Definition')), "r") as read_file:
    characterClassDB = commentjson.load(read_file)

log("Character Classes loaded: " + str(len(characterClassDB)), "info")

with open(str(Config.get('Spells', 'Definition')), "r") as read_file:
    spellsDB = commentjson.load(read_file)

log("Spells loaded: " + str(len(spellsDB)), "info")

# List NPC dictionary for debugging purposes
#print(" ")
# print("LIVE:")
# print(npcsDB)
#print(" ")
# for x in npcsDB:
#print (x)
# for y in npcsDB[x]:
#print (y,':',npcsDB[x][y])

# Loading Items
if os.path.isfile("universe_items.json"):
    with open("universe_items.json", "r") as read_file:
        itemsInWorld = commentjson.load(read_file)

if os.path.isfile("universe_itemsdb.json"):
    with open("universe_itemsdb.json", "r") as read_file:
        itemsDB = commentjson.load(read_file)
else:
    with open(str(Config.get('Items', 'Definition')), "r") as read_file:
        itemsDB = commentjson.load(read_file)

output_dict = {}
for key, value in itemsDB.items():
    output_dict[int(key)] = value

itemsDB = output_dict

for k in itemsDB:
    for v in itemsDB[k]:
        if not(v == "name" or
               v == "long_description" or
               v == "short_description" or
               v == "open_description" or
               v == "open_failed_description" or
               v == "close_description" or
               v == "room" or
               v == "language" or
               v == "state" or
               v == "type" or
               v == "writeWithItems" or
               v == "written" or
               v == "written_description" or
               v == "contains" or
               v == "exit" or
               v == "exitName" or
               v == "article"):
            itemsDB[k][v] = int(itemsDB[k][v])

log("Items loaded: " + str(len(itemsDB)), "info")

# List items for debugging purposes
# print("TEST:")
# for x in itemsDB:
# print (x)
# for y in itemsDB[x]:
# print(y,':',itemsDB[x][y])
# print(itemsDB)

# Load scripted event declarations from disk
files = glob.glob(str(Config.get('Events', 'Location')) + "/*.event")
counter = 0
for file in files:
    counter += 1
    f = open(file, 'r')
    # print(file)
    lines = [line.rstrip() for line in f.readlines()[2:]]
    for l in lines[1:]:
        if len(l) > 0:
            scriptedEventsDB.append([lines[0]] + l.split('|'))
            # print(lines)
            f.close()

log("Scripted Events loaded: " + str(counter), "info")

# Load registered players DB
playersDB = loadPlayersDB()
log("Registered player accounts loaded: " + str(len(playersDB)), "info")

# Execute Reserved Event 1 and 2
# Using -1 for target since no players can be targeted with an event at
# this time
log("Executing boot time events", "info")
addToScheduler(1, -1, eventSchedule, scriptedEventsDB)
addToScheduler(2, -1, eventSchedule, scriptedEventsDB)
addToScheduler(3, -1, eventSchedule, scriptedEventsDB)

# Declare number of seconds to elapse between State Saves
# A State Save takes values held in memory and updates the database
# at set intervals to achieve player state persistence
stateSaveInterval = int(Config.get('World', 'StateSaveInterval'))
log("State Save interval: " + str(stateSaveInterval) + " seconds", "info")

# Set last state save to 'now' on server boot
lastStateSave = int(time.time())

# Deepcopy npcs fetched from a database into a master template
npcsTemplate = deepcopy(npcs)

# List items in world for debugging purposes
# for x in itemsInWorld:
# print (x)
# for y in itemsInWorld[x]:
# print(y,':',itemsInWorld[x][y])

# stores the players in the game
players = {}

# list of players
playerList = []

# start the server
mud = MudServer()

# weather
currHour = datetime.datetime.utcnow().hour
currMin = datetime.datetime.utcnow().minute
daysSinceEpoch = (
    datetime.datetime.utcnow() -
    datetime.datetime(
        1970,
        1,
        1)).days
dayMins = (currHour * 60) + currMin
random.seed((daysSinceEpoch * 1440) + dayMins)
lastWeatherUpdate = int(time.time())
weatherUpdateInterval = 120
clouds = {}
cloudGrid = {}
tileSize = 2
temperature = getTemperature()
r1 = random.Random((daysSinceEpoch * 1440) + dayMins)
windDirection = int(r1.random() * 359)
windDirection = generateCloud(
    r1,
    rooms,
    mapArea,
    clouds,
    cloudGrid,
    tileSize,
    windDirection)
log("Clouds generated. Wind direction " + str(windDirection), "info")

lastTempHitPointsUpdate = int(time.time())
tempHitPointsUpdateInterval = 60

lastRestUpdate = int(time.time())

blocklist = []
if loadBlocklist("blocked.txt", blocklist):
    log("Blocklist loaded", "info")

# main game loop. We loop forever (i.e. until the program is terminated)
while True:
    # print(int(time.time()))

    now = int(time.time())
    if now >= lastTempHitPointsUpdate + tempHitPointsUpdateInterval:
        lastTempHitPointsUpdate = now
        updateTemporaryHitPoints(mud, players, False)
        updateTemporaryHitPoints(mud, npcs, True)
        updateTemporaryIncapacitation(mud, players, False)
        updateTemporaryIncapacitation(mud, npcs, True)

    now = int(time.time())
    if now >= lastWeatherUpdate + weatherUpdateInterval:
        lastWeatherUpdate = now
        temperature = getTemperature()
        #print("Temperature " + str(temperature))
        windDirection = generateCloud(
            r1,
            rooms,
            mapArea,
            clouds,
            cloudGrid,
            tileSize,
            windDirection)
        #plotClouds(rooms, mapArea, clouds, temperature)

    # update player list
    playerList = []
    for p in players:
        if players[p]['name'] is not None and players[p]['authenticated'] is not None:
            if players[p]['name'] not in playerList:
                playerList.append(players[p]['name'])

    # pause for 1/5 of a second on each loop, so that we don't constantly
    # use 100% CPU time
    time.sleep(0.1)
    # print(eventSchedule)

    # 'update' must be called in the loop to keep the game running and give
    # us up-to-date information
    mud.update()

    # Check if State Save is due and execute it if required
    now = int(time.time())
    if int(now >= lastStateSave + stateSaveInterval):
        sendToChannel("Server", "system", "Saving server state...", channels)
        # State Save logic Start
        for (pid, pl) in list(players.items()):
            if players[pid]['authenticated'] is not None:
                # print('Saving' + players[pid]['name'])
                saveState(players[pid], playersDB, False)
                playersDB = loadPlayersDB()
                # State Save logic End
                lastStateSave = now
        saveUniverse(rooms, npcsDB, npcs, itemsDB, items, envDB, env)
        lastStateSave = now

    # Handle Player Deaths
    runDeaths(mud, players, corpses, fights, eventSchedule, scriptedEventsDB)

    # Handle Fights
    runFights(
        mud,
        players,
        npcs,
        fights,
        itemsInWorld,
        itemsDB,
        rooms,
        maxTerrainDifficulty,
        mapArea,
        clouds,
        racesDB,
        characterClassDB)

    # Iterate through NPCs, check if its time to talk, then check if anyone is
    # attacking it
    runNPCs(
        mud,
        npcs,
        players,
        fights,
        corpses,
        scriptedEventsDB,
        itemsDB,
        npcsTemplate)

    runEnvironment(mud, players, env)

    removeCorpses(corpses)

    npcRespawns(npcs)

    runSchedule(
        mud,
        eventSchedule,
        players,
        npcs,
        itemsInWorld,
        env,
        npcsDB,
        envDB)

    disconnectIdlePlayers(mud, players, allowedPlayerIdle)

    npcsTemplate = deepcopy(npcs)

    runMessages(mud, channels, players)

    channels.clear()

    runPlayerConnections(mud, id, players, playersDB, fights, Config)

    # rest restores hp and allows spell learning
    now = int(time.time())
    if now >= lastRestUpdate + 1:
        lastRestUpdate = now
        playersRest(mud, players)
        npcsRest(npcs)

    # go through any new commands sent from players
    for (id, command, params) in mud.get_commands():
        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in players:
            continue

        # print(str(players[id]['authenticated']))
        if command.lower(
        ) == "startover" and players[id]['exAttribute0'] is not None and players[id]['authenticated'] is None:
            if not os.path.isfile(".disableRegistrations"):
                players[id]['idleStart'] = int(time.time())
                mud.send_message(
                    id, "<f220>Ok, Starting character creation from the beginning!\n")
                players[id]['exAttribute0'] = 1000

        if command.lower(
        ) == "exit" and players[id]['exAttribute0'] is not None and players[id]['authenticated'] is None:
            players[id]['idleStart'] = int(time.time())
            mud.send_message(id, "<f220>Ok, leaving the character creation.\n")
            players[id]['exAttribute0'] = None
            mud.send_message(
                id,
                "<f15>What is your username?<r>\n<f246>Type '<f253>new<r><f246>' to create a character.\n\n")
            log("Client ID: " + str(id) +
                " has aborted character creation.", "info")
            break

        if players[id]['exAttribute0'] == 1000:
            players[id]['idleStart'] = int(time.time())
            # First step of char creation
            mud.send_message(id, "<f220>\nWhat is going to be your name?\n\n")
            for c in mud._clients:
                # print(str(mud._clients[c].address))
                pass
            players[id]['exAttribute0'] = 1001
            break

        if players[id]['exAttribute0'] == 1001:
            players[id]['idleStart'] = int(time.time())
            taken = False
            for p in playersDB:
                if playersDB[p]['name'].lower() == command.lower():
                    mud.send_message(
                        id, "\n<f220>This character name is already taken!")
                    mud.send_message(id, "Press ENTER to continue...\n\n")
                    taken = True
                    break
            if not taken:
                players[id]['exAttribute1'] = command
                mud.send_message(
                    id, "<f220>Now what would you like your password to be?\n\n")
                players[id]['exAttribute0'] = 1002
                break
            else:
                players[id]['idleStart'] = int(time.time())
                players[id]['exAttribute0'] = 1000
                break

        if players[id]['exAttribute0'] == 1002:
            # store the password
            mud.send_message(id, "<f220>\nOk, got that.\n")
            players[id]['exAttribute2'] = command

            players[id]['idleStart'] = int(time.time())
            mud.send_message(id, "<f220>\nSelect your character race:\n\n")
            ctr = 0
            typesStr = '  '
            for (name, p) in list(racesDB.items()):
                if ctr > 0:
                    typesStr = typesStr + ', <f220>' + name + '<r>'
                else:
                    typesStr = typesStr + '<f220>' + name + '<r>'
                ctr = ctr + 1
                if ctr > 7:
                    typesStr = typesStr + '\n  '
                    ctr = 0
            mud.send_message(id, typesStr + '\n\n')
            players[id]['exAttribute0'] = 1003
            break

        if players[id]['exAttribute0'] == 1003:
            players[id]['idleStart'] = int(time.time())
            selectedRace = command.lower().strip()
            if not racesDB.get(selectedRace):
                mud.send_message(
                    id, "<f220>\nUnrecognized character race.<r>\n\n")
                players[id]['exAttribute0'] = 1000
                mud.send_message(
                    id,
                    "<f15>What is your username?<r>\n<f246>Type '<f253>new<r><f246>' to create a character.\n\n")
                break

            if not os.path.isfile("witches"):
                command = 'witch'
                players[id]['exAttribute0'] = 1004
            else:
                mud.send_message(
                    id, "<f220>\nSelect your character class:\n\n")
                ctr = 0
                classStr = '  '
                for (name, p) in list(characterClassDB.items()):
                    if name == 'witch' or name == 'ghost':
                        continue
                    if ctr > 0:
                        classStr = classStr + ', <f220>' + name + '<r>'
                    else:
                        classStr = classStr + '<f220>' + name + '<r>'
                    ctr = ctr + 1
                    if ctr > 7:
                        classStr = classStr + '\n  '
                        ctr = 0
                mud.send_message(id, classStr + '\n\n')
                players[id]['exAttribute0'] = 1004
                break

        if players[id]['exAttribute0'] == 1004:
            players[id]['idleStart'] = int(time.time())
            selectedCharacterClass = command.lower().strip()
            unrecognized = False
            if selectedCharacterClass == 'witch':
                if os.path.isfile("witches"):
                    unrecognized = True

            if not characterClassDB.get(
                    selectedCharacterClass) or selectedCharacterClass == 'ghost':
                unrecognized = True

            if unrecognized:
                mud.send_message(
                    id, "<f220>\nUnrecognized character class.<r>\n\n")
                players[id]['exAttribute0'] = 1000
                mud.send_message(
                    id,
                    "<f15>What is your username?<r>\n<f246>Type '<f253>new<r><f246>' to create a character.\n\n")
                break

            # Load the player template from a file
            with open(str(Config.get('Players', 'Location')) + "/player.template", "r") as read_file:
                template = commentjson.load(read_file)

            setRace(template, racesDB, selectedRace)

            # Make required changes to template before saving again into
            # <Name>.player
            template['name'] = players[id]['exAttribute1']
            template['pwd'] = hash_password(players[id]['exAttribute2'])

            template['characterClass'] = selectedCharacterClass

            # First player becomes a witch
            if not os.path.isfile("witches"):
                template['characterClass'] = 'witch'
                # admin speaks all languages
                template['language'] = []
                for race, raceStats in racesDB.items():
                    for lang in raceStats['language']:
                        if lang not in template['language']:
                            template['language'].append(lang)
                template['language'].append('cant')
                with open("witches", "w") as witches_file:
                    witches_file.write(template['name'])

            # populate initial inventory from character class
            template['inv'] = []
            for invItem in characterClassDB[template['characterClass']]['inv']:
                template['inv'].append(invItem)

            # populate proficencies from character class
            template['proficiencies'] = []
            for prof in characterClassDB[template['characterClass']][str(
                    template['lvl'])]:
                template['proficiencies'].append(prof)

            # additional languages for the character class
            for lang in characterClassDB[template['characterClass']
                                         ]['extraLanguage']:
                template['language'].append(lang)

            # Save template into a new player file
            # print(template)
            with open(str(Config.get('Players', 'Location')) + "/" + template['name'] + ".player", 'w') as fp:
                commentjson.dump(template, fp)

            # Reload PlayersDB to include this newly created player
            playersDB = loadPlayersDB()

            players[id]['exAttribute0'] = None
            mud.send_message(
                id,
                '<f220>Your character has now been created, you can log in using credentials you have provided.\n')
            # mud.send_message(id, '<f15>What is your username?')
            mud.send_message(
                id,
                "<f15>What is your username?<r>\n<f246>Type '<f253>new<r><f246>' to create a character.\n\n")
            log("Client ID: " +
                str(id) +
                " has completed character creation (" +
                template['name'] +
                ").", "info")
            break

        # if the player hasn't given their name yet, use this first command as
        # their name and move them to the starting room.
        if players[id]['name'] is None and players[id]['exAttribute0'] is None:
            if command.lower() != "new":
                players[id]['idleStart'] = int(time.time())
                dbResponse = None
                file = loadPlayer(command, playersDB)
                if file is not None:
                    dbResponse = tuple(file.values())

                # print(dbResponse)

                if dbResponse is not None:
                    players[id]['name'] = dbResponse[0]

                    log("Client ID: " + str(id) +
                        " has requested existing user (" + command + ")", "info")
                    mud.send_message(id, 'Hi <u><f32>' + command + '<r>!')
                    mud.send_message(id, '<f15>What is your password?\n\n')
                else:
                    mud.send_message(
                        id,
                        '<f202>User <f32>' +
                        command +
                        '<r> was not found!\n')
                    mud.send_message(id, '<f15>What is your username?\n\n')
                    log("Client ID: " +
                        str(id) +
                        " has requested non existent user (" +
                        command +
                        ")", "info")
            else:
                # New player creation here
                if not os.path.isfile(".disableRegistrations"):
                    players[id]['idleStart'] = int(time.time())
                    log("Client ID: " + str(id) +
                        " has initiated character creation.", "info")
                    mud.send_message(
                        id,
                        "<f220>Welcome Traveller! So you have decided to create an account, that's awesome! Thank you for your interest in AberMUSH, hope you enjoy yourself while you're here.")
                    mud.send_message(
                        id,
                        "Note: You can type 'startover' at any time to restart the character creation process.\n")
                    mud.send_message(
                        id, "<f230>Press ENTER to continue...\n\n")
                    # mud.send_message(id, "<f220>What is going to be your name?")
                    # Set eAttribute0 to 1000, signifying this client has
                    # initialised a player creation process.
                    players[id]['exAttribute0'] = 1000
                else:
                    mud.send_message(
                        id, "<f220>New registrations are closed at this time.")
                    mud.send_message(
                        id, "<f230>Press ENTER to continue...\n\n")
        elif players[id]['name'] is not None \
                and players[id]['authenticated'] is None:
            pl = loadPlayer(players[id]['name'], playersDB)
            # print(pl)
            dbPass = pl['pwd']

            if players[id]['name'] == 'Guest':
                dbPass = hash_password(pl['pwd'])

            # Iterate through players in game and see if our newly connected
            # players is not already in game.
            playerFound = False
            for pl in players:
                if players[id]['name'] is not None and players[pl]['name'] is not None and players[id]['name'] == players[pl]['name'] and pl != id:
                    playerFound = True

            if verify_password(dbPass, command):
                if not playerFound:
                    players[id]['authenticated'] = True
                    players[id]['prefix'] = "None"
                    players[id]['room'] = dbResponse[1]
                    players[id]['lvl'] = dbResponse[2]
                    players[id]['exp'] = dbResponse[3]
                    players[id]['str'] = dbResponse[4]
                    players[id]['siz'] = dbResponse[5]
                    players[id]['wei'] = dbResponse[6]
                    players[id]['per'] = dbResponse[7]
                    players[id]['endu'] = dbResponse[8]
                    players[id]['cha'] = dbResponse[9]
                    players[id]['int'] = dbResponse[10]
                    players[id]['agi'] = dbResponse[11]
                    players[id]['luc'] = dbResponse[12]
                    players[id]['cool'] = dbResponse[13]
                    players[id]['cred'] = dbResponse[14]
                    players[id]['inv'] = dbResponse[15]  # .split(',')
                    players[id]['speakLanguage'] = dbResponse[16]
                    players[id]['language'] = dbResponse[17]
                    players[id]['convstate'] = dbResponse[18]  # .split(',')
                    # Example: item_list = [e for e in item_list if e not in ('item', 5)]
                    #players[id]['inv'] = [e for e in players[id]['inv'] if e not in ('', ' ')]
                    players[id]['clo_head'] = dbResponse[20]
                    players[id]['clo_neck'] = dbResponse[21]
                    players[id]['clo_larm'] = dbResponse[22]
                    players[id]['clo_rarm'] = dbResponse[23]
                    players[id]['clo_lhand'] = dbResponse[24]
                    players[id]['clo_rhand'] = dbResponse[25]
                    players[id]['clo_lwrist'] = dbResponse[26]
                    players[id]['clo_rwrist'] = dbResponse[27]
                    players[id]['clo_chest'] = dbResponse[28]
                    players[id]['clo_lleg'] = dbResponse[29]
                    players[id]['clo_rleg'] = dbResponse[30]
                    players[id]['clo_feet'] = dbResponse[31]
                    players[id]['imp_head'] = dbResponse[32]
                    players[id]['imp_larm'] = dbResponse[33]
                    players[id]['imp_rarm'] = dbResponse[34]
                    players[id]['imp_lhand'] = dbResponse[35]
                    players[id]['imp_rhand'] = dbResponse[36]
                    players[id]['imp_chest'] = dbResponse[37]
                    players[id]['imp_lleg'] = dbResponse[38]
                    players[id]['imp_rleg'] = dbResponse[39]
                    players[id]['imp_feet'] = dbResponse[40]
                    players[id]['hpMax'] = dbResponse[41]
                    players[id]['hp'] = dbResponse[42]
                    players[id]['charge'] = dbResponse[43]
                    players[id]['inDescription'] = dbResponse[44]
                    players[id]['outDescription'] = dbResponse[45]
                    players[id]['lookDescription'] = dbResponse[46]
                    players[id]['isInCombat'] = 0
                    players[id]['lastCombatAction'] = int(time.time())
                    players[id]['isAttackable'] = 1
                    players[id]['corpseTTL'] = 60
                    players[id]['idleStart'] = int(time.time())
                    players[id]['channels'] = dbResponse[47]
                    players[id]['permissionLevel'] = dbResponse[48]
                    players[id]['exAttribute0'] = dbResponse[49]
                    players[id]['exAttribute1'] = dbResponse[50]
                    players[id]['exAttribute2'] = dbResponse[51]
                    players[id]['canGo'] = dbResponse[52]
                    players[id]['canLook'] = dbResponse[53]
                    players[id]['canSay'] = dbResponse[54]
                    players[id]['canAttack'] = dbResponse[55]
                    players[id]['canDirectMessage'] = dbResponse[56]
                    players[id]['ref'] = dbResponse[57]
                    players[id]['bodyType'] = dbResponse[58]
                    players[id]['race'] = dbResponse[59]
                    players[id]['characterClass'] = dbResponse[60]
                    players[id]['proficiencies'] = dbResponse[61]
                    players[id]['fightingStyle'] = dbResponse[62]
                    players[id]['restRequired'] = dbResponse[63]
                    players[id]['enemy'] = dbResponse[64]
                    players[id]['archetype'] = dbResponse[65]
                    players[id]['preparedSpells'] = dbResponse[66]
                    players[id]['spellSlots'] = dbResponse[67]
                    players[id]['tempHitPoints'] = dbResponse[68]
                    players[id]['tempHitPointsStart'] = dbResponse[69]
                    players[id]['tempHitPointsDuration'] = dbResponse[70]
                    players[id]['prepareSpell'] = dbResponse[71]
                    players[id]['prepareSpellProgress'] = dbResponse[72]
                    players[id]['prepareSpellTime'] = dbResponse[73]
                    players[id]['frozenDescription'] = dbResponse[74]
                    players[id]['frozenStart'] = dbResponse[75]
                    players[id]['frozenDuration'] = dbResponse[76]
                    players[id]['affinity'] = dbResponse[77]
                    players[id]['familiar'] = dbResponse[78]

                    log("Client ID: " +
                        str(id) +
                        " has successfully authenticated user " +
                        players[id]['name'], "info")
                    # print(players[id])
                    # go through all the players in the game
                    for (pid, pl) in list(players.items()):
                        # send each player a message to tell them about the new
                        # player
                        if players[pid]['authenticated'] is not None \
                           and players[pid]['room'] == players[id]['room'] \
                           and players[pid]['name'] != players[id]['name']:
                            mud.send_message(
                                pid, '{} has materialised out of thin air nearby.'.format(
                                    players[id]['name']) + "\n\n")

                    # send the new player a welcome message
                    mud.send_message(
                        id, '\n<f220>Welcome to AberMUSH!, {}. '.format(
                            players[id]['name']))
                    mud.send_message(id, '\n<f255>Hello there traveller! You have connected to an AberMUSH server. You can move around the rooms along with other players (if you are lucky to meet any), attack each other (including NPCs), pick up and drop items and chat. Make sure to visit the repo for further info. Thanks for your interest in AberMUSH.')
                    mud.send_message(
                        id,
                        "\n<f255>Type '<r><f220>help<r><f255>' for a list of all currently implemented commands/functions. Have fun!\n\n")

                    familiarRecall(mud, players, id, npcs, npcsDB)
                else:
                    mud.send_message(
                        id, '<f202>This character is already in the world!')
                    log("Client ID: " + str(id) +
                        " has requested a character which is already in the world!", "info")
                    players[id]['name'] = None
                    mud.send_message(id, '<f15>What is your username? ')
            else:
                mud.send_message(id, '<f202>Password incorrect!\n')
                log("Client ID: " + str(id) + " has failed authentication", "info")
                players[id]['name'] = None
                mud.send_message(id, '<f15>What is your username? ')

        else:
            players[id]['idleStart'] = int(time.time())
            if players[id]['exAttribute0'] < 1000:
                if len(command) > 0:
                    runCommand(
                        command.lower(),
                        params,
                        mud,
                        playersDB,
                        players,
                        rooms,
                        npcsDB,
                        npcs,
                        itemsDB,
                        itemsInWorld,
                        envDB,
                        env,
                        scriptedEventsDB,
                        eventSchedule,
                        id,
                        fights,
                        corpses,
                        blocklist,
                        mapArea,
                        characterClassDB,
                        spellsDB,
                        sentimentDB)
