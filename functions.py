__filename__ = "functions.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Core"

import time
import os
import json
import errno
# from copy import deepcopy
import configparser
import hashlib
import binascii
from random import randint

# example of config file usage
# print(str(Config.get('Database', 'Hostname')))
Config = configparser.ConfigParser()
Config.read('config.ini')

WEAR_LOCATION = (
    'head', 'neck', 'lwrist', 'rwrist', 'larm', 'rarm',
    'chest', 'feet', 'lfinger', 'rfinger', 'back',
    'lleg', 'rleg', 'gloves'
)

_dispatcher = {}


def _copy_list(list_to_copy: [], dispatch):
    """Copy a list
    """
    ret = list_to_copy.copy()
    for idx, item in enumerate(ret):
        cp1 = dispatch.get(type(item))
        if cp1 is not None:
            ret[idx] = cp1(item, dispatch)
    return ret


def _copy_dict(d, dispatch):
    """Copy a dict
    """
    ret = d.copy()
    for key, value in ret.items():
        cp1 = dispatch.get(type(value))
        if cp1 is not None:
            ret[key] = cp1(value, dispatch)

    return ret


_dispatcher[list] = _copy_list
_dispatcher[dict] = _copy_dict


def deepcopy(sth):
    """Deep copy an object
    """
    cp1 = _dispatcher.get(type(sth))
    if cp1 is None:
        return sth
    return cp1(sth, _dispatcher)


def time_string_to_sec(duration_str: str) -> int:
    """Converts a description of a duration such as '1 hour'
       into a number of seconds
    """
    if ' ' not in duration_str:
        return 1
    dur = duration_str.lower().split(' ')
    if dur[1].startswith('s'):
        return int(dur[0])
    if dur[1].startswith('min'):
        return int(dur[0]) * 60
    if dur[1].startswith('hour') or dur[1].startswith('hr'):
        return int(dur[0]) * 60 * 60
    if dur[1].startswith('day'):
        return int(dur[0]) * 60 * 60 * 24
    return 1


def get_sentiment(text: str, sentiment_db: {}) -> int:
    """Returns a sentiment score for the given text
       which can be positive or negative
    """
    text_lower = text.lower()
    sentiment = 0
    for word, value in sentiment_db.items():
        if word in text_lower:
            sentiment = sentiment + value
    return sentiment


def get_guild_sentiment(players: {}, id, npcs: {}, p, guilds: {}) -> int:
    """Returns the sentiment of the guild of the first player
    towards the second
    """
    if not players[id].get('guild'):
        return 0
    if not players[id].get('guildRole'):
        return 0
    guild_name = players[id]['guild']
    if not guilds.get(guild_name):
        return 0
    other_player_name = npcs[p]['name']
    if not guilds[guild_name]['affinity'].get(other_player_name):
        return 0
    # NOTE: this could be adjusted by the strength of affinity
    # between the player and the guild, but for now it's just hardcoded
    return int(guilds[guild_name]['affinity'][other_player_name] / 2)


def _baseline_affinity(players, id):
    """Returns the average affinity value for the player
    """
    average_affinity = 0
    ctr = 0
    for name, value in players[id]['affinity'].items():
        average_affinity = average_affinity + value
        ctr += 1

    if ctr > 0:
        average_affinity = int(average_affinity / ctr)

    if average_affinity == 0:
        average_affinity = 1
    return average_affinity


def increase_affinity_between_players(players: {}, id, npcs: {},
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

    recipient_name = npcs[p]['name']
    if players[id]['affinity'].get(recipient_name):
        if players[id]['affinity'][recipient_name] < max_affinity:
            players[id]['affinity'][recipient_name] += 1
    else:
        # set the affinity to an assumed average
        players[id]['affinity'][recipient_name] = \
            _baseline_affinity(players, id)

    # adjust guild affinity
    if players[id].get('guild') and players[id].get('guildRole'):
        guild_name = players[id]['guild']
        if guilds.get(guild_name):
            guild = guilds[guild_name]
            if guild['affinity'].get(recipient_name):
                if guild['affinity'][recipient_name] < max_affinity:
                    guild['affinity'][recipient_name] += 1
            else:
                guild['affinity'][recipient_name] = \
                    _baseline_affinity(players, id)


def decrease_affinity_between_players(players: {}, id, npcs: {},
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

    recipient_name = npcs[p]['name']
    if players[id]['affinity'].get(recipient_name):
        if players[id]['affinity'][recipient_name] > min_affinity:
            players[id]['affinity'][recipient_name] -= 1

        # Avoid zero values
        if players[id]['affinity'][recipient_name] == 0:
            players[id]['affinity'][recipient_name] = -1
    else:
        # set the affinity to an assumed average
        players[id]['affinity'][recipient_name] = \
            _baseline_affinity(players, id)

    # adjust guild affinity
    if players[id].get('guild') and players[id].get('guildRole'):
        guild_name = players[id]['guild']
        if guilds.get(guild_name):
            guild = guilds[guild_name]
            if guild['affinity'].get(recipient_name):
                if guild['affinity'][recipient_name] > min_affinity:
                    guild['affinity'][recipient_name] -= 1
                # Avoid zero values
                if guild['affinity'][recipient_name] == 0:
                    guild['affinity'][recipient_name] = -1
            else:
                guild['affinity'][recipient_name] = \
                    _baseline_affinity(players, id)


def random_desc(description_list):
    if isinstance(description_list, list):
        desc_list = description_list
    else:
        if '|' in description_list:
            desc_list = description_list.split('|')
        else:
            return description_list
    return desc_list[randint(0, len(desc_list) - 1)]


def levelUp(id, players, character_class_db, increment):
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
            for prof in character_class_db[idx][str(players[id]['lvl'])]:
                if prof not in players[id]['proficiencies']:
                    players[id]['proficiencies'].append(prof)


def stow_hands(id, players: {}, items_db: {}, mud):
    """Stows items held
    """
    if int(players[id]['clo_rhand']) > 0:
        item_id = int(players[id]['clo_rhand'])
        mud.send_message(
            id, 'You stow <b234>' +
            items_db[item_id]['article'] +
            ' ' +
            items_db[item_id]['name'] +
            '<r>\n\n')
        players[id]['clo_rhand'] = 0

    if int(players[id]['clo_lhand']) > 0:
        item_id = int(players[id]['clo_lhand'])
        mud.send_message(
            id, 'You stow <b234>' +
            items_db[item_id]['article'] +
            ' ' +
            items_db[item_id]['name'] +
            '<r>\n\n')
        players[id]['clo_lhand'] = 0


def size_from_description(description: str):
    """Returns the size of an entiry based on its description
    """
    tiny_entity = (
        'tiny', 'moth', 'butterfly', 'insect', 'beetle', 'ant',
        'bee', 'wasp', 'hornet', 'mosquito', 'lizard', 'mouse',
        'rat', 'crab', 'roach', 'snail', 'slug', 'hamster',
        'gerbil'
    )
    small_entity = (
        'small', 'dog', 'cat', 'weasel', 'otter', 'owl', 'hawk',
        'crow', 'rook', 'robin', 'penguin', 'bird', 'pidgeon',
        'wolf', 'badger', 'fox', 'rat', 'dwarf', 'mini', 'fish',
        'lobster', 'koala', 'gremlin', 'goblin', 'hare'
    )
    large_entity = (
        'large', 'tiger', 'lion', 'tiger', 'wolf', 'leopard',
        'bear', 'elk', 'deer', 'horse', 'bison', 'moose',
        'kanga', 'zebra', 'oxe', 'beest', 'troll', 'taur'
    )
    huge_entity = (
        'huge', 'ogre', 'elephant', 'mastodon', 'giraffe', 'titan'
    )
    gargantuan_entity = (
        'gargantuan', 'dragon', 'whale'
    )
    smaller_entity = (
        'young', 'child', 'cub', 'kitten', 'puppy', 'juvenile',
        'kid'
    )
    description2 = description.lower()
    size = 2
    for ent in tiny_entity:
        if ent in description2:
            size = 0
            break
    for ent in small_entity:
        if ent in description2:
            size = 1
            break
    for ent in large_entity:
        if ent in description2:
            size = 3
            break
    for ent in huge_entity:
        if ent in description2:
            size = 4
            break
    for ent in gargantuan_entity:
        if ent in description2:
            size = 5
            break
    if size > 0:
        for ent in smaller_entity:
            if ent in description2:
                size = size - 1
                break

    return size


def update_player_attributes(id, players: {},
                             items_db: {}, item_id: str, mult: int):
    player_attributes = ('luc', 'per', 'cha', 'int', 'cool', 'exp')
    for attr in player_attributes:
        players[id][attr] = \
            players[id][attr] + \
            (mult * items_db[item_id]['mod_' + attr])
    # experience returns to zero
    items_db[item_id]['mod_exp'] = 0


def player_inventory_weight(id, players, items_db):
    """Returns the total weight of a player's inventory
    """
    if len(list(players[id]['inv'])) == 0:
        return 0

    weight = 0
    for i in list(players[id]['inv']):
        weight = weight + items_db[int(i)]['weight']

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


def _silent_remove(filename: str):
    """Function to silently remove file
    """
    try:
        os.remove(filename)
    except OSError as ex:
        if ex.errno != errno.ENOENT:
            raise


def load_players_db(force_lowercase=True):
    """Function to load all registered players from JSON files
    """
    locn = Config.get('Players', 'Location')
    location = str(locn)
    db1 = {}
    player_files = \
        [i for i in os.listdir(location)
         if os.path.splitext(i)[1] == ".player"]
    for fil in player_files:
        print('Player: ' + fil)
        with open(os.path.join(location, fil)) as file_object:
            db1[fil] = json.loads(file_object.read())

            # add any missing fields
            if not db1[fil].get('culture'):
                db1[fil]['culture'] = ""
            if 'magicShield' not in db1[fil]:
                db1[fil]['magicShield'] = 0
                db1[fil]['magicShieldStart'] = 0
                db1[fil]['magicShieldDuration'] = 0
            if 'isFishing' in db1[fil]:
                del db1[fil]['isFishing']

    if force_lowercase is True:
        out = {}
        for key, value in db1.items():
            out[key.lower()] = value

        return out
    return db1


def log(content, type):
    """Function used for logging messages to stdout and a disk file
    """
    # logfile = './dum.log'
    logfile = str(Config.get('Logs', 'ServerLog'))
    print(str(time.strftime("%d/%m/%Y") + " " +
              time.strftime("%I:%M:%S") + " [" + type + "] " + content))
    if os.path.exists(logfile):
        log1 = open(logfile, 'a')
    else:
        log1 = open(logfile, 'w')
    log1.write(str(time.strftime("%d/%m/%Y") + " " +
                   time.strftime("%I:%M:%S") +
                   " [" + type + "] " + content) + '\n')
    log1.close()


def get_free_key(items_dict, start=None):
    """Function for returning a first available key value for appending a new
    element to a dictionary
    """
    if start is None:
        try:
            for x_co in range(0, len(items_dict) + 1):
                if len(items_dict[x_co]) > 0:
                    pass
        except BaseException:
            pass
        return x_co
    else:
        found = False
        while found is False:
            if start in items_dict:
                start += 1
            else:
                found = True
        return start


def get_free_room_key(rooms):
    """Function for returning a first available room key value for appending a
    room element to a dictionary
    """
    max_room_id = -1
    for rmkey in rooms.keys():
        room_id_str = rmkey.replace('$', '').replace('rid=', '')
        if len(room_id_str) == 0:
            continue

        room_id = int(room_id_str)
        if room_id > max_room_id:
            max_room_id = room_id

    if max_room_id > -1:
        return '$rid=' + str(max_room_id + 1) + '$'
    return ''


def add_to_scheduler(event_id, target_id, scheduler, database):
    """Function for adding events to event scheduler
    """
    if isinstance(event_id, int):
        for item in database:
            if int(item[0]) == event_id:
                scheduler[get_free_key(scheduler)] = {
                    'time': int(time.time() + int(item[1])),
                    'target': int(target_id),
                    'type': item[2],
                    'body': item[3]
                }
    elif isinstance(event_id, str):
        item = event_id.split('|')
        scheduler[get_free_key(scheduler)] = {
            'time': int(time.time() + int(item[0])),
            'target': int(target_id),
            'type': item[1],
            'body': item[2]
        }


def load_player(name: str) -> dict:
    location = str(Config.get('Players', 'Location'))
    try:
        with open(os.path.join(location, name + ".player"), "r") as read_file:
            return json.loads(read_file.read())
    except BaseException:
        pass
    return {}


def _get_player_path():
    locn = Config.get('Players', 'Location')
    return str(locn) + "/"


def _save_player(player, main_db: {}, save_password: str):
    path = _get_player_path()
    dbase = load_players_db(force_lowercase=False)
    for plyr in dbase:
        if (player['name'] + ".player").lower() == plyr.lower():
            with open(path + plyr, "r") as read_file:
                temp = json.loads(read_file.read())
            _silent_remove(path + player['name'] + ".player")
            new_player = deepcopy(temp)
            new_player['pwd'] = temp['pwd']
            for key in new_player:
                if key != "pwd" or save_password:
                    if player.get(key):
                        new_player[key] = player[key]

            with open(path + player['name'] + ".player", 'w') as fp_pla:
                fp_pla.write(json.dumps(new_player))
            load_players_db()


def save_state(player, main_db: {}, save_password: str):
    """Saves a player state
    """
    _save_player(player, main_db, save_password)
    # main_db = load_players_db()


def save_universe(rooms: {}, npcs_db: {}, npcs: {},
                  items_db: {}, items: {},
                  env_db: {}, env: {}, guilds_db: {}):
    """Saves the state of the universe
    """
    # save rooms
    if os.path.isfile('universe.json'):
        os.rename('universe.json', 'universe2.json')
    with open("universe.json", 'w') as fp_uni:
        fp_uni.write(json.dumps(rooms))

    # save items
    if os.path.isfile('universe_items.json'):
        os.rename('universe_items.json', 'universe_items2.json')
    with open("universe_items.json", 'w') as fp_items:
        fp_items.write(json.dumps(items))

    # save items_db
    if os.path.isfile('universe_itemsdb.json'):
        os.rename('universe_itemsdb.json', 'universe_itemsdb2.json')
    with open("universe_itemsdb.json", 'w') as fp_items:
        fp_items.write(json.dumps(items_db))

    # save environment actors
    if os.path.isfile('universe_actorsdb.json'):
        os.rename('universe_actorsdb.json', 'universe_actorsdb2.json')
    with open("universe_actorsdb.json", 'w') as fp_actors:
        fp_actors.write(json.dumps(env_db))

    # save environment actors
    if os.path.isfile('universe_actors.json'):
        os.rename('universe_actors.json', 'universe_actors2.json')
    with open("universe_actors.json", 'w') as fp_actors:
        fp_actors.write(json.dumps(env))

    # save npcs
    if os.path.isfile('universe_npcs.json'):
        os.rename('universe_npcs.json', 'universe_npcs2.json')
    with open("universe_npcs.json", 'w') as fp_npcs:
        fp_npcs.write(json.dumps(npcs))

    # save npcs_db
    if os.path.isfile('universe_npcsdb.json'):
        os.rename('universe_npcsdb.json', 'universe_npcsdb2.json')
    with open("universe_npcsdb.json", 'w') as fp_npcs:
        fp_npcs.write(json.dumps(npcs_db))


def str2bool(v) -> bool:
    """Returns true if the given value is a boolean
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    return False


def send_to_channel(sender, channel, message, channels):
    # print("Im in!")
    channels[get_free_key(channels)] = {
        "channel": str(channel),
        "message": str(message),
        "sender": str(sender)}
    # print(channels)


def load_blocklist(filename, blocklist):
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


def save_blocklist(filename, blocklist):
    with open(filename, "w", encoding='utf-8') as blockfile:
        for blockedstr in blocklist:
            blockfile.write(blockedstr + '\n')


def set_race(template, races_db, name):
    """Set the player race
    """
    template['speakLanguage'] = races_db[name]['language'][0]
    template['language'].clear()
    template['language'].append(races_db[name]['language'][0])
    template['race'] = name
    template['str'] = races_db[name]['str']
    template['siz'] = races_db[name]['siz']
    template['per'] = races_db[name]['per']
    template['endu'] = races_db[name]['endu']
    template['cha'] = races_db[name]['cha']
    template['int'] = races_db[name]['int']
    template['agi'] = races_db[name]['agi']
    template['luc'] = races_db[name]['luc']
    template['cool'] = races_db[name]['cool']
    template['ref'] = races_db[name]['ref']


def prepare_spells(mud, id, players):
    """Player prepares spells, called once per second
    """
    if len(players[id]['prepareSpell']) == 0:
        return

    if players[id]['prepareSpellTime'] > 0:
        if players[id]['prepareSpellProgress'] >= \
           players[id]['prepareSpellTime']:
            spell_name = players[id]['prepareSpell']
            players[id]['preparedSpells'][spell_name] = 1
            players[id]['spellSlots'][spell_name] = 1
            players[id]['prepareSpell'] = ""
            players[id]['prepareSpellProgress'] = 0
            players[id]['prepareSpellTime'] = 0
            mud.send_message(
                id, "You prepared the spell <f220>" +
                spell_name + "<r>\n\n")
        else:
            players[id]['prepareSpellProgress'] = \
                players[id]['prepareSpellProgress'] + 1


def is_wearing(id, players: {}, item_list: []) -> bool:
    """Given a list of possible item IDs is the player wearing any of them?
    """
    if not item_list:
        return False

    for item_id in item_list:
        if not str(item_id).isdigit():
            print('is_wearing: ' + str(item_id) + ' is not a digit')
            continue
        item_id = int(item_id)
        for locn in WEAR_LOCATION:
            if int(players[id]['clo_' + locn]) == item_id:
                return True
        if int(players[id]['clo_lhand']) == item_id or \
           int(players[id]['clo_rhand']) == item_id:
            return True
    return False


def player_is_visible(mud, observerId: int, observers: {},
                      other_playerId: int, others: {}) -> bool:
    """Is the other player visible to the observer?
    """
    observerId = int(observerId)
    other_playerId = int(other_playerId)
    if not others[other_playerId].get('visibleWhenWearing'):
        return True
    if others[other_playerId].get('visibleWhenWearing'):
        if is_wearing(observerId, observers,
                      others[other_playerId]['visibleWhenWearing']):
            return True
    return False


def message_to_room_players(mud, players, id, msg):
    # go through all the players in the game
    for pid, _ in list(players.items()):
        # if player is in the same room and isn't the player
        # sending the command
        if players[pid]['room'] == players[id]['room'] and \
           pid != id:
            if player_is_visible(mud, pid, players, id, players):
                mud.send_message(pid, msg)


def show_timing(previous_timing, comment_str: str):
    """Shows the length of time since the previous benchmark
    """
    curr_time = time.time()
    # timeDiff = int((curr_time - previous_timing) * 1000)
    # print('TIMING: ' + comment_str + ' = ' + str(timeDiff) + 'mS')
    return curr_time


def player_is_prone(id, players: {}) -> bool:
    """Returns true if the given player is prone
    """
    if players[id].get('prone'):
        if players[id]['prone'] == 1:
            return True
    return False


def set_player_prone(id, players: {}, prone: bool) -> None:
    """Sets the prone state for a player
    """
    if prone:
        players[id]['prone'] = 1
    else:
        players[id]['prone'] = 0


def parse_cost(cost_str: str) -> (int, str):
    """Parses a cost string and returns quantity and denomination
    """
    denomination = None
    if cost_str.endswith('gp'):
        denomination = 'gp'
    elif cost_str.endswith('sp'):
        denomination = 'sp'
    elif cost_str.endswith('cp'):
        denomination = 'cp'
    elif cost_str.endswith('ep'):
        denomination = 'ep'
    elif cost_str.endswith('pp'):
        denomination = 'pp'
    if not denomination:
        return None, None
    qty = int(cost_str.replace(denomination, ''))
    return qty, denomination


def item_in_room(items: {}, id, room):
    for i in items.items():
        if i[1]['room'] == room:
            if id == i[1]['id']:
                return True
    return False


def language_path(filename: str, language: str,
                  check: bool) -> str:
    """returns a language specific version of the given filename
    """
    if not language:
        return filename
    if len(language) < 2:
        return filename
    language = language.lower()
    if '/' + language + '/' in filename:
        return filename
    if '/' in filename:
        file_str = filename.split('/')[-1]
        new_filename = filename.replace('/' + file_str,
                                        '/' + language + '/' + file_str)
    else:
        new_filename = '/' + language + '/' + filename

    if check:
        if os.path.isfile(new_filename):
            filename = new_filename
    else:
        filename = new_filename
    return filename
