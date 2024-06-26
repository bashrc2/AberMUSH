__filename__ = "cards.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Tabletop Games"

# Some functions based on:
# https://rosettacode.org/wiki/Poker_hand_analyser#Python

import os
from collections import namedtuple
from itertools import product
from random import randrange

SUIT = '♥ ♦ ♣ ♠'.split()

# ordered strings of faces
FACES = '2 3 4 5 6 7 8 9 10 j q k a'
LOWACES = 'a 2 3 4 5 6 7 8 9 10 j q k'

# faces as lists
face = FACES.split()
lowace = LOWACES.split()


class Card(namedtuple('Card', 'face, suit')):
    """Types of cards
    """
    def __repr__(self):
        return ''.join(self)


class Deck():
    """Deck object
    """
    def __init__(self):
        self.__deck = [Card(f, s) for f, s in product(face, SUIT)]

    def __repr__(self):
        return ' '.join(repr(card) for card in self.__deck)

    def shuffle(self):
        """Shuffle the deck
        """
        pass

    def deal(self):
        """Deal cards
        """
        return self.__deck.pop(randrange(len(self.__deck)))


def straightflush(hand: str) -> bool:
    """Is the given hand a straight flush?
    """
    fac, ffs = ((lowace, LOWACES) if any(card.face == '2' for card in hand)
                else (face, FACES))
    ordered = sorted(hand, key=lambda card: (fac.index(card.face), card.suit))
    first, rest = ordered[0], ordered[1:]
    if all(card.suit == first.suit for card in rest) and \
       ' '.join(card.face for card in ordered) in ffs:
        return 'a straight flush', ordered[-1].face
    return False


def fourofakind(hand: str) -> bool:
    """Is the given hand four of a kind?
    """
    allfaces = [f for f, s in hand]
    allftypes = set(allfaces)
    if len(allftypes) != 2:
        return False
    for fac in allftypes:
        if allfaces.count(fac) == 4:
            allftypes.remove(fac)
            return 'four of a kind', [fac, allftypes.pop()]
    return False


def fullhouse(hand: str) -> bool:
    """Is the given hand a full house?
    """
    allfaces = [f for f, s in hand]
    allftypes = set(allfaces)
    if len(allftypes) != 2:
        return False
    for fac in allftypes:
        if allfaces.count(fac) == 3:
            allftypes.remove(fac)
            return 'a full house', [fac, allftypes.pop()]
    return False


def flush(hand: str) -> bool:
    """Is the given hand a flush?
    """
    allstypes = {s for f, s in hand}
    if len(allstypes) == 1:
        allfaces = [f for f, s in hand]
        return 'a flush', sorted(allfaces,
                                 key=lambda f: face.index(f),
                                 reverse=True)
    return False


def straight(hand: str) -> bool:
    """Is the given hand a straight?
    """
    fac, ffs = ((lowace, LOWACES) if any(card.face == '2' for card in hand)
                else (face, FACES))
    ordered = sorted(hand, key=lambda card: (fac.index(card.face), card.suit))
    if ' '.join(card.face for card in ordered) in ffs:
        return 'a straight', ordered[-1].face
    return False


def threeofakind(hand: str) -> bool:
    """Is the given hand three of a kind?
    """
    allfaces = [f for f, s in hand]
    allftypes = set(allfaces)
    if len(allftypes) <= 2:
        return False
    for fac in allftypes:
        if allfaces.count(fac) == 3:
            allftypes.remove(fac)
            return ('three of a kind',
                    [fac] + sorted(allftypes,
                                   key=lambda f: face.index(f),
                                   reverse=True))
    return False


def twopair(hand: str) -> bool:
    """Is the given hand two pairs?
    """
    allfaces = [f for f, s in hand]
    allftypes = set(allfaces)
    pairs = [f for f in allftypes if allfaces.count(f) == 2]
    if len(pairs) != 2:
        return False
    pp0, pp1 = pairs
    other = [(allftypes - set(pairs)).pop()]
    return 'two pairs', pairs + other \
        if face.index(pp0) > face.index(pp1) else pairs[::-1] + other


def onepair(hand: str) -> bool:
    """Is the given hand one pair?
    """
    allfaces = [f for f, s in hand]
    allftypes = set(allfaces)
    pairs = [f for f in allftypes if allfaces.count(f) == 2]
    if len(pairs) != 1:
        return False
    allftypes.remove(pairs[0])
    return 'one pair', pairs + sorted(allftypes,
                                      key=lambda f: face.index(f),
                                      reverse=True)


def highcard(hand: str):
    """Does the given hand have a high card?
    """
    allfaces = [f for f, s in hand]
    return 'a high-card', sorted(allfaces,
                                 key=lambda f: face.index(f),
                                 reverse=True)


def _handy(cards: str):
    """Returns the hand
    """
    hand = []
    for card in cards.split():
        fac, sut = card[:-1], card[-1]
        if fac not in face:
            return None
        if sut not in SUIT:
            return None
        hand.append(Card(fac, sut))
    if len(hand) != 5:
        return None
    if len(set(hand)) != 5:
        return None
    return hand


def _card_rank(cards: str) -> []:
    """Returns the rank
    """
    hand = _handy(cards)
    if not hand:
        return None
    rank = None
    handrankorder = (
        straightflush, fourofakind, fullhouse,
        flush, straight, threeofakind,
        twopair, onepair, highcard
    )
    for ranker in handrankorder:
        rank = ranker(hand)
        if rank:
            break
    return rank


def _parse_card(card_description: str) -> str:
    """Takes a card description, such as "the ace of spades"
    and turns it into "a♠"
    """
    suit_name = {
        "sword": "♥",
        "collar": "♥",
        "heart": "♥",
        "diamond": "♦",
        "horn": "♦",
        "coin": "♦",
        "club": "♣",
        "loop": "♣",
        "leashe": "♠",
        "cup": "♠",
        "spade": "♠"
    }
    detected_suit = ''
    detected_face = ''
    card_description = card_description.lower().replace('the ', '')
    card_description = card_description.replace(' of ', ' ').replace('.', '')
    card_description = card_description.replace(',', '')
    for name, symbol in suit_name.items():
        if name + 's' in card_description:
            detected_suit = symbol
        elif name in card_description:
            detected_suit = symbol
    if not detected_suit:
        return None
    face_names = {
        "2": "2",
        "two": "2",
        "3": "3",
        "three": "3",
        "4": "4",
        "four": "4",
        "5": "5",
        "five": "5",
        "6": "6",
        "six": "6",
        "7": "7",
        "seven": "7",
        "8": "8",
        "eight": "8",
        "9": "9",
        "nine": "9",
        "10": "10",
        "ten": "10",
        "jack": "j",
        "knave": "j",
        "queen": "q",
        "king": "k",
        "ace": "a"
    }
    for name, symbol in face_names.items():
        if name in card_description:
            detected_face = symbol
    if not detected_face:
        for i in range(10, 2, -1):
            if str(i) in card_description:
                detected_face = str(i)
        return None
    return detected_face + detected_suit


def _deal_cards_to_player(players: {}, dealer_id: int, name: str,
                          no_of_cards: int,
                          deck, mud, hands, rooms: {}, items: {},
                          items_db: {}) -> bool:
    """Deals a number of cards to a player
    """
    card_player_id = None
    name = name.lower()
    for plyr_id, plyr in players.items():
        if plyr['room'] == players[dealer_id]['room']:
            if plyr['name'].lower() == name:
                card_player_id = plyr_id
                break
    if card_player_id is None:
        if 'myself' in name or ' me' in name or ' self' in name:
            card_player_id = dealer_id
        else:
            mud.send_message(dealer_id, "\nThey're not in the room.\n")
            return False
    card_player_name = players[card_player_id]['name']
    hands[card_player_name] = ''
    ctr = 0
    for _ in range(no_of_cards):
        top_card = deck.deal()
        if top_card:
            if ctr == 0:
                hands[card_player_name] += str(top_card)
            else:
                hands[card_player_name] += ' ' + str(top_card)
            ctr += 1
    if ctr > 0:
        hands[card_player_name] = hands[card_player_name]
        if dealer_id == card_player_id:
            mud.send_message(dealer_id, '\nYou deal ' + str(ctr) +
                             ' cards to yourself.\n')
        else:
            mud.send_message(dealer_id,
                             '\nYou deal ' + str(ctr) +
                             ' cards to ' + card_player_name + '.\n')
            mud.send_message(card_player_id,
                             '\n' + players[dealer_id]['name'] + ' deals ' +
                             str(ctr) + ' cards to you.\n')
        return True
    return False


def _card_game_in_room(players: {}, id: int, rooms: {}, items: {},
                       items_db: {}) -> int:
    """Returns the item ID if there is a card game in the room
    """
    rid = players[id]['room']
    for item_id, itemobj in items.items():
        if itemobj['room'] != rid:
            continue
        if 'cards' in items_db[itemobj['id']]['game'].lower():
            return item_id
    return None


def _card_game_pack(players: {}, pid: int, rooms: {},
                    items: {}, items_db: {}) -> str:
    """Returns the card pack name to use
    """
    rid = players[pid]['room']
    for _, itemobj in items.items():
        if itemobj['room'] != rid:
            continue
        if 'cards' in items_db[itemobj['id']]['game'].lower():
            if items_db[itemobj['id']].get('cardPack'):
                return items_db[itemobj['id']]['cardPack']
    return None


def _get_number_from_text(text: str) -> int:
    """If there is a number in the given text then return it
    """
    for i in range(10, 2, -1):
        if str(i) in text:
            return i
    num_str = {
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10
    }
    for name, num in num_str.items():
        if name in text:
            return num
    return None


def deal_to_players(players: {}, dealer_id: int, description: str,
                    mud, rooms: {}, items: {}, items_db: {}) -> None:
    """Deal cards to players
    """
    game_item_id = \
        _card_game_in_room(players, dealer_id, rooms, items, items_db)
    if not game_item_id:
        mud.send_message(dealer_id,
                         '\nThere are no playing cards here.\n')
        return

    no_of_cards = _get_number_from_text(description)
    if no_of_cards is None:
        no_of_cards = 5

    description = description.lower().replace('.', ' ').replace(',', ' ') + ' '
    description = description.replace('myself', players[dealer_id]['name'])
    description = description.replace(' me ', ' ' +
                                      players[dealer_id]['name'] + ' ')
    description = description.replace(' self ', ' ' +
                                      players[dealer_id]['name'] + ' ')

    player_count = 0
    for _, plyr in players.items():
        if plyr['room'] != players[dealer_id]['room']:
            continue
        if plyr['name'].lower() not in description:
            continue
        player_count += 1

    if player_count == 0:
        mud.send_message(dealer_id, '\nName some players to deal to.\n')
        return

    # initialise the deck
    deck = Deck()

    # create game state
    if not items[game_item_id].get('gameState'):
        items[game_item_id]['gameState'] = {}

    hands = {}
    for pid, plyr in players.items():
        if plyr['room'] != players[dealer_id]['room']:
            continue
        if plyr['name'].lower() not in description:
            continue
        if _deal_cards_to_player(players, dealer_id, plyr['name'],
                                 no_of_cards, deck, mud, hands,
                                 rooms, items, items_db):
            items[game_item_id]['gameState']['hands'] = hands
            items[game_item_id]['gameState']['table'] = {}
            items[game_item_id]['gameState']['deck'] = str(deck)
            hand_of_cards_show(players, pid, mud, rooms, items, items_db)

    # no cards played
    items[game_item_id]['gameState']['hands'] = hands
    items[game_item_id]['gameState']['called'] = 0
    items[game_item_id]['gameState']['deck'] = str(deck)


def _get_card_description(pack: str, rank: str, suit: str) -> str:
    """Given rank as a single character and suit
    returns a description of the card
    This is used for non-graphical output
    """
    rank_str = str(rank).upper()
    if rank_str.startswith('K'):
        rank_str = 'King'
    elif rank_str.startswith('Q'):
        if pack == 'set1':
            rank_str = 'Knight'
        else:
            rank_str = 'Queen'
    elif rank_str.startswith('A'):
        rank_str = 'Ace'
    elif rank_str.startswith('J'):
        rank_str = 'Jack'
    elif rank_str.startswith('2'):
        rank_str = 'Two'
    elif rank_str.startswith('3'):
        rank_str = 'Three'
    elif rank_str.startswith('4'):
        rank_str = 'Four'
    elif rank_str.startswith('5'):
        rank_str = 'Five'
    elif rank_str.startswith('6'):
        rank_str = 'Six'
    elif rank_str.startswith('7'):
        rank_str = 'Seven'
    elif rank_str.startswith('8'):
        rank_str = 'Eight'
    elif rank_str.startswith('9'):
        rank_str = 'Nine'
    elif rank_str.startswith('10'):
        rank_str = 'Ten'

    if suit == '♥':
        if pack == 'cloisters':
            return str(rank_str) + ' of collars\n'
        if pack == 'set1':
            return str(rank_str) + ' of swords\n'
        return str(rank_str) + ' of hearts\n'
    if suit == '♦':
        if pack == 'cloisters':
            return str(rank_str) + ' of horns\n'
        if pack == 'set1':
            return str(rank_str) + ' of coins\n'
        return str(rank_str) + ' of diamonds\n'
    if suit == '♣':
        if pack == 'cloisters':
            return str(rank_str) + ' of loops\n'
        return str(rank_str) + ' of clubs\n'
    if pack == 'cloisters':
        return str(rank_str) + ' of leashes\n'
    if pack == 'set1':
        return str(rank_str) + ' of cups\n'
    return str(rank_str) + ' of spades\n'


def hand_of_cards_show(players: {}, id: int, mud, rooms: {},
                       items: {}, items_db: {}) -> None:
    """Shows the cards for the given player
    """
    game_item_id = _card_game_in_room(players, id, rooms, items, items_db)
    if not game_item_id:
        mud.send_message(id, '\nThere are no playing cards here.\n')
        return

    # get the pack to be shown within the web interface
    pack = _card_game_pack(players, id, rooms, items, items_db)
    if not pack:
        pack = 'standard'

    player_name = players[id]['name']
    if not items[game_item_id].get('gameState'):
        mud.send_message(id, '\nNo cards have been dealt.\n')
        return

    if not items[game_item_id]['gameState'].get('hands'):
        mud.send_message(id, '\nNo hands have been dealt.\n')
        return

    if not items[game_item_id]['gameState']['hands'].get(player_name):
        mud.send_message(id, '\nNo hands have been dealt to ' +
                         player_name + '.\n')
        return

    hand_str = items[game_item_id]['gameState']['hands'][player_name]
    hand = hand_str.split()
    lines = [[] for i in range(9)]
    card_descriptions = ''
    html_str = '<table id="cards"><tr>'

    for card_str in hand:
        if len(card_str) < 2:
            continue
        rank_color = "\u001b[38;5;0m"
        if card_str[1] != '0':
            rank = card_str[0].upper()
            suit = card_str[1]
        else:
            rank = card_str[0] + card_str[1]
            suit = card_str[2]
        suit_color = "\u001b[38;5;0m"

        desc = _get_card_description(pack, rank, suit)
        card_descriptions += desc.strip()

        # create html for the web interface
        html_str += '<td>'
        html_str += '<img class="playingcard" ' + \
            'src="cardpacks/' + pack.lower() + '/' + \
            desc.replace(' ', '_').lower() + '.jpg" />'
        html_str += '</td>'

        card_background_color_start = \
            '\u001b[0m\u001b[0m\u001b[38;5;0m\u001b[48;5;15m'
        card_background_color_end = '\u001b[38;5;7m\u001b[49m'
        card_color = "\u001b[38;5;0m"
        if suit in ('♥', '♦'):
            suit_color = \
                "\u001b[0m\u001b[0m\u001b[38;5;1m\u001b[48;5;15m"
            rank_color = suit_color
            card_color = "\u001b[38;5;7m\u001b[49m" + \
                card_background_color_start
        if rank == '10':
            space = ''
        else:
            space = ' '

        for line_ctr in range(9):
            lines[line_ctr].append(' ')

        # try to load a utf8 art card from file
        utf8_pack = 'classic'
        if pack not in ('cloisters', 'set1'):
            utf8_pack = pack
        utf8_desc = _get_card_description(utf8_pack, rank, suit)
        utf8_card_filename = \
            'cardpacks_utf8/' + utf8_pack + '/' + \
            utf8_desc.replace('\n', '').replace(' ', '_').lower() + '.utf8ans'
        loaded_card = False
        if os.path.isfile(utf8_card_filename):
            try:
                with open(utf8_card_filename, 'r',
                          encoding='utf-8') as fp_card:
                    card_lines = fp_card.readlines()
                    if card_lines:
                        if len(card_lines) >= 9:
                            loaded_card = True
                            for line_ctr in range(9):
                                card_lines[line_ctr] = \
                                    card_lines[line_ctr].replace('\n', '')
                                lines[line_ctr].append(' ' +
                                                       card_lines[line_ctr])
                        else:
                            print('playing card too short: ' +
                                  utf8_card_filename)
            except OSError:
                print('EX: hand_of_cards_show ' + utf8_card_filename)
        else:
            print('card file not found: ' + utf8_card_filename)
        if not loaded_card:
            for line_ctr in range(9):
                lines[line_ctr].append(card_background_color_start)

            lines[0].append('┌─────────┐')
            lines[1].append('│{}{}{}{}       │'.format(rank_color, rank,
                                                       card_color, space))
            lines[2].append('│         │')
            lines[3].append('│         │')
            lines[4].append('│    {}{}{}    │'.format(suit_color, suit,
                                                      card_color))
            lines[5].append('│         │')
            lines[6].append('│         │')
            lines[7].append('│       {}{}{}{}│'.format(space, rank_color,
                                                       rank, card_color))
            lines[8].append('└─────────┘')

            for line_ctr in range(9):
                lines[line_ctr].append(card_background_color_end)

    html_str += '</tr></table>'
    card_color = "\u001b[38;5;0m"
    board_str = card_color + '\n'

    graphical_cards = True
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            graphical_cards = False
    if graphical_cards:
        if mud.player_using_web_interface(id):
            board_str = html_str
        else:
            for line_row_str in lines:
                line_str = ''
                for sline in line_row_str:
                    line_str = line_str + sline
                board_str += line_str + '\n'
    else:
        board_str += card_descriptions

    mud.send_game_board(id, board_str)
    ranked_str = _card_rank(hand_str)
    if ranked_str:
        mud.send_message(id, 'You have ' + str(ranked_str[0]) + '.\n\n')

    if not items[game_item_id]['gameState'].get('called'):
        return
    if not items[game_item_id]['gameState']['called'] == 0:
        return

    # show your hand to other players
    for plyr_id, plyr in players.items():
        if plyr['room'] != players[id]['room']:
            continue
        if id == plyr_id:
            continue
        if items[game_item_id]['gameState']['hands'].get(plyr['name']):
            mud.send_message(plyr_id, '\n' + players[id]['name'] +
                             ' shows their hand.\n' + board_str)
            if ranked_str:
                mud.send_message(plyr_id, players[id]['name'] + ' has ' +
                                 str(ranked_str[0]) + '.\n\n')


def swap_card(card_description: str, players: {}, id: int, mud, rooms: {},
              items: {}, items_db: {}) -> None:
    game_item_id = _card_game_in_room(players, id, rooms, items, items_db)
    if not game_item_id:
        mud.send_message(id, '\nThere are no playing cards here.\n')
        return

    card_str = _parse_card(card_description)
    if not card_str:
        mud.send_message(id, "\nThat's not a card.\n")
        return

    player_name = players[id]['name']
    if not items[game_item_id].get('gameState'):
        mud.send_message(id, '\nNo cards have been dealt.\n')
        return

    if items[game_item_id]['gameState'].get('called'):
        if items[game_item_id]['gameState']['called'] != 0:
            mud.send_message(id, '\nThis round is over. Deal again.\n')
            return

    if not items[game_item_id]['gameState'].get('hands'):
        mud.send_message(id, '\nNo hands have been dealt.\n')
        return

    if not items[game_item_id]['gameState']['hands'].get(player_name):
        mud.send_message(id, '\nNo hands have been dealt to you.\n')
        return

    hand_str = items[game_item_id]['gameState']['hands'][player_name]
    if card_str not in hand_str:
        mud.send_message(id, '\n' + card_str.upper() +
                         ' is not in your hand.\n')
        return

    deck = items[game_item_id]['gameState']['deck'].split()
    if len(deck) == 0:
        mud.send_message(id, '\nNo more cards in the deck.\n')
        return
    next_card = deck.pop(randrange(len(deck)))
    items[game_item_id]['gameState']['deck'] = ""
    for deck_card_str in deck:
        if items[game_item_id]['gameState']['deck'] != "":
            items[game_item_id]['gameState']['deck'] += ' ' + deck_card_str
        else:
            items[game_item_id]['gameState']['deck'] += deck_card_str

    items[game_item_id]['gameState']['hands'][player_name] = \
        hand_str.replace(card_str, next_card)

    # tell other players that a card was swapped
    for plyr_id, plyr in players.items():
        if plyr['room'] != players[id]['room']:
            continue
        if plyr_id == id:
            continue
        other_player_name = plyr['name']
        if items[game_item_id]['gameState']['hands'].get(other_player_name):
            mud.send_message(plyr_id, '\n' + player_name + ' swaps a card.\n')
    mud.send_message(id, '\nYou swap a card.\n')
    hand_of_cards_show(players, id, mud, rooms, items, items_db)


def shuffle_cards(players: {}, pid, mud, rooms: {},
                  items: {}, items_db: {}) -> None:
    game_item_id = _card_game_in_room(players, id, rooms, items, items_db)
    if not game_item_id:
        mud.send_message(pid, '\nThere are no playing cards here.\n')
        return

    mud.send_message(pid, '\nYou shuffle the cards.\n')

    for plyr_id, plyr in players.items():
        if plyr['room'] != players[pid]['room']:
            continue
        if plyr_id == pid:
            continue
        mud.send_message(plyr_id,
                         '\n' + players[pid]['name'] + ' shuffles cards.\n')


def call_cards(players: {}, pid: int, mud, rooms: {},
               items: {}, items_db: {}) -> None:
    game_item_id = _card_game_in_room(players, pid, rooms, items, items_db)
    if not game_item_id:
        mud.send_message(pid, '\nThere are no playing cards here.\n')
        return

    player_name = players[pid]['name']
    if not items[game_item_id].get('gameState'):
        mud.send_message(pid, '\nNo cards have been dealt.\n')
        return

    if not items[game_item_id]['gameState'].get('hands'):
        mud.send_message(pid, '\nNo hands have been dealt.\n')
        return

    mud.send_message(pid, '\nYou call.\n')
    items[game_item_id]['gameState']['called'] = 1
    for plyr_id, plyr in players.items():
        if plyr['room'] != players[pid]['room']:
            continue
        if plyr_id == pid:
            continue
        pname = plyr['name']
        if items[game_item_id]['gameState']['hands'].get(pname):
            mud.send_message(plyr_id, '\n' + player_name + ' calls.\n')

    result_str = ''
    for _, plyr in players.items():
        if plyr['room'] != players[pid]['room']:
            continue
        pname = plyr['name']
        if items[game_item_id]['gameState']['hands'].get(pname):
            hand_str = \
                items[game_item_id]['gameState']['hands'][pname]
            ranked_str = _card_rank(hand_str)
            if ranked_str:
                result_str += '<f0><f32>' + plyr['name'] + \
                    '<r> has ' + str(ranked_str[0]) + '.\n'
            else:
                result_str += '<f0><f32>' + plyr['name'] + \
                    '<r> has nothing.\n'

    if len(result_str) == 0:
        mud.send_message(pid, '\nNo hands have been dealt.\n')
        return

    for plyr_id, plyr in players.items():
        if plyr['room'] != players[pid]['room']:
            continue
        pname = plyr['name']
        if items[game_item_id]['gameState']['hands'].get(pname):
            mud.send_message(plyr_id, '\n' + result_str)
