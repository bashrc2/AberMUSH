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

def noOfMills(side: str,board: str) -> int:
    """Count the number of mills for the side
    """
    if side=='white':
        piece='●'
    else:
        piece='○'
    millsCtr=0
    #vertical
    if board[0]==piece and board[9]==piece and board[21]==piece:
        millsCtr+=1
    if board[3]==piece and board[10]==piece and board[18]==piece:
        millsCtr+=1
    if board[6]==piece and board[11]==piece and board[15]==piece:
        millsCtr+=1
    if board[1]==piece and board[4]==piece and board[7]==piece:
        millsCtr+=1
    if board[16]==piece and board[19]==piece and board[22]==piece:
        millsCtr+=1
    if board[8]==piece and board[12]==piece and board[17]==piece:
        millsCtr+=1
    if board[5]==piece and board[13]==piece and board[20]==piece:
        millsCtr+=1
    if board[2]==piece and board[14]==piece and board[23]==piece:
        millsCtr+=1
    # horizontal
    if board[0]==piece and board[1]==piece and board[2]==piece:
        millsCtr+=1
    if board[3]==piece and board[4]==piece and board[5]==piece:
        millsCtr+=1
    if board[6]==piece and board[7]==piece and board[8]==piece:
        millsCtr+=1
    if board[9]==piece and board[10]==piece and board[11]==piece:
        millsCtr+=1
    if board[12]==piece and board[13]==piece and board[14]==piece:
        millsCtr+=1
    if board[15]==piece and board[16]==piece and board[17]==piece:
        millsCtr+=1
    if board[18]==piece and board[19]==piece and board[20]==piece:
        millsCtr+=1
    if board[21]==piece and board[22]==piece and board[23]==piece:
        millsCtr+=1
    return millsCtr

def morrisBoardSet(board: str,index: int,piece: str) -> str:
    return board[:index]+piece+board[(index+1):]

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

    if not items[gameItemID]['gameState'].get('millsWhite'):
        items[gameItemID]['gameState']['millsWhite']=0
    if not items[gameItemID]['gameState'].get('millsBlack'):
        items[gameItemID]['gameState']['millsBlack']=0
        
    if items[gameItemID]['gameState'].get('morris'):
        board=items[gameItemID]['gameState']['morris']
    else:
        board='·' * 24
        items[gameItemID]['gameState']['morris']=board

    # check for a win
    if whiteCounters==0 and blackCounters==0:
        if morrisPieces('white',board)<=2 or \
           morrisPieces('black',board)<=2:
            showMorrisBoard(players,id,mud,rooms,items,itemsDB)
            return

    if noOfMills('black',board)>items[gameItemID]['gameState']['millsBlack']:
        showMorrisBoard(players,id,mud,rooms,items,itemsDB)
        return
    if noOfMills('white',board)>items[gameItemID]['gameState']['millsWhite']:
        showMorrisBoard(players,id,mud,rooms,items,itemsDB)
        return

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
        if len(w)==4:
            if w[1].isdigit() and w[3].isdigit():
                if ord(w[0])>=ord('a') and \
                   ord(w[0])<=ord('g') and \
                   int(w[1])>=1 and \
                   int(w[1])<=7 and \
                   ord(w[2])>=ord('a') and \
                   ord(w[2])<=ord('g') and \
                   int(w[3])>=1 and \
                   int(w[4])<=7:
                    if w[:2] in validMorrisBoardLocations and \
                       w[2:] in validMorrisBoardLocations:
                        boardMove.append(w[:2])
                        boardMove.append(w[2:])
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
                    if turn=='white':
                        if whiteCounters>0:
                            board=morrisBoardSet(board,index,'●')
                            whiteCounters-=1
                            moveSucceeded=True
                            items[gameItemID]['gameState']['morrisWhite']=whiteCounters
                            items[gameItemID]['gameState']['morris']=board
                            items[gameItemID]['gameState']['morrisTurn']='black'
                        else:
                            mud.send_message(id, '\nAll your counters have been placed.\n')
                    else:
                        if blackCounters>0:
                            board=morrisBoardSet(board,index,'○')
                            blackCounters-=1
                            moveSucceeded=True
                            items[gameItemID]['gameState']['morrisBlack']=blackCounters
                            items[gameItemID]['gameState']['morris']=board
                            items[gameItemID]['gameState']['morrisTurn']='white'
                        else:
                            mud.send_message(id, '\nAll your counters have been placed.\n')
                break
            index+=1
    else:
        if turn=='white' and whiteCounters>0:
            mud.send_message(id, '\nPlace your counters first before moving any of them.\n')
            return
        elif turn=='black' and blackCounters>0:
            mud.send_message(id, '\nPlace your counters first before moving any of them.\n')
            return

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
                    board=morrisBoardSet(board,toIndex,'●')
                    items[gameItemID]['gameState']['morrisTurn']='black'
                else:
                    board=morrisBoardSet(board,toIndex,'○')
                    items[gameItemID]['gameState']['morrisTurn']='white'
                board=morrisBoardSet(board,fromIndex,'·')
                items[gameItemID]['gameState']['morris']=board
                moveSucceeded=True
                break
            toIndex+=1
    showMorrisBoard(players,id,mud,rooms,items,itemsDB)

def morrisPieces(side: str,board: str) -> int:
    ctr=0
    if side=='white':
        for piece in board:
            if piece=='●':
                ctr+=1
    else:
        for piece in board:
            if piece=='○':
                ctr+=1
    return ctr

def resetMorrisBoard(players: {},id,mud,rooms: {}, \
                     items: {},itemsDB: {}) -> None:
    gameItemID=morrisBoardInRoom(players,id,rooms,items,itemsDB)
    if not gameItemID:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return

    if not items[gameItemID].get('gameState'):
        items[gameItemID]['gameState']={}

    board='·' * 24
    items[gameItemID]['gameState']['morris']=board
    items[gameItemID]['gameState']['morrisWhite']=9
    items[gameItemID]['gameState']['millsWhite']=0
    items[gameItemID]['gameState']['morrisBlack']=9
    items[gameItemID]['gameState']['millsBlack']=0
    items[gameItemID]['gameState']['morrisTurn']='white'
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

    if not items[gameItemID]['gameState'].get('millsWhite'):
        items[gameItemID]['gameState']['millsWhite']=0
    if not items[gameItemID]['gameState'].get('millsBlack'):
        items[gameItemID]['gameState']['millsBlack']=0

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

    whiteCounters=9
    if items[gameItemID]['gameState'].get('morrisWhite'):
        whiteCounters=int(items[gameItemID]['gameState']['morrisWhite'])

    blackCounters=9
    if items[gameItemID]['gameState'].get('morrisBlack'):
        blackCounters=int(items[gameItemID]['gameState']['morrisBlack'])

    if whiteCounters==0 and blackCounters==0:
        if morrisPieces('white',board)<=2:
            mud.send_message(id, 'Black wins\n')
            return
        elif morrisPieces('black',board)<=2:
            mud.send_message(id, 'White wins\n')
            return

    if noOfMills('black',board)>items[gameItemID]['gameState']['millsBlack']:
        mud.send_message(id, 'Black has a mill. Take a white counter.\n')
        return
    if noOfMills('white',board)>items[gameItemID]['gameState']['millsWhite']:
        mud.send_message(id, 'White has a mill. Take a black counter.\n')
        return

    if not items[gameItemID]['gameState'].get('morrisTurn'):
        items[gameItemID]['gameState']['morrisTurn']='white'
    mud.send_message(id, items[gameItemID]['gameState']['morrisTurn']+"'s move\n")

def takeMorrisCounter(takeDescription: str, \
                      players: {},id,mud,rooms: {}, \
                      items: {},itemsDB: {}) -> None:
    """Takes an opponent counter from the board
    """
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

    takeDescription= \
        takeDescription.lower().replace('.',' ').replace(',',' ').strip()
    words=takeDescription.split()
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
    if len(boardMove)!=1:
        mud.send_message(id, '\nSpecify the coordinate of the counter to be taken.\n')
        return

    if noOfMills('black',board)>items[gameItemID]['gameState']['millsBlack']:
        index=0
        for loc in validMorrisBoardLocations:
            if loc==boardMove[0]:
                if board[index]=='●':
                    items[gameItemID]['gameState']['millsBlack']=noOfMills('black',board)
                    board=morrisBoardSet(board,index,'·')
                    items[gameItemID]['gameState']['morris']=board
                    showMorrisBoard(players,id,mud,rooms,items,itemsDB)
            index+=1
    elif noOfMills('white',board)>items[gameItemID]['gameState']['millsWhite']:
        index=0
        for loc in validMorrisBoardLocations:
            if loc==boardMove[0]:
                if board[index]=='○':
                    items[gameItemID]['gameState']['millsWhite']=noOfMills('white',board)
                    board=morrisBoardSet(board,index,'·')
                    items[gameItemID]['gameState']['morris']=board
                    showMorrisBoard(players,id,mud,rooms,items,itemsDB)
            index+=1
            
    
