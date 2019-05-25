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

import time

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
