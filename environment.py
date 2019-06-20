__filename__ = "environment.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

from functions import log
from random import randint
import random
from copy import deepcopy
from math import sin

import datetime
import time

rainThreshold = 230


def runTide():
    """Calculates the tide level as the addition of sine waves
    """
    lunar_orbit_mins = 39312

    daysSinceEpoch = (
        datetime.datetime.utcnow() -
        datetime.datetime(
            1970,
            1,
            1)).days
    currHour = datetime.datetime.utcnow().hour
    currMin = datetime.datetime.utcnow().minute
    timeMins = (daysSinceEpoch * 60 * 24) + (currHour * 60) + currMin

    lunarMins = timeMins % int(lunar_orbit_mins)
    solarMins = timeMins % int(24 * 60 * 365)
    dailyMins = timeMins % int(24 * 60)

    lunar = sin(lunarMins * 2 * 3.1415927 / lunar_orbit_mins) * 0.5
    solar = sin(solarMins * 2 * 3.1415927 / (24 * 60 * 365)) * 0.1
    daily = sin(dailyMins * 2 * 3.1415927 / (24 * 60)) * 0.5

    return daily + lunar + solar


def assignTerrainDifficulty(rooms):
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
        'ice')
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


def assignInitialCoordinates(rooms, rm):
    """Sets initial zero room coordinates
    """
    if len(rooms[rm]['coords']) == 0:
        rooms[rm]['coords'] = [0, 0, 0]


def findRoomWithoutCoords(rooms):
    """Finds the next room without assigned coordinates
    """
    for rm in rooms:
        # Room with coords
        if len(rooms[rm]['coords']) > 0:
            # Search the exits for ones without coords
            for ex in rooms[rm]['exits']:
                roomID = rooms[rm]['exits'][ex]
                rm2 = rooms[rooms[rm]['exits'][ex]]
                if len(rm2['coords']) == 0:
                    if ex == 'north':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] += 1
                        return rm2
                    if ex == 'northeast':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] += 1
                        rm2['coords'][1] -= 1
                        return rm2
                    if ex == 'northwest':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] += 1
                        rm2['coords'][1] += 1
                        return rm2
                    if ex == 'south':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] -= 1
                        return rm2
                    if ex == 'southeast':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] -= 1
                        rm2['coords'][1] -= 1
                        return rm2
                    if ex == 'southwest':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] -= 1
                        rm2['coords'][1] += 1
                        return rm2
                    if ex == 'east':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][1] -= 1
                        return rm2
                    if ex == 'west':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][1] += 1
                        return rm2
                    if ex == 'up':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][2] += 1
                        return rm2
                    if ex == 'down':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][2] -= 1
                        return rm2
    for rm in rooms:
        # Room without coords
        if len(rooms[rm]['coords']) == 0:
            rooms[rm]['coords'] = [0, 0, 0]
            return rooms[rm]

    return None


def assignCoordinates(rooms):
    """Assigns cartesian coordinates to each room and returns the limits
    """
    mapArea = [[9999, -9999], [9999, -9999], [9999, -9999]]
    roomFound = True
    while roomFound:
        newRoom = findRoomWithoutCoords(rooms)
        if newRoom is None:
            roomFound = False
            break
        coords = newRoom['coords']
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


def highestPointAtCoord(rooms, mapArea, x, y):
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
        randnumgen,
        rooms,
        mapArea,
        clouds,
        cloudGrid,
        tileSize,
        windDirection):
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
                int((cloudGrid[tile_bx][tile_ty] - cloudGrid[tile_tx][tile_ty]) *
                    (x % tileSize) / tileSize)

            interpolate_bottom = \
                cloudGrid[tile_tx][tile_by] + \
                int((cloudGrid[tile_bx][tile_by] - cloudGrid[tile_tx][tile_by]) *
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


def getCloudThreshold(temperature):
    """Temperature threshold at which cloud is formed
    """
    return (10 + temperature) * 7


def altitudeTemperatureAdjustment(rooms, mapArea, x, y):
    """Temperature decreases with altitude
    """
    return highestPointAtCoord(rooms, mapArea, x, y) * 2.0 / 255.0


def terrainTemperatureAdjustment(temperature, rooms, mapArea, x, y):
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

    maxTerrainDifficulty = 1
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


def plotClouds(rooms, mapArea, clouds, temperature):
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


def getTemperatureSeasonal():
    """Average temperature for the time of year
    """
    dayOfYear = int(datetime.datetime.utcnow().strftime("%j"))
    tempFraction = (
        (sin((0.75 + (dayOfYear / 365.0)) * 2 * 3.1415927) + 1) / 2.0)
    return 8 + (7 * tempFraction)


def getTemperature():
    """Average daily seasonal temperature for the universe
    """
    avTemp = getTemperatureSeasonal()

    daysSinceEpoch = (
        datetime.datetime.utcnow() -
        datetime.datetime(
            1970,
            1,
            1)).days

    # Temperature can vary randomly from one day to the next
    r1 = random.Random(daysSinceEpoch)
    dailyVariance = avTemp * 0.4 * (r1.random() - 0.5)

    # Calculate number of minutes elapsed in the day so far
    currHour = datetime.datetime.utcnow().hour
    currMin = datetime.datetime.utcnow().minute
    dayMins = (currHour * 60) + currMin

    # Seed number generator for the current minute of the day
    dayFraction = dayMins / (60.0 * 24.0)
    r1 = random.Random((daysSinceEpoch * 1440) + dayMins)

    solarVariance = avTemp * 0.2
    solarCycle = sin((0.75 + dayFraction) * 2 * 3.1415927) * solarVariance

    #print("avTemp " + str(avTemp) + " dailyVariance " + str(dailyVariance) + " solarCycle " + str(solarCycle))
    return avTemp + dailyVariance + solarCycle


def getTemperatureAtCoords(coords, rooms, mapArea, clouds):
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
    if clouds[x][y] > rainThreshold:
        currTemp = currTemp * 0.8

    if clouds[x][y] < getCloudThreshold(currTemp):
        # without cloud
        return currTemp

    # with cloud
    return currTemp * 0.8
