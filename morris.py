__filename__ = "morris.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

import re, sys

validMorrisBoardLocations=[
    'a1','d1','g1',
    'b2','d2','f2',
    'c3','d3','e3',
    'a4','b4','c4','e4','f4','g4',
    'c5','d5','e5',
    'b6','d6','f6',
    'a7','d7','g7'        
]

def morrisBoardInRoom(players: {},id,rooms: {},items: {},itemsDB: {}):
    """Returns the item ID if there is a Morris board in the room
    """
    rid=players[id]['room']
    for i in items:
        if items[i]['room'] != rid:
            continue
        if 'morris' in itemsDB[items[i]['id']]['game'].lower():
            return i
    return None

def morrisBoardSet(board: str,index: int,piece: str):
    board=board[:index]+piece+board[(index+1):]

def morrisMove(moveDescription: str, \
               players: {},id,mud,rooms: {}, \
               items: {},itemsDB: {}) -> None:
    gameItemID=morrisBoardInRoom(players,id,rooms,items,itemsDB)
    if not gameItemID:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return

    if not items[gameItemID].get('gameState'):
        items[gameItemID]['gameState']={}

    turn='white'
    if items[gameItemID]['gameState'].get('morrisTurn'):
        turn=items[gameItemID]['gameState']['morrisTurn']
    else:
        items[gameItemID]['gameState']['morrisTurn']=turn

    whiteCounters=9
    if items[gameItemID]['gameState'].get('morrisWhite'):
        whiteCounters=int(items[gameItemID]['gameState']['morrisWhite'])

    blackCounters=9
    if items[gameItemID]['gameState'].get('morrisBlack'):
        blackCounters=int(items[gameItemID]['gameState']['morrisBlack'])

    if items[gameItemID]['gameState'].get('morris'):
        board=items[gameItemID]['gameState']['morris']
    else:
        board='·' * 24
        items[gameItemID]['gameState']['morris']=board
    
    moveDescription= \
        moveDescription.lower().replace('.',' ').replace(',',' ').strip()
    words=moveDescription.split()
    boardMove=[]
    for w in words:
        if len(w)==2:
            if w[1].isdigit():
                if ord(w[0])>=ord('a') and \
                   ord(w[0])<=ord('g') and \
                   int(w[1])>=1 and \
                   int(w[1])<=7:
                    if w in validMorrisBoardLocations:
                        boardMove.append(w)
    if len(boardMove)==0 or len(boardMove)>2:
        mud.send_message(id, "\nThat's not a valid move.\n")
        return

    moveSucceeded=False
    
    if len(boardMove)==1:
        # single move to place a counter
        index=0
        for loc in validMorrisBoardLocations:
            if loc==boardMove[0]:
                if board[index]=='·':
                    mud.send_message(id, '\nPlacing counter\n')
                    if turn=='white':
                        if whiteCounters>0:
                            morrisBoardSet(board,index,'●')
                            whiteCounters-=1
                            moveSucceeded=True
                            items[gameItemID]['gameState']['morrisWhite']=whiteCounters
                            items[gameItemID]['gameState']['morris']=board
                            items[gameItemID]['gameState']['morrisTurn']='black'
                            mud.send_game_board(id, '\nBoard2: '+board+'\n')
                    else:
                        if blackCounters>0:
                            morrisBoardSet(board,index,'○')
                            blackCounters-=1
                            moveSucceeded=True
                            items[gameItemID]['gameState']['morrisBlack']=blackCounters
                            items[gameItemID]['gameState']['morris']=board
                            items[gameItemID]['gameState']['morrisTurn']='white'
                            mud.send_game_board(id, '\nBoard3: '+board+'\n')
                break
            index+=1
    else:
        # move a counter from one place to another
        if boardMove[0]==boardMove[1]:
            mud.send_message(id,'\nSpecify coordinates to move from and to.\n')
            return                        
        if boardMove[0][0]!=boardMove[1][0] and \
           boardMove[0][1]!=boardMove[1][1]:
            mud.send_message(id,'\nYou can only move vertically or horizontally.\n')
            return            
        fromIndex=0
        for loc in validMorrisBoardLocations:
            if loc==boardMove[0]:
                if turn=='white' and board[fromIndex]!='●':
                    mud.send_message(id,"\nThere isn't a counter at "+loc+'\n')
                    return
                if turn=='black' and board[fromIndex]!='○':
                    mud.send_message(id,"\nThere isn't a counter at "+loc+'\n')
                    return
                break
            fromIndex+=1
        toIndex=0
        for loc in validMorrisBoardLocations:
            if loc==boardMove[1]:
                if board[toIndex]!='':
                    mud.send_message(id,"\nThere is already a counter at "+loc+'\n')
                    return
                if turn=='white':
                    morrisBoardSet(board,toIndex,'●')
                    items[gameItemID]['gameState']['morrisTurn']='black'
                else:
                    morrisBoardSet(board,toIndex,'○')
                    items[gameItemID]['gameState']['morrisTurn']='white'
                morrisBoardSet(board,fromIndex,'·')
                items[gameItemID]['gameState']['morris']=board
                moveSucceeded=True
                break
            toIndex+=1
    mud.send_game_board(id, '\nBoard4: '+board+'\n')
    showMorrisBoard(players,id,mud,rooms,items,itemsDB)

def showMorrisBoard(players: {},id,mud,rooms: {}, \
                    items: {},itemsDB: {}) -> None:
    gameItemID=morrisBoardInRoom(players,id,rooms,items,itemsDB)
    if not gameItemID:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return

    if not items[gameItemID].get('gameState'):
        items[gameItemID]['gameState']={}

    if items[gameItemID]['gameState'].get('morris'):
        board=items[gameItemID]['gameState']['morris']
    else:
        board='·' * 24
        items[gameItemID]['gameState']['morris']=board

    mud.send_game_board(id, '\nBoard: '+board+'\n')
        
    boardStr='\n'
    boardStr+=' 7 '+board[21]+'─────'+board[22]+'─────'+board[23]+'\n'
    boardStr+=' 6 │ '+board[18]+'───'+board[19]+'───'+board[20]+' │\n'
    boardStr+=' 5 │ │ '+board[15]+'─'+board[16]+'─'+board[17]+' │ │\n'
    boardStr+=' 4 '+board[9]+'-'+board[10]+'-'+board[11]+'   '+board[12]+'-'+board[13]+'-'+board[14]+'\n'
    boardStr+=' 3 │ │ '+board[6]+'─'+board[7]+'─'+board[8]+' │ │\n'
    boardStr+=' 2 │ '+board[3]+'───'+board[4]+'───'+board[5]+' │\n'
    boardStr+=' 1 '+board[0]+'─────'+board[1]+'─────'+board[2]+'\n'
    boardStr+='   a b c d e f g\n'

    mud.send_game_board(id, boardStr)
