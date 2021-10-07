__filename__ = "chess.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Tabletop Games"

import re

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
    'R': '♜', 'N': '♞', 'B': '♝', 'Q': '♛', 'K': '♚', 'P': '♟',
    'r': '♖', 'n': '♘', 'b': '♗', 'q': '♕', 'k': '♔', 'p': '♙', '.': '·'
}

uni_pieces_html = {
    'r': 'black_rook', 'n': 'black_knight', 'b': 'black_bishop',
    'q': 'black_queen', 'k': 'black_king', 'p': 'black_pawn',
    'R': 'white_rook', 'N': 'white_knight', 'B': 'white_bishop',
    'Q': 'white_queen', 'K': 'white_king', 'P': 'white_pawn'
}


def showChessBoard(boardName: str, gameState: [],
                   id: int, mud, turn: str) -> None:
    """Shows the chess board
    """
    if mud.playerUsingWebInterface(id):
        _showChessBoardAsHtml(boardName, gameState, id, mud, turn)
        return
    mud.sendMessage(id, '\n')
    boardStr = ''
    i = 0
    if turn == 'white':
        for row in gameState:
            boardRowStr = ' ' + str(8 - i) + ' '
            for p in row:
                boardRowStr += ' ' + uni_pieces[p]
            boardStr += boardRowStr + '\n'
            i += 1
        boardStr += '\n    a b c d e f g h \n\n'
    else:
        for row in gameState:
            boardRowStr = ''
            for p in row:
                boardRowStr = ' ' + uni_pieces[p] + boardRowStr
            boardStr = ' ' + str(8 - i) + ' ' + boardRowStr + '\n' + boardStr
            i += 1
        boardStr += '\n    h g f e d c b a \n\n'
    mud.send_game_board(id, boardStr)


def _showChessBoardAsHtml(boardName: str, gameState: [], id: int,
                          mud, turn: str) -> None:
    """Shows the chess board as html for the web interface
    """
    if not boardName:
        print('No chess board name is specified for this room')
        return
    boardDir = 'chessboards/' + boardName + '/'
    boardHtml = '<table id="chess">'
    i = 0
    if turn == 'white':
        for row in gameState:
            boardHtml += '<tr>'

            # show row number
            boardHtml += '<td>'
            boardHtml += '<label class="coord">' + str(8 - i) + '</label>'
            boardHtml += '</td>'

            j = 0
            for p in row:
                boardHtml += '<td><div class="parent">'

                if (j + (i % 2)) % 2 == 0:
                    boardHtml += '<img class="board" src="' + \
                        boardDir + 'black_square.png" />'
                else:
                    boardHtml += '<img class="board" src="' + \
                        boardDir + 'white_square.png" />'

                if p != '.':
                    boardHtml += '<img class="boardpiece" src="' + \
                        boardDir + uni_pieces_html[p] + '.png" />'

                boardHtml += '</div></td>'
                j += 1

            boardHtml += '</tr>'
            i += 1
        boardHtml += '<tr><td> </td>' + \
            '<td><label class="coord"><center>a</center></label></td>' + \
            '<td><label class="coord"><center>b</center></label></td>' + \
            '<td><label class="coord"><center>c</center></label></td>' + \
            '<td><label class="coord"><center>d</center></label></td>' + \
            '<td><label class="coord"><center>e</center></label></td>' + \
            '<td><label class="coord"><center>f</center></label></td>' + \
            '<td><label class="coord"><center>g</center></label></td>' + \
            '<td><label class="coord"><center>h</center></label></td>' + \
            '</tr></table>'
    else:
        boardHtml = ''
        for row in gameState:
            boardRowStr = ''
            j = 0
            for p in row:
                pieceStr = '<td><div class="parent">'

                if (j + (i % 2)) % 2 == 0:
                    pieceStr += '<img class="board" src="' + \
                        boardDir + 'black_square.png" />'
                else:
                    pieceStr += '<img class="board" src="' + \
                        boardDir + 'white_square.png" />'

                if p != '.':
                    pieceStr += '<img class="boardpiece" src="' + \
                        boardDir + uni_pieces_html[p] + '.png" />'
                pieceStr += '</div></td>'

                boardRowStr = pieceStr + boardRowStr
                j += 1

            # show row number
            boardRowStr = '<tr><td><label class="coord">' + \
                str(8 - i) + '</label></td>' + \
                boardRowStr + '</tr>'

            boardHtml = boardRowStr + boardHtml

            i += 1

        boardHtml = '<table id="chess">' + boardHtml
        boardHtml += '<tr><td> </td>' + \
            '<td><label class="coord"><center>h</center></label></td>' + \
            '<td><label class="coord"><center>g</center></label></td>' + \
            '<td><label class="coord"><center>f</center></label></td>' + \
            '<td><label class="coord"><center>e</center></label></td>' + \
            '<td><label class="coord"><center>d</center></label></td>' + \
            '<td><label class="coord"><center>c</center></label></td>' + \
            '<td><label class="coord"><center>b</center></label></td>' + \
            '<td><label class="coord"><center>a</center></label></td>' + \
            '</tr></table>'
    mud.send_game_board(id, boardHtml + '\n')


def initialChessBoard() -> []:
    """Returns the initial state of a chess game
    """
    return initial.copy()


def _chessPieceAt(gameState: [], coord: str) -> str:
    if len(coord) != 2:
        return '.'
    if ord(coord[0]) < ord('a') or ord(coord[0]) > ord('h'):
        return '.'
    if ord(coord[1]) < ord('1') or ord(coord[1]) > ord('8'):
        return '.'
    return gameState[ord('8') - ord(coord[1])][ord(coord[0]) - ord('a')]


def _chessPieceSet(gameState: [], coord: str, piece: str) -> None:
    if len(coord) != 2:
        return
    if ord(coord[0]) < ord('a') or ord(coord[0]) > ord('h'):
        return
    if ord(coord[1]) < ord('1') or ord(coord[1]) > ord('8'):
        return
    row = gameState[ord('8') - ord(coord[1])]
    col = ord(coord[0]) - ord('a')
    gameState[ord('8') - ord(coord[1])] = \
        row[:col] + piece + row[(col + 1):]


def moveChessPiece(moveStr: str, gameState: [],
                   turn: str, id: int, mud) -> bool:
    movematch = re.match('([a-h][1-8])'*2, moveStr.lower())
    if not movematch:
        return False
    moveFrom = movematch.group(1)
    moveTo = movematch.group(2)
    fromPiece = _chessPieceAt(gameState, moveFrom)
    if fromPiece == '.':
        return False
    if turn == 'white':
        if fromPiece.upper() != fromPiece:
            return False
    else:
        if fromPiece.lower() != fromPiece:
            return False
    _chessPieceSet(gameState, moveFrom, '.')
    _chessPieceSet(gameState, moveTo, fromPiece)
    return True
