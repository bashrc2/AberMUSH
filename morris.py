__filename__ = "morris.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Tabletop Games"

import os

validMorrisBoardLocations = [
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


def _morrisBoardInRoom(players: {}, id, rooms: {}, items: {}, items_db: {}):
    """Returns the item ID if there is a Morris board in the room
    """
    rid = players[id]['room']
    for i in items:
        if items[i]['room'] != rid:
            continue
        if 'morris' in items_db[items[i]['id']]['game'].lower():
            return i
    return None


def _noOfMills(side: str, board: str) -> int:
    """Count the number of mills for the side
    """
    if side == 'white':
        piece = '●'
    else:
        piece = '○'
    millsCtr = 0
    # vertical
    if board[0] == piece and board[9] == piece and board[21] == piece:
        millsCtr += 1
    if board[3] == piece and board[10] == piece and board[18] == piece:
        millsCtr += 1
    if board[6] == piece and board[11] == piece and board[15] == piece:
        millsCtr += 1
    if board[1] == piece and board[4] == piece and board[7] == piece:
        millsCtr += 1
    if board[16] == piece and board[19] == piece and board[22] == piece:
        millsCtr += 1
    if board[8] == piece and board[12] == piece and board[17] == piece:
        millsCtr += 1
    if board[5] == piece and board[13] == piece and board[20] == piece:
        millsCtr += 1
    if board[2] == piece and board[14] == piece and board[23] == piece:
        millsCtr += 1
    # horizontal
    if board[0] == piece and board[1] == piece and board[2] == piece:
        millsCtr += 1
    if board[3] == piece and board[4] == piece and board[5] == piece:
        millsCtr += 1
    if board[6] == piece and board[7] == piece and board[8] == piece:
        millsCtr += 1
    if board[9] == piece and board[10] == piece and board[11] == piece:
        millsCtr += 1
    if board[12] == piece and board[13] == piece and board[14] == piece:
        millsCtr += 1
    if board[15] == piece and board[16] == piece and board[17] == piece:
        millsCtr += 1
    if board[18] == piece and board[19] == piece and board[20] == piece:
        millsCtr += 1
    if board[21] == piece and board[22] == piece and board[23] == piece:
        millsCtr += 1
    return millsCtr


def _morrisBoardSet(board: str, index: int, piece: str) -> str:
    return board[:index] + piece + board[(index + 1):]


def morris_move(moveDescription: str,
                players: {}, id, mud, rooms: {},
                items: {}, items_db: {}) -> None:
    gameItemID = _morrisBoardInRoom(players, id, rooms, items, items_db)
    if not gameItemID:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return

    if not items[gameItemID].get('gameState'):
        items[gameItemID]['gameState'] = {}

    turn = 'white'
    if items[gameItemID]['gameState'].get('morrisTurn'):
        turn = items[gameItemID]['gameState']['morrisTurn']
    else:
        items[gameItemID]['gameState']['morrisTurn'] = turn

    whiteCounters = 9
    if items[gameItemID]['gameState'].get('morrisWhite'):
        whiteCounters = int(items[gameItemID]['gameState']['morrisWhite'])

    blackCounters = 9
    if items[gameItemID]['gameState'].get('morrisBlack'):
        blackCounters = int(items[gameItemID]['gameState']['morrisBlack'])

    if not items[gameItemID]['gameState'].get('millsWhite'):
        items[gameItemID]['gameState']['millsWhite'] = 0
    if not items[gameItemID]['gameState'].get('millsBlack'):
        items[gameItemID]['gameState']['millsBlack'] = 0

    if items[gameItemID]['gameState'].get('morris'):
        board = items[gameItemID]['gameState']['morris']
    else:
        board = '·' * 24
        items[gameItemID]['gameState']['morris'] = board

    boardName = get_morris_board_name(players, id, rooms, items, items_db)

    # check for a win
    if whiteCounters == 0 and blackCounters == 0:
        if _morrisPieces('white', board) <= 2 or \
           _morrisPieces('black', board) <= 2:
            show_morris_board(boardName, players, id, mud, rooms,
                              items, items_db)
            return

    if _noOfMills('black', board) > \
       items[gameItemID]['gameState']['millsBlack']:
        show_morris_board(boardName, players, id, mud, rooms, items, items_db)
        return
    if _noOfMills('white', board) > \
       items[gameItemID]['gameState']['millsWhite']:
        show_morris_board(boardName, players, id, mud, rooms, items, items_db)
        return

    moveDescription = \
        moveDescription.lower().replace('.', ' ').replace(',', ' ').strip()
    words = moveDescription.split()
    boardMove = []
    for w in words:
        if len(w) == 2:
            if w[1].isdigit():
                if ord(w[0]) >= ord('a') and \
                   ord(w[0]) <= ord('g') and \
                   int(w[1]) >= 1 and \
                   int(w[1]) <= 7:
                    if w in validMorrisBoardLocations:
                        boardMove.append(w)
        if len(w) == 4:
            if w[1].isdigit() and w[3].isdigit():
                if ord(w[0]) >= ord('a') and \
                   ord(w[0]) <= ord('g') and \
                   int(w[1]) >= 1 and \
                   int(w[1]) <= 7 and \
                   ord(w[2]) >= ord('a') and \
                   ord(w[2]) <= ord('g') and \
                   int(w[3]) >= 1 and \
                   int(w[4]) <= 7:
                    if w[:2] in validMorrisBoardLocations and \
                       w[2:] in validMorrisBoardLocations:
                        boardMove.append(w[:2])
                        boardMove.append(w[2:])
    if len(boardMove) == 0 or len(boardMove) > 2:
        mud.send_message(id, "\nThat's not a valid move.\n")
        return

    if len(boardMove) == 1:
        # single move to place a counter
        index = 0
        for loc in validMorrisBoardLocations:
            if loc == boardMove[0]:
                if board[index] == '·':
                    if turn == 'white':
                        if whiteCounters > 0:
                            board = _morrisBoardSet(board, index, '●')
                            whiteCounters -= 1
                            gameState = items[gameItemID]['gameState']
                            gameState['morrisWhite'] = whiteCounters
                            gameState['morris'] = board
                            gameState['morrisTurn'] = 'black'
                        else:
                            mud.send_message(id, '\nAll your counters ' +
                                             'have been placed.\n')
                    else:
                        if blackCounters > 0:
                            board = _morrisBoardSet(board, index, '○')
                            blackCounters -= 1
                            gameState = items[gameItemID]['gameState']
                            gameState['morrisBlack'] = blackCounters
                            gameState['morris'] = board
                            gameState['morrisTurn'] = 'white'
                        else:
                            mud.send_message(id, '\nAll your counters ' +
                                             'have been placed.\n')
                break
            index += 1
    else:
        if turn == 'white' and whiteCounters > 0:
            mud.send_message(id, '\nPlace your counters first before ' +
                             'moving any of them.\n')
            return
        elif turn == 'black' and blackCounters > 0:
            mud.send_message(id, '\nPlace your counters first before ' +
                             'moving any of them.\n')
            return

        # move a counter from one place to another
        if boardMove[0] == boardMove[1]:
            mud.send_message(id, '\nSpecify coordinates to move ' +
                             'from and to.\n')
            return
        if boardMove[0][0] != boardMove[1][0] and \
           boardMove[0][1] != boardMove[1][1]:
            mud.send_message(id, '\nYou can only move vertically ' +
                             'or horizontally.\n')
            return
        fromIndex = 0
        for loc in validMorrisBoardLocations:
            if loc == boardMove[0]:
                if turn == 'white' and board[fromIndex] != '●':
                    mud.send_message(id, "\nThere isn't a counter at " +
                                     loc + '\n')
                    return
                if turn == 'black' and board[fromIndex] != '○':
                    mud.send_message(id, "\nThere isn't a counter at " +
                                     loc + '\n')
                    return
                break
            fromIndex += 1
        toIndex = 0
        for loc in validMorrisBoardLocations:
            if loc == boardMove[1]:
                if board[toIndex] != '':
                    mud.send_message(id, "\nThere is already a counter at " +
                                     loc + '\n')
                    return
                if turn == 'white':
                    board = _morrisBoardSet(board, toIndex, '●')
                    items[gameItemID]['gameState']['morrisTurn'] = 'black'
                else:
                    board = _morrisBoardSet(board, toIndex, '○')
                    items[gameItemID]['gameState']['morrisTurn'] = 'white'
                board = _morrisBoardSet(board, fromIndex, '·')
                items[gameItemID]['gameState']['morris'] = board
                break
            toIndex += 1
    show_morris_board(boardName, players, id, mud, rooms, items, items_db)


def _morrisPieces(side: str, board: str) -> int:
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
    gameItemID = _morrisBoardInRoom(players, id, rooms, items, items_db)
    if not gameItemID:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return

    if not items[gameItemID].get('gameState'):
        items[gameItemID]['gameState'] = {}

    boardName = get_morris_board_name(players, id, rooms, items, items_db)

    board = '·' * 24
    items[gameItemID]['gameState']['morris'] = board
    items[gameItemID]['gameState']['morrisWhite'] = 9
    items[gameItemID]['gameState']['millsWhite'] = 0
    items[gameItemID]['gameState']['morrisBlack'] = 9
    items[gameItemID]['gameState']['millsBlack'] = 0
    items[gameItemID]['gameState']['morrisTurn'] = 'white'
    show_morris_board(boardName, players, id, mud, rooms, items, items_db)


def _boardLocationIndexes(boardName: str) -> {}:
    """Returns a dictionary containing board coordinates for each index
    """
    locationsFilename = 'morrisboards/' + boardName + '/locations.txt'
    if not os.path.isfile(locationsFilename):
        print('No morris locations file: ' + locationsFilename)
        return None
    index = 0
    locations = {}
    # read the locations file
    with open(locationsFilename, "r") as f:
        lines = f.readlines()
        for horizontal in lines:
            if ' ' not in horizontal:
                continue
            coords = horizontal.strip().split(' ')
            for locn in coords:
                if ',' not in locn:
                    continue
                x = locn.split(',')[0].strip()
                y = locn.split(',')[1].strip()
                if x.isdigit() and y.isdigit():
                    locations[index] = [int(x), int(y)]
                    index += 1
    if index != 24:
        print('Invalid morris locations file: ' + locationsFilename)
        print('Indexes: ' + str(index))
        print('locations: ' + str(locations))
        return None
    return locations


def _show_morris_boardAsHtml(boardName: str,
                             players: {}, id: int, mud, rooms: {},
                             items: {}, items_db: {}) -> None:
    """Shows the board as html for the web interface
    """
    locations = _boardLocationIndexes(boardName)
    if not locations:
        mud.send_message(id, '\nSomething went wrong loading morris ' +
                         'board files.\n')
        return

    gameItemID = _morrisBoardInRoom(players, id, rooms, items, items_db)
    if not gameItemID:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return
    boardDir = 'morrisboards/' + boardName + '/'

    if not items[gameItemID].get('gameState'):
        items[gameItemID]['gameState'] = {}

    if items[gameItemID]['gameState'].get('morris'):
        board = items[gameItemID]['gameState']['morris']
    else:
        board = '·' * 24
        items[gameItemID]['gameState']['morris'] = board

    if not items[gameItemID]['gameState'].get('millsWhite'):
        items[gameItemID]['gameState']['millsWhite'] = 0
    if not items[gameItemID]['gameState'].get('millsBlack'):
        items[gameItemID]['gameState']['millsBlack'] = 0

    boardHtml = '<div class="parent">'
    boardHtml += \
        '<img class="morrisboard" src="' + boardDir + 'board.jpg" />'
    counterWidth = 8
    counterWidthHalf = counterWidth / 2
    for i in range(24):
        x = int(locations[i][0])
        y = int(locations[i][1])
        if board[i] == '○':
            boardHtml += \
                '<img src="' + boardDir + 'player1.png" ' \
                'style="position:absolute;' + \
                'width:' + str(counterWidth) + '%;' + \
                'left:' + \
                str(int((x * 100 / 1024) - counterWidthHalf)) + '%;' + \
                'top:' + \
                str(int((y * 100 / 1024) - counterWidthHalf)) + '%;' + \
                '" />'
        elif board[i] == '●':
            boardHtml += \
                '<img src="' + boardDir + 'player2.png" ' \
                'style="position:absolute;' + \
                'width:' + str(counterWidth) + '%;' + \
                'left:' + \
                str(int((x * 100 / 1024) - counterWidthHalf)) + '%;' + \
                'top:' + \
                str(int((y * 100 / 1024) - counterWidthHalf)) + '%;' + \
                '" />'
    boardHtml += '</div>\n'

    mud.send_game_board(id, boardHtml)

    whiteCounters = 9
    if items[gameItemID]['gameState'].get('morrisWhite'):
        whiteCounters = int(items[gameItemID]['gameState']['morrisWhite'])

    blackCounters = 9
    if items[gameItemID]['gameState'].get('morrisBlack'):
        blackCounters = int(items[gameItemID]['gameState']['morrisBlack'])

    if whiteCounters == 0 and blackCounters == 0:
        if _morrisPieces('white', board) <= 2:
            mud.send_message(id, 'Black wins\n')
            return
        elif _morrisPieces('black', board) <= 2:
            mud.send_message(id, 'White wins\n')
            return

    if _noOfMills('black', board) > \
       items[gameItemID]['gameState']['millsBlack']:
        mud.send_message(id, 'Black has a mill. Take a white counter.\n')
        return
    if _noOfMills('white', board) > \
       items[gameItemID]['gameState']['millsWhite']:
        mud.send_message(id, 'White has a mill. Take a black counter.\n')
        return

    if not items[gameItemID]['gameState'].get('morrisTurn'):
        items[gameItemID]['gameState']['morrisTurn'] = 'white'
    mud.send_message(id, items[gameItemID]['gameState']['morrisTurn'] +
                     "'s move\n")


def show_morris_board(boardName: str,
                      players: {}, id: int, mud, rooms: {},
                      items: {}, items_db: {}) -> None:
    """Draws the morris board
    """
    if mud.player_using_web_interface(id):
        _show_morris_boardAsHtml(boardName, players, id, mud, rooms,
                                 items, items_db)
        return
    gameItemID = _morrisBoardInRoom(players, id, rooms, items, items_db)
    if not gameItemID:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return

    if not items[gameItemID].get('gameState'):
        items[gameItemID]['gameState'] = {}

    if items[gameItemID]['gameState'].get('morris'):
        board = items[gameItemID]['gameState']['morris']
    else:
        board = '·' * 24
        items[gameItemID]['gameState']['morris'] = board

    if not items[gameItemID]['gameState'].get('millsWhite'):
        items[gameItemID]['gameState']['millsWhite'] = 0
    if not items[gameItemID]['gameState'].get('millsBlack'):
        items[gameItemID]['gameState']['millsBlack'] = 0

    boardStr = '\n'
    boardStr += ' 7 ' + board[21] + '─────' + board[22] + \
        '─────' + board[23] + '\n'
    boardStr += ' 6 │ ' + board[18] + '───' + board[19] + \
        '───' + board[20] + ' │\n'
    boardStr += ' 5 │ │ ' + board[15] + '─' + board[16] + \
        '─' + board[17] + ' │ │\n'
    boardStr += ' 4 ' + board[9] + '-' + board[10] + '-' + \
        board[11] + '   ' + board[12] + '-' + board[13] + '-' + \
        board[14] + '\n'
    boardStr += ' 3 │ │ ' + board[6] + '─' + board[7] + \
        '─' + board[8] + ' │ │\n'
    boardStr += ' 2 │ ' + board[3] + '───' + board[4] + \
        '───' + board[5] + ' │\n'
    boardStr += ' 1 ' + board[0] + '─────' + board[1] + \
        '─────' + board[2] + '\n'
    boardStr += '   a b c d e f g\n'

    mud.send_game_board(id, boardStr)

    whiteCounters = 9
    if items[gameItemID]['gameState'].get('morrisWhite'):
        whiteCounters = int(items[gameItemID]['gameState']['morrisWhite'])

    blackCounters = 9
    if items[gameItemID]['gameState'].get('morrisBlack'):
        blackCounters = int(items[gameItemID]['gameState']['morrisBlack'])

    if whiteCounters == 0 and blackCounters == 0:
        if _morrisPieces('white', board) <= 2:
            mud.send_message(id, 'Black wins\n')
            return
        elif _morrisPieces('black', board) <= 2:
            mud.send_message(id, 'White wins\n')
            return

    if _noOfMills('black', board) > \
       items[gameItemID]['gameState']['millsBlack']:
        mud.send_message(id, 'Black has a mill. Take a white counter.\n')
        return
    if _noOfMills('white', board) > \
       items[gameItemID]['gameState']['millsWhite']:
        mud.send_message(id, 'White has a mill. Take a black counter.\n')
        return

    if not items[gameItemID]['gameState'].get('morrisTurn'):
        items[gameItemID]['gameState']['morrisTurn'] = 'white'
    mud.send_message(id, items[gameItemID]['gameState']['morrisTurn'] +
                     "'s move\n")


def take_morris_counter(takeDescription: str,
                        players: {}, id, mud, rooms: {},
                        items: {}, items_db: {}) -> None:
    """Takes an opponent counter from the board
    """
    gameItemID = _morrisBoardInRoom(players, id, rooms, items, items_db)
    if not gameItemID:
        mud.send_message(id, '\nThere are no Morris board here.\n')
        return

    boardName = get_morris_board_name(players, id, rooms, items, items_db)

    if not items[gameItemID].get('gameState'):
        items[gameItemID]['gameState'] = {}

    if items[gameItemID]['gameState'].get('morris'):
        board = items[gameItemID]['gameState']['morris']
    else:
        board = '·' * 24
        items[gameItemID]['gameState']['morris'] = board

    takeDescription = \
        takeDescription.lower().replace('.', ' ').replace(',', ' ').strip()
    words = takeDescription.split()
    boardMove = []
    for w in words:
        if len(w) == 2:
            if w[1].isdigit():
                if ord(w[0]) >= ord('a') and \
                   ord(w[0]) <= ord('g') and \
                   int(w[1]) >= 1 and \
                   int(w[1]) <= 7:
                    if w in validMorrisBoardLocations:
                        boardMove.append(w)
    if len(boardMove) != 1:
        mud.send_message(id, '\nSpecify the coordinate of the ' +
                         'counter to be taken.\n')
        return

    if _noOfMills('black', board) > \
       items[gameItemID]['gameState']['millsBlack']:
        index = 0
        for loc in validMorrisBoardLocations:
            if loc == boardMove[0]:
                if board[index] == '●':
                    items[gameItemID]['gameState']['millsBlack'] = \
                        _noOfMills('black', board)
                    board = _morrisBoardSet(board, index, '·')
                    items[gameItemID]['gameState']['morris'] = board
                    show_morris_board(boardName,
                                      players, id, mud, rooms, items, items_db)
            index += 1
    elif (_noOfMills('white', board) >
          items[gameItemID]['gameState']['millsWhite']):
        index = 0
        for loc in validMorrisBoardLocations:
            if loc == boardMove[0]:
                if board[index] == '○':
                    items[gameItemID]['gameState']['millsWhite'] = \
                        _noOfMills('white', board)
                    board = _morrisBoardSet(board, index, '·')
                    items[gameItemID]['gameState']['morris'] = board
                    show_morris_board(boardName,
                                      players, id, mud, rooms, items, items_db)
            index += 1
