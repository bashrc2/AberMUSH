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


def show_chess_board(board_name: str, game_state: [],
                     id: int, mud, turn: str) -> None:
    """Shows the chess board
    """
    if mud.player_using_web_interface(id):
        _show_chess_board_as_html(board_name, game_state, id, mud, turn)
        return
    mud.send_message(id, '\n')
    board_square = '░░'
    board_str = ''
    i = 0
    if turn == 'white':
        for row in game_state:
            board_row_str = ' ' + str(8 - i) + ' '
            x_coord = 0
            for pic in row:
                piece_str = uni_pieces[pic]
                if pic == '.':
                    piece_str = ' '
                    if (x_coord + (i % 2)) % 2 == 0:
                        piece_str = board_square
                board_row_str += ' ' + piece_str
                x_coord += 1
            board_str += board_row_str + '\n'
            i += 1
        board_str += '\n    a b c d e f g h \n\n'
    else:
        for row in game_state:
            board_row_str = ''
            x_coord = 0
            for pic in row:
                piece_str = uni_pieces[pic]
                if pic == '.':
                    piece_str = ' '
                    if (x_coord + (i % 2)) % 2 == 0:
                        piece_str = board_square
                board_row_str = ' ' + piece_str + board_row_str
                x_coord += 1
            board_str = \
                ' ' + str(8 - i) + ' ' + board_row_str + '\n' + board_str
            i += 1
        board_str += '\n    h g f e d c b a \n\n'
    mud.send_game_board(id, board_str)


def _show_chess_board_as_html(board_name: str, game_state: [], id: int,
                              mud, turn: str) -> None:
    """Shows the chess board as html for the web interface
    """
    if not board_name:
        print('No chess board name is specified for this room')
        return
    board_dir = 'chessboards/' + board_name + '/'
    board_html = '<table id="chess">'
    i = 0
    if turn == 'white':
        for row in game_state:
            board_html += '<tr>'

            # show row number
            board_html += '<td>'
            board_html += '<label class="coord">' + str(8 - i) + '</label>'
            board_html += '</td>'

            j = 0
            for pic in row:
                board_html += '<td><div class="parent">'

                if (j + (i % 2)) % 2 == 0:
                    board_html += '<img class="board" src="' + \
                        board_dir + 'black_square.png" />'
                else:
                    board_html += '<img class="board" src="' + \
                        board_dir + 'white_square.png" />'

                if pic != '.':
                    board_html += '<img class="boardpiece" src="' + \
                        board_dir + uni_pieces_html[pic] + '.png" />'

                board_html += '</div></td>'
                j += 1

            board_html += '</tr>'
            i += 1
        board_html += '<tr><td> </td>' + \
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
        board_html = ''
        for row in game_state:
            board_row_str = ''
            j = 0
            for pic in row:
                piece_str = '<td><div class="parent">'

                if (j + (i % 2)) % 2 == 0:
                    piece_str += '<img class="board" src="' + \
                        board_dir + 'black_square.png" />'
                else:
                    piece_str += '<img class="board" src="' + \
                        board_dir + 'white_square.png" />'

                if pic != '.':
                    piece_str += '<img class="boardpiece" src="' + \
                        board_dir + uni_pieces_html[pic] + '.png" />'
                piece_str += '</div></td>'

                board_row_str = piece_str + board_row_str
                j += 1

            # show row number
            board_row_str = '<tr><td><label class="coord">' + \
                str(8 - i) + '</label></td>' + \
                board_row_str + '</tr>'

            board_html = board_row_str + board_html

            i += 1

        board_html = '<table id="chess">' + board_html
        board_html += '<tr><td> </td>' + \
            '<td><label class="coord"><center>h</center></label></td>' + \
            '<td><label class="coord"><center>g</center></label></td>' + \
            '<td><label class="coord"><center>f</center></label></td>' + \
            '<td><label class="coord"><center>e</center></label></td>' + \
            '<td><label class="coord"><center>d</center></label></td>' + \
            '<td><label class="coord"><center>c</center></label></td>' + \
            '<td><label class="coord"><center>b</center></label></td>' + \
            '<td><label class="coord"><center>a</center></label></td>' + \
            '</tr></table>'
    mud.send_game_board(id, board_html + '\n')


def initial_chess_board() -> []:
    """Returns the initial state of a chess game
    """
    return initial.copy()


def _chess_piece_at(game_state: [], coord: str) -> str:
    """Return the chess piece at the given coord
    """
    if len(coord) != 2:
        return '.'
    if ord(coord[0]) < ord('a') or ord(coord[0]) > ord('h'):
        return '.'
    if ord(coord[1]) < ord('1') or ord(coord[1]) > ord('8'):
        return '.'
    return game_state[ord('8') - ord(coord[1])][ord(coord[0]) - ord('a')]


def _chess_piece_set(game_state: [], coord: str, piece: str) -> None:
    """Set the coord of a chess piece
    """
    if len(coord) != 2:
        return
    if ord(coord[0]) < ord('a') or ord(coord[0]) > ord('h'):
        return
    if ord(coord[1]) < ord('1') or ord(coord[1]) > ord('8'):
        return
    row = game_state[ord('8') - ord(coord[1])]
    col = ord(coord[0]) - ord('a')
    game_state[ord('8') - ord(coord[1])] = \
        row[:col] + piece + row[(col + 1):]


def move_chess_piece(move_str: str, game_state: [],
                     turn: str, id: int, mud) -> bool:
    """Move a chess piece
    """
    movematch = re.match('([a-h][1-8])'*2, move_str.lower())
    if not movematch:
        return False
    move_from = movematch.group(1)
    move_to = movematch.group(2)
    from_piece = _chess_piece_at(game_state, move_from)
    if from_piece == '.':
        return False
    if turn == 'white':
        if from_piece.upper() != from_piece:
            return False
    else:
        if from_piece.lower() != from_piece:
            return False
    _chess_piece_set(game_state, move_from, '.')
    _chess_piece_set(game_state, move_to, from_piece)
    return True
