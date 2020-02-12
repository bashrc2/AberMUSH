__filename__ = "chess.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

import re, sys

initial = [
    'rnbqkbnr',
    'pppppppp',
    '........',
    '........',
    '........',
    '........',
    'PPPPPPPP',
    'RNBQKBNR'
]

uni_pieces = {
    'R':'♜', 'N':'♞', 'B':'♝', 'Q':'♛', 'K':'♚', 'P':'♟', \
    'r':'♖', 'n':'♘', 'b':'♗', 'q':'♕', 'k':'♔', 'p':'♙', '.':'·'
}

def showChessBoard(gameState: [],id,mud,turn: str) -> None:
    """Shows the chess board
    """
    mud.send_message(id, '\n')
    boardStr=''
    i=0
    if turn=='white':
        for row in gameState:
            boardRowStr=' '+str(8-i)+' '
            for p in row:
                boardRowStr+=' '+uni_pieces[p]
            boardStr+=boardRowStr+'\n'
            i+=1
        boardStr+='\n    a b c d e f g h \n\n'
    else:
        for row in gameState:
            boardRowStr=' '+str(i)+' '
            for p in row:
                boardRowStr=' '+uni_pieces[p]+boardRowStr
            boardStr=boardRowStr+'\n'+boardStr
            i+=1
        boardStr+='\n    h g f e d c b a \n\n'
    mud.send_game_board(id,boardStr)

def initialChessBoard() -> []:
    """Returns the initial state of a chess game
    """
    return initial

def chessPieceAt(gameState: [],coord: str) -> str:
    if len(coord)!=2:
        return '.'
    if ord(coord[0])<ord('a') or ord(coord[0])>ord('h'):
        return '.'
    if ord(coord[1])<ord('1') or ord(coord[1])>ord('8'):
        return '.'
    return gameState[ord('8')-ord(coord[1])][ord(coord[0])-ord('a')]

def chessPieceSet(gameState: [],coord: str,piece: str) -> None:
    if len(coord)!=2:
        return
    if ord(coord[0])<ord('a') or ord(coord[0])>ord('h'):
        return
    if ord(coord[1])<ord('1') or ord(coord[1])>ord('8'):
        return
    gameState[ord('8')-ord(coord[1])][ord(coord[0])-ord('a')]=piece

def moveChessPiece(moveStr: str,gameState: [],turn: str,id,mud) -> bool:
    match = re.match('([a-h][1-8])'*2, moveStr.lower())
    mud.send_message(id,'matching\n')
    if not match:
        return False
    mud.send_message(id,'matched\n')
    moveFrom=match.group(1)
    mud.send_message(id,'moveFrom '+moveFrom+'\n')
    moveTo=match.group(2)
    mud.send_message(id,'moveTo '+moveTo+'\n')
    fromPiece=chessPieceAt(gameState,moveFrom)
    mud.send_message(id,'fromPiece '+fromPiece+'\n')
    if fromPiece=='.':
        return False
    if turn=='white':
        if fromPiece.upper()!=fromPiece:
            return False
    else:
        if fromPiece.lower()!=fromPiece:
            return False
    chessPieceSet(gameState,moveFrom,'.')
    chessPieceSet(gameState,moveTo,fromPiece)
    return True
