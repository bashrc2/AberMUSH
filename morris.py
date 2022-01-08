__filename__ = "morris.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Tabletop Games"

import os

VALID_MORRIS_BOARD_LOCATIONS = [
    'a1', 'd1', 'g1',
    'b2', 'd2', 'f2',
    'c3', 'd3', 'e3',
    'a4', 'b4', 'c4', 'e4', 'f4', 'g4',
    'c5', 'd5', 'e5',
    'b6', 'd6', 'f6',
    'a7', 'd7', 'g7'
]


def get_morris_board_name(players: {}, id: int, rooms: {},
                          items: {}, items_db: {}) -> str:
    """Returns the name of the morris board if there is one in the room
    This then corresponds to the subdirectory within morrisboards, where
    icons exist
    """
    rid = players[id]['room']
    for i in items:
        if items[i]['room'] != rid:
            continue
        if items_db[items[i]['id']].get('morrisBoardName'):
            return items_db[items[i]['id']]['morrisBoardName']
    return None


def _morris_board_in_room(players: {}, id, rooms: {}, items: {}, items_db: {}):
    """Returns the item ID if there is a Morris board in the room
    """
    rid = players[id]['room']
    for i in items:
        if items[i]['room'] != rid:
            continue
        if 'morris' in items_db[items[i]['id']]['game'].lower():
            return i
    return None


def _no_of_mills(side: str, board: str) -> int:
    """Count the number of mills for the side
    """
    if side == 'white':
        piece = '●'
    else:
        piece = '○'
    mills_ctr = 0
    # vertical
    if board[0] == piece and board[9] == piece and board[21] == piece:
        mills_ctr += 1
    if board[3] == piece and board[10] == piece and board[18] == piece:
        mills_ctr += 1
    if board[6] == piece and board[11] == piece and board[15] == piece:
        mills_ctr += 1
    if board[1] == piece and board[4] == piece and board[7] == piece:
        mills_ctr += 1
    if board[16] == piece and board[19] == piece and board[22] == piece:
        mills_ctr += 1
    if board[8] == piece and board[12] == piece and board[17] == piece:
        mills_ctr += 1
    if board[5] == piece and board[13] == piece and board[20] == piece:
        mills_ctr += 1
    if board[2] == piece and board[14] == piece and board[23] == piece:
        mills_ctr += 1
    # horizontal
    if board[0] == piece and board[1] == piece and board[2] == piece:
        mills_ctr += 1
    if board[3] == piece and board[4] == piece and board[5] == piece:
        mills_ctr += 1
    if board[6] == piece and board[7] == piece and board[8] == piece:
        mills_ctr += 1
    if board[9] == piece and board[10] == piece and board[11] == piece:
        mills_ctr += 1
    if board[12] == piece and board[13] == piece and board[14] == piece:
        mills_ctr += 1
    if board[15] == piece and board[16] == piece and board[17] == piece:
        mills_ctr += 1
    if board[18] == piece and board[19] == piece and board[20] == piece:
        mills_ctr += 1
    if board[21] == piece and board[22] == piece and board[23] == piece:
        mills_ctr += 1
    return mills_ctr


def _morris_board_set(board: str, index: int, piece: str) -> str:
    return board[:index] + piece + board[(index + 1):]


def morris_move(move_description: str,
                players: {}, id, mud, rooms: {},
                items: {}, items_db: {}) -> None:
    game_item_id = _morris_board_in_room(players, id, rooms, items, items_db)
    if not game_item_id:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return

    if not items[game_item_id].get('gameState'):
        items[game_item_id]['gameState'] = {}

    turn = 'white'
    if items[game_item_id]['gameState'].get('morrisTurn'):
        turn = items[game_item_id]['gameState']['morrisTurn']
    else:
        items[game_item_id]['gameState']['morrisTurn'] = turn

    white_counters = 9
    if items[game_item_id]['gameState'].get('morrisWhite'):
        white_counters = int(items[game_item_id]['gameState']['morrisWhite'])

    black_counters = 9
    if items[game_item_id]['gameState'].get('morrisBlack'):
        black_counters = int(items[game_item_id]['gameState']['morrisBlack'])

    if not items[game_item_id]['gameState'].get('millsWhite'):
        items[game_item_id]['gameState']['millsWhite'] = 0
    if not items[game_item_id]['gameState'].get('millsBlack'):
        items[game_item_id]['gameState']['millsBlack'] = 0

    if items[game_item_id]['gameState'].get('morris'):
        board = items[game_item_id]['gameState']['morris']
    else:
        board = '·' * 24
        items[game_item_id]['gameState']['morris'] = board

    board_name = get_morris_board_name(players, id, rooms, items, items_db)

    # check for a win
    if white_counters == 0 and black_counters == 0:
        if _morris_pieces('white', board) <= 2 or \
           _morris_pieces('black', board) <= 2:
            show_morris_board(board_name, players, id, mud, rooms,
                              items, items_db)
            return

    if _no_of_mills('black', board) > \
       items[game_item_id]['gameState']['millsBlack']:
        show_morris_board(board_name, players, id, mud, rooms, items, items_db)
        return
    if _no_of_mills('white', board) > \
       items[game_item_id]['gameState']['millsWhite']:
        show_morris_board(board_name, players, id, mud, rooms, items, items_db)
        return

    move_description = \
        move_description.lower().replace('.', ' ').replace(',', ' ').strip()
    words = move_description.split()
    board_move = []
    for wrd in words:
        if len(wrd) == 2:
            if wrd[1].isdigit():
                if ord(wrd[0]) >= ord('a') and \
                   ord(wrd[0]) <= ord('g') and \
                   int(wrd[1]) >= 1 and \
                   int(wrd[1]) <= 7:
                    if wrd in VALID_MORRIS_BOARD_LOCATIONS:
                        board_move.append(wrd)
        if len(wrd) == 4:
            if wrd[1].isdigit() and wrd[3].isdigit():
                if ord(wrd[0]) >= ord('a') and \
                   ord(wrd[0]) <= ord('g') and \
                   int(wrd[1]) >= 1 and \
                   int(wrd[1]) <= 7 and \
                   ord(wrd[2]) >= ord('a') and \
                   ord(wrd[2]) <= ord('g') and \
                   int(wrd[3]) >= 1 and \
                   int(wrd[4]) <= 7:
                    if wrd[:2] in VALID_MORRIS_BOARD_LOCATIONS and \
                       wrd[2:] in VALID_MORRIS_BOARD_LOCATIONS:
                        board_move.append(wrd[:2])
                        board_move.append(wrd[2:])
    if len(board_move) == 0 or len(board_move) > 2:
        mud.send_message(id, "\nThat's not a valid move.\n")
        return

    if len(board_move) == 1:
        # single move to place a counter
        index = 0
        for loc in VALID_MORRIS_BOARD_LOCATIONS:
            if loc == board_move[0]:
                if board[index] == '·':
                    if turn == 'white':
                        if white_counters > 0:
                            board = _morris_board_set(board, index, '●')
                            white_counters -= 1
                            game_state = items[game_item_id]['gameState']
                            game_state['morrisWhite'] = white_counters
                            game_state['morris'] = board
                            game_state['morrisTurn'] = 'black'
                        else:
                            mud.send_message(id, '\nAll your counters ' +
                                             'have been placed.\n')
                    else:
                        if black_counters > 0:
                            board = _morris_board_set(board, index, '○')
                            black_counters -= 1
                            game_state = items[game_item_id]['gameState']
                            game_state['morrisBlack'] = black_counters
                            game_state['morris'] = board
                            game_state['morrisTurn'] = 'white'
                        else:
                            mud.send_message(id, '\nAll your counters ' +
                                             'have been placed.\n')
                break
            index += 1
    else:
        if turn == 'white' and white_counters > 0:
            mud.send_message(id, '\nPlace your counters first before ' +
                             'moving any of them.\n')
            return
        elif turn == 'black' and black_counters > 0:
            mud.send_message(id, '\nPlace your counters first before ' +
                             'moving any of them.\n')
            return

        # move a counter from one place to another
        if board_move[0] == board_move[1]:
            mud.send_message(id, '\nSpecify coordinates to move ' +
                             'from and to.\n')
            return
        if board_move[0][0] != board_move[1][0] and \
           board_move[0][1] != board_move[1][1]:
            mud.send_message(id, '\nYou can only move vertically ' +
                             'or horizontally.\n')
            return
        from_index = 0
        for loc in VALID_MORRIS_BOARD_LOCATIONS:
            if loc == board_move[0]:
                if turn == 'white' and board[from_index] != '●':
                    mud.send_message(id, "\nThere isn't a counter at " +
                                     loc + '\n')
                    return
                if turn == 'black' and board[from_index] != '○':
                    mud.send_message(id, "\nThere isn't a counter at " +
                                     loc + '\n')
                    return
                break
            from_index += 1
        to_index = 0
        for loc in VALID_MORRIS_BOARD_LOCATIONS:
            if loc == board_move[1]:
                if board[to_index] != '':
                    mud.send_message(id, "\nThere is already a counter at " +
                                     loc + '\n')
                    return
                if turn == 'white':
                    board = _morris_board_set(board, to_index, '●')
                    items[game_item_id]['gameState']['morrisTurn'] = 'black'
                else:
                    board = _morris_board_set(board, to_index, '○')
                    items[game_item_id]['gameState']['morrisTurn'] = 'white'
                board = _morris_board_set(board, from_index, '·')
                items[game_item_id]['gameState']['morris'] = board
                break
            to_index += 1
    show_morris_board(board_name, players, id, mud, rooms, items, items_db)


def _morris_pieces(side: str, board: str) -> int:
    ctr = 0
    if side == 'white':
        for piece in board:
            if piece == '●':
                ctr += 1
    else:
        for piece in board:
            if piece == '○':
                ctr += 1
    return ctr


def reset_morris_board(players: {}, id: int, mud, rooms: {},
                       items: {}, items_db: {}) -> None:
    game_item_id = _morris_board_in_room(players, id, rooms, items, items_db)
    if not game_item_id:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return

    if not items[game_item_id].get('gameState'):
        items[game_item_id]['gameState'] = {}

    board_name = get_morris_board_name(players, id, rooms, items, items_db)

    board = '·' * 24
    items[game_item_id]['gameState']['morris'] = board
    items[game_item_id]['gameState']['morrisWhite'] = 9
    items[game_item_id]['gameState']['millsWhite'] = 0
    items[game_item_id]['gameState']['morrisBlack'] = 9
    items[game_item_id]['gameState']['millsBlack'] = 0
    items[game_item_id]['gameState']['morrisTurn'] = 'white'
    show_morris_board(board_name, players, id, mud, rooms, items, items_db)


def _board_location_indexes(board_name: str) -> {}:
    """Returns a dictionary containing board coordinates for each index
    """
    locations_filename = 'morrisboards/' + board_name + '/locations.txt'
    if not os.path.isfile(locations_filename):
        print('No morris locations file: ' + locations_filename)
        return None
    index = 0
    locations = {}
    # read the locations file
    with open(locations_filename, "r") as fp_loc:
        lines = fp_loc.readlines()
        for horizontal in lines:
            if ' ' not in horizontal:
                continue
            coords = horizontal.strip().split(' ')
            for locn in coords:
                if ',' not in locn:
                    continue
                x_co = locn.split(',')[0].strip()
                y_co = locn.split(',')[1].strip()
                if x_co.isdigit() and y_co.isdigit():
                    locations[index] = [int(x_co), int(y_co)]
                    index += 1
    if index != 24:
        print('Invalid morris locations file: ' + locations_filename)
        print('Indexes: ' + str(index))
        print('locations: ' + str(locations))
        return None
    return locations


def _show_morris_board_as_html(board_name: str,
                               players: {}, id: int, mud, rooms: {},
                               items: {}, items_db: {}) -> None:
    """Shows the board as html for the web interface
    """
    locations = _board_location_indexes(board_name)
    if not locations:
        mud.send_message(id, '\nSomething went wrong loading morris ' +
                         'board files.\n')
        return

    game_item_id = _morris_board_in_room(players, id, rooms, items, items_db)
    if not game_item_id:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return
    board_dir = 'morrisboards/' + board_name + '/'

    if not items[game_item_id].get('gameState'):
        items[game_item_id]['gameState'] = {}

    if items[game_item_id]['gameState'].get('morris'):
        board = items[game_item_id]['gameState']['morris']
    else:
        board = '·' * 24
        items[game_item_id]['gameState']['morris'] = board

    if not items[game_item_id]['gameState'].get('millsWhite'):
        items[game_item_id]['gameState']['millsWhite'] = 0
    if not items[game_item_id]['gameState'].get('millsBlack'):
        items[game_item_id]['gameState']['millsBlack'] = 0

    board_html = '<div class="parent">'
    board_html += \
        '<img class="morrisboard" src="' + board_dir + 'board.jpg" />'
    counter_width = 8
    counter_width_half = counter_width / 2
    for i in range(24):
        x_co = int(locations[i][0])
        y_co = int(locations[i][1])
        if board[i] == '○':
            board_html += \
                '<img src="' + board_dir + 'player1.png" ' \
                'style="position:absolute;' + \
                'width:' + str(counter_width) + '%;' + \
                'left:' + \
                str(int((x_co * 100 / 1024) - counter_width_half)) + '%;' + \
                'top:' + \
                str(int((y_co * 100 / 1024) - counter_width_half)) + '%;' + \
                '" />'
        elif board[i] == '●':
            board_html += \
                '<img src="' + board_dir + 'player2.png" ' \
                'style="position:absolute;' + \
                'width:' + str(counter_width) + '%;' + \
                'left:' + \
                str(int((x_co * 100 / 1024) - counter_width_half)) + '%;' + \
                'top:' + \
                str(int((y_co * 100 / 1024) - counter_width_half)) + '%;' + \
                '" />'
    board_html += '</div>\n'

    mud.send_game_board(id, board_html)

    white_counters = 9
    if items[game_item_id]['gameState'].get('morrisWhite'):
        white_counters = int(items[game_item_id]['gameState']['morrisWhite'])

    black_counters = 9
    if items[game_item_id]['gameState'].get('morrisBlack'):
        black_counters = int(items[game_item_id]['gameState']['morrisBlack'])

    if white_counters == 0 and black_counters == 0:
        if _morris_pieces('white', board) <= 2:
            mud.send_message(id, 'Black wins\n')
            return
        if _morris_pieces('black', board) <= 2:
            mud.send_message(id, 'White wins\n')
            return

    if _no_of_mills('black', board) > \
       items[game_item_id]['gameState']['millsBlack']:
        mud.send_message(id, 'Black has a mill. Take a white counter.\n')
        return
    if _no_of_mills('white', board) > \
       items[game_item_id]['gameState']['millsWhite']:
        mud.send_message(id, 'White has a mill. Take a black counter.\n')
        return

    if not items[game_item_id]['gameState'].get('morrisTurn'):
        items[game_item_id]['gameState']['morrisTurn'] = 'white'
    mud.send_message(id, items[game_item_id]['gameState']['morrisTurn'] +
                     "'s move\n")


def show_morris_board(board_name: str,
                      players: {}, id: int, mud, rooms: {},
                      items: {}, items_db: {}) -> None:
    """Draws the morris board
    """
    if mud.player_using_web_interface(id):
        _show_morris_board_as_html(board_name, players, id, mud, rooms,
                                   items, items_db)
        return
    game_item_id = _morris_board_in_room(players, id, rooms, items, items_db)
    if not game_item_id:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return

    if not items[game_item_id].get('gameState'):
        items[game_item_id]['gameState'] = {}

    if items[game_item_id]['gameState'].get('morris'):
        board = items[game_item_id]['gameState']['morris']
    else:
        board = '·' * 24
        items[game_item_id]['gameState']['morris'] = board

    if not items[game_item_id]['gameState'].get('millsWhite'):
        items[game_item_id]['gameState']['millsWhite'] = 0
    if not items[game_item_id]['gameState'].get('millsBlack'):
        items[game_item_id]['gameState']['millsBlack'] = 0

    board_str = '\n'
    board_str += ' 7 ' + board[21] + '─────' + board[22] + \
        '─────' + board[23] + '\n'
    board_str += ' 6 │ ' + board[18] + '───' + board[19] + \
        '───' + board[20] + ' │\n'
    board_str += ' 5 │ │ ' + board[15] + '─' + board[16] + \
        '─' + board[17] + ' │ │\n'
    board_str += ' 4 ' + board[9] + '-' + board[10] + '-' + \
        board[11] + '   ' + board[12] + '-' + board[13] + '-' + \
        board[14] + '\n'
    board_str += ' 3 │ │ ' + board[6] + '─' + board[7] + \
        '─' + board[8] + ' │ │\n'
    board_str += ' 2 │ ' + board[3] + '───' + board[4] + \
        '───' + board[5] + ' │\n'
    board_str += ' 1 ' + board[0] + '─────' + board[1] + \
        '─────' + board[2] + '\n'
    board_str += '   a b c d e f g\n'

    mud.send_game_board(id, board_str)

    white_counters = 9
    if items[game_item_id]['gameState'].get('morrisWhite'):
        white_counters = int(items[game_item_id]['gameState']['morrisWhite'])

    black_counters = 9
    if items[game_item_id]['gameState'].get('morrisBlack'):
        black_counters = int(items[game_item_id]['gameState']['morrisBlack'])

    if white_counters == 0 and black_counters == 0:
        if _morris_pieces('white', board) <= 2:
            mud.send_message(id, 'Black wins\n')
            return
        if _morris_pieces('black', board) <= 2:
            mud.send_message(id, 'White wins\n')
            return

    if _no_of_mills('black', board) > \
       items[game_item_id]['gameState']['millsBlack']:
        mud.send_message(id, 'Black has a mill. Take a white counter.\n')
        return
    if _no_of_mills('white', board) > \
       items[game_item_id]['gameState']['millsWhite']:
        mud.send_message(id, 'White has a mill. Take a black counter.\n')
        return

    if not items[game_item_id]['gameState'].get('morrisTurn'):
        items[game_item_id]['gameState']['morrisTurn'] = 'white'
    mud.send_message(id, items[game_item_id]['gameState']['morrisTurn'] +
                     "'s move\n")


def take_morris_counter(takeDescription: str,
                        players: {}, id, mud, rooms: {},
                        items: {}, items_db: {}) -> None:
    """Takes an opponent counter from the board
    """
    game_item_id = _morris_board_in_room(players, id, rooms, items, items_db)
    if not game_item_id:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return

    board_name = get_morris_board_name(players, id, rooms, items, items_db)

    if not items[game_item_id].get('gameState'):
        items[game_item_id]['gameState'] = {}

    if items[game_item_id]['gameState'].get('morris'):
        board = items[game_item_id]['gameState']['morris']
    else:
        board = '·' * 24
        items[game_item_id]['gameState']['morris'] = board

    takeDescription = \
        takeDescription.lower().replace('.', ' ').replace(',', ' ').strip()
    words = takeDescription.split()
    board_move = []
    for wrd in words:
        if len(wrd) == 2:
            if wrd[1].isdigit():
                if ord(wrd[0]) >= ord('a') and \
                   ord(wrd[0]) <= ord('g') and \
                   int(wrd[1]) >= 1 and \
                   int(wrd[1]) <= 7:
                    if wrd in VALID_MORRIS_BOARD_LOCATIONS:
                        board_move.append(wrd)
    if len(board_move) != 1:
        mud.send_message(id, '\nSpecify the coordinate of the ' +
                         'counter to be taken.\n')
        return

    if _no_of_mills('black', board) > \
       items[game_item_id]['gameState']['millsBlack']:
        index = 0
        for loc in VALID_MORRIS_BOARD_LOCATIONS:
            if loc == board_move[0]:
                if board[index] == '●':
                    items[game_item_id]['gameState']['millsBlack'] = \
                        _no_of_mills('black', board)
                    board = _morris_board_set(board, index, '·')
                    items[game_item_id]['gameState']['morris'] = board
                    show_morris_board(board_name,
                                      players, id, mud, rooms, items, items_db)
            index += 1
    elif (_no_of_mills('white', board) >
          items[game_item_id]['gameState']['millsWhite']):
        index = 0
        for loc in VALID_MORRIS_BOARD_LOCATIONS:
            if loc == board_move[0]:
                if board[index] == '○':
                    items[game_item_id]['gameState']['millsWhite'] = \
                        _no_of_mills('white', board)
                    board = _morris_board_set(board, index, '·')
                    items[game_item_id]['gameState']['morris'] = board
                    show_morris_board(board_name,
                                      players, id, mud, rooms, items, items_db)
            index += 1
