__filename__ = "abermush.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski", "Mark Frimston"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Command Interface"

import os
import json
import ssl
import argparse
import sys
import datetime
import time
import glob

# import random generator library
import random
from random import randint

# import config parser
import configparser

from functions import deepcopy
from functions import show_timing
from functions import log
from functions import save_state
from functions import save_universe
from functions import add_to_scheduler
from functions import load_player
from functions import load_players_db
from functions import send_to_channel
from functions import hash_password
from functions import verify_password
from functions import load_blocklist
from functions import set_race
from functions import str2bool
from functions import language_path

from commands import run_command
from combat import npc_aggression
from combat import run_fights
from combat import players_rest
from combat import update_temporary_hit_points
from combat import update_temporary_incapacitation
from combat import update_temporary_charm
from combat import update_magic_shield
from playerconnections import initial_setup_after_login
from playerconnections import run_player_connections
from playerconnections import disconnect_idle_players
from playerconnections import player_in_game
from npcs import npc_respawns
from npcs import run_npcs
from npcs import run_mobile_items
from npcs import npcs_rest
from familiar import familiar_recall
from reaper import remove_corpses
from reaper import run_deaths
from scheduler import run_schedule
from scheduler import run_environment
from scheduler import run_messages
from environment import plot_clouds
from environment import players_fishing
from environment import assign_terrain_difficulty
from environment import assign_coordinates
from environment import generate_cloud
from environment import get_temperature
from environment import find_room_collisions
from environment import map_level_as_csv
from environment import assign_environment_to_rooms
from history import assign_items_history
from worldmap import export_mmp
from markets import assign_markets
from traps import run_traps
from tests import run_all_tests

from gcos import terminal_emulator

# import the MUD server class
from mudserver import MudServer


def _command_options() -> None:
    """Parse the command options
    """
    parser = argparse.ArgumentParser(description='AberMUSH Server')
    parser.add_argument("--tests", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Run unit tests")
    parser.add_argument("--debug", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Debug mode")
    parser.add_argument('--mapLevel', dest='mapLevel', type=int,
                        default=None,
                        help='Shows a vertical map level as a CSV')
    parser.add_argument('--language', dest='language', type=str,
                        default=None,
                        help='Language used')
    parser.add_argument("--mmp", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Map in MMP XML format")
    args = parser.parse_args()
    if args.tests:
        run_all_tests()
        sys.exit()

    log("", "Server Boot")

    log("", "Loading configuration file")

    # load the configuration file
    config = configparser.ConfigParser()
    config.read('config.ini')
    # example of config file usage
    # print(str(config.get('Database', 'Hostname')))

    # Declare rooms dictionary
    rooms = {}

    # Environments for rooms
    environments = {}

    # Declare NPC database dict
    npcs_db = {}

    # Declare NPCs dictionary
    npcs = {}

    # Declare NPCs master (template) dict
    npcs_template = {}

    # Declare env dict
    env = {}

    # Declare env database dict
    env_db = {}

    # Declare fights dict
    fights = {}

    # Declare corpses dict
    corpses = {}

    # Declare items dict
    items_db = {}

    # Declare items_in_world dict
    items_in_world = {}

    # Declare scripted_events_db list
    scripted_events_db = []

    # Declare event_schedule dict
    event_schedule = {}

    # Declare channels message queue dictionary
    channels = {}

    # Specify allowed player idle time
    allowed_player_idle = int(config.get('World', 'IdleTimeBeforeDisconnect'))

    # websocket settings
    websocket_tls = False
    websocket_cert = None
    websocket_key = None
    websocket_ver = ssl.PROTOCOL_TLS_SERVER
    if 'true' in config.get('Web', 'tlsEnabled').lower():
        websocket_tls = True
        # resolve any symbolic links with realpath
        websocket_cert = os.path.realpath(str(config.get('Web', 'tlsCert')))
        websocket_key = os.path.realpath(str(config.get('Web', 'tlsKey')))

    log("Loading sentiment...", "info")

    sentiment_filename_json = str(config.get('Sentiment', 'Definition'))
    sentiment_filename_json = language_path(sentiment_filename_json,
                                            args.language, True)
    with open(sentiment_filename_json, "r", encoding='utf-8') as fp_read:
        sentiment_db = json.loads(fp_read.read())

    count_str = str(len(sentiment_db))
    log("Sentiment loaded: " + count_str, "info")

    log("Loading cultures...", "info")

    cultures_db = None
    cultures_filename_json = str(config.get('Cultures', 'Definition'))
    cultures_filename_json = language_path(cultures_filename_json,
                                           args.language, True)
    with open(cultures_filename_json, "r", encoding='utf-8') as fp_read:
        cultures_db = json.loads(fp_read.read())

    count_str = str(len(cultures_db))
    log("Cultures loaded: " + count_str, "info")

    log("Loading rooms...", "info")

    # Loading rooms
    if os.path.isfile("universe.json"):
        with open("universe.json", "r", encoding='utf-8') as fp_read:
            rooms = json.loads(fp_read.read())
        # Clear room coordinates
        for _, rm in rooms.items():
            rm['coords'] = []
    else:
        rooms_filename_json = str(config.get('Rooms', 'Definition'))
        rooms_filename_json = language_path(rooms_filename_json,
                                            args.language, True)
        with open(rooms_filename_json, "r", encoding='utf-8') as fp_read:
            rooms = json.loads(fp_read.read())

    for room_id, rm in rooms.items():
        room_id = room_id.replace('$rid=', '').replace('$', '')
        if not os.path.isfile('images/rooms/' + str(room_id)):
            if not args.mapLevel:
                print('Missing room image: ' + str(room_id))

    count_str = str(len(rooms))
    log("Rooms loaded: " + count_str, "info")

    log("Loading environments...", "info")
    environments_filename_json = str(config.get('Environments', 'Definition'))
    environments_filename_json = language_path(environments_filename_json,
                                               args.language, True)
    with open(environments_filename_json, "r", encoding='utf-8') as fp_read:
        environments = json.loads(fp_read.read())
    percent_assigned = str(assign_environment_to_rooms(environments, rooms))
    log(percent_assigned + '% of rooms have environments assigned', "info")

    max_terrain_difficulty = assign_terrain_difficulty(rooms)

    max_terrain_difficulty_str = str(max_terrain_difficulty)
    log("Terrain difficulty calculated. max=" +
        max_terrain_difficulty_str, "info")

    # Loading Items
    if os.path.isfile("universe_items.json"):
        try:
            with open("universe_items.json", "r", encoding='utf-8') as fp_read:
                items_in_world = json.loads(fp_read.read())
        except OSError:
            print('WARN: unable to load universe_items.json')

    if os.path.isfile("universe_itemsdb.json"):
        try:
            with open("universe_itemsdb.json", "r",
                      encoding='utf-8') as fp_read:
                items_db = json.loads(fp_read.read())
        except OSError:
            print('WARN: unable to load universe_itemsdb.json')

    if not items_db:
        items_filename_json = str(config.get('Items', 'Definition'))
        items_filename_json = language_path(items_filename_json,
                                            args.language, True)
        with open(items_filename_json, "r", encoding='utf-8') as fp_read:
            items_db = json.loads(fp_read.read())

    output_dict = {}
    for key, value in items_db.items():
        output_dict[int(key)] = value

    items_db = output_dict

    item_history = {}
    item_history_filename_json = str(config.get('ItemHistory', 'Definition'))
    item_history_filename_json = language_path(item_history_filename_json,
                                               args.language, True)
    with open(item_history_filename_json, "r", encoding='utf-8') as fp_read:
        item_history = json.loads(fp_read.read())
    item_ctr = assign_items_history(items_db, item_history)
    item_ctr_str = str(item_ctr)
    log('Assigned history to ' + item_ctr_str + ' items', "info")

    items_fields_excluded = (
        "name",
        "long_description",
        "short_description",
        "open_description",
        "open_failed_description",
        "close_description",
        "room",
        "language",
        "culture",
        "state",
        "visibleWhenWearing",
        "climbWhenWearing",
        "respawnInRegion",
        "type",
        "writeWithItems",
        "written",
        "written_description",
        "contains",
        "climbThrough",
        "damage",
        "damageChart",
        "cost",
        "range",
        "heave",
        "jumpTo",
        "game",
        "gameState",
        "exit",
        "exitName",
        "moveTimes",
        "conditional",
        "takeFail",
        "climbFail",
        "cardPack",
        "itemName",
        "chessBoardName",
        "morrisBoardName",
        "article"
    )

    for _, itemobj in items_db.items():
        for v in itemobj:
            if v not in items_fields_excluded:
                itemobj[v] = int(itemobj[v])

    count_str = str(len(items_db))
    log("Items loaded: " + count_str, "info")

    # Load scripted event declarations from disk
    files = glob.glob(str(config.get('Events', 'Location')) + "/*.event")
    counter = 0
    for file in files:
        counter += 1
        with open(file, 'r', encoding='utf-8') as f:
            # print(file)
            lines = [line.rstrip() for line in f.readlines()[2:]]
            for file_line in lines[1:]:
                if len(file_line) > 0:
                    scripted_events_db.append([lines[0]] +
                                              file_line.split('|'))

    count_str = str(counter)
    log("Scripted Events loaded: " + count_str, "info")

    map_area = \
        assign_coordinates(rooms, items_db, scripted_events_db, environments)

    if args.mmp:
        export_mmp(rooms, environments, 'mmp.xml')
        print('Map exported to mmp.xml')
        sys.exit()

    if args.mapLevel is not None:
        map_level_as_csv(rooms, args.mapLevel)
        sys.exit()

    # check that there are no room collisions
    find_room_collisions(rooms)

    map_area_str = str(map_area)
    log("Map coordinates:" + map_area_str, "info")

    # Loading environment actors
    if os.path.isfile("universe_actors.json"):
        try:
            with open("universe_actors.json", "r",
                      encoding='utf-8') as read_file:
                env = json.loads(read_file.read())
        except OSError:
            print('WARN: unable to load universe_actors.json')

    if os.path.isfile("universe_actorsdb.json"):
        try:
            with open("universe_actorsdb.json", "r",
                      encoding='utf-8') as read_file:
                env_db = json.loads(read_file.read())
        except OSError:
            print('WARN: unable to load universe_actorsdb.json')

    if not env_db:
        actors_filename_json = str(config.get('Actors', 'Definition'))
        actors_filename_json = language_path(actors_filename_json,
                                             args.language, True)
        with open(actors_filename_json, "r", encoding='utf-8') as read_file:
            env_db = json.loads(read_file.read())

    output_dict = {}
    for key, value in env_db.items():
        output_dict[int(key)] = value

    env_db = output_dict

    env_fields_excluded = (
        "name",
        "room",
        "vocabulary"
     )

    for _, envobj in env_db.items():
        if not os.path.isfile("universe_actors.json"):
            envobj['vocabulary'] = envobj['vocabulary'].split('|')
        for v in envobj:
            if v not in env_fields_excluded:
                envobj[v] = int(envobj[v])

    count_str = str(len(env_db))
    log("Environment Actors loaded: " + count_str, "info")

    if args.debug:
        # List ENV dictionary for debugging purposes
        print(env)
        print("Test:")
        for x in env:
            print(x)
            for y in env[x]:
                print(y, ':', env[x][y])

    log("Loading NPCs...", "info")
    if os.path.isfile("universe_npcsdb.json"):
        try:
            with open("universe_npcsdb.json", "r",
                      encoding='utf-8') as fp_read:
                npcs_db = json.loads(fp_read.read())
        except OSError:
            print('WARN: unable to load universe_npcsdb.json')

    if not npcs_db:
        npcs_filename_json = str(config.get('NPCs', 'Definition'))
        npcs_filename_json = language_path(npcs_filename_json,
                                           args.language, True)
        with open(npcs_filename_json, "r", encoding='utf-8') as fp_read:
            npcs_db = json.loads(fp_read.read())

    output_dict = {}
    for key, value in npcs_db.items():
        output_dict[int(key)] = value

    npcs_db = output_dict

    npcs_fields_excluded = (
        "name",
        "room",
        "inv",
        "visibleWhenWearing",
        "climbWhenWearing",
        "speakLanguage",
        "language",
        "culture",
        "race",
        "familiarOf",
        "familiarTarget",
        "familiarType",
        "familiarMode",
        "animalType",
        "archetype",
        "characterClass",
        "proficiencies",
        "fightingStyle",
        "enemy",
        "tempCharmTarget",
        "guild",
        "guildRole",
        "affinity",
        "preparedSpells",
        "spellSlots",
        "conv",
        "path",
        "moveTimes",
        "follow",
        "moveDelay",
        "moveType",
        "vocabulary",
        "inDescription",
        "outDescription",
        "lookDescription",
        "lastRoom",
        "loot",
        "frozenDescription",
        "bodyType",
        "whenDied"
    )

    for _, npc1 in npcs_db.items():
        npc1['lastRoom'] = None
        npc1['whenDied'] = None
        if not os.path.isfile("universe_npcs.json"):
            npc1['vocabulary'] = npc1['vocabulary'].split('|')
        for v in npc1:
            if v not in npcs_fields_excluded:
                npc1[v] = int(npc1[v])

    count_str = str(len(npcs_db))
    log("NPCs loaded: " + count_str, "info")

    races_filename_json = str(config.get('Races', 'Definition'))
    races_filename_json = language_path(races_filename_json,
                                        args.language, True)
    with open(races_filename_json, "r", encoding='utf-8') as fp_read:
        races_db = json.loads(fp_read.read())

    count_str = str(len(races_db))
    log("Races loaded: " + count_str, "info")

    character_class_filename_json = \
        str(config.get('CharacterClass', 'Definition'))
    character_class_filename_json = \
        language_path(character_class_filename_json,
                      args.language, True)
    with open(character_class_filename_json, "r", encoding='utf-8') as fp_read:
        character_class_db = json.loads(fp_read.read())

    count_str = str(len(character_class_db))
    log("Character Classes loaded: " + count_str, "info")

    spells_filename_json = str(config.get('Spells', 'Definition'))
    spells_filename_json = language_path(spells_filename_json,
                                         args.language, True)
    with open(spells_filename_json, "r", encoding='utf-8') as fp_read:
        spells_db = json.loads(fp_read.read())

    count_str = str(len(spells_db))
    log("Spells loaded: " + count_str, "info")

    guilds_filename_json = str(config.get('Guilds', 'Definition'))
    guilds_filename_json = language_path(guilds_filename_json,
                                         args.language, True)
    with open(guilds_filename_json, "r", encoding='utf-8') as fp_read:
        guilds_db = json.loads(fp_read.read())

    count_str = str(len(guilds_db))
    log("Guilds loaded: " + count_str, "info")

    attacks_filename_json = str(config.get('Attacks', 'Definition'))
    attacks_filename_json = language_path(attacks_filename_json,
                                          args.language, True)
    with open(attacks_filename_json, "r", encoding='utf-8') as fp_read:
        attack_db = json.loads(fp_read.read())

    count_str = str(len(attack_db))
    log("Attacks loaded: " + count_str, "info")

    if args.debug:
        # List NPC dictionary for debugging purposes
        print(" ")
        print("LIVE:")
        print(npcs_db)
        print(" ")
        for x in npcs_db:
            print(x)
            for y in npcs_db[x]:
                print(y, ':', npcs_db[x][y])

        # List items for debugging purposes
        print("TEST:")
        for x in items_db:
            print(x)
            for y in items_db[x]:
                print(y, ':', items_db[x][y])
        print(items_db)

    # Load registered players DB
    players_db = load_players_db()
    count_str = str(len(players_db))
    log("Registered players: " + count_str, "info")

    # Execute Reserved Event 1 and 2
    # Using -1 for target since no players can be targeted with an event at
    # this time
    log("Executing boot time events", "info")
    add_to_scheduler(1, -1, event_schedule, scripted_events_db)
    add_to_scheduler(2, -1, event_schedule, scripted_events_db)
    add_to_scheduler(3, -1, event_schedule, scripted_events_db)

    # Declare number of seconds to elapse between State Saves
    # A State Save takes values held in memory and updates the database
    # at set intervals to achieve player state persistence
    state_save_interval = int(config.get('World', 'StateSaveInterval'))
    state_save_inter_str = str(state_save_interval)
    log("State Save interval: " + state_save_inter_str + " seconds", "info")

    # Set last state save to 'now' on server boot
    last_state_save = int(time.time())

    # Deepcopy npcs fetched from a database into a master template
    npcs_template = deepcopy(npcs)

    if args.debug:
        # List items in world for debugging purposes
        for x in items_in_world:
            print(x)
            for y in items_in_world[x]:
                print(y, ':', items_in_world[x][y])

    # stores the players in the game
    players = {}

    # list of players
    player_list = []

    # start the server
    mud = MudServer(websocket_tls, websocket_cert, websocket_key,
                    websocket_ver)

    # weather
    curr_hour = datetime.datetime.today().hour
    curr_min = datetime.datetime.today().minute
    days_since_epoch = (datetime.datetime.today() -
                        datetime.datetime(1970, 1, 1)).days
    day_mins = (curr_hour * 60) + curr_min
    random.seed((days_since_epoch * 1440) + day_mins)
    last_weather_update = int(time.time())
    last_mobile_items_update = last_weather_update
    last_npcs_update = last_weather_update
    weather_update_interval = 120
    mobile_items_update_interval = 4
    npcs_update_interval = 2
    fishing_update_interval = 120
    last_fishing_update = int(time.time())
    clouds = {}
    cloud_grid = {}
    tile_size = 2
    temperature = get_temperature()
    r1 = random.Random((days_since_epoch * 1440) + day_mins)
    wind_direction = int(r1.random() * 359)
    wind_direction = \
        generate_cloud(r1, rooms, map_area, clouds,
                       cloud_grid, tile_size, wind_direction)
    wind_direction_str = str(wind_direction)
    log("Clouds generated. Wind direction " + wind_direction_str, "info")

    last_temp_hit_points_update = int(time.time())
    temp_hit_points_update_interval = 60

    last_room_teleport = int(time.time())
    room_teleport_interval = 60

    last_rest_update = int(time.time())

    blocklist = []
    if load_blocklist("blocked.txt", blocklist):
        log("Blocklist loaded", "info")

    terminal_mode = {}

    markets_filename_json = str(config.get('Markets', 'Definition'))
    markets_filename_json = language_path(markets_filename_json,
                                          args.language, True)
    with open(markets_filename_json, "r", encoding='utf-8') as fp_read:
        markets = json.loads(fp_read.read())
        no_of_markets = str(assign_markets(markets, rooms, items_db,
                                           cultures_db))
        markets_str = str(no_of_markets)
        log(markets_str + ' markets were created', "info")

    previous_timing = time.time()

    # main game loop. We loop forever (i.e. until the program is terminated)
    while True:
        # print(int(time.time()))

        # automatic teleport from one room to another every N seconds
        now = int(time.time())
        if now >= last_room_teleport + room_teleport_interval:
            last_room_teleport = now
            for _, plyr in players.items():
                rm = plyr['room']
                if rm:
                    if rooms[rm].get('roomTeleport'):
                        plyr['room'] = rooms[rm]['roomTeleport']

        previous_timing = \
            show_timing(previous_timing, "teleport every N seconds",
                        args.debug)

        previous_timing2 = time.time()

        now = int(time.time())
        if now >= \
           last_temp_hit_points_update + temp_hit_points_update_interval:
            last_temp_hit_points_update = now
            update_temporary_hit_points(mud, players, False)
            update_temporary_hit_points(mud, npcs, True)

            previous_timing = \
                show_timing(previous_timing, "update hit points", args.debug)

            update_temporary_incapacitation(mud, players, False)
            update_temporary_incapacitation(mud, npcs, True)

            previous_timing = \
                show_timing(previous_timing, "update incapacitation",
                            args.debug)

            update_temporary_charm(mud, players, False)
            update_temporary_charm(mud, npcs, True)

            update_magic_shield(mud, players, False)
            update_magic_shield(mud, npcs, True)

            previous_timing = \
                show_timing(previous_timing, "update charm", args.debug)

            run_traps(mud, rooms, players, npcs)

            previous_timing = \
                show_timing(previous_timing, "update traps", args.debug)

        previous_timing = \
            show_timing(previous_timing2, "various updates", args.debug)

        now = int(time.time())
        if now >= last_weather_update + weather_update_interval:
            last_weather_update = now
            previous_timing = \
                show_timing(previous_timing, "get temperature", args.debug)
            if args.debug:
                temperature = get_temperature()
                print("Temperature " + str(temperature))
            wind_direction = \
                generate_cloud(r1, rooms, map_area, clouds, cloud_grid,
                               tile_size, wind_direction)
            previous_timing = \
                show_timing(previous_timing, "calc wind directions",
                            args.debug)
            if args.debug:
                plot_clouds(rooms, map_area, clouds, temperature)

        if now >= last_fishing_update + fishing_update_interval:
            players_fishing(players, rooms, items_db, mud)
            last_fishing_update = now

        # update player list
        player_list = []
        for _, plyr in players.items():
            if plyr['name'] is not None and \
               plyr['authenticated'] is not None:
                if plyr['name'] not in player_list:
                    player_list.append(plyr['name'])

        previous_timing = \
            show_timing(previous_timing, "update player list", args.debug)

        # Aggressive NPCs may attack players
        npc_aggression(npcs, players, fights, mud, items_in_world,
                       items_db, races_db, rooms)

        previous_timing = \
            show_timing(previous_timing, "update npc attacks", args.debug)

        # pause for 1/5 of a second on each loop, so that we don't constantly
        # use 100% CPU time
        time.sleep(0.1)
        # print(event_schedule)

        previous_timing = \
            show_timing(previous_timing, "sleep", args.debug)

        # 'update' must be called in the loop to keep the game running and give
        # us up-to-date information
        mud.update()

        previous_timing = \
            show_timing(previous_timing, "update mud", args.debug)

        if disconnect_idle_players(mud, players, allowed_player_idle,
                                   players_db):
            players_db = load_players_db()

        previous_timing = \
            show_timing(previous_timing, "disconnect idle platers", args.debug)

        # Check if State Save is due and execute it if required
        now = int(time.time())
        if int(now >= last_state_save + state_save_interval):
            send_to_channel("Server", "system",
                            "Saving server state...", channels)
            # State Save logic Start
            players_were_saved = False
            for _, pl in players.items():
                if pl['authenticated'] is not None:
                    save_state(pl, players_db, False)
                    players_were_saved = True
            if players_were_saved:
                players_db = load_players_db()
                save_universe(rooms, npcs_db, npcs,
                              items_db, items_in_world,
                              env_db, env, guilds_db)
            last_state_save = now

        previous_timing = \
            show_timing(previous_timing, "save game", args.debug)

        # Handle Player Deaths
        run_deaths(mud, players, npcs, corpses, fights,
                   event_schedule, scripted_events_db)

        previous_timing = \
            show_timing(previous_timing, "handle deaths", args.debug)

        # Handle Fights
        run_fights(mud, players, npcs, fights, items_in_world, items_db, rooms,
                   max_terrain_difficulty, map_area, clouds, races_db,
                   character_class_db, guilds_db, attack_db)

        previous_timing = \
            show_timing(previous_timing, "update fights", args.debug)

        # Some items can appear only at certain times
        if now >= last_mobile_items_update + mobile_items_update_interval:
            run_mobile_items(items_db, items_in_world, event_schedule,
                             scripted_events_db, rooms, map_area, clouds)
            last_mobile_items_update = now

            previous_timing = \
                show_timing(previous_timing, "update mobile items", args.debug)

        # Iterate through NPCs, check if its time to talk, then check if
        # anyone is attacking it
        if now >= last_npcs_update + npcs_update_interval:
            run_npcs(mud, npcs, players, fights, corpses, scripted_events_db,
                     items_db, npcs_template, rooms, map_area, clouds,
                     event_schedule)
            last_npcs_update = now

            previous_timing = \
                show_timing(previous_timing, "update npcs", args.debug)

        run_environment(mud, players, env)

        previous_timing = \
            show_timing(previous_timing, "update environment", args.debug)

        remove_corpses(corpses)

        previous_timing = \
            show_timing(previous_timing, "remove dead", args.debug)

        npc_respawns(npcs)

        previous_timing = \
            show_timing(previous_timing, "respawns", args.debug)

        run_schedule(mud, event_schedule, players, npcs, items_in_world, env,
                     npcs_db, env_db)

        previous_timing = \
            show_timing(previous_timing, "schedule", args.debug)

        run_messages(mud, channels, players)

        previous_timing = \
            show_timing(previous_timing, "messages", args.debug)

        channels.clear()

        run_player_connections(mud, players, players_db, fights,
                               config, terminal_mode)

        previous_timing = \
            show_timing(previous_timing, "player connections", args.debug)

        # rest restores hp and allows spell learning
        now = int(time.time())
        if now >= last_rest_update + 1:
            last_rest_update = now
            players_rest(mud, players)
            npcs_rest(npcs)

        previous_timing = \
            show_timing(previous_timing, "resting", args.debug)

        # go through any new commands sent from players
        for id, command, params in mud.get_commands():
            # if for any reason the player isn't in the player map, skip them
            # and move on to the next one
            if id not in players:
                continue

            if command.lower() == "startover" and \
               players[id]['exAttribute0'] is not None and \
               players[id]['authenticated'] is None:
                if not os.path.isfile(".disableRegistrations"):
                    players[id]['idleStart'] = int(time.time())
                    mud.send_message(
                        id, "<f220>Ok, Starting character creation " +
                        "from the beginning!\n")
                    players[id]['exAttribute0'] = 1000

            if command.lower() == "exit" and \
               players[id]['exAttribute0'] is not None and \
               players[id]['authenticated'] is None:
                players[id]['idleStart'] = int(time.time())
                mud.send_message(id,
                                 "<f220>Ok, leaving the character creation.\n")
                players[id]['exAttribute0'] = None
                mud.send_message(
                    id,
                    "<f15>What is your username?<r>\n<f246>Type " +
                    "'<f253>new<r><f246>' to create a character.\n\n")
                id_str = str(id)
                log("Player ID " + id_str +
                    " has aborted character creation.", "info")
                break

            if players[id]['exAttribute0'] == 1000:
                players[id]['idleStart'] = int(time.time())
                # First step of char creation
                known_str = "<f220>\nBy what name do you wish to be known?\n\n"
                mud.send_message(id, known_str)
                players[id]['exAttribute0'] = 1001
                break

            if players[id]['exAttribute0'] == 1001:
                players[id]['idleStart'] = int(time.time())
                taken = False

                if not taken and terminal_mode.get(str(id)) is True:
                    taken = True
                    if terminal_emulator(command, params, mud, id):
                        terminal_mode[str(id)] = True
                        id_str = str(id)
                        log("Player ID " + id_str +
                            " logged into GCOS-3/TSS with command - " +
                            command + ' ' + params, "info")
                    else:
                        if command.startswith('restart') or \
                           command.startswith('shutdown'):
                            terminal_mode[str(id)] = False
                            mud.send_message(id, "\nBYE\n\n")
                        else:
                            mud.send_message(id, ">")
                            id_str = str(id)
                            log("Player ID " + id_str +
                                " logged into GCOS-3/TSS with command - " +
                                command + ' ' + params, "info")

                if not taken and not terminal_mode.get(str(id)):
                    if command.strip().isdigit():
                        mud.send_message(
                            id, "\n<f220>Name cannot be a digit")
                        mud.send_message(id, "Press ENTER to continue...\n\n")
                        taken = True

                    if not taken:
                        if len(command.strip()) < 2:
                            mud.send_message(
                                id,
                                "\n<f220>Name must be at least two characters")
                            mud.send_message(id,
                                             "Press ENTER to continue...\n\n")
                            taken = True

                    if not taken:
                        for _, plyr in players_db.items():
                            if plyr['name'].lower() == command.lower():
                                mud.send_message(
                                    id, "\n<f220>This character name is " +
                                    "already taken!")
                                mud.send_message(id,
                                                 "Press ENTER to continue" +
                                                 "...\n\n")
                                taken = True
                                break

                if not taken:
                    if terminal_emulator(command, params, mud, id):
                        terminal_mode[str(id)] = True
                        taken = True
                        str_id = str(id)
                        log("Player ID " + str_id +
                            " logged into GCOS-3/TSS with command - " +
                            command + ' ' + params, "info")
                    else:
                        if terminal_mode.get(str(id)) is True:
                            mud.send_message(id, ">")
                            str_id = str(id)
                            log("Player ID " + str_id +
                                " logged into GCOS-3/TSS with command - " +
                                command + ' ' + params, "info")

                if not taken:
                    players[id]['exAttribute1'] = command.strip()
                    mud.send_message(
                        id, "<f220>Now what would you like your " +
                        "password to be?\n\n")
                    players[id]['exAttribute0'] = 1002
                    break
                players[id]['idleStart'] = int(time.time())
                players[id]['exAttribute0'] = 1000
                break

            if players[id]['exAttribute0'] == 1002:
                # store the password
                mud.send_message(id, "<f220>\nOk, got that.\n")
                players[id]['exAttribute2'] = command.strip()

                players[id]['idleStart'] = int(time.time())
                mud.send_message(id, "<f220>\nSelect your character race:\n\n")
                ctr = 0
                types_str = '  '
                for name, _ in races_db.items():
                    if ctr > 0:
                        types_str = types_str + ', <f220>' + name + '<r>'
                    else:
                        types_str = types_str + '<f220>' + name + '<r>'
                    ctr += 1
                    if ctr > 7:
                        types_str = types_str + '\n  '
                        ctr = 0
                mud.send_message(id, types_str + '\n\n')
                players[id]['exAttribute0'] = 1003
                break

            if players[id]['exAttribute0'] == 1003:
                players[id]['idleStart'] = int(time.time())
                selected_race = command.lower().strip()
                if not races_db.get(selected_race):
                    mud.send_message(
                        id, "<f220>\nUnrecognized character race.<r>\n\n")
                    players[id]['exAttribute0'] = 1000
                    mud.send_message(
                        id,
                        "<f15>What is your username?<r>\n<f246>Type " +
                        "'<f253>new<r><f246>' to create a character.\n\n")
                    break

                if not os.path.isfile("witches"):
                    command = 'witch'
                    players[id]['exAttribute0'] = 1004
                else:
                    mud.send_message(
                        id, "<f220>\nSelect your character class:\n\n")
                    ctr = 0
                    class_str = '  '
                    for name, _ in character_class_db.items():
                        if name in ('witch', 'ghost'):
                            continue
                        if ctr > 0:
                            class_str = class_str + ', <f220>' + name + '<r>'
                        else:
                            class_str = class_str + '<f220>' + name + '<r>'
                        ctr += 1
                        if ctr > 7:
                            class_str = class_str + '\n  '
                            ctr = 0
                    mud.send_message(id, class_str + '\n\n')
                    players[id]['exAttribute0'] = 1004
                    break

            if players[id]['exAttribute0'] == 1004:
                players[id]['idleStart'] = int(time.time())
                selected_character_class = command.lower().strip()
                unrecognized = False
                if selected_character_class == 'witch':
                    if os.path.isfile("witches"):
                        unrecognized = True

                if not character_class_db.get(selected_character_class) or \
                   selected_character_class == 'ghost':
                    unrecognized = True

                if unrecognized:
                    mud.send_message(
                        id, "<f220>\nUnrecognized character class.<r>\n\n")
                    players[id]['exAttribute0'] = 1000
                    mud.send_message(
                        id,
                        "<f15>What is your username?<r>\n<f246>Type " +
                        "'<f253>new<r><f246>' to create a character.\n\n")
                    break

                # Load the player template from a file
                player_template_filename_json = \
                    str(config.get('Players', 'Location')) + \
                    "/player.template"
                player_template_filename_json = \
                    language_path(player_template_filename_json,
                                  args.language, True)
                with open(player_template_filename_json, "r",
                          encoding='utf-8') as fp_read:
                    template = json.loads(fp_read.read())

                set_race(template, races_db, selected_race)

                # Make required changes to template before saving again into
                # <Name>.player
                template['name'] = players[id]['exAttribute1']
                template['pwd'] = hash_password(players[id]['exAttribute2'])

                template['characterClass'] = selected_character_class

                # initial money
                mfield = 'startingMoney'
                starting_money_roll = \
                    character_class_db[selected_character_class][mfield]
                die = int(starting_money_roll.split('d')[1])
                no_of_rolls = int(starting_money_roll.split('d')[0])
                starting_gp = 0
                for _ in range(no_of_rolls):
                    starting_gp += int(randint(1, die + 1) * 10)
                template['gp'] = starting_gp

                # First player becomes a witch
                if not os.path.isfile("witches"):
                    template['characterClass'] = 'witch'
                    # admin speaks all languages
                    template['language'] = []
                    for _, race_stats in races_db.items():
                        for lang in race_stats['language']:
                            if lang not in template['language']:
                                template['language'].append(lang)
                    template['language'].append('cant')
                    with open("witches", "w", encoding='utf-8') as fp_witches:
                        fp_witches.write(template['name'])

                # populate initial inventory from character class
                template['inv'] = []
                ch_class = template['characterClass']
                for inv_item in character_class_db[ch_class]['inv']:
                    template['inv'].append(inv_item)

                # populate proficencies from character class
                template['proficiencies'] = []
                idx = template['characterClass']
                for prof in character_class_db[idx][str(template['lvl'])]:
                    template['proficiencies'].append(prof)

                # additional languages for the character class
                for lang in character_class_db[idx]['extraLanguage']:
                    template['language'].append(lang)

                # Save template into a new player file
                # print(template)
                with open(str(config.get('Players', 'Location')) + "/" +
                          template['name'] + ".player", 'w',
                          encoding='utf-8') as fp_player:
                    fp_player.write(json.dumps(template))

                # Reload PlayersDB to include this newly created player
                players_db = load_players_db()

                players[id]['exAttribute0'] = None
                mud.send_message(
                    id,
                    '<f220>Your character has now been created, ' +
                    'you can log in using credentials you have provided.\n')
                # mud.send_message(id, '<f15>What is your username?')
                mud.send_message(
                    id,
                    "<f15>What is your username?<r>\n<f246>Type " +
                    "'<f253>new<r><f246>' to create a character.\n\n")
                str_id = str(id)
                log("Player ID " + str_id +
                    " has completed character creation [" +
                    template['name'] + "].", "info")
                break

            # if the player hasn't given their name yet, use this first
            # command as their name and move them to the starting room.
            if players[id]['name'] is None and \
               players[id]['exAttribute0'] is None:
                if command.lower() != "new":
                    players[id]['idleStart'] = int(time.time())
                    pl = None

                    # check for logins with CONNECT username password
                    connect_str = command.strip().lower()
                    connect_command = False
                    if connect_str.lower() == 'connect':
                        mud.send_message(id, "Login via CONNECT\n\n")
                        if ' ' in params:
                            connect_username = params.split(' ', 1)[0]
                            players[id]['name'] = connect_username
                            connect_password = params.split(' ', 1)[1].strip()
                            pl = load_player(connect_username)
                            if pl:
                                db_pass = pl['pwd']
                                if connect_username == 'Guest':
                                    db_pass = hash_password(pl['pwd'])
                                if verify_password(db_pass, connect_password):
                                    if not player_in_game(id, connect_username,
                                                          players):
                                        players[id]['exAttribute1'] = \
                                            connect_username
                                        players[id]['exAttribute2'] = \
                                            connect_password
                                        players[id]['exAttribute0'] = None
                                        initial_setup_after_login(mud, id,
                                                                  players, pl)
                                        familiar_recall(mud, players, id,
                                                        npcs, npcs_db)
                                        mud.send_message(id,
                                                         "CONNECT login " +
                                                         "success\n\n")
                                        connect_command = True
                                    else:
                                        mud.send_message(id,
                                                         "CONNECT " +
                                                         "login failed: " +
                                                         "player already in " +
                                                         "game\n\n")
                                else:
                                    mud.send_message(id,
                                                     "CONNECT " +
                                                     "login failed\n\n")
                        command = ''

                    if not connect_command:
                        if not terminal_mode.get(str(id)):
                            if command.strip().isdigit():
                                mud.send_message(
                                    id, "\n<f220>Name cannot be a digit")
                                mud.send_message(id,
                                                 "Press ENTER to continue" +
                                                 "...\n\n")
                                command = ''

                            if len(command.strip()) < 2:
                                mud.send_message(
                                    id, "\n<f220>" +
                                    "Name must be at least two characters")
                                mud.send_message(id,
                                                 "Press ENTER to continue" +
                                                 "...\n\n")
                                command = ''

                        str_id = str(id)
                        if terminal_emulator(command, params, mud, id):
                            terminal_mode[str_id] = True
                            log("Player ID " + str_id +
                                " logged into GCOS-3/TSS with command - " +
                                command + ' ' + params, "info")
                            command = ''
                        else:
                            if terminal_mode.get(str_id) is True:
                                mud.send_message(id, ">")

                    if command:
                        pl = load_player(command)

                    # print(dbResponse)
                    ask_for_password = False
                    if pl is not None and not connect_command:
                        if pl.get('name'):
                            players[id]['name'] = pl['name']
                            str_id = str(id)
                            log("Player ID " + str_id +
                                " has requested existing user [" +
                                command + "]", "info")
                            mud.send_message(id, 'Hi <u><f32>' +
                                             command + '<r>!')
                            mud.send_message(id, '<f15>' +
                                             'What is your password?<r>\n\n')
                            ask_for_password = True

                    if not ask_for_password:
                        if not connect_command:
                            if not terminal_mode.get(str(id)):
                                mud.send_message(
                                    id,
                                    '<f202>User <f32>' +
                                    command +
                                    '<r> was not found!\n')
                                mud.send_message(id,
                                                 '<f15>' +
                                                 'What is your username?\n\n')
                                str_id = str(id)
                                log("Player ID " + str_id +
                                    " has requested non existent user [" +
                                    command + "]", "info")
                        else:
                            mud.send_message(id, 'Hi <u><f32>' +
                                             players[id]['name'] + '<r>!\n\n')
                else:
                    # New player creation here
                    if not os.path.isfile(".disableRegistrations"):
                        players[id]['idleStart'] = int(time.time())
                        str_id = str(id)
                        log("Player ID " + str_id +
                            " has initiated character creation.", "info")
                        mud.send_message(
                            id,
                            "<f220>Welcome Traveller! So you have decided " +
                            "to create an account, that's awesome! Thank " +
                            "you for your interest in AberMUSH, hope you " +
                            "enjoy yourself while you're here.")
                        mud.send_message(
                            id,
                            "Note: You can type 'startover' at any time to " +
                            "restart the character creation process.\n")
                        mud.send_message(
                            id, "<f230>Press ENTER to continue...\n\n")
                        # mud.send_message(id,
                        #         "<f220>What is going to be your name?")
                        # Set eAttribute0 to 1000, signifying this client has
                        # initialised a player creation process.
                        players[id]['exAttribute0'] = 1000
                    else:
                        mud.send_message(
                            id,
                            "<f220>New registrations are closed at this time.")
                        mud.send_message(
                            id, "<f230>Press ENTER to continue...\n\n")
            elif (players[id]['name'] is not None and
                  players[id]['authenticated'] is None):
                pl = load_player(players[id]['name'])
                # print(pl)
                db_pass = ''
                if pl:
                    db_pass = pl['pwd']

                if players[id]['name'] == 'Guest':
                    db_pass = hash_password(db_pass)

                if terminal_mode.get(str(id)) is True:
                    taken = True
                    if not terminal_emulator(players[id]['name'], '', mud, id):
                        if players[id]['name'].startswith('restart') or \
                           players[id]['name'].startswith('shutdown'):
                            terminal_mode[str(id)] = False
                            mud.send_message(id, "\nBYE\n\n")
                        else:
                            mud.send_message(id, ">")
                            str_id = str(id)
                            log("Player ID " + str_id +
                                " logged into GCOS-3/TSS with command - " +
                                players[id]['name'], "info")
                else:
                    if terminal_emulator(players[id]['name'], '', mud, id):
                        terminal_mode[str(id)] = True
                        taken = True
                        str_id = str(id)
                        log("Player ID " + str_id +
                            " logged into GCOS-3/TSS with command - " +
                            players[id]['name'], "info")

                player_found = player_in_game(id, players[id]['name'], players)
                if verify_password(db_pass, command):
                    if not player_found:
                        initial_setup_after_login(mud, id, players, pl)
                        familiar_recall(mud, players, id, npcs, npcs_db)
                    else:
                        mud.send_message(
                            id,
                            '<f202>This character is already in the world!')
                        str_id = str(id)
                        log("Player ID " + str_id +
                            " has requested a character which is already in " +
                            "the world!", "info")
                        players[id]['name'] = None
                        mud.send_message(id, '<f15>What is your username? ')
                else:
                    mud.send_message(id, '<f202>Password incorrect!\n')
                    str_id = str(id)
                    log("Player ID " + str_id + " has failed authentication",
                        "info")
                    players[id]['name'] = None
                    mud.send_message(id, '<f15>What is your username? ')

            else:
                players[id]['idleStart'] = int(time.time())
                if players[id]['exAttribute0'] < 1000:
                    if len(command) > 0:
                        command_lower = command.lower()
                        run_command(command_lower, params, mud, players_db,
                                    players, rooms, npcs_db, npcs, items_db,
                                    items_in_world, env_db, env,
                                    scripted_events_db,
                                    event_schedule, id, fights,
                                    corpses, blocklist,
                                    map_area, character_class_db, spells_db,
                                    sentiment_db, guilds_db, clouds, races_db,
                                    item_history, markets, cultures_db)
        previous_timing = \
            show_timing(previous_timing, "player commands", args.debug)


if __name__ == "__main__":
    argb2, opt2 = _command_options()
