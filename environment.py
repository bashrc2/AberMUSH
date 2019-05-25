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

def generateCloud(rooms, mapArea, clouds, cloudGrid, tileSize, windDirection):
    mapWidth = mapArea[1][1] - mapArea[1][0]
    mapHeight = mapArea[0][1] - mapArea[0][0]
    cloudGridWidth = int(mapWidth/tileSize)
    cloudGridHeight = int(mapHeight/tileSize)

    if len(clouds)==0:
        for x in range (0,mapWidth):
            clouds[x]={}
            for y in range (0,mapHeight):
                clouds[x][y]=0

    if len(cloudGrid)==0:
        for x in range (0,cloudGridWidth):
            cloudGrid[x]={}
            for y in range (0,cloudGridHeight):
                cloudGrid[x][y]=randint(0,255)

    for x in range (0,mapWidth-1):
        tile_tx = int(x / tileSize)
        tile_bx = tile_tx + 1
        if tile_bx >= cloudGridWidth:
            tile_bx = 0
        for y in range (0,mapHeight-1):
            tile_ty = int(y / tileSize)
            tile_by = tile_ty + 1
            if tile_by >= cloudGridHeight:
                tile_by = 0

            interpolate_top = \
                cloudGrid[tile_tx][tile_ty] + \
                int((cloudGrid[tile_bx][tile_ty] - cloudGrid[tile_tx][tile_ty]) * \
                    (x % tileSize) / tileSize)

            interpolate_bottom = \
                cloudGrid[tile_tx][tile_by] + \
                int((cloudGrid[tile_bx][tile_by] - cloudGrid[tile_tx][tile_by]) * \
                    (x % tileSize) / tileSize)

            clouds[x][y] = \
                interpolate_top + \
                int((interpolate_bottom - interpolate_top) * \
                    (y % tileSize) / tileSize)

    for x in range (0,cloudGridWidth):
        for y in range (0,cloudGridHeight):
            cloudGrid[x][y]=cloudGrid[x][y]+randint(-5,5)
            if cloudGrid[x][y] < 0:
                cloudGrid[x][y] = cloudGrid[x][y] + 255
            if cloudGrid[x][y] > 255:
                cloudGrid[x][y] = cloudGrid[x][y] - 255

    windDirection = (windDirection + randint(-1,1)) % 360
    if windDirection < 0:
        windDirection = windDirection + 360

    dx=0
    dy=0
    if windDirection >= 290 or windDirection <=70:
        dy=1
    if windDirection >= 200 and windDirection < 160:
        dy=-1
    if windDirection < 315 and windDirection >= 225:
        dx=-1
    if windDirection > 45 and windDirection <= 90+45:
        dx=1

    cloudGridNew={}
    for x in range (0,cloudGridWidth):
        cloudGridNew[x]={}
        for y in range (0,cloudGridHeight):
            cloudGridNew[x][y]=cloudGrid[x][y]

    for x in range (0,cloudGridWidth):
        old_x = x + dx
        for y in range (0,cloudGridHeight):
            old_y = y + dy
            if old_x >= 0 and old_x <= cloudGridWidth-1 and \
               old_y >=0 and old_y <= cloudGridHeight-1:
                cloudGridNew[x][y]=cloudGrid[old_x][old_y]
            else:
                if old_x < 0:
                    old_x = old_x + cloudGridWidth
                if old_y < 0:
                    old_y = old_y + cloudGridHeight
                if old_x > cloudGridWidth-1:
                    old_x = old_x - cloudGridWidth
                if old_y > cloudGridHeight-1:
                    old_y = old_y - cloudGridHeight
                cloudGridNew[x][y]=randint(0,255)

    for x in range (0,cloudGridWidth):
        for y in range (0,cloudGridHeight):
            cloudGrid[x][y]=cloudGridNew[x][y]

    return windDirection

def plotClouds(mapArea, clouds, temperature):
    mapWidth = mapArea[1][1] - mapArea[1][0]
    mapHeight = mapArea[0][1] - mapArea[0][0]

    for y in range (0,mapHeight-1):
        lineStr=''
        for x in range (0,mapWidth-1):
            lineChar='.'
            if clouds[x][y]>temperature*6:
                lineChar='o'
            if clouds[x][y]>temperature*7:
                lineChar='O'
            lineStr = lineStr + lineChar
        print(lineStr+'\n')
    print('\n')
