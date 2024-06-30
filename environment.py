__filename__ = "environment.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Environment Simulation"

from random import randint
import random
import math
from math import sin
import datetime
from functions import random_desc
import decimal
dec = decimal.Decimal

RAIN_THRESHOLD = 230


def run_tide() -> float:
    """Calculates the tide level as the addition of sine waves
    """
    lunar_orbit_mins = 39312

    days_since_epoch = (
        datetime.datetime.today() -
        datetime.datetime(
            1970,
            1,
            1)).days
    curr_hour = datetime.datetime.today().hour
    curr_min = datetime.datetime.today().minute
    time_mins = (days_since_epoch * 60 * 24) + (curr_hour * 60) + curr_min

    lunar_mins = time_mins % int(lunar_orbit_mins)
    solar_mins = time_mins % int(24 * 60 * 365)
    daily_mins = time_mins % int(24 * 60)

    lunar = sin(float(lunar_mins) * 2.0 * 3.1415927 /
                float(lunar_orbit_mins)) * 0.08
    solar = sin(float(solar_mins) * 2.0 * 3.1415927 /
                float(24 * 60 * 365)) * 0.02
    daily = sin(float(daily_mins) * 2.0 * 3.1415927 /
                float(24 * 60)) * 0.9

    return daily + lunar + solar


def assign_terrain_difficulty(rooms: {}) -> int:
    """Updates the terrain difficulty for each room and returns the maximum
    """
    terrain_difficulty_words = (
        'rock',
        'boulder',
        'slip',
        'steep',
        'rough',
        'volcan',
        'sewer',
        'sand',
        'pebble',
        'mountain',
        'algae',
        'mist',
        'slimy',
        'fog',
        'narrow',
        'bush',
        'dense',
        'trees',
        'forest',
        'tangle',
        'thick',
        'rubble',
        'ruin',
        'tough',
        'snow',
        'ice',
        'marsh')
    max_terrain_difficulty = 1
    for _, room in rooms.items():
        difficulty = room['terrainDifficulty']
        if difficulty == 0:
            room_description = room['description'].lower()
            difficulty = 0
            for wrd in terrain_difficulty_words:
                if wrd in room_description:
                    difficulty += 1
            room['terrainDifficulty'] = difficulty
        if difficulty > max_terrain_difficulty:
            max_terrain_difficulty = difficulty
    return max_terrain_difficulty


def _room_at_zero_coord(rooms: {}, room_id: str) -> bool:
    """Room is at coord 0,0,0
    """
    room = rooms[room_id]
    if not room.get('coords'):
        return False
    room_coord = room['coords']
    if len(room_coord) < 3:
        return False
    if room_coord[0] == 0 and \
       room_coord[1] == 0 and \
       room_coord[2] == 0:
        return True
    return False


def find_room_collisions(rooms: {}) -> None:
    """Marks rooms whose geolocations collide
    """
    ctr = 0
    total_ctr = 0
    room_dict = {}
    for room_id, _ in rooms.items():
        room_dict[ctr] = room_id
        ctr += 1
    ctr = 0
    for index1, _ in enumerate(rooms):
        rmid = room_dict[index1]
        if not rooms[rmid].get('coords'):
            continue
        # Room with coords
        if len(rooms[rmid]['coords']) <= 2:
            continue
        if _room_at_zero_coord(rooms, rmid):
            continue
        total_ctr += 1
        for index2 in range(index1, len(rooms)):
            rm2 = room_dict[index2]
            if not rooms[rm2].get('coords'):
                continue
            # Other room with coords
            if len(rooms[rm2]['coords']) <= 2:
                continue
            # not the same room
            if rm2 == rmid:
                continue
            if _room_at_zero_coord(rooms, rm2):
                continue
            if rooms[rmid]['coords'][0] != rooms[rm2]['coords'][0]:
                continue
            if rooms[rmid]['coords'][1] != rooms[rm2]['coords'][1]:
                continue
            if rooms[rmid]['coords'][2] != rooms[rm2]['coords'][2]:
                continue
            print('Collision between rooms ' +
                  str(rmid) + ' and ' + str(rm2))
            print(rooms[rmid]['name'] + ' ' + str(rooms[rmid]['coords']))
            print(rooms[rm2]['name'] + ' ' + str(rooms[rm2]['coords']))
            rooms[rmid]['collides'] = rm2
            ctr += 1
    if ctr > 0:
        print(str(ctr) + ' room collisions out of ' + str(total_ctr))


def _distance_between_rooms(rooms: {}, room_id: str, environments: {}) -> int:
    """Returns the travel distance between rooms, which depends upon
    the type of environment
    """
    if rooms[room_id].get('environmentId'):
        environment_id = rooms[room_id]['environmentId']
        env = environments[str(environment_id)]
        if 'collisions' in env:
            if env['collisions'] is False:
                return 0
        if env.get('travelDistance'):
            return env['travelDistance']
    return 1


def _is_on_map(rooms: {}, room_id: str, environments: {}) -> bool:
    """Returns true if the room should not be assigned map coordinates
    """
    if _distance_between_rooms(rooms, room_id, environments) == 0:
        return False
    return True


def _get_all_room_exits(rooms: {}, room_id: str) -> {}:
    """combine exits with virtual exists so that we know
    all the possible directions from here
    """
    curr_room = rooms[room_id]
    exit_dict = curr_room['exits'].copy()

    if curr_room.get('virtualExits'):
        exit_dict.update(curr_room['virtualExits'])

    if curr_room.get('tideOutExits'):
        exit_dict.update(curr_room['tideOutExits'])

    return exit_dict


def _assign_coords_to_surrounding_rooms(this_room: str, rooms: {},
                                        rooms_on_map: [], environments: {},
                                        other_rooms_found: []) -> bool:
    """Assigns coordinates to rooms surrounding one which has coordinates
    """
    exit_dict = rooms[this_room]['allExits']
    # distance moved between rooms
    distance = _distance_between_rooms(rooms, this_room, environments)
    directions = ('north', 'south', 'east', 'west', 'up', 'down')
    for ex, room_id in exit_dict.items():
        if room_id == this_room:
            continue
        if ex not in directions:
            continue
        if room_id not in rooms_on_map:
            continue
        # room which is exited to
        other_room = rooms[room_id]
        if other_room['coordsAssigned']:
            continue
        if not rooms[this_room].get('coords'):
            continue
        other_room['coords'] = rooms[this_room]['coords'].copy()
        # the other room does not have coordinates assigned
        if ex == 'north':
            other_room['coords'][0] += distance
        elif ex == 'south':
            other_room['coords'][0] -= distance
        elif ex == 'east':
            other_room['coords'][1] -= distance
        elif ex == 'west':
            other_room['coords'][1] += distance
        elif ex == 'up':
            other_room['coords'][2] += 1
        elif ex == 'down':
            other_room['coords'][2] -= 1
        other_room['coordsAssigned'] = True
        other_rooms_found.append(other_room)
    if other_rooms_found:
        return True
    return False


def _infer_coords_from_surrounding_rooms(this_room: str, rooms: {},
                                         rooms_on_map: [], environments: {},
                                         rooms_found: []) -> bool:
    """Infers the coordinates for the given room from the
    coordinates of the surrounding rooms
    """
    exit_dict = rooms[this_room]['allExits']
    directions = ('north', 'south', 'east', 'west', 'up', 'down')
    # Search the exits for rooms which have coords
    for ex, room_id in exit_dict.items():
        if room_id == this_room:
            continue
        if ex not in directions:
            continue
        if room_id not in rooms_on_map:
            continue
        # room which is exited to
        other_room = rooms[room_id]
        # if the other room has coorninates assigned
        if not other_room['coordsAssigned']:
            continue
        # distance moved between rooms
        distance = _distance_between_rooms(rooms, room_id, environments)
        # make this room relative to the other
        if not other_room.get('coords'):
            continue
        rooms[this_room]['coords'] = other_room['coords'].copy()
        if ex == 'north':
            rooms[this_room]['coords'][0] -= distance
        elif ex == 'south':
            rooms[this_room]['coords'][0] += distance
        elif ex == 'east':
            rooms[this_room]['coords'][1] += distance
        elif ex == 'west':
            rooms[this_room]['coords'][1] -= distance
        elif ex == 'up':
            rooms[this_room]['coords'][2] -= distance
        elif ex == 'down':
            rooms[this_room]['coords'][2] += distance
        rooms[this_room]['coordsAssigned'] = True
        return True
    return False


def _assign_relative_room_coords(rooms: {}, rooms_on_map: [],
                                 environments: {}) -> []:
    """Finds the next room without assigned coordinates
    """
    other_rooms_found = []

    for rmid in rooms_on_map:
        if not rooms[rmid]['coordsAssigned']:
            continue
        rooms_found = []
        if _assign_coords_to_surrounding_rooms(rmid, rooms,
                                               rooms_on_map, environments,
                                               rooms_found):
            if rooms_found:
                other_rooms_found += rooms_found
                break

    for rmid in rooms_on_map:
        if not rooms[rmid]['coordsAssigned']:
            if _infer_coords_from_surrounding_rooms(rmid, rooms,
                                                    rooms_on_map, environments,
                                                    other_rooms_found):
                other_rooms_found += [rooms[rmid]]
                break

    return other_rooms_found


def _find_rooms_without_coords(rooms: {}, rooms_on_map: [],
                               environments: {}) -> []:
    """Finds the next room without assigned coordinates
    """
    other_rooms = \
        _assign_relative_room_coords(rooms, rooms_on_map, environments)
    if other_rooms:
        return other_rooms

    # get the maximum east coordinate
    max_east = 0
    for rmid in rooms_on_map:
        if not rooms[rmid]['coordsAssigned']:
            continue
        if not rooms[rmid].get('coords'):
            continue
        if rooms[rmid]['coords'][1] > max_east:
            max_east = rooms[rmid]['coords'][1]

    # initial assignment of room coordinates
    no_of_rooms = len(rooms)
    for rmid in rooms_on_map:
        # Room should not yet have coords
        if rooms[rmid]['coordsAssigned']:
            continue
        # assign some initial coordinates
        rooms[rmid]['coordsAssigned'] = True
        rooms[rmid]['coords'] = [0, max_east + no_of_rooms, 0]
        return [rooms[rmid]]

    return []


def map_level_as_csv(rooms: {}, level: int):
    """Print a vertical level of the map as a CSV
    """
    min_x = 999999
    max_x = -999999
    min_y = 999999
    max_y = -999999

    for _, room in rooms.items():
        if not room.get('coords'):
            continue
        if not room['coordsAssigned']:
            continue
        if len(room['coords']) <= 2:
            continue
        if room['coords'][2] != level:
            continue
        x_co = room['coords'][1]
        y_co = room['coords'][0]
        if y_co < min_y:
            min_y = y_co
        if y_co > max_y:
            max_y = y_co
        if x_co < min_x:
            min_x = x_co
        if x_co > max_x:
            max_x = x_co

    w_co = max_x - min_x + 1
    h_co = max_y - min_y + 1
    grid = [[' ' for y_co in range(h_co)] for x_co in range(w_co)]

    map_str = ''
    for room_id, room in rooms.items():
        if not room.get('coords'):
            continue
        if not room['coordsAssigned']:
            continue
        if len(room['coords']) <= 2:
            continue
        if room['coords'][2] != level:
            continue
        x_co = room['coords'][1] - min_x
        y_co = room['coords'][0] - min_y
        rid = int(room_id.replace('$', '').replace('rid=', ''))
        grid[x_co][y_co] = str(rid) + ' ' + room['name']

        exit_dict = room['exits'].copy()
        if room.get('virtualExits'):
            exit_dict.update(room['virtualExits'])
        if room.get('tideOutExits'):
            exit_dict.update(room['tideOutExits'])

        if exit_dict.get('north'):
            if exit_dict.get('west'):
                grid[x_co][y_co] = '          ▲\n⮜ ' + grid[x_co][y_co]
            else:
                grid[x_co][y_co] = '          ▲\n  ' + grid[x_co][y_co]
        else:
            if exit_dict.get('west'):
                grid[x_co][y_co] = '⮜ ' + grid[x_co][y_co]
            else:
                grid[x_co][y_co] = '\n   ' + grid[x_co][y_co]
        if exit_dict.get('east'):
            grid[x_co][y_co] = grid[x_co][y_co] + ' ⮞'
        else:
            grid[x_co][y_co] = grid[x_co][y_co] + '   '
        if exit_dict.get('south'):
            grid[x_co][y_co] = grid[x_co][y_co] + '\n          ▼'
        else:
            grid[x_co][y_co] = grid[x_co][y_co] + '\n'
        grid[x_co][y_co] = '"\n' + grid[x_co][y_co] + '\n"'

    for yy1 in range(h_co):
        y_co = h_co - yy1 - 1
        line_str = ''
        for xx1 in range(w_co):
            x_co = w_co - xx1 - 1
            if grid[x_co][y_co] == ' ':
                line_str += ','
                continue
            line_str += grid[x_co][y_co] + ','
        map_str += line_str.strip() + '\n'

    filename = 'map_level_' + str(level) + '.csv'
    try:
        with open(filename, 'w+', encoding='utf-8') as csv_file:
            if csv_file:
                csv_file.write(map_str)
                print('Map level ' + str(level) + ' saved')
    except OSError:
        print('EX: map_level_as_csv ' + filename)


def _remove_coordinate_gaps(rooms: {}) -> None:
    """Removes gaps in the east line coordinates of rooms
    """
    max_east = 0
    for _, room in rooms.items():
        # Room without coords
        if not room.get('coords'):
            continue
        if not room['coordsAssigned']:
            continue
        if room['coords'][1] > max_east:
            max_east = room['coords'][1]

    east_line = [0] * (max_east + 1)
    for _, room in rooms.items():
        if not room.get('coords'):
            continue
        if not room['coordsAssigned']:
            continue
        e_co = room['coords'][1]
        east_line[e_co] = 1

    start_east = None
    gaps = []
    for e_co in range(max_east + 1):
        if not start_east:
            if east_line[e_co] == 0:
                start_east = e_co
        else:
            if east_line[e_co] == 1:
                if e_co - start_east > 5:
                    gaps = [[start_east, e_co - start_east]] + gaps
                start_east = None

    for g_co in gaps:
        start_east = g_co[0]
        gap_width = g_co[1]
        for _, room in rooms.items():
            if not room.get('coords'):
                continue
            if not room['coordsAssigned']:
                continue
            e_co = room['coords'][1]
            if e_co >= start_east:
                room['coords'][1] -= gap_width

    east_line = [0] * (max_east + 1)
    for _, room in rooms.items():
        if not room.get('coords'):
            continue
        if not room['coordsAssigned']:
            continue
        e_co = room['coords'][1]
        east_line[e_co] = 1

    start_east = None
    for e_co in range(max_east + 1):
        if not start_east:
            if east_line[e_co] == 0:
                start_east = e_co
        else:
            if east_line[e_co] == 1:
                if e_co - start_east > 5:
                    print('East line gap ' +
                          str(start_east) + ' -> ' + str(e_co - 1))
                start_east = None


def _create_virtual_exits(rooms: {}, items_db: {},
                          scripted_events_db: {}) -> None:
    """If there are any doors then this Generates the
    virtual exits dicts for each room
    """
    for _, room in rooms.items():
        room['virtualExits'] = {}

    # get a list of door items
    door_ctr = 0
    for item_id, itemobj in items_db.items():
        if not itemobj.get('exit'):
            continue
        if not itemobj.get('exitName'):
            continue
        if '|' not in itemobj['exitName']:
            continue
        room_id = None
        for event in scripted_events_db:
            if event[2] != 'spawnItem':
                continue
            event_item = event[3].split(';')
            if event_item[0] != str(item_id):
                continue
            room_id = event_item[1]
            break
        if room_id:
            exit_direction = itemobj['exitName'].split('|')[0]
            collides = False
            if rooms[room_id]['exits'].get(exit_direction):
                print('Room ' + room_id + ' has item ' +
                      str(item_id) + ' with colliding exit ' + exit_direction)
                collides = True

            if rooms[room_id].get('tideOutExits'):
                if rooms[room_id]['tideOutExits'].get(exit_direction):
                    print('Room ' + room_id + ' has item ' +
                          str(item_id) + ' with colliding tide out exit ' +
                          exit_direction)
                collides = True

            if not collides:
                exit_room_id = itemobj['exit']
                rooms[room_id]['virtualExits'][exit_direction] = exit_room_id
                door_ctr += 1
    print('Door items: ' + str(door_ctr))


def assign_coordinates(rooms: {}, items_db: {},
                       scripted_events_db: {}, environments: {}) -> []:
    """Assigns cartesian coordinates to each room and returns the limits
    """
    _create_virtual_exits(rooms, items_db, scripted_events_db)

    map_area = [
        [9999999999, -9999999999],
        [9999999999, -9999999999],
        [9999999999, -9999999999]
    ]

    # create a list of rooms which are on the map
    rooms_on_map = []
    for room_id, room in rooms.items():
        room['coordsAssigned'] = False
        if _is_on_map(rooms, room_id, environments):
            rooms_on_map.append(room_id)
        room['allExits'] = _get_all_room_exits(rooms, room_id)

    # assign coordinates
    while True:
        new_rooms = \
            _find_rooms_without_coords(rooms, rooms_on_map, environments)
        if not new_rooms:
            break
        for new_rm in new_rooms:
            if not new_rm.get('coords'):
                continue
            coords = new_rm['coords']
            # east/west extent
            if coords[1] > map_area[1][1]:
                map_area[1][1] = coords[1]
            if coords[1] < map_area[1][0]:
                map_area[1][0] = coords[1]

    # map out gaps in horizontal spacing
    min_east = map_area[1][0]
    max_east = map_area[1][1]
    occupied = [False] * ((max_east - min_east) + 1)
    for _, room in rooms.items():
        if not room.get('coords'):
            continue
        if len(room['coords']) > 1:
            occupied[room['coords'][1] - min_east] = True

    # remove the horizontal spacing to compact the map
    state = 0
    start_east = 0
    end_east = 0
    trim_coords = []
    for idx, _ in enumerate(occupied):
        if state == 0:
            if not occupied[idx]:
                state = 1
                start_east = idx
        elif state == 1:
            if occupied[idx]:
                state = 0
                end_east = idx
                trim_coords.append([start_east - min_east,
                                   end_east - min_east])

    max_range = len(trim_coords)
    map_area = [
        [9999999999, -9999999999],
        [9999999999, -9999999999],
        [9999999999, -9999999999]
    ]
    for i in range(max_range - 1, 0, -1):
        for _, room in rooms.items():
            if not room.get('coords'):
                continue
            if len(room['coords']) < 3:
                continue
            if room['coords'][1] >= trim_coords[i][1]:
                adjust = (trim_coords[i][1] - trim_coords[i][0]) - 2
                room['coords'][1] -= adjust

    _remove_coordinate_gaps(rooms)

    # recalculate the map area
    for _, room in rooms.items():
        if not room.get('coords'):
            continue
        coords = room['coords']
        if len(room['coords']) < 3:
            continue
        # north/south extent
        if coords[0] > map_area[0][1]:
            map_area[0][1] = coords[0]
        if coords[0] < map_area[0][0]:
            map_area[0][0] = coords[0]
        # east/west extent
        if coords[1] > map_area[1][1]:
            map_area[1][1] = coords[1]
        if coords[1] < map_area[1][0]:
            map_area[1][0] = coords[1]
        # up/down extent
        if coords[2] > map_area[2][1]:
            map_area[2][1] = coords[2]
        if coords[2] < map_area[2][0]:
            map_area[2][0] = coords[2]

    for _, room in rooms.items():
        del room['allExits']

    return map_area


def _highest_point_at_coord(rooms: {}, map_area: [], x: int, y: int) -> float:
    """Returns the highest elevation at the given location
    """
    highest = 0

    vertical_range = map_area[2][1] - map_area[2][0]
    if vertical_range < 1:
        vertical_range = 1

    for _, room in rooms.items():
        if not room.get('coords'):
            continue
        if len(room['coords']) < 3:
            continue
        if room['coords'][0] - map_area[0][0] != y:
            continue
        if room['coords'][1] - map_area[1][0] != x:
            continue
        if room['coords'][2] > highest:
            highest = room['coords'][2]

    return (highest - map_area[2][0]) * 255 / vertical_range


def generate_cloud(
        randnumgen: int,
        rooms: {},
        map_area: [],
        clouds: {},
        cloud_grid: {},
        tileSize: int,
        wind_direction: int) -> int:
    """Weather simulation
       This uses a simple cloud model adjusted for topology in which
       clouds get smaller as temperature increases and bigger with
       more chance of rain as temperature falls.
       Wind blows clouds in one of 8 possible directions, or can be still.
    """
    map_width = map_area[1][1] - map_area[1][0]
    map_height = map_area[0][1] - map_area[0][0]
    cloud_grid_width = int(map_width / tileSize)
    cloud_grid_height = int(map_height / tileSize)

    if len(clouds) == 0:
        # Generate the clouds map
        for x_co in range(0, map_width):
            clouds[x_co] = {}
            for y_co in range(0, map_height):
                clouds[x_co][y_co] = 0

    if len(cloud_grid) == 0:
        # Initialize clouds grid randomly
        # This is lower resolution than the map
        for x_co in range(0, cloud_grid_width):
            cloud_grid[x_co] = {}
            for y_co in range(0, cloud_grid_height):
                cloud_grid[x_co][y_co] = int(randnumgen.random() * 255)

    # Update clouds (same resolution as the map)
    for x_co in range(0, map_width - 1):
        tile_tx = int(x_co / tileSize)
        tile_bx = tile_tx + 1
        if tile_bx >= cloud_grid_width:
            tile_bx = 0
        for y_co in range(0, map_height - 1):
            tile_ty = int(y_co / tileSize)
            tile_by = tile_ty + 1
            if tile_by >= cloud_grid_height:
                tile_by = 0

            interpolate_top = \
                cloud_grid[tile_tx][tile_ty] + \
                int((cloud_grid[tile_bx][tile_ty] -
                     cloud_grid[tile_tx][tile_ty]) *
                    (x_co % tileSize) / tileSize)

            interpolate_bottom = \
                cloud_grid[tile_tx][tile_by] + \
                int((cloud_grid[tile_bx][tile_by] -
                     cloud_grid[tile_tx][tile_by]) *
                    (x_co % tileSize) / tileSize)

            clouds[x_co][y_co] = \
                interpolate_top + \
                int((interpolate_bottom - interpolate_top) *
                    (y_co % tileSize) / tileSize)

    # Clouds change
    for x_co in range(0, cloud_grid_width):
        for y_co in range(0, cloud_grid_height):
            cloud_grid[x_co][y_co] = cloud_grid[x_co][y_co] + \
                (int(randnumgen.random() * 11) - 5)
            if cloud_grid[x_co][y_co] < 0:
                cloud_grid[x_co][y_co] = cloud_grid[x_co][y_co] + 255
            if cloud_grid[x_co][y_co] > 255:
                cloud_grid[x_co][y_co] = cloud_grid[x_co][y_co] - 255

    # change wind direction
    wind_direction = (wind_direction + int(randnumgen.random() * 9) - 4) % 360
    if wind_direction < 0:
        wind_direction = wind_direction + 360

    # Which directions to shift the clouds
    dxx = 0
    dyy = 0
    if wind_direction >= 320 or wind_direction <= 40:
        dyy = 1
    if wind_direction in range(161, 201):
        dyy = -1
    if wind_direction in range(230, 300):
        dxx = -1
    if wind_direction in range(51, 131):
        dxx = 1

    # Move clouds in the wind direction
    cloud_grid_new = {}
    for x_co in range(0, cloud_grid_width):
        cloud_grid_new[x_co] = {}
        for y_co in range(0, cloud_grid_height):
            cloud_grid_new[x_co][y_co] = cloud_grid[x_co][y_co]

    for x_co in range(0, cloud_grid_width):
        old_x = x_co + dxx
        for y_co in range(0, cloud_grid_height):
            old_y = y_co + dyy
            if old_x in range(0, cloud_grid_width) and \
               old_y in range(0, cloud_grid_height):
                cloud_grid_new[x_co][y_co] = cloud_grid[old_x][old_y]
            else:
                if old_x < 0:
                    old_x = old_x + cloud_grid_width
                if old_y < 0:
                    old_y = old_y + cloud_grid_height
                if old_x > cloud_grid_width - 1:
                    old_x = old_x - cloud_grid_width
                if old_y > cloud_grid_height - 1:
                    old_y = old_y - cloud_grid_height
                cloud_grid_new[x_co][y_co] = randint(0, 255)

    for x_co in range(0, cloud_grid_width):
        for y_co in range(0, cloud_grid_height):
            cloud_grid[x_co][y_co] = cloud_grid_new[x_co][y_co]

    return wind_direction


def _get_cloud_threshold(temperature: float) -> float:
    """Temperature threshold at which cloud is formed
    """
    return (10 + temperature) * 7


def _altitude_temperature_adjustment(rooms: {}, map_area: [],
                                     x: int, y: int) -> float:
    """Temperature decreases with altitude
    """
    return _highest_point_at_coord(rooms, map_area, x, y) * 2.0 / 255.0


def _terrain_temperature_adjustment(temperature: float, rooms: {},
                                    map_area: [],
                                    x: int, y: int) -> float:
    """Temperature is adjusted for different types of terrain
    """
    terrain_freezing_words = ('snow', 'ice')
    terrain_cooling_words = (
        'rock',
        'steep',
        'sewer',
        'sea',
        'lake',
        'river',
        'stream',
        'water',
        'forest',
        'trees',
        'mist',
        'fog',
        'beach',
        'shore')
    terrain_heating_words = (
        'sun', 'lava', 'volcan', 'molten', 'desert', 'dry'
    )

    for _, room in rooms.items():
        if not room.get('coords'):
            continue
        coords = room['coords']
        if len(coords) < 2:
            continue
        if coords[0] - map_area[0][0] != y:
            continue
        if coords[1] - map_area[1][0] != x:
            continue
        room_description = room['description'].lower()
        for wrd in terrain_freezing_words:
            if wrd in room_description:
                temperature = temperature * 0.1
        for wrd in terrain_cooling_words:
            if wrd in room_description:
                temperature = temperature * 0.98
        for wrd in terrain_heating_words:
            if wrd in room_description:
                temperature = temperature * 1.05
    return temperature


def plot_clouds(rooms: {}, map_area: [], clouds: {},
                temperature: float) -> None:
    """Show clouds as ASCII diagram for debugging purposes
    """
    cloud_threshold = _get_cloud_threshold(temperature)
    map_width = map_area[1][1] - map_area[1][0]
    map_height = map_area[0][1] - map_area[0][0]

    for y_coord in range(0, map_height - 1):
        line_str = ''
        for x_coord in range(0, map_width - 1):
            map_temp = clouds[x_coord][y_coord] - \
                (_altitude_temperature_adjustment(rooms, map_area,
                                                  x_coord, y_coord) * 7)
            map_temp = _terrain_temperature_adjustment(
                map_temp, rooms, map_area, x_coord, y_coord)
            line_char = '.'
            if map_temp > cloud_threshold:
                line_char = 'o'
            if map_temp > RAIN_THRESHOLD:
                line_char = 'O'
            line_str = line_str + line_char
        print(line_str + '\n')
    print('\n')


def _get_temperature_seasonal() -> float:
    """Average temperature for the time of year
    """
    day_of_year = int(datetime.datetime.today().strftime("%j"))
    temp_fraction = (
        (sin((0.75 + (day_of_year / 365.0)) * 2 * 3.1415927) + 1) / 2.0)
    return 8 + (7 * temp_fraction)


def get_temperature() -> float:
    """Average daily seasonal temperature for the universe
    """
    av_temp = _get_temperature_seasonal()

    days_since_epoch = (
        datetime.datetime.today() -
        datetime.datetime(
            1970,
            1,
            1)).days

    # Temperature can vary randomly from one day to the next
    ran1 = random.Random(days_since_epoch)
    daily_variance = av_temp * 0.4 * (ran1.random() - 0.5)

    # Calculate number of minutes elapsed in the day so far
    curr_hour = datetime.datetime.today().hour
    curr_min = datetime.datetime.today().minute
    day_mins = (curr_hour * 60) + curr_min

    # Seed number generator for the current minute of the day
    day_fraction = day_mins / (60.0 * 24.0)
#    ran1 = random.Random((days_since_epoch * 1440) + day_mins)

    solar_variance = av_temp * 0.2
    solar_cycle = sin((0.75 + day_fraction) * 2 * 3.1415927) * solar_variance

    # print("av_temp " + str(av_temp) + " daily_variance " +
    # str(daily_variance) + " solar_cycle " + str(solar_cycle))
    return av_temp + daily_variance + solar_cycle


def get_temperature_at_coords(coords: [], rooms: {}, map_area: [],
                              clouds: {}) -> float:
    """Returns the temperature at the given coordinates
    """
    # Average temperature of the universe
    curr_temp = get_temperature()

    if not coords:
        return curr_temp

    x_co = coords[1] - map_area[1][0]
    y_co = coords[0] - map_area[0][0]

    # Adjust for altitude
    curr_temp = \
        curr_temp - _altitude_temperature_adjustment(rooms, map_area,
                                                     x_co, y_co)

    # Adjust for terrain
    curr_temp = \
        _terrain_temperature_adjustment(curr_temp, rooms, map_area, x_co, y_co)

    # Adjust for rain
    if get_rain_at_coords([coords[0], coords[1]], map_area, clouds):
        curr_temp = curr_temp * 0.8

    if clouds[x_co][y_co] < _get_cloud_threshold(curr_temp):
        # without cloud
        return curr_temp

    # with cloud
    return curr_temp * 0.8


def get_rain_at_coords(coords: [], map_area: [], clouds: {}) -> bool:
    """Returns whether it is raining at the civen coordinates
    """
    if not coords:
        return False
    x_coord = coords[1] - map_area[1][0]
    y_coord = coords[0] - map_area[0][0]
    try:
        if clouds[x_coord][y_coord] > RAIN_THRESHOLD:
            return True
    except BaseException:
        print('Rain map coords out of range ' +
              str(x_coord) + ', ' + str(y_coord))
    return False


def assign_environment_to_rooms(environments: {}, rooms: {}) -> int:
    """Assigns environment numbers to rooms based upon their descriptions
    Returns the percentage of rooms assigned to environments
    """
    assigned_rooms = 0
    no_of_rooms = 0
    for room_id, room in rooms.items():
        no_of_rooms += 1
        room_name = room['name'].lower()
        room_words = room_name.split(' ')
        max_score = 0
        env = 0
        for environment_id, env_item in environments.items():
            score = 0
            for word in room_words:
                if word in env_item['name'].lower():
                    score += 10
            if env_item.get('keywords'):
                for word in env_item['keywords']:
                    if word in room_name:
                        score += 10
            if score > max_score:
                max_score = score
                env = int(environment_id)
        if env > 0:
            assigned_rooms += 1
        else:
            print('Environment not assigned to ' + room['name'])
        rooms[room_id]['environmentId'] = env
    percent_assigned = 0
    if no_of_rooms > 0:
        percent_assigned = int(assigned_rooms * 100 / no_of_rooms)
    return percent_assigned


def get_room_culture(cultures_db: {}, rooms: {}, room_id: str) -> str:
    """Returns the culture for a room
    """
    if not rooms[room_id].get('region'):
        return None
    region = rooms[room_id]['region']
    if not region:
        return None
    for culture_name, item in cultures_db.items():
        if region in item['regions']:
            return culture_name
    return None


def is_fishing_site(rooms: {}, rid: str) -> bool:
    """Is the given location a fishing site?
    """
    fishing_sites = ('river', 'lake', 'sea', 'ocean', 'pond')
    if rooms[rid]['weather'] != 1:
        return False
    room_name_lower = rooms[rid]['name'].lower()
    for site in fishing_sites:
        if site in room_name_lower:
            return True
    return False


def holding_fishing_rod(players: {}, id, items_db: {}) -> bool:
    """Is the given player holding a fishing rod?
    """
    hand_locations = ('clo_lhand', 'clo_rhand')
    for hand in hand_locations:
        item_id = int(players[id][hand])
        if item_id > 0:
            if 'fishing' in items_db[item_id]['name']:
                return True
    return False


def holding_fly_fishing_rod(players: {}, id, items_db: {}) -> bool:
    """Is the given player holding a fly fishing rod?
    """
    hand_locations = ('clo_lhand', 'clo_rhand')
    for hand in hand_locations:
        item_id = int(players[id][hand])
        if item_id > 0:
            if 'fishing' in items_db[item_id]['name']:
                if 'fly' in items_db[item_id]['name']:
                    return True
    return False


def _catch_fish(players: {}, id, rooms: {}, items_db: {}, mud) -> None:
    """The player catches a fish
    """
    if randint(1, 100) < 80:
        return
    rid = players[id]['room']
    if not holding_fishing_rod(players, id, items_db):
        return
    if not is_fishing_site(rooms, rid):
        return
    room_name_lower = rooms[rid]['name'].lower()
    fish_names = []
    fishing_season = {
        "carp": [4, 5, 6, 7, 8, 9, 10, 11, 12],
        "pike fish": [1, 2, 3, 9, 10, 11, 12],
        "minnow": [],
        "tench": [],
        "chub": [1, 2, 3, 6, 7, 8, 9, 10, 11, 12],
        "trout": [1, 2, 3, 4, 5, 6, 9, 10, 11, 12],
        "cod fish": [1, 2, 10, 11, 12],
        "haddock": [1, 9, 10, 11, 12],
        "turbot": [1, 9, 10, 11, 12],
        "sturgeon": [],
        "dogfish": [4, 5, 6, 7, 8, 9, 10],
        "pollack": [4, 5, 6, 7, 8, 9, 10],
        "sea bass": [5, 6, 7, 8, 9, 10, 11, 12],
        "mullet": [5, 6, 7, 8, 9, 10, 11, 12]
    }
    if 'lake' in room_name_lower:
        fish_names = (
            'carp', 'pike fish', 'minnow', 'tench'
        )
    elif 'river' in room_name_lower:
        fish_names = (
            'trout', 'chub'
        )
    elif 'sea' in room_name_lower or 'ocean' in room_name_lower:
        if not holding_fly_fishing_rod(players, id, items_db):
            fish_names = (
                'cod fish', 'haddock', 'turbot', 'sturgeon',
                'dogfish', 'pollack', 'sea bass', 'mullet'
            )
        else:
            fish_names = (
                'sea bass', 'mullet'
            )
    elif 'pond' in room_name_lower:
        if not holding_fly_fishing_rod(players, id, items_db):
            fish_names = (
                'pond weed'
            )
    if not fish_names:
        return
    fish_ids = []
    curr_month_number = int(datetime.datetime.today().strftime("%m"))
    no_of_fish = 0
    for iid, item in items_db.items():
        if item['edible'] <= 0:
            continue
        if item['weight'] <= 0:
            continue
        item_name_lower = item['name'].lower()
        for fish in fish_names:
            if fish in item_name_lower:
                if iid in players[id]['inv']:
                    no_of_fish += 1
                # is this fishable at this time of year?
                if fishing_season.get(fish):
                    if curr_month_number in fishing_season[fish]:
                        fish_ids.append(iid)
                else:
                    fish_ids.append(iid)
    if no_of_fish > 1:
        return
    if not fish_ids:
        return
    caught_id = random.choice(fish_ids)
    if caught_id in players[id]['inv']:
        return
    caught_str = \
        items_db[caught_id]['article'] + ' ' + items_db[caught_id]['name']
    msg_str = random_desc('You catch ' + caught_str)
    players[id]['inv'].append(caught_id)
    del players[id]['isFishing']
    mud.send_message(id, msg_str + '\n\n')


def players_fishing(players: {}, rooms: {}, items_db: {}, mud) -> None:
    """Updates players that are fishing
    """
    for plyr_id, plyr in players.items():
        if plyr.get('isFishing'):
            _catch_fish(players, plyr_id, rooms, items_db, mud)


def _moon_position(curr_time) -> int:
    """Returns a number representing the position of the moon
    """
    diff = curr_time - datetime.datetime(2001, 1, 1)
    days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
    lunations = dec("0.20439731") + (days * dec("0.03386319269"))
    return lunations % dec(1)


def moon_phase(curr_time) -> int:
    """Returns a number representing the phase of the moon
    """
    position = _moon_position(curr_time)
    index = (position * dec(8)) + dec("0.5")
    index = math.floor(index)
    return int(index) & 7


def moon_illumination(curr_time) -> int:
    """Returns additional illumination due to moonlight
    """
    position = _moon_position(curr_time)
    pos = int(position) & 7
    return int((5 - abs(4 - pos)) * 2)
