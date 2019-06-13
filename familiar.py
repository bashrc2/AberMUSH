__filename__ = "familiar.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from functions import log
from functions import moveNPCs
from random import randint
from copy import deepcopy

import time

# Movement modes for familiars
familiarModes = ("follow","scout")

def getFamiliarModes():
    return familiarModes

def getFamiliarName(players,id,npcs):
    """Returns the name of the familiar of the given player
    """
    if players[id]['familiar']!=-1:
        for (nid, pl) in list(npcs.items()):
            if npcs[nid]['familiarOf'] == players[id]['name']:
                return npcs[nid]['name']
    return ''

def familiarRecall(mud, players, id, npcs, npcsDB):
    """Move any familiar to the player's location
    """
    # remove any existing familiars
    removals = []
    for (index, details) in npcs.items():
        if details['familiarOf'] == players[id]['name']:
            removals.append(index)

    for index in removals:
        del npcs[index]

    # By default player has no familiar
    players[id]['familiar'] = -1

    # Find familiar and set its room to that of the player
    for (index, details) in npcsDB.items():
        if details['familiarOf'] == players[id]['name']:
            players[id]['familiar'] = int(index)
            details['room'] = players[id]['room']
            if not npcs.get(str(index)):
                npcs[str(index)] = deepcopy(npcsDB[index])
            npcs[str(index)]['room'] = players[id]['room']
            mud.send_message(id, "Your familiar is recalled.\n\n")
            break

def familiarDefaultMode(nid, npcs, npcsDB):
    npcs[nid]['familiarMode']="follow"
    npcsDB[nid]['familiarMode']="follow"
    npcs[nid]['moveType']=""
    npcsDB[nid]['moveType']=""
    npcs[nid]['path']=[]
    npcsDB[nid]['path']=[]

def familiarScoutAnyDirection(startRoomID, roomExits):
    """Scout in any direction
    """
    newPath=[startRoomID]
    for ex,rm in roomExits.items():
        newPath.append(rm)
        newPath.append(startRoomID)
    if len(newPath)==1:
        newPath.clear()
    return newPath

def familiarScoutInDirection(startRoomID, roomExits, direction):
    """Scout in the given direction
    """
    newPath=[]
    if roomExits.get(direction):
        newPath=[startRoomID, roomExits[direction]]
    return newPath

def familiarScout(nid, npcs, npcsDB, rooms, direction):
    """familiar begins scouting the surrounding rooms
    """
    startRoomID = npcs[nid]['room']
    roomExits = rooms[startRoomID]['exits']

    newPath=[]

    if direction=='any' or direction=='all' or len(direction)==0:
        newPath=familiarScoutAnyDirection(startRoomID, roomExits)
    else:
        newPath=familiarScoutInDirection(startRoomID, roomExits, direction)

    if len(newPath)>0:
        npcs[nid]['familiarMode']="scout"
        npcs[nid]['moveType']="patrol"
        npcs[nid]['path']=deepcopy(newPath)
        npcsDB[nid]['familiarMode']="scout"
        npcsDB[nid]['moveType']="patrol"
        npcsDB[nid]['path']=deepcopy(newPath)
    else:
        familiarDefaultMode(nid, npcs, npcsDB)
