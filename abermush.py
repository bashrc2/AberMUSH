__filename__ = "abermush.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski", "Mark Frimston"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"
__module_group__ = "Command Interface"

import os
import json
import ssl
import argparse
import sys

from functions import deepcopy
from functions import showTiming
from functions import log
from functions import saveState
from functions import saveUniverse
from functions import addToScheduler
from functions import loadPlayer
from functions import loadPlayersDB
from functions import sendToChannel
from functions import hash_password
from functions import verify_password
from functions import loadBlocklist
from functions import setRace
from functions import str2bool

from commands import runCommand
from combat import npcAggression
from combat import runFights
from combat import playersRest
from combat import updateTemporaryHitPoints
from combat import updateTemporaryIncapacitation
from combat import updateTemporaryCharm
from playerconnections import initialSetupAfterLogin
from playerconnections import runPlayerConnections
from playerconnections import disconnectIdlePlayers
from playerconnections import playerInGame
from npcs import npcRespawns
from npcs import runNPCs
from npcs import runMobileItems
from npcs import npcsRest
from familiar import familiarRecall
from reaper import removeCorpses
from reaper import runDeaths
from scheduler import runSchedule
from scheduler import runEnvironment
from scheduler import runMessages
from environment import assignTerrainDifficulty
from environment import assignCoordinates
from environment import generateCloud
from environment import getTemperature
from environment import findRoomCollisions
from environment import mapLevelAsCsv
from environment import assignEnvironmentToRooms
from mmp import exportMMP
from traps import runTraps
from tests import runAllTests

from gcos import terminalEmulator

import datetime
import time

# import the MUD server class
from mudserver import MudServer

# import random generator library
import random

# import the deepcopy library
# from copy import deepcopy

# import config parser
import configparser

# import glob module
import glob


parser = argparse.ArgumentParser(description='AberMUSH Server')
parser.add_argument("--tests", type=str2bool, nargs='?',
                    const=True, default=False,
                    help="Run unit tests")
parser.add_argument('--mapLevel', dest='mapLevel', type=int,
                    default=None,
                    help='Shows a vertical map level as a CSV')
parser.add_argument("--mmp", type=str2bool, nargs='?',
                    const=True, default=False,
                    help="Map in MMP XML format")
args = parser.parse_args()
if args.tests:
    runAllTests()
    sys.exit()

log("", "Server Boot")

log("", "Loading configuration file")

# load the configuration file
Config = configparser.ConfigParser()
Config.read('config.ini')
# example of config file usage
# print(str(Config.get('Database', 'Hostname')))

# Declare rooms dictionary
rooms = {}

# Environments for rooms
environments = {}

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

# Specify allowed player idle time
allowedPlayerIdle = int(Config.get('World', 'IdleTimeBeforeDisconnect'))

# websocket settings
websocket_tls = False
websocket_cert = None
websocket_key = None
websocket_ver = ssl.PROTOCOL_TLS_SERVER
if 'true' in Config.get('Web', 'tlsEnabled').lower():
    websocket_tls = True
    # resolve any symbolic links with realpath
    websocket_cert = os.path.realpath(str(Config.get('Web', 'tlsCert')))
    websocket_key = os.path.realpath(str(Config.get('Web', 'tlsKey')))

log("Loading sentiment...", "info")

with open(str(Config.get('Sentiment', 'Definition')), "r") as read_file:
    sentimentDB = json.loads(read_file.read())

countStr = str(len(sentimentDB))
log("Sentiment loaded: " + countStr, "info")

log("Loading rooms...", "info")

# Loading rooms
if os.path.isfile("universe.json"):
    with open("universe.json", "r") as read_file:
        rooms = json.loads(read_file.read())
    # Clear room coordinates
    for rm in rooms:
        rooms[rm]['coords'] = []
else:
    with open(str(Config.get('Rooms', 'Definition')), "r") as read_file:
        rooms = json.loads(read_file.read())

for roomID, rm in rooms.items():
    roomID = roomID.replace('$rid=', '').replace('$', '')
    if not os.path.isfile('/home/bashrc/develop/AberMUSH/images/rooms/' +
                          str(roomID)):
        if not args.mapLevel:
            print('Missing room image: ' + str(roomID))

countStr = str(len(rooms))
log("Rooms loaded: " + countStr, "info")

log("Loading environments...", "info")
with open(str(Config.get('Environments', 'Definition')), "r") as read_file:
    environments = json.loads(read_file.read())
percentAssigned = str(assignEnvironmentToRooms(environments, rooms))
log(percentAssigned + '% of rooms have environments assigned', "info")

maxTerrainDifficulty = assignTerrainDifficulty(rooms)

maxTerrainDifficultyStr = str(maxTerrainDifficulty)
log("Terrain difficulty calculated. max=" + maxTerrainDifficultyStr, "info")

# Loading Items
if os.path.isfile("universe_items.json"):
    try:
        with open("universe_items.json", "r") as read_file:
            itemsInWorld = json.loads(read_file.read())
    except BaseException:
        print('WARN: unable to load universe_items.json')
        pass

if os.path.isfile("universe_itemsdb.json"):
    try:
        with open("universe_itemsdb.json", "r") as read_file:
            itemsDB = json.loads(read_file.read())
    except BaseException:
        print('WARN: unable to load universe_itemsdb.json')
        pass

if not itemsDB:
    with open(str(Config.get('Items', 'Definition')), "r") as read_file:
        itemsDB = json.loads(read_file.read())

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
               v == "visibleWhenWearing" or
               v == "climbWhenWearing" or
               v == "type" or
               v == "writeWithItems" or
               v == "written" or
               v == "written_description" or
               v == "contains" or
               v == "climbThrough" or
               v == "damage" or
               v == "cost" or
               v == "range" or
               v == "heave" or
               v == "jumpTo" or
               v == "game" or
               v == "gameState" or
               v == "exit" or
               v == "exitName" or
               v == "moveTimes" or
               v == "takeFail" or
               v == "climbFail" or
               v == "cardPack" or
               v == "chessBoardName" or
               v == "morrisBoardName" or
               v == "article"):
            itemsDB[k][v] = int(itemsDB[k][v])

countStr = str(len(itemsDB))
log("Items loaded: " + countStr, "info")

# Load scripted event declarations from disk
files = glob.glob(str(Config.get('Events', 'Location')) + "/*.event")
counter = 0
for file in files:
    counter += 1
    f = open(file, 'r')
    # print(file)
    lines = [line.rstrip() for line in f.readlines()[2:]]
    for fileLine in lines[1:]:
        if len(fileLine) > 0:
            scriptedEventsDB.append([lines[0]] + fileLine.split('|'))
            # print(lines)
            f.close()

countStr = str(counter)
log("Scripted Events loaded: " + countStr, "info")

mapArea = assignCoordinates(rooms, itemsDB, scriptedEventsDB)

if args.mmp:
    exportMMP(rooms, environments, 'mmp.xml')
    print('Map exported to mmp.xml')
    sys.exit()

if args.mapLevel is not None:
    mapLevelAsCsv(rooms, args.mapLevel)
    sys.exit()

# check that there are no room collisions
findRoomCollisions(rooms)

mapAreaStr = str(mapArea)
log("Map coordinates:" + mapAreaStr, "info")

# Loading environment actors
if os.path.isfile("universe_actors.json"):
    try:
        with open("universe_actors.json", "r") as read_file:
            env = json.loads(read_file.read())
    except BaseException:
        print('WARN: unable to load universe_actors.json')
        pass

if os.path.isfile("universe_actorsdb.json"):
    try:
        with open("universe_actorsdb.json", "r") as read_file:
            envDB = json.loads(read_file.read())
    except BaseException:
        print('WARN: unable to load universe_actorsdb.json')
        pass

if not envDB:
    with open(str(Config.get('Actors', 'Definition')), "r") as read_file:
        envDB = json.loads(read_file.read())

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

countStr = str(len(envDB))
log("Environment Actors loaded: " + countStr, "info")

# List ENV dictionary for debugging purposes
# print(env)
# print("Test:")
# for x in env:
# print (x)
# for y in env[x]:
# print (y,':',env[x][y])

log("Loading NPCs...", "info")
# if os.path.isfile("universe_npcs.json"):
#     with open("universe_npcs.json", "r") as read_file:
#         npcs = json.loads(read_file.read())

if os.path.isfile("universe_npcsdb.json"):
    try:
        with open("universe_npcsdb.json", "r") as read_file:
            npcsDB = json.loads(read_file.read())
    except BaseException:
        print('WARN: unable to load universe_npcsdb.json')
        pass

if not npcsDB:
    with open(str(Config.get('NPCs', 'Definition')), "r") as read_file:
        npcsDB = json.loads(read_file.read())

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
               v == "visibleWhenWearing" or
               v == "climbWhenWearing" or
               v == "speakLanguage" or
               v == "language" or
               v == "race" or
               v == "familiarOf" or
               v == "familiarTarget" or
               v == "familiarType" or
               v == "familiarMode" or
               v == "animalType" or
               v == "archetype" or
               v == "characterClass" or
               v == "proficiencies" or
               v == "fightingStyle" or
               v == "enemy" or
               v == "tempCharmTarget" or
               v == "guild" or
               v == "guildRole" or
               v == "affinity" or
               v == "preparedSpells" or
               v == "spellSlots" or
               v == "conv" or
               v == "path" or
               v == "moveTimes" or
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

countStr = str(len(npcsDB))
log("NPCs loaded: " + countStr, "info")

with open(str(Config.get('Races', 'Definition')), "r") as read_file:
    racesDB = json.loads(read_file.read())

countStr = str(len(racesDB))
log("Races loaded: " + countStr, "info")

with open(str(Config.get('CharacterClass', 'Definition')), "r") as read_file:
    characterClassDB = json.loads(read_file.read())

countStr = str(len(characterClassDB))
log("Character Classes loaded: " + countStr, "info")

with open(str(Config.get('Spells', 'Definition')), "r") as read_file:
    spellsDB = json.loads(read_file.read())

countStr = str(len(spellsDB))
log("Spells loaded: " + countStr, "info")

with open(str(Config.get('Guilds', 'Definition')), "r") as read_file:
    guildsDB = json.loads(read_file.read())

countStr = str(len(guildsDB))
log("Guilds loaded: " + countStr, "info")

with open(str(Config.get('Attacks', 'Definition')), "r") as read_file:
    attackDB = json.loads(read_file.read())

countStr = str(len(attackDB))
log("Attacks loaded: " + countStr, "info")

# List NPC dictionary for debugging purposes
# print(" ")
# print("LIVE:")
# print(npcsDB)
# print(" ")
# for x in npcsDB:
# print (x)
# for y in npcsDB[x]:
# print (y,':',npcsDB[x][y])

# List items for debugging purposes
# print("TEST:")
# for x in itemsDB:
# print (x)
# for y in itemsDB[x]:
# print(y,':',itemsDB[x][y])
# print(itemsDB)

# Load registered players DB
playersDB = loadPlayersDB()
countStr = str(len(playersDB))
log("Registered players: " + countStr, "info")

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
stateSaveInterStr = str(stateSaveInterval)
log("State Save interval: " + stateSaveInterStr + " seconds", "info")

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
mud = MudServer(websocket_tls, websocket_cert, websocket_key, websocket_ver)

# weather
currHour = datetime.datetime.today().hour
currMin = datetime.datetime.today().minute
daysSinceEpoch = (datetime.datetime.today() -
                  datetime.datetime(1970, 1, 1)).days
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
windDirection = \
    generateCloud(r1, rooms, mapArea, clouds,
                  cloudGrid, tileSize, windDirection)
windDirectionStr = str(windDirection)
log("Clouds generated. Wind direction " + windDirectionStr, "info")

lastTempHitPointsUpdate = int(time.time())
tempHitPointsUpdateInterval = 60

lastRoomTeleport = int(time.time())
roomTeleportInterval = 60

lastRestUpdate = int(time.time())

blocklist = []
if loadBlocklist("blocked.txt", blocklist):
    log("Blocklist loaded", "info")

terminalMode = {}

previousTiming = time.time()

# main game loop. We loop forever (i.e. until the program is terminated)
while True:
    # print(int(time.time()))

    # automatic teleport from one room to another every N seconds
    now = int(time.time())
    if now >= lastRoomTeleport + roomTeleportInterval:
        lastRoomTeleport = now
        for p in players:
            rm = players[p]['room']
            if rm:
                if rooms[rm].get('roomTeleport'):
                    players[p]['room'] = rooms[rm]['roomTeleport']

    previousTiming = \
        showTiming(previousTiming, "teleport every N seconds")

    previousTiming2 = time.time()

    now = int(time.time())
    if now >= lastTempHitPointsUpdate + tempHitPointsUpdateInterval:
        lastTempHitPointsUpdate = now
        updateTemporaryHitPoints(mud, players, False)
        updateTemporaryHitPoints(mud, npcs, True)

        previousTiming = \
            showTiming(previousTiming, "update hit points")

        updateTemporaryIncapacitation(mud, players, False)
        updateTemporaryIncapacitation(mud, npcs, True)

        previousTiming = \
            showTiming(previousTiming, "update incapacitation")

        updateTemporaryCharm(mud, players, False)
        updateTemporaryCharm(mud, npcs, True)

        previousTiming = \
            showTiming(previousTiming, "update charm")

        runTraps(mud, rooms, players, npcs)

        previousTiming = \
            showTiming(previousTiming, "update traps")

    previousTiming = \
        showTiming(previousTiming2, "various updates")

    now = int(time.time())
    if now >= lastWeatherUpdate + weatherUpdateInterval:
        lastWeatherUpdate = now
        temperature = getTemperature()
        previousTiming = \
            showTiming(previousTiming, "get temperature")
        # print("Temperature " + str(temperature))
        windDirection = generateCloud(r1, rooms, mapArea, clouds, cloudGrid,
                                      tileSize, windDirection)
        previousTiming = \
            showTiming(previousTiming, "calc wind directions")
        # plotClouds(rooms, mapArea, clouds, temperature)

    # update player list
    playerList = []
    for p in players:
        if players[p]['name'] is not None and \
           players[p]['authenticated'] is not None:
            if players[p]['name'] not in playerList:
                playerList.append(players[p]['name'])

    previousTiming = \
        showTiming(previousTiming, "update player list")

    # Aggressive NPCs may attack players
    npcAggression(npcs, players, fights, mud, itemsInWorld, itemsDB, racesDB)

    previousTiming = \
        showTiming(previousTiming, "update npc attacks")

    # pause for 1/5 of a second on each loop, so that we don't constantly
    # use 100% CPU time
    time.sleep(0.1)
    # print(eventSchedule)

    previousTiming = \
        showTiming(previousTiming, "sleep")

    # 'update' must be called in the loop to keep the game running and give
    # us up-to-date information
    mud.update()

    previousTiming = \
        showTiming(previousTiming, "update mud")

    if disconnectIdlePlayers(mud, players, allowedPlayerIdle, playersDB):
        playersDB = loadPlayersDB()

    previousTiming = \
        showTiming(previousTiming, "disconnect idle platers")

    # Check if State Save is due and execute it if required
    now = int(time.time())
    if int(now >= lastStateSave + stateSaveInterval):
        sendToChannel("Server", "system", "Saving server state...", channels)
        # State Save logic Start
        playersWereSaved = False
        for (pid, pl) in list(players.items()):
            if players[pid]['authenticated'] is not None:
                saveState(players[pid], playersDB, False)
                playersWereSaved = True
        if playersWereSaved:
            playersDB = loadPlayersDB()
            saveUniverse(rooms, npcsDB, npcs,
                         itemsDB, itemsInWorld,
                         envDB, env, guildsDB)
        lastStateSave = now

    previousTiming = \
        showTiming(previousTiming, "save game")

    # Handle Player Deaths
    runDeaths(mud, players, npcs, corpses, fights,
              eventSchedule, scriptedEventsDB)

    previousTiming = \
        showTiming(previousTiming, "handle deaths")

    # Handle Fights
    runFights(mud, players, npcs, fights, itemsInWorld, itemsDB, rooms,
              maxTerrainDifficulty, mapArea, clouds, racesDB, characterClassDB,
              guildsDB, attackDB)

    previousTiming = \
        showTiming(previousTiming, "update fights")

    # Some items can appear only at certain times
    runMobileItems(itemsDB, itemsInWorld, eventSchedule,
                   scriptedEventsDB, rooms, mapArea, clouds)

    previousTiming = \
        showTiming(previousTiming, "update mobile items")

    # Iterate through NPCs, check if its time to talk, then check if anyone is
    # attacking it
    runNPCs(mud, npcs, players, fights, corpses, scriptedEventsDB, itemsDB,
            npcsTemplate, rooms, mapArea, clouds, eventSchedule)

    previousTiming = \
        showTiming(previousTiming, "update npcs")

    runEnvironment(mud, players, env)

    previousTiming = \
        showTiming(previousTiming, "update environment")

    removeCorpses(corpses)

    previousTiming = \
        showTiming(previousTiming, "remove dead")

    npcRespawns(npcs)

    previousTiming = \
        showTiming(previousTiming, "respawns")

    runSchedule(mud, eventSchedule, players, npcs, itemsInWorld, env,
                npcsDB, envDB)

    previousTiming = \
        showTiming(previousTiming, "schedule")

    npcsTemplate = deepcopy(npcs)

    previousTiming = \
        showTiming(previousTiming, "copy npcs")

    runMessages(mud, channels, players)

    previousTiming = \
        showTiming(previousTiming, "messages")

    channels.clear()

    runPlayerConnections(mud, id, players, playersDB, fights,
                         Config, terminalMode)

    previousTiming = \
        showTiming(previousTiming, "player connections")

    # rest restores hp and allows spell learning
    now = int(time.time())
    if now >= lastRestUpdate + 1:
        lastRestUpdate = now
        playersRest(mud, players)
        npcsRest(npcs)

    previousTiming = \
        showTiming(previousTiming, "resting")

    # go through any new commands sent from players
    for (id, command, params) in mud.get_commands():
        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in players:
            continue

        if command.lower() == "startover" and \
           players[id]['exAttribute0'] is not None and \
           players[id]['authenticated'] is None:
            if not os.path.isfile(".disableRegistrations"):
                players[id]['idleStart'] = int(time.time())
                mud.sendMessage(
                    id, "<f220>Ok, Starting character creation " +
                    "from the beginning!\n")
                players[id]['exAttribute0'] = 1000

        if command.lower() == "exit" and \
           players[id]['exAttribute0'] is not None and \
           players[id]['authenticated'] is None:
            players[id]['idleStart'] = int(time.time())
            mud.sendMessage(id, "<f220>Ok, leaving the character creation.\n")
            players[id]['exAttribute0'] = None
            mud.sendMessage(
                id,
                "<f15>What is your username?<r>\n<f246>Type " +
                "'<f253>new<r><f246>' to create a character.\n\n")
            idStr = str(id)
            log("Player ID " + idStr +
                " has aborted character creation.", "info")
            break

        if players[id]['exAttribute0'] == 1000:
            players[id]['idleStart'] = int(time.time())
            # First step of char creation
            mud.sendMessage(id, "<f220>\nWhat is going to be your name?\n\n")
            for c in mud._clients:
                # print(str(mud._clients[c].address))
                pass
            players[id]['exAttribute0'] = 1001
            break

        if players[id]['exAttribute0'] == 1001:
            players[id]['idleStart'] = int(time.time())
            taken = False

            if not taken and terminalMode.get(str(id)) is True:
                taken = True
                if terminalEmulator(command, params, mud, id):
                    terminalMode[str(id)] = True
                    idStr = str(id)
                    log("Player ID " + idStr +
                        " logged into GCOS-3/TSS with command - " +
                        command + ' ' + params, "info")
                else:
                    if command.startswith('restart') or \
                       command.startswith('shutdown'):
                        terminalMode[str(id)] = False
                        mud.sendMessage(id, "\nBYE\n\n")
                    else:
                        mud.sendMessage(id, ">")
                        idStr = str(id)
                        log("Player ID " + idStr +
                            " logged into GCOS-3/TSS with command - " +
                            command + ' ' + params, "info")

            if not taken and not terminalMode.get(str(id)):
                if command.strip().isdigit():
                    mud.sendMessage(
                        id, "\n<f220>Name cannot be a digit")
                    mud.sendMessage(id, "Press ENTER to continue...\n\n")
                    taken = True

                if not taken:
                    if len(command.strip()) < 2:
                        mud.sendMessage(
                            id, "\n<f220>Name must be at least two characters")
                        mud.sendMessage(id, "Press ENTER to continue...\n\n")
                        taken = True

                if not taken:
                    for p in playersDB:
                        if playersDB[p]['name'].lower() == command.lower():
                            mud.sendMessage(
                                id, "\n<f220>This character name is " +
                                "already taken!")
                            mud.sendMessage(id,
                                            "Press ENTER to continue...\n\n")
                            taken = True
                            break

            if not taken:
                if terminalEmulator(command, params, mud, id):
                    terminalMode[str(id)] = True
                    taken = True
                    strId = str(id)
                    log("Player ID " + strId +
                        " logged into GCOS-3/TSS with command - " +
                        command + ' ' + params, "info")
                else:
                    if terminalMode.get(str(id)) is True:
                        mud.sendMessage(id, ">")
                        strId = str(id)
                        log("Player ID " + strId +
                            " logged into GCOS-3/TSS with command - " +
                            command + ' ' + params, "info")

            if not taken:
                players[id]['exAttribute1'] = command.strip()
                mud.sendMessage(
                    id, "<f220>Now what would you like your " +
                    "password to be?\n\n")
                players[id]['exAttribute0'] = 1002
                break
            else:
                players[id]['idleStart'] = int(time.time())
                players[id]['exAttribute0'] = 1000
                break

        if players[id]['exAttribute0'] == 1002:
            # store the password
            mud.sendMessage(id, "<f220>\nOk, got that.\n")
            players[id]['exAttribute2'] = command.strip()

            players[id]['idleStart'] = int(time.time())
            mud.sendMessage(id, "<f220>\nSelect your character race:\n\n")
            ctr = 0
            typesStr = '  '
            for (name, p) in list(racesDB.items()):
                if ctr > 0:
                    typesStr = typesStr + ', <f220>' + name + '<r>'
                else:
                    typesStr = typesStr + '<f220>' + name + '<r>'
                ctr += 1
                if ctr > 7:
                    typesStr = typesStr + '\n  '
                    ctr = 0
            mud.sendMessage(id, typesStr + '\n\n')
            players[id]['exAttribute0'] = 1003
            break

        if players[id]['exAttribute0'] == 1003:
            players[id]['idleStart'] = int(time.time())
            selectedRace = command.lower().strip()
            if not racesDB.get(selectedRace):
                mud.sendMessage(
                    id, "<f220>\nUnrecognized character race.<r>\n\n")
                players[id]['exAttribute0'] = 1000
                mud.sendMessage(
                    id,
                    "<f15>What is your username?<r>\n<f246>Type " +
                    "'<f253>new<r><f246>' to create a character.\n\n")
                break

            if not os.path.isfile("witches"):
                command = 'witch'
                players[id]['exAttribute0'] = 1004
            else:
                mud.sendMessage(
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
                    ctr += 1
                    if ctr > 7:
                        classStr = classStr + '\n  '
                        ctr = 0
                mud.sendMessage(id, classStr + '\n\n')
                players[id]['exAttribute0'] = 1004
                break

        if players[id]['exAttribute0'] == 1004:
            players[id]['idleStart'] = int(time.time())
            selectedCharacterClass = command.lower().strip()
            unrecognized = False
            if selectedCharacterClass == 'witch':
                if os.path.isfile("witches"):
                    unrecognized = True

            if not characterClassDB.get(selectedCharacterClass) or \
               selectedCharacterClass == 'ghost':
                unrecognized = True

            if unrecognized:
                mud.sendMessage(
                    id, "<f220>\nUnrecognized character class.<r>\n\n")
                players[id]['exAttribute0'] = 1000
                mud.sendMessage(
                    id,
                    "<f15>What is your username?<r>\n<f246>Type " +
                    "'<f253>new<r><f246>' to create a character.\n\n")
                break

            # Load the player template from a file
            with open(str(Config.get('Players', 'Location')) +
                      "/player.template", "r") as read_file:
                template = json.loads(read_file.read())

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
            idx = template['characterClass']
            for prof in characterClassDB[idx][str(template['lvl'])]:
                template['proficiencies'].append(prof)

            # additional languages for the character class
            for lang in characterClassDB[idx]['extraLanguage']:
                template['language'].append(lang)

            # Save template into a new player file
            # print(template)
            with open(str(Config.get('Players', 'Location')) + "/" +
                      template['name'] + ".player", 'w') as fp:
                fp.write(json.dumps(template))

            # Reload PlayersDB to include this newly created player
            playersDB = loadPlayersDB()

            players[id]['exAttribute0'] = None
            mud.sendMessage(
                id,
                '<f220>Your character has now been created, ' +
                'you can log in using credentials you have provided.\n')
            # mud.sendMessage(id, '<f15>What is your username?')
            mud.sendMessage(
                id,
                "<f15>What is your username?<r>\n<f246>Type " +
                "'<f253>new<r><f246>' to create a character.\n\n")
            strId = str(id)
            log("Player ID " + strId +
                " has completed character creation [" +
                template['name'] + "].", "info")
            break

        # if the player hasn't given their name yet, use this first command as
        # their name and move them to the starting room.
        if players[id]['name'] is None and \
           players[id]['exAttribute0'] is None:
            if command.lower() != "new":
                players[id]['idleStart'] = int(time.time())
                pl = None

                # check for logins with CONNECT username password
                connectStr = command.strip().lower()
                connectCommand = False
                if connectStr.lower() == 'connect':
                    mud.sendMessage(id, "Login via CONNECT\n\n")
                    if ' ' in params:
                        connectUsername = params.split(' ', 1)[0]
                        players[id]['name'] = connectUsername
                        connectPassword = params.split(' ', 1)[1].strip()
                        pl = loadPlayer(connectUsername)
                        if pl is not None:
                            dbPass = pl['pwd']
                            if connectUsername == 'Guest':
                                dbPass = hash_password(pl['pwd'])
                            if verify_password(dbPass, connectPassword):
                                if not playerInGame(id, connectUsername,
                                                    players):
                                    players[id]['exAttribute1'] = \
                                        connectUsername
                                    players[id]['exAttribute2'] = \
                                        connectPassword
                                    players[id]['exAttribute0'] = None
                                    initialSetupAfterLogin(mud, id,
                                                           players, pl)
                                    familiarRecall(mud, players, id,
                                                   npcs, npcsDB)
                                    mud.sendMessage(id,
                                                    "CONNECT login " +
                                                    "success\n\n")
                                    connectCommand = True
                                else:
                                    mud.sendMessage(id,
                                                    "CONNECT login failed: " +
                                                    "player already in " +
                                                    "game\n\n")
                            else:
                                mud.sendMessage(id,
                                                "CONNECT login failed\n\n")
                    command = ''

                if not connectCommand:
                    if not terminalMode.get(str(id)):
                        if command.strip().isdigit():
                            mud.sendMessage(
                                id, "\n<f220>Name cannot be a digit")
                            mud.sendMessage(id,
                                            "Press ENTER to continue...\n\n")
                            command = ''

                        if len(command.strip()) < 2:
                            mud.sendMessage(
                                id,
                                "\n<f220>Name must be at least two characters")
                            mud.sendMessage(id,
                                            "Press ENTER to continue...\n\n")
                            command = ''

                    strId = str(id)
                    if terminalEmulator(command, params, mud, id):
                        terminalMode[strId] = True
                        log("Player ID " + strId +
                            " logged into GCOS-3/TSS with command - " +
                            command + ' ' + params, "info")
                        command = ''
                    else:
                        if terminalMode.get(strId) is True:
                            mud.sendMessage(id, ">")

                if command:
                    pl = loadPlayer(command)

                # print(dbResponse)
                askForPassword = False
                if pl is not None and not connectCommand:
                    if pl.get('name'):
                        players[id]['name'] = pl['name']
                        strId = str(id)
                        log("Player ID " + strId +
                            " has requested existing user [" + command + "]",
                            "info")
                        mud.sendMessage(id, 'Hi <u><f32>' + command + '<r>!')
                        mud.sendMessage(id,
                                        '<f15>What is your password?<r>\n\n')
                        askForPassword = True

                if not askForPassword:
                    if not connectCommand:
                        if not terminalMode.get(str(id)):
                            mud.sendMessage(
                                id,
                                '<f202>User <f32>' +
                                command +
                                '<r> was not found!\n')
                            mud.sendMessage(id,
                                            '<f15>What is your username?\n\n')
                            strId = str(id)
                            log("Player ID " + strId +
                                " has requested non existent user [" +
                                command + "]", "info")
                    else:
                        mud.sendMessage(id, 'Hi <u><f32>' +
                                        players[id]['name'] + '<r>!\n\n')
            else:
                # New player creation here
                if not os.path.isfile(".disableRegistrations"):
                    players[id]['idleStart'] = int(time.time())
                    strId = str(id)
                    log("Player ID " + strId +
                        " has initiated character creation.", "info")
                    mud.sendMessage(
                        id,
                        "<f220>Welcome Traveller! So you have decided " +
                        "to create an account, that's awesome! Thank " +
                        "you for your interest in AberMUSH, hope you " +
                        "enjoy yourself while you're here.")
                    mud.sendMessage(
                        id,
                        "Note: You can type 'startover' at any time to " +
                        "restart the character creation process.\n")
                    mud.sendMessage(
                        id, "<f230>Press ENTER to continue...\n\n")
                    # mud.sendMessage(id,
                    #                  "<f220>What is going to be your name?")
                    # Set eAttribute0 to 1000, signifying this client has
                    # initialised a player creation process.
                    players[id]['exAttribute0'] = 1000
                else:
                    mud.sendMessage(
                        id, "<f220>New registrations are closed at this time.")
                    mud.sendMessage(
                        id, "<f230>Press ENTER to continue...\n\n")
        elif (players[id]['name'] is not None and
              players[id]['authenticated'] is None):
            pl = loadPlayer(players[id]['name'])
            # print(pl)
            dbPass = pl['pwd']

            if players[id]['name'] == 'Guest':
                dbPass = hash_password(pl['pwd'])

            if terminalMode.get(str(id)) is True:
                taken = True
                if not terminalEmulator(players[id]['name'], '', mud, id):
                    if players[id]['name'].startswith('restart') or \
                       players[id]['name'].startswith('shutdown'):
                        terminalMode[str(id)] = False
                        mud.sendMessage(id, "\nBYE\n\n")
                    else:
                        mud.sendMessage(id, ">")
                        strId = str(id)
                        log("Player ID " + strId +
                            " logged into GCOS-3/TSS with command - " +
                            players[id]['name'], "info")
            else:
                if terminalEmulator(players[id]['name'], '', mud, id):
                    terminalMode[str(id)] = True
                    taken = True
                    strId = str(id)
                    log("Player ID " + strId +
                        " logged into GCOS-3/TSS with command - " +
                        players[id]['name'], "info")

            playerFound = playerInGame(id, players[id]['name'], players)
            if verify_password(dbPass, command):
                if not playerFound:
                    initialSetupAfterLogin(mud, id, players, pl)
                    familiarRecall(mud, players, id, npcs, npcsDB)
                else:
                    mud.sendMessage(
                        id, '<f202>This character is already in the world!')
                    strId = str(id)
                    log("Player ID " + strId +
                        " has requested a character which is already in " +
                        "the world!", "info")
                    players[id]['name'] = None
                    mud.sendMessage(id, '<f15>What is your username? ')
            else:
                mud.sendMessage(id, '<f202>Password incorrect!\n')
                strId = str(id)
                log("Player ID " + strId + " has failed authentication",
                    "info")
                players[id]['name'] = None
                mud.sendMessage(id, '<f15>What is your username? ')

        else:
            players[id]['idleStart'] = int(time.time())
            if players[id]['exAttribute0'] < 1000:
                if len(command) > 0:
                    commandLower = command.lower()
                    runCommand(commandLower, params, mud, playersDB,
                               players, rooms, npcsDB, npcs, itemsDB,
                               itemsInWorld, envDB, env, scriptedEventsDB,
                               eventSchedule, id, fights, corpses, blocklist,
                               mapArea, characterClassDB, spellsDB,
                               sentimentDB, guildsDB, clouds, racesDB)
    previousTiming = \
        showTiming(previousTiming, "player commands")
