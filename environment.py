__filename__ = "environment.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

from random import randint
import random
from math import sin

import datetime

rainThreshold = 230


def runTide() -> float:
    """Calculates the tide level as the addition of sine waves
    """
    lunar_orbit_mins = 39312

    daysSinceEpoch = (
        datetime.datetime.today() -
        datetime.datetime(
            1970,
            1,
            1)).days
    currHour = datetime.datetime.today().hour
    currMin = datetime.datetime.today().minute
    timeMins = (daysSinceEpoch * 60 * 24) + (currHour * 60) + currMin

    lunarMins = timeMins % int(lunar_orbit_mins)
    solarMins = timeMins % int(24 * 60 * 365)
    dailyMins = timeMins % int(24 * 60)

    lunar = sin(float(lunarMins) * 2.0 * 3.1415927 /
                float(lunar_orbit_mins)) * 0.08
    solar = sin(float(solarMins) * 2.0 * 3.1415927 /
                float(24 * 60 * 365)) * 0.02
    daily = sin(float(dailyMins) * 2.0 * 3.1415927 /
                float(24 * 60)) * 0.9

    return daily + lunar + solar


def assignTerrainDifficulty(rooms: {}) -> int:
    """Updates the terrain difficulty for each room and returns the maximum
    """
    terrainDifficultyWords = (
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
        'mist',
        'fog',
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
    maxTerrainDifficulty = 1
    for rm in rooms:
        difficulty = rooms[rm]['terrainDifficulty']
        if difficulty == 0:
            roomDescription = rooms[rm]['description'].lower()
            difficulty = 0
            for w in terrainDifficultyWords:
                if w in roomDescription:
                    difficulty += 1
            rooms[rm]['terrainDifficulty'] = difficulty
        if difficulty > maxTerrainDifficulty:
            maxTerrainDifficulty = difficulty
    return maxTerrainDifficulty


def assignInitialCoordinates(rooms: {}, rm: str) -> None:
    """Sets initial zero room coordinates
    """
    if len(rooms[rm]['coords']) == 0:
        rooms[rm]['coords'] = [0, 0, 0]


def findRoomCollisions(rooms: {}) -> None:
    """Marks rooms whose geolocations collide
    """
    ctr = 0
    totalCtr = 0
    roomDict = {}
    for rm in rooms:
        roomDict[ctr] = rm
        ctr += 1
    ctr = 0
    for index1 in range(len(rooms)):
        rm = roomDict[index1]
        # Room with coords
        if len(rooms[rm]['coords']) > 2:
            if rooms[rm]['coords'][0] == 0 and \
               rooms[rm]['coords'][1] == 0 and \
               rooms[rm]['coords'][2] == 0:
                continue
            totalCtr += 1
            for index2 in range(index1, len(rooms)):
                rm2 = roomDict[index2]
                if len(rooms[rm2]['coords']) > 2:
                    if rm2 == rm:
                        continue
                    if rooms[rm2]['coords'][0] == 0 and \
                       rooms[rm2]['coords'][1] == 0 and \
                       rooms[rm2]['coords'][2] == 0:
                        continue
                    if rooms[rm]['coords'][0] != rooms[rm2]['coords'][0]:
                        continue
                    if rooms[rm]['coords'][1] != rooms[rm2]['coords'][1]:
                        continue
                    if rooms[rm]['coords'][2] != rooms[rm2]['coords'][2]:
                        continue
                    print('Collision between rooms ' +
                          str(rm) + ' and ' + str(rm2))
                    print(rooms[rm]['name'] + ' ' + str(rooms[rm]['coords']))
                    print(rooms[rm2]['name'] + ' ' + str(rooms[rm2]['coords']))
                    rooms[rm]['collides'] = rm2
                    ctr += 1
    if ctr > 0:
        print(str(ctr) + ' room collisions out of ' + str(totalCtr))


def findRoomWithoutCoords(rooms: {}):
    """Finds the next room without assigned coordinates
    """
    for rm in rooms:
        # Room with coords
        if rooms[rm]['coordsAssigned']:
            # combine exits with virtual exists so that we know
            # all the possible directions from here
            exitDict = rooms[rm]['exits'].copy()
            if rooms[rm].get('virtualExits'):
                exitDict.update(rooms[rm]['virtualExits'])
            if rooms[rm].get('tideOutExits'):
                exitDict.update(rooms[rm]['tideOutExits'])
            # Search the exits for ones without coords
            for ex, roomId in exitDict.items():
                # room which is exited to
                rm2 = rooms[str(roomId)]
                if not rm2['coordsAssigned']:
                    if ex == 'north':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] += 1
                        rm2['coordsAssigned'] = True
                        return rm2
                    elif ex == 'northeast':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] += 1
                        rm2['coords'][1] -= 1
                        rm2['coordsAssigned'] = True
                        return rm2
                    elif ex == 'northwest':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] += 1
                        rm2['coords'][1] += 1
                        rm2['coordsAssigned'] = True
                        return rm2
                    elif ex == 'south':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] -= 1
                        rm2['coordsAssigned'] = True
                        return rm2
                    elif ex == 'southeast':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] -= 1
                        rm2['coords'][1] -= 1
                        rm2['coordsAssigned'] = True
                        return rm2
                    elif ex == 'southwest':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] -= 1
                        rm2['coords'][1] += 1
                        rm2['coordsAssigned'] = True
                        return rm2
                    elif ex == 'east':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][1] -= 1
                        rm2['coordsAssigned'] = True
                        return rm2
                    elif ex == 'west':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][1] += 1
                        rm2['coordsAssigned'] = True
                        return rm2
                    elif ex == 'up':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][2] += 1
                        rm2['coordsAssigned'] = True
                        return rm2
                    elif ex == 'down':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][2] -= 1
                        rm2['coordsAssigned'] = True
                        return rm2
    max_east = 0
    for rm in rooms:
        # Room without coords
        if not rooms[rm]['coordsAssigned']:
            continue
        if rooms[rm]['coords'][1] > max_east:
            max_east = rooms[rm]['coords'][1]

    noOfRooms = len(rooms)
    for rm in rooms:
        # Room without coords
        if rooms[rm]['coordsAssigned']:
            continue
        rooms[rm]['coordsAssigned'] = True
        rooms[rm]['coords'] = [0, max_east + noOfRooms, 0]
        return rooms[rm]

    return None


def _removeCoordinateGaps(rooms: {}) -> None:
    """Removes gaps in the east line coordinates of rooms
    """
    max_east = 0
    for rm in rooms:
        # Room without coords
        if not rooms[rm]['coordsAssigned']:
            continue
        if rooms[rm]['coords'][1] > max_east:
            max_east = rooms[rm]['coords'][1]

    eastLine = [0] * (max_east + 1)
    for rm in rooms:
        if not rooms[rm]['coordsAssigned']:
            continue
        e = rooms[rm]['coords'][1]
        eastLine[e] = 1

    start_east = None
    gaps = []
    for e in range(max_east + 1):
        if not start_east:
            if eastLine[e] == 0:
                start_east = e
        else:
            if eastLine[e] == 1:
                if e - start_east > 5:
                    gaps = [[start_east, e - start_east]] + gaps
                start_east = None

    for g in gaps:
        start_east = g[0]
        gap_width = g[1]
        for rm in rooms:
            if not rooms[rm]['coordsAssigned']:
                continue
            e = rooms[rm]['coords'][1]
            if e >= start_east:
                rooms[rm]['coords'][1] -= gap_width

    eastLine = [0] * (max_east + 1)
    for rm in rooms:
        if not rooms[rm]['coordsAssigned']:
            continue
        e = rooms[rm]['coords'][1]
        eastLine[e] = 1

    start_east = None
    for e in range(max_east + 1):
        if not start_east:
            if eastLine[e] == 0:
                start_east = e
        else:
            if eastLine[e] == 1:
                if e - start_east > 5:
                    print('East line gap ' +
                          str(start_east) + ' -> ' + str(e-1))
                start_east = None


def _createVirtualExits(rooms: {}, itemsDB: {}, scriptedEventsDB: {}) -> None:
    """If there are any doors then this Generates the
    virtual exits dicts for each room
    """
    for rm in rooms:
        rooms[rm]['virtualExits'] = {}

    # get a list of door items
    doorCtr = 0
    for itemId in itemsDB:
        if not itemsDB[itemId].get('exit'):
            continue
        if not itemsDB[itemId].get('exitName'):
            continue
        if '|' not in itemsDB[itemId]['exitName']:
            continue
        roomId = None
        for event in scriptedEventsDB:
            if event[2] != 'spawnItem':
                continue
            eventItem = event[3].split(';')
            if eventItem[0] != str(itemId):
                continue
            roomId = eventItem[1]
            break
        if roomId:
            exitDirection = itemsDB[itemId]['exitName'].split('|')[0]
            collides = False
            if rooms[roomId]['exits'].get(exitDirection):
                print('Room ' + roomId + ' has item ' +
                      str(itemId) + ' with colliding exit ' + exitDirection)
                collides = True

            if rooms[roomId].get('tideOutExits'):
                if rooms[roomId]['tideOutExits'].get(exitDirection):
                    print('Room ' + roomId + ' has item ' +
                          str(itemId) + ' with colliding tide out exit ' +
                          exitDirection)
                collides = True

            if not collides:
                exitRoomId = itemsDB[itemId]['exit']
                rooms[roomId]['virtualExits'][exitDirection] = exitRoomId
                doorCtr += 1
    print('Door items: ' + str(doorCtr))


def assignCoordinates(rooms: {}, itemsDB: {}, scriptedEventsDB: {}) -> []:
    """Assigns cartesian coordinates to each room and returns the limits
    """
    _createVirtualExits(rooms, itemsDB, scriptedEventsDB)

    mapArea = [[9999999999, -9999999999],
               [9999999999, -9999999999],
               [9999999999, -9999999999]]
    roomFound = True
    for rm in rooms:
        rooms[rm]['coordsAssigned'] = False
    while roomFound:
        newRoom = findRoomWithoutCoords(rooms)
        if newRoom is None:
            roomFound = False
            break
        coords = newRoom['coords']
        # east/west extent
        if coords[1] > mapArea[1][1]:
            mapArea[1][1] = coords[1]
        if coords[1] < mapArea[1][0]:
            mapArea[1][0] = coords[1]

    # map out gaps in horizontal spacing
    min_east = mapArea[1][0]
    max_east = mapArea[1][1]
    occupied = [False] * ((max_east - min_east) + 1)
    for rm in rooms:
        if len(rooms[rm]['coords']) > 1:
            occupied[rooms[rm]['coords'][1] - min_east] = True

    # remove the horizontal spacing to compact the map
    state = 0
    start_east = 0
    end_east = 0
    trimCoords = []
    for i in range(len(occupied)):
        if state == 0:
            if not occupied[i]:
                state = 1
                start_east = i
        elif state == 1:
            if occupied[i]:
                state = 0
                end_east = i
                trimCoords.append([start_east - min_east,
                                   end_east - min_east])

    maxRange = len(trimCoords)
    mapArea = [[9999999999, -9999999999],
               [9999999999, -9999999999],
               [9999999999, -9999999999]]
    for i in range(maxRange - 1, 0, -1):
        for rm in rooms:
            if len(rooms[rm]['coords']) < 3:
                continue
            if rooms[rm]['coords'][1] >= trimCoords[i][1]:
                adjust = (trimCoords[i][1] - trimCoords[i][0]) - 2
                rooms[rm]['coords'][1] -= adjust

    _removeCoordinateGaps(rooms)

    # recalculate the map area
    for rm in rooms:
        coords = rooms[rm]['coords']
        # north/south extent
        if coords[0] > mapArea[0][1]:
            mapArea[0][1] = coords[0]
        if coords[0] < mapArea[0][0]:
            mapArea[0][0] = coords[0]
        # east/west extent
        if coords[1] > mapArea[1][1]:
            mapArea[1][1] = coords[1]
        if coords[1] < mapArea[1][0]:
            mapArea[1][0] = coords[1]
        # up/down extent
        if coords[2] > mapArea[2][1]:
            mapArea[2][1] = coords[2]
        if coords[2] < mapArea[2][0]:
            mapArea[2][0] = coords[2]

    return mapArea


def highestPointAtCoord(rooms: {}, mapArea: [], x: int, y: int) -> float:
    """Returns the highest elevation at the given location
    """
    highest = 0

    vertical_range = mapArea[2][1] - mapArea[2][0]
    if vertical_range < 1:
        vertical_range = 1

    for rm in rooms:
        if rooms[rm]['coords'][0] - mapArea[0][0] == y:
            if rooms[rm]['coords'][1] - mapArea[1][0] == x:
                if rooms[rm]['coords'][2] > highest:
                    highest = rooms[rm]['coords'][2]

    return (highest - mapArea[2][0]) * 255 / vertical_range


def generateCloud(
        randnumgen: int,
        rooms: {},
        mapArea: [],
        clouds: {},
        cloudGrid: {},
        tileSize: int,
        windDirection: int) -> int:
    """Weather simulation
       This uses a simple cloud model adjusted for topology in which
       clouds get smaller as temperature increases and bigger with
       more chance of rain as temperature falls.
       Wind blows clouds in one of 8 possible directions, or can be still.
    """
    mapWidth = mapArea[1][1] - mapArea[1][0]
    mapHeight = mapArea[0][1] - mapArea[0][0]
    cloudGridWidth = int(mapWidth / tileSize)
    cloudGridHeight = int(mapHeight / tileSize)

    if len(clouds) == 0:
        # Generate the clouds map
        for x in range(0, mapWidth):
            clouds[x] = {}
            for y in range(0, mapHeight):
                clouds[x][y] = 0

    if len(cloudGrid) == 0:
        # Initialize clouds grid randomly
        # This is lower resolution than the map
        for x in range(0, cloudGridWidth):
            cloudGrid[x] = {}
            for y in range(0, cloudGridHeight):
                cloudGrid[x][y] = int(randnumgen.random() * 255)

    # Update clouds (same resolution as the map)
    for x in range(0, mapWidth - 1):
        tile_tx = int(x / tileSize)
        tile_bx = tile_tx + 1
        if tile_bx >= cloudGridWidth:
            tile_bx = 0
        for y in range(0, mapHeight - 1):
            tile_ty = int(y / tileSize)
            tile_by = tile_ty + 1
            if tile_by >= cloudGridHeight:
                tile_by = 0

            interpolate_top = \
                cloudGrid[tile_tx][tile_ty] + \
                int((cloudGrid[tile_bx][tile_ty] -
                     cloudGrid[tile_tx][tile_ty]) *
                    (x % tileSize) / tileSize)

            interpolate_bottom = \
                cloudGrid[tile_tx][tile_by] + \
                int((cloudGrid[tile_bx][tile_by] -
                     cloudGrid[tile_tx][tile_by]) *
                    (x % tileSize) / tileSize)

            clouds[x][y] = \
                interpolate_top + \
                int((interpolate_bottom - interpolate_top) *
                    (y % tileSize) / tileSize)

    # Clouds change
    for x in range(0, cloudGridWidth):
        for y in range(0, cloudGridHeight):
            cloudGrid[x][y] = cloudGrid[x][y] + \
                (int(randnumgen.random() * 11) - 5)
            if cloudGrid[x][y] < 0:
                cloudGrid[x][y] = cloudGrid[x][y] + 255
            if cloudGrid[x][y] > 255:
                cloudGrid[x][y] = cloudGrid[x][y] - 255

    # change wind direction
    windDirection = (windDirection + int(randnumgen.random() * 9) - 4) % 360
    if windDirection < 0:
        windDirection = windDirection + 360

    # Which directions to shift the clouds
    dx = 0
    dy = 0
    if windDirection >= 320 or windDirection <= 40:
        dy = 1
    if windDirection <= 200 and windDirection > 160:
        dy = -1
    if windDirection < 300 and windDirection >= 230:
        dx = -1
    if windDirection > 50 and windDirection <= 130:
        dx = 1

    # Move clouds in the wind direction
    cloudGridNew = {}
    for x in range(0, cloudGridWidth):
        cloudGridNew[x] = {}
        for y in range(0, cloudGridHeight):
            cloudGridNew[x][y] = cloudGrid[x][y]

    for x in range(0, cloudGridWidth):
        old_x = x + dx
        for y in range(0, cloudGridHeight):
            old_y = y + dy
            if old_x >= 0 and old_x <= cloudGridWidth - 1 and \
               old_y >= 0 and old_y <= cloudGridHeight - 1:
                cloudGridNew[x][y] = cloudGrid[old_x][old_y]
            else:
                if old_x < 0:
                    old_x = old_x + cloudGridWidth
                if old_y < 0:
                    old_y = old_y + cloudGridHeight
                if old_x > cloudGridWidth - 1:
                    old_x = old_x - cloudGridWidth
                if old_y > cloudGridHeight - 1:
                    old_y = old_y - cloudGridHeight
                cloudGridNew[x][y] = randint(0, 255)

    for x in range(0, cloudGridWidth):
        for y in range(0, cloudGridHeight):
            cloudGrid[x][y] = cloudGridNew[x][y]

    return windDirection


def getCloudThreshold(temperature: float) -> float:
    """Temperature threshold at which cloud is formed
    """
    return (10 + temperature) * 7


def altitudeTemperatureAdjustment(rooms: {}, mapArea: [],
                                  x: int, y: int) -> float:
    """Temperature decreases with altitude
    """
    return highestPointAtCoord(rooms, mapArea, x, y) * 2.0 / 255.0


def terrainTemperatureAdjustment(temperature: float, rooms: {}, mapArea: [],
                                 x: int, y: int) -> float:
    """Temperature is adjusted for different types of terrain
    """
    terrainFreezingWords = ('snow', 'ice')
    terrainCoolingWords = (
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
    terrainHeatingWords = ('sun', 'lava', 'volcan', 'molten', 'desert', 'dry')

    for rm in rooms:
        coords = rooms[rm]['coords']
        if coords[0] - mapArea[0][0] == y:
            if coords[1] - mapArea[1][0] == x:
                roomDescription = rooms[rm]['description'].lower()
                for w in terrainFreezingWords:
                    if w in roomDescription:
                        temperature = temperature * 0.1
                for w in terrainCoolingWords:
                    if w in roomDescription:
                        temperature = temperature * 0.98
                for w in terrainHeatingWords:
                    if w in roomDescription:
                        temperature = temperature * 1.05
    return temperature


def plotClouds(rooms: {}, mapArea: [], clouds: {}, temperature: float) -> None:
    """Show clouds as ASCII diagram for debugging purposes
    """
    cloudThreshold = getCloudThreshold(temperature)
    mapWidth = mapArea[1][1] - mapArea[1][0]
    mapHeight = mapArea[0][1] - mapArea[0][0]

    for y in range(0, mapHeight - 1):
        lineStr = ''
        for x in range(0, mapWidth - 1):
            mapTemp = clouds[x][y] - \
                (altitudeTemperatureAdjustment(rooms, mapArea, x, y) * 7)
            mapTemp = terrainTemperatureAdjustment(
                mapTemp, rooms, mapArea, x, y)
            lineChar = '.'
            if mapTemp > cloudThreshold:
                lineChar = 'o'
            if mapTemp > rainThreshold:
                lineChar = 'O'
            lineStr = lineStr + lineChar
        print(lineStr + '\n')
    print('\n')


def getTemperatureSeasonal() -> float:
    """Average temperature for the time of year
    """
    dayOfYear = int(datetime.datetime.today().strftime("%j"))
    tempFraction = (
        (sin((0.75 + (dayOfYear / 365.0)) * 2 * 3.1415927) + 1) / 2.0)
    return 8 + (7 * tempFraction)


def getTemperature() -> float:
    """Average daily seasonal temperature for the universe
    """
    avTemp = getTemperatureSeasonal()

    daysSinceEpoch = (
        datetime.datetime.today() -
        datetime.datetime(
            1970,
            1,
            1)).days

    # Temperature can vary randomly from one day to the next
    r1 = random.Random(daysSinceEpoch)
    dailyVariance = avTemp * 0.4 * (r1.random() - 0.5)

    # Calculate number of minutes elapsed in the day so far
    currHour = datetime.datetime.today().hour
    currMin = datetime.datetime.today().minute
    dayMins = (currHour * 60) + currMin

    # Seed number generator for the current minute of the day
    dayFraction = dayMins / (60.0 * 24.0)
    r1 = random.Random((daysSinceEpoch * 1440) + dayMins)

    solarVariance = avTemp * 0.2
    solarCycle = sin((0.75 + dayFraction) * 2 * 3.1415927) * solarVariance

    # print("avTemp " + str(avTemp) + " dailyVariance " +
    # str(dailyVariance) + " solarCycle " + str(solarCycle))
    return avTemp + dailyVariance + solarCycle


def getTemperatureAtCoords(coords: [], rooms: {}, mapArea: [],
                           clouds: {}) -> float:
    """Returns the temperature at the given coordinates
    """
    x = coords[1] - mapArea[1][0]
    y = coords[0] - mapArea[0][0]

    # Average temperature of the universe
    currTemp = getTemperature()

    # Adjust for altitude
    currTemp = currTemp - altitudeTemperatureAdjustment(rooms, mapArea, x, y)

    # Adjust for terrain
    currTemp = terrainTemperatureAdjustment(currTemp, rooms, mapArea, x, y)

    # Adjust for rain
    if getRainAtCoords([coords[0], coords[1]], mapArea, clouds):
        currTemp = currTemp * 0.8

    if clouds[x][y] < getCloudThreshold(currTemp):
        # without cloud
        return currTemp

    # with cloud
    return currTemp * 0.8


def getRainAtCoords(coords: [], mapArea: [], clouds: {}) -> bool:
    """Returns whether it is raining at the civen coordinates
    """
    x = coords[1] - mapArea[1][0]
    y = coords[0] - mapArea[0][0]
    if clouds[x][y] > rainThreshold:
        return True
    return False
