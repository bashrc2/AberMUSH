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
from copy import deepcopy

import time

# For weather simulation
bits_neg = (-131072 * 254) / 256
bits_pos = ( 131071 * 254) / 256
# pressure threshold for cloud
weather_cloud = 32768 >> 4

def assignTerrainDifficulty(rooms):
    terrainDifficultyWords=['rock','boulder','slip','steep','rough','volcan','sewer','sand','pebble','mountain','mist','fog','bush','dense','trees','forest','tangle','thick','tough']
    maxTerrainDifficulty=1
    for rm in rooms:
        difficulty=rooms[rm]['terrainDifficulty']
        if difficulty==0:
            roomDescription=rooms[rm]['description'].lower()
            difficulty=0
            for w in terrainDifficultyWords:
                if w in roomDescription:
                    difficulty = difficulty + 1
            rooms[rm]['terrainDifficulty'] = difficulty
        if difficulty > maxTerrainDifficulty:
            maxTerrainDifficulty = difficulty
    return maxTerrainDifficulty

def assignInitialCoordinates(rooms,rm):
    if len(rooms[rm]['coords'])==0:
        rooms[rm]['coords'] = [0,0,0]

def findRoomWithoutCoords(rooms):
    for rm in rooms:
        # Room with coords
        if len(rooms[rm]['coords'])>0:
            # Search the exits for ones without coords
            for ex in rooms[rm]['exits']:
                roomID=rooms[rm]['exits'][ex]
                rm2 = rooms[rooms[rm]['exits'][ex]]
                if len(rm2['coords'])==0:
                    if ex=='north':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] = rm2['coords'][0] + 1
                        return rm2
                    if ex=='northeast':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] = rm2['coords'][0] + 1
                        rm2['coords'][1] = rm2['coords'][1] - 1
                        return rm2
                    if ex=='northwest':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] = rm2['coords'][0] + 1
                        rm2['coords'][1] = rm2['coords'][1] + 1
                        return rm2
                    if ex=='south':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] = rm2['coords'][0] - 1
                        return rm2
                    if ex=='southeast':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] = rm2['coords'][0] - 1
                        rm2['coords'][1] = rm2['coords'][1] - 1
                        return rm2
                    if ex=='southwest':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][0] = rm2['coords'][0] - 1
                        rm2['coords'][1] = rm2['coords'][1] + 1
                        return rm2
                    if ex=='east':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][1] = rm2['coords'][1] - 1
                        return rm2
                    if ex=='west':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][1] = rm2['coords'][1] + 1
                        return rm2
                    if ex=='up':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][2] = rm2['coords'][2] + 1
                        return rm2
                    if ex=='down':
                        rm2['coords'] = rooms[rm]['coords'].copy()
                        rm2['coords'][2] = rm2['coords'][2] - 1
                        return rm2
    for rm in rooms:
        # Room without coords
        if len(rooms[rm]['coords'])==0:
            rooms[rm]['coords'] = [0,0,0]
            return rooms[rm]

    return None

def assignCoordinates(rooms):
    # assigns cartesian coordinates to each room and returns the limits
    mapArea=[[9999,-9999],[9999,-9999],[9999,-9999]]
    roomFound=True
    while roomFound:
        newRoom = findRoomWithoutCoords(rooms)
        if newRoom == None:
            roomFound = False
            break
        coords=newRoom['coords']
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

def highestPointAtCoord(rooms,mapArea,x,y):
    highest=0

    vertical_range=mapArea[2][1]-mapArea[2][0]
    if vertical_range<1:
        vertical_range=1

    for rm in rooms:
        if rooms[rm]['coords'][0]-mapArea[0][0]==y:
            if rooms[rm]['coords'][1]-mapArea[1][0]==x:
                if rooms[rm]['coords'][2]>highest:
                    highest=rooms[rm]['coords'][2]

    return (highest-mapArea[2][0])*255/vertical_range

def weatherInit(rooms, mapArea, atmosphere, delta_pressure, MAP_DIMENSION_X, MAP_DIMENSION_Y):
    if len(atmosphere)>0:
        return 0

    wind_dissipation = randint(0,1024) & 3
    wind_aim =  -96 + (randint(0,2048) % 194)
    wind_value_x = wind_aim
    wind_aim =  -96 + (randint(0,2048) % 194)
    wind_aim_y = wind_aim
    wind_aim =  -96 + (randint(0,2048) % 194)
    wind_value_y = wind_aim
    wind_aim =  -96 + (randint(0,2048) % 194)
    wind_aim_x = wind_aim

    local_delta = 0

    delta_pressure_lowest = 0xffff
    delta_pressure_highest = 1

    # calculate the topography from the arrangement of rooms
    # up and down exit directions indicate verticality
    topography={}
    for x in range (0,MAP_DIMENSION_X):
        topography[x]={}
        for y in range (0,MAP_DIMENSION_Y):
            topography[x][y]=highestPointAtCoord(rooms,mapArea,x,y)

    for x in range (0,MAP_DIMENSION_X):
        atmosphere[x]={}
        delta_pressure[x]={}
        for y in range (0,MAP_DIMENSION_Y):
            delta_pressure[x][y]=0
            atmosphere[x][y]=topography[x][y] * 4

    delta_pressure_highest = -99999
    delta_pressure_lowest = 99999
    for x in range (1,MAP_DIMENSION_X-1):
        for y in range (1,MAP_DIMENSION_Y-1):
            delta_pressure[x][y] = atmosphere[x + 1][y] - \
                atmosphere[x - 1][y] + \
                atmosphere[x][y + 1] - \
                atmosphere[x][y - 1] + \
                512
            if delta_pressure[x][y] > delta_pressure_highest:
                delta_pressure_highest = delta_pressure[x][y]

            if delta_pressure[x][y] < delta_pressure_lowest:
                delta_pressure_lowest = delta_pressure[x][y]
    return wind_dissipation,wind_aim_x,wind_aim_y,wind_value_x,wind_value_y,delta_pressure_lowest,delta_pressure_highest

def updateRoomWeather(rooms,mapArea,atmosphere,MAP_DIMENSION_X,MAP_DIMENSION_Y):
    for rm in rooms:
        if rooms[rm]['weather']==0:
            continue

        # coordinates at this location
        x = rooms[rm]['coords'][1] - mapArea[1][0]
        if x < 0:
            x = 0
        if x >= MAP_DIMENSION_X:
            x = MAP_DIMENSION_X-1
        y = rooms[rm]['coords'][0] - mapArea[0][0]
        if y < 0:
            y = 0
        if y >= MAP_DIMENSION_Y:
            y = MAP_DIMENSION_Y-1

        rooms[rm]['weather']=1
        # cloudy
        if atmosphere[x][y] > weather_cloud:
            rooms[rm]['weather']=2
        # rain
        if atmosphere[x][y] > weather_cloud*3:
            rooms[rm]['weather']=3

def plotClouds(rooms, mapArea):
    MAP_DIMENSION_X=mapArea[1][1] - mapArea[1][0]
    MAP_DIMENSION_Y=mapArea[0][1] - mapArea[0][0]

    for ly in range (0,MAP_DIMENSION_Y):
        weatherStr=''
        for lx in range (0,MAP_DIMENSION_X):
            weatherChar='.'
            for rm in rooms:
                if rooms[rm]['coords'][0]-mapArea[0][0]==ly:
                    if rooms[rm]['coords'][1]-mapArea[1][0]==lx:
                        if rooms[rm]['weather']==2:
                            weatherChar='o'
                        if rooms[rm]['weather']==3:
                            weatherChar='O'
            weatherStr=weatherStr+weatherChar
        print(weatherStr+'\n')
    print('\n')

def weatherCycle(rooms, mapArea, atmosphere, delta_pressure, wind_dissipation, local_delta,wind_aim_x,wind_aim_y,wind_value_x,wind_value_y,delta_pressure_lowest,delta_pressure_highest):
    dissipation = wind_dissipation + 1020
    new_delta = 0
    # east/west
    MAP_DIMENSION_X=mapArea[1][1] - mapArea[1][0]
    # north/south
    MAP_DIMENSION_Y=mapArea[0][1] - mapArea[0][0]
    MAP_BITS = 8

    if len(atmosphere)==0:
        wind_dissipation,wind_aim_x, wind_aim_y,wind_value_x,wind_value_y,delta_pressure_lowest,delta_pressure_highest=weatherInit(rooms, mapArea, atmosphere, delta_pressure, MAP_DIMENSION_X, MAP_DIMENSION_Y)

    atmosphere_lowest = bits_pos
    atmosphere_highest = bits_neg

    atmosphere_next = atmosphere.copy()

    for ly in range (1,MAP_DIMENSION_Y-1):
        for lx in range (1,MAP_DIMENSION_X-1):
            value = int(dissipation * atmosphere[lx][ly]) >> 10

            local_atm = \
                (2 * atmosphere[lx][ly-1]) + \
                (2 * atmosphere[lx-1][ly]) - \
                (2 * atmosphere[lx+1][ly]) - \
                (2 * atmosphere[lx][ly+1])

            value = value + \
                 (int(local_atm - local_delta) >> MAP_BITS) + \
                 delta_pressure[lx][ly]

            atmosphere_next[lx][ly] = value
            new_delta = new_delta + value

            if value > atmosphere_highest:
                atmosphere_highest = value

            if value < atmosphere_lowest:
                atmosphere_lowest = value

    local_delta = int(new_delta) >> MAP_BITS

    atmosphere = atmosphere_next.copy()

    updateRoomWeather(rooms,mapArea,atmosphere,MAP_DIMENSION_X,MAP_DIMENSION_Y)

    return local_delta,wind_dissipation,wind_aim_x,wind_aim_y,wind_value_x,wind_value_y,delta_pressure_lowest,delta_pressure_highest,atmosphere_lowest,atmosphere_highest

def tile_wind_pp(atmosphere, delta_pressure, MAP_DIMENSION_X, MAP_DIMENSION_Y, wind_value_x, wind_value_y, delta_pressure_highest):
    # Add dynamic wind
    p01 = wind_value_x
    p10 = wind_value_y
    atmosphere_new = atmosphere.copy()
    for ly in range (1,MAP_DIMENSION_Y-1):
        for lx in range (1,MAP_DIMENSION_X-1):
            tp01 = (p01 * delta_pressure[lx][ly]) / delta_pressure_highest
            tp10 = (p10 * delta_pressure[lx][ly]) / delta_pressure_highest
            tp00 = 256 - tp01 - tp10
            local_atm = \
                (tp00 * atmosphere[lx][ly]) + \
                (tp10 * atmosphere[lx][ly+1]) + \
                (tp01 * atmosphere[lx+1][ly])
            atmosphere_new[lx][ly] = int(local_atm) >> 8;
    atmosphere = atmosphere_new.copy()

def tile_wind_np(atmosphere, delta_pressure, MAP_DIMENSION_X, MAP_DIMENSION_Y, wind_value_x, wind_value_y, delta_pressure_highest):
    # Add dynamic wind
    p01 = wind_value_x
    p10 = 0 - wind_value_y
    atmosphere_new = atmosphere.copy()
    for ly in range (1,MAP_DIMENSION_Y-1):
        for lx in range (1,MAP_DIMENSION_X-1):
            tp01 = (p01 * delta_pressure[lx][ly]) / delta_pressure_highest
            tp10 = (p10 * delta_pressure[lx][ly]) / delta_pressure_highest
            tp00 = 256 - tp01 - tp10
            local_atm = \
                (tp00 * atmosphere[lx][ly]) + \
                (tp10 * atmosphere[lx][ly-1]) + \
                (tp01 * atmosphere[lx+1][ly])
            atmosphere_new[lx][ly] = int(local_atm) >> 8;
    atmosphere = atmosphere_new.copy()

def tile_wind_pn(atmosphere, delta_pressure, MAP_DIMENSION_X, MAP_DIMENSION_Y, wind_value_x, wind_value_y, delta_pressure_highest):
    # Add dynamic wind
    p01 = 0 - wind_value_x
    p10 = wind_value_y
    atmosphere_new = atmosphere.copy()
    for ly in range (1,MAP_DIMENSION_Y-1):
        for lx in range (1,MAP_DIMENSION_X-1):
            tp01 = (p01 * delta_pressure[lx][ly]) / delta_pressure_highest
            tp10 = (p10 * delta_pressure[lx][ly]) / delta_pressure_highest
            tp00 = 256 - tp01 - tp10
            local_atm = \
                (tp00 * atmosphere[lx][ly]) + \
                (tp10 * atmosphere[lx][ly+1]) + \
                (tp01 * atmosphere[lx-1][ly])
            atmosphere_new[lx][ly] = int(local_atm) >> 8;
    atmosphere = atmosphere_new.copy()

def tile_wind_nn(atmosphere, delta_pressure, MAP_DIMENSION_X, MAP_DIMENSION_Y, wind_value_x, wind_value_y, delta_pressure_highest):
    # Add dynamic wind
    p01 = 0 - wind_value_x
    p10 = 0 - wind_value_y
    atmosphere_new = atmosphere.copy()
    for ly in range (1,MAP_DIMENSION_Y-1):
        for lx in range (1,MAP_DIMENSION_X-1):
            tp01 = (p01 * delta_pressure[lx][ly]) / delta_pressure_highest
            tp10 = (p10 * delta_pressure[lx][ly]) / delta_pressure_highest
            tp00 = 256 - tp01 - tp10
            local_atm = \
                (tp00 * atmosphere[lx][ly]) + \
                (tp10 * atmosphere[lx][ly-1]) + \
                (tp01 * atmosphere[lx-1][ly])
            atmosphere_new[lx][ly] = int(local_atm) >> 8;
    atmosphere = atmosphere_new.copy()

def title_wind_calculation(wind_dissipation,wind_aim_x,wind_aim_y,wind_value_x,wind_value_y):
    if (randint(0,2048) & 31) == 0:
        wind_dissipation = randint(0,1024) & 3
        wind_aim =  -96 + (randint(0,2048) % 194)
        wind_value_x = wind_aim
        wind_aim =  -96 + (randint(0,2048) % 194)
        wind_aim_y = wind_aim
        wind_aim =  -96 + (randint(0,2048) % 194)
        wind_value_y = wind_aim
        wind_aim =  -96 + (randint(0,2048) % 194)
        wind_aim_x = wind_aim

    if wind_aim_x > wind_value_x:
        wind_value_x = wind_value_x + 1

    if wind_aim_x < wind_value_x:
        wind_value_x=wind_value_x-1

    if wind_aim_y > wind_value_y:
        wind_value_y=wind_value_y+1

    if wind_aim_y < wind_value_y:
        wind_value_y=wind_value_y-1

    return wind_dissipation,wind_aim_x,wind_aim_y,wind_value_x,wind_value_y

def tile_wrap(atmosphere,MAP_DIMENSION_X,MAP_DIMENSION_Y):
    for ly in range (0,MAP_DIMENSION_Y):
        for lx in range (0,MAP_DIMENSION_X):
            atmosphere[lx][ly] = (atmosphere[lx][ly] * 253) / 256

def windCycle(rooms, mapArea, atmosphere, delta_pressure, wind_dissipation, local_delta, wind_aim_x, wind_aim_y, wind_value_x, wind_value_y,delta_pressure_highest,atmosphere_lowest,atmosphere_highest):
    # east/west
    MAP_DIMENSION_X=mapArea[1][1] - mapArea[1][0]
    # north/south
    MAP_DIMENSION_Y=mapArea[0][1] - mapArea[0][0]

    wind_dissipation,wind_aim_x,wind_aim_y,wind_value_x,wind_value_y = title_wind_calculation(wind_dissipation,wind_aim_x,wind_aim_y,wind_value_x,wind_value_y)
    p01 = wind_value_x
    p10 = wind_value_y
    if p01 > -1:
        if p10 > -1:
            tile_wind_pp(atmosphere, delta_pressure, MAP_DIMENSION_X, MAP_DIMENSION_Y, wind_value_x, wind_value_y, delta_pressure_highest)
        else:
            tile_wind_np(atmosphere, delta_pressure, MAP_DIMENSION_X, MAP_DIMENSION_Y, wind_value_x, wind_value_y, delta_pressure_highest)
    else:
        if p10 > -1:
            tile_wind_pn(atmosphere, delta_pressure, MAP_DIMENSION_X, MAP_DIMENSION_Y, wind_value_x, wind_value_y, delta_pressure_highest)
        else:
            tile_wind_nn(atmosphere, delta_pressure, MAP_DIMENSION_X, MAP_DIMENSION_Y, wind_value_x, wind_value_y, delta_pressure_highest)

    if atmosphere_lowest < bits_neg or atmosphere_highest > bits_pos:
        tile_wrap(atmosphere,MAP_DIMENSION_X,MAP_DIMENSION_Y)
