__filename__ = "cards.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

# Some functions based on:
# https://rosettacode.org/wiki/Poker_hand_analyser#Python

from collections import namedtuple
from itertools import product
from random import randrange

suit = '♥ ♦ ♣ ♠'.split()
# ordered strings of faces
faces = '2 3 4 5 6 7 8 9 10 j q k a'
lowaces = 'a 2 3 4 5 6 7 8 9 10 j q k'
# faces as lists
face = faces.split()
lowace = lowaces.split()


class Card(namedtuple('Card', 'face, suit')):
    def __repr__(self):
        return ''.join(self)


class Deck():
    def __init__(self):
        self.__deck = [Card(f, s) for f, s in product(face, suit)]

    def __repr__(self):
        return ' '.join(repr(card) for card in self.__deck)

    def shuffle(self):
        pass

    def deal(self):
        return self.__deck.pop(randrange(len(self.__deck)))


def straightflush(hand: str) -> bool:
    f, fs = ((lowace, lowaces) if any(card.face == '2' for card in hand)
             else (face, faces))
    ordered = sorted(hand, key=lambda card: (f.index(card.face), card.suit))
    first, rest = ordered[0], ordered[1:]
    if all(card.suit == first.suit for card in rest) and \
       ' '.join(card.face for card in ordered) in fs:
        return 'a straight flush', ordered[-1].face
    return False


def fourofakind(hand: str) -> bool:
    allfaces = [f for f, s in hand]
    allftypes = set(allfaces)
    if len(allftypes) != 2:
        return False
    for f in allftypes:
        if allfaces.count(f) == 4:
            allftypes.remove(f)
            return 'four of a kind', [f, allftypes.pop()]
    else:
        return False


def fullhouse(hand: str) -> bool:
    allfaces = [f for f, s in hand]
    allftypes = set(allfaces)
    if len(allftypes) != 2:
        return False
    for f in allftypes:
        if allfaces.count(f) == 3:
            allftypes.remove(f)
            return 'a full house', [f, allftypes.pop()]
    else:
        return False


def flush(hand: str) -> bool:
    allstypes = {s for f, s in hand}
    if len(allstypes) == 1:
        allfaces = [f for f, s in hand]
        return 'a flush', sorted(allfaces,
                                 key=lambda f: face.index(f),
                                 reverse=True)
    return False


def straight(hand: str) -> bool:
    f, fs = ((lowace, lowaces) if any(card.face == '2' for card in hand)
             else (face, faces))
    ordered = sorted(hand, key=lambda card: (f.index(card.face), card.suit))
    if ' '.join(card.face for card in ordered) in fs:
        return 'a straight', ordered[-1].face
    return False


def threeofakind(hand: str) -> bool:
    allfaces = [f for f, s in hand]
    allftypes = set(allfaces)
    if len(allftypes) <= 2:
        return False
    for f in allftypes:
        if allfaces.count(f) == 3:
            allftypes.remove(f)
            return ('three of a kind',
                    [f] + sorted(allftypes,
                                 key=lambda f: face.index(f),
                                 reverse=True))
    else:
        return False


def twopair(hand: str) -> bool:
    allfaces = [f for f, s in hand]
    allftypes = set(allfaces)
    pairs = [f for f in allftypes if allfaces.count(f) == 2]
    if len(pairs) != 2:
        return False
    p0, p1 = pairs
    other = [(allftypes - set(pairs)).pop()]
    return 'two pairs', pairs + other \
        if face.index(p0) > face.index(p1) else pairs[::-1] + other


def onepair(hand: str) -> bool:
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
    allfaces = [f for f, s in hand]
    return 'a high-card', sorted(allfaces,
                                 key=lambda f: face.index(f),
                                 reverse=True)


def handy(cards: str):
    hand = []
    for card in cards.split():
        f, s = card[:-1], card[-1]
        if f not in face:
            return None
        if s not in suit:
            return None
        hand.append(Card(f, s))
    if len(hand) != 5:
        return None
    if len(set(hand)) != 5:
        return None
    return hand


def cardRank(cards: str) -> []:
    hand = handy(cards)
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


def parseCard(cardDescription: str) -> str:
    """Takes a card description, such as "the ace of spades"
    and turns it into "a♠"
    """
    suitName = {
        "heart": "♥",
        "diamond": "♦",
        "club": "♣",
        "spade": "♠"
    }
    detectedSuit = ''
    detectedFace = ''
    cardDescription = cardDescription.lower().replace('the ', '')
    cardDescription = cardDescription.replace(' of ', ' ').replace('.', '')
    cardDescription = cardDescription.replace(',', '')
    for name, symbol in suitName.items():
        if name + 's' in cardDescription:
            detectedSuit = symbol
        elif name in cardDescription:
            detectedSuit = symbol
    if not detectedSuit:
        return None
    faceNames = {
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
        "jack": "j",
        "queen": "q",
        "king": "k",
        "ace": "a"
    }
    for name, symbol in faceNames.items():
        if name in cardDescription:
            detectedFace = symbol
    if not detectedFace:
        for i in range(10, 2, -1):
            if str(i) in cardDescription:
                detectedFace = str(i)
        return None
    return detectedFace+detectedSuit


def dealCardsToPlayer(players: {}, dealerId, name: str, noOfCards: int, deck,
                      mud, hands, rooms: {}, items: {}, itemsDB: {}) -> bool:
    """Deals a number of cards to a player
    """
    cardPlayerId = None
    name = name.lower()
    for p in players:
        if players[p]['room'] == players[dealerId]['room']:
            if players[p]['name'].lower() == name:
                cardPlayerId = p
                break
    if cardPlayerId is None:
        if 'myself' in name or ' me' in name or ' self' in name:
            cardPlayerId = dealerId
        else:
            mud.sendMessage(dealerId, "\nThey're not in the room.\n")
            return False
    cardPlayerName = players[cardPlayerId]['name']
    hands[cardPlayerName] = ''
    ctr = 0
    for i in range(noOfCards):
        topCard = deck.deal()
        if topCard:
            if ctr == 0:
                hands[cardPlayerName] += str(topCard)
            else:
                hands[cardPlayerName] += ' ' + str(topCard)
            ctr += 1
    if ctr > 0:
        hands[cardPlayerName] = hands[cardPlayerName]
        if dealerId == cardPlayerId:
            mud.sendMessage(dealerId, '\nYou deal ' + str(ctr) +
                            ' cards to yourself.\n')
        else:
            mud.sendMessage(dealerId,
                            '\nYou deal ' + str(ctr) +
                            ' cards to '+cardPlayerName+'.\n')
            mud.sendMessage(cardPlayerId,
                            '\n' + players[dealerId]['name'] + ' deals ' +
                            str(ctr) + ' cards to you.\n')
        return True
    return False


def cardGameInRoom(players: {}, id, rooms: {}, items: {}, itemsDB: {}):
    """Returns the item ID if there is a card game in the room
    """
    rid = players[id]['room']
    for i in items:
        if items[i]['room'] != rid:
            continue
        if 'cards' in itemsDB[items[i]['id']]['game'].lower():
            return i
    return None


def getNumberFromText(text: str) -> int:
    """If there is a number in the given text then return it
    """
    for i in range(10, 2, -1):
        if str(i) in text:
            return i
    numStr = {
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
    for name, num in numStr.items():
        if name in text:
            return num
    return None


def dealToPlayers(players: {}, dealerId, description: str,
                  mud, rooms: {}, items: {}, itemsDB: {}) -> None:
    """Deal cards to players
    """
    gameItemID = cardGameInRoom(players, dealerId, rooms, items, itemsDB)
    if not gameItemID:
        mud.sendMessage(dealerId,
                        '\nThere are no playing cards here.\n')
        return

    noOfCards = getNumberFromText(description)
    if noOfCards is None:
        noOfCards = 5

    description = description.lower().replace('.', ' ').replace(',', ' ') + ' '
    description = description.replace('myself', players[dealerId]['name'])
    description = description.replace(' me ', ' ' +
                                      players[dealerId]['name'] + ' ')
    description = description.replace(' self ', ' ' +
                                      players[dealerId]['name'] + ' ')

    playerCount = 0
    for p in players:
        if players[p]['room'] != players[dealerId]['room']:
            continue
        if players[p]['name'].lower() not in description:
            continue
        playerCount += 1

    if playerCount == 0:
        mud.sendMessage(dealerId, '\nName some players to deal to.\n')
        return

    # initialise the deck
    deck = Deck()

    # create game state
    if not items[gameItemID].get('gameState'):
        items[gameItemID]['gameState'] = {}

    hands = {}
    for p in players:
        if players[p]['room'] != players[dealerId]['room']:
            continue
        if players[p]['name'].lower() not in description:
            continue
        if dealCardsToPlayer(players, dealerId, players[p]['name'],
                             noOfCards, deck, mud, hands,
                             rooms, items, itemsDB):
            items[gameItemID]['gameState']['hands'] = hands
            items[gameItemID]['gameState']['table'] = {}
            items[gameItemID]['gameState']['deck'] = str(deck)
            showHandOfCards(players, p, mud, rooms, items, itemsDB)

    # no cards played
    items[gameItemID]['gameState']['hands'] = hands
    items[gameItemID]['gameState']['called'] = 0
    items[gameItemID]['gameState']['deck'] = str(deck)


def getCardDescription(rank: str, suit: str) -> str:
    """Given rank as a single character and suit
    returns a description of the card
    This is used for non-graphical output
    """
    rankStr = str(rank).upper()
    if rankStr.startswith('K'):
        rankStr = 'King'
    elif rankStr.startswith('Q'):
        rankStr = 'Queen'
    elif rankStr.startswith('A'):
        rankStr = 'Ace'
    elif rankStr.startswith('J'):
        rankStr = 'Jack'

    if suit == '♥':
        return str(rankStr) + ' of hearts\n'
    elif suit == '♦':
        return str(rankStr) + ' of diamonds\n'
    elif suit == '♣':
        return str(rankStr) + ' of clubs\n'
    return str(rankStr) + ' of spades\n'


def showHandOfCards(players: {}, id, mud, rooms: {},
                    items: {}, itemsDB: {}) -> None:
    """Shows the cards for the given player
    """
    gameItemID = cardGameInRoom(players, id, rooms, items, itemsDB)
    if not gameItemID:
        mud.sendMessage(id, '\nThere are no playing cards here.\n')
        return

    playerName = players[id]['name']
    if not items[gameItemID].get('gameState'):
        mud.sendMessage(id, '\nNo cards have been dealt.\n')
        return

    if not items[gameItemID]['gameState'].get('hands'):
        mud.sendMessage(id, '\nNo hands have been dealt.\n')
        return

    if not items[gameItemID]['gameState']['hands'].get(playerName):
        mud.sendMessage(id, '\nNo hands have been dealt to ' +
                        playerName+'.\n')
        return

    handStr = items[gameItemID]['gameState']['hands'][playerName]
    hand = handStr.split()
    lines = [[] for i in range(9)]
    cardColor = "\u001b[38;5;240m"
    cardDescriptions = ''

    for cardStr in hand:
        if len(cardStr) < 2:
            continue
        rankColor = "\u001b[38;5;250m"
        if cardStr[1] != '0':
            rank = cardStr[0].upper()
            suit = cardStr[1]
        else:
            rank = cardStr[0] + cardStr[1]
            suit = cardStr[2]
        suitColor = "\u001b[38;5;245m"

        cardDescriptions += getCardDescription(rank, suit)

        if suit == '♥' or suit == '♦':
            suitColor = "\u001b[31m"
            rankColor = suitColor
        if rank == '10':
            space = ''
        else:
            space = ' '
        lines[0].append('┌─────────┐')
        lines[1].append('│{}{}{}{}       │'.format(rankColor, rank,
                                                   cardColor, space))
        lines[2].append('│         │')
        lines[3].append('│         │')
        lines[4].append('│    {}{}{}    │'.format(suitColor, suit, cardColor))
        lines[5].append('│         │')
        lines[6].append('│         │')
        lines[7].append('│       {}{}{}{}│'.format(space, rankColor,
                                                   rank, cardColor))
        lines[8].append('└─────────┘')

    boardStr = cardColor + '\n'

    graphicalCards = True
    if players[id].get('graphics'):
        if players[id]['graphics'] == 'off':
            graphicalCards = False
    if graphicalCards:
        for lineRowStr in lines:
            lineStr = ''
            for s in lineRowStr:
                lineStr += s
            boardStr += lineStr+'\n'
    else:
        boardStr += cardDescriptions

    mud.send_game_board(id, boardStr)
    rankedStr = cardRank(handStr)
    if rankedStr:
        mud.sendMessage(id, 'You have ' + str(rankedStr[0]) + '.\n\n')

    if not items[gameItemID]['gameState'].get('called'):
        return
    if not items[gameItemID]['gameState']['called'] == 0:
        return

    # show your hand to other players
    for p in players:
        if players[p]['room'] != players[id]['room']:
            continue
        if id == p:
            continue
        if items[gameItemID]['gameState']['hands'].get(players[p]['name']):
            mud.sendMessage(p, '\n' + players[id]['name'] +
                            ' shows their hand.\n' + boardStr)
            if rankedStr:
                mud.sendMessage(p, players[id]['name'] + ' has ' +
                                str(rankedStr[0]) + '.\n\n')


def swapCard(cardDescription: str, players: {}, id, mud, rooms: {},
             items: {}, itemsDB: {}) -> None:
    gameItemID = cardGameInRoom(players, id, rooms, items, itemsDB)
    if not gameItemID:
        mud.sendMessage(id, '\nThere are no playing cards here.\n')
        return

    cardStr = parseCard(cardDescription)
    if not cardStr:
        mud.sendMessage(id, "\nThat's not a card.\n")
        return

    playerName = players[id]['name']
    if not items[gameItemID].get('gameState'):
        mud.sendMessage(id, '\nNo cards have been dealt.\n')
        return

    if items[gameItemID]['gameState'].get('called'):
        if items[gameItemID]['gameState']['called'] != 0:
            mud.sendMessage(id, '\nThis round is over. Deal again.\n')
            return

    if not items[gameItemID]['gameState'].get('hands'):
        mud.sendMessage(id, '\nNo hands have been dealt.\n')
        return

    if not items[gameItemID]['gameState']['hands'].get(playerName):
        mud.sendMessage(id, '\nNo hands have been dealt to you.\n')
        return

    handStr = items[gameItemID]['gameState']['hands'][playerName]
    if cardStr not in handStr:
        mud.sendMessage(id, '\n' + cardStr.upper() +
                        ' is not in your hand.\n')
        return

    deck = items[gameItemID]['gameState']['deck'].split()
    if len(deck) == 0:
        mud.sendMessage(id, '\nNo more cards in the deck.\n')
        return
    nextCard = deck.pop(randrange(len(deck)))
    items[gameItemID]['gameState']['deck'] = ""
    for deckCardStr in deck:
        if items[gameItemID]['gameState']['deck'] != "":
            items[gameItemID]['gameState']['deck'] += ' ' + deckCardStr
        else:
            items[gameItemID]['gameState']['deck'] += deckCardStr

    items[gameItemID]['gameState']['hands'][playerName] = \
        handStr.replace(cardStr, nextCard)

    # tell other players that a card was swapped
    for p in players:
        if players[p]['room'] != players[id]['room']:
            continue
        if p == id:
            continue
        otherPlayerName = players[p]['name']
        if items[gameItemID]['gameState']['hands'].get(otherPlayerName):
            mud.sendMessage(p, '\n' + playerName + ' swaps a card.\n')
    mud.sendMessage(p, '\nYou swap a card.\n')
    showHandOfCards(players, id, mud, rooms, items, itemsDB)


def shuffleCards(players: {}, id, mud, rooms: {},
                 items: {}, itemsDB: {}) -> None:
    gameItemID = cardGameInRoom(players, id, rooms, items, itemsDB)
    if not gameItemID:
        mud.sendMessage(id, '\nThere are no playing cards here.\n')
        return

    mud.sendMessage(id, '\nYou shuffle the cards.\n')

    for p in players:
        if players[p]['room'] != players[id]['room']:
            continue
        if p == id:
            continue
        mud.sendMessage(p, '\n' + players[id]['name'] + ' shuffles cards.\n')


def callCards(players: {}, id, mud, rooms: {},
              items: {}, itemsDB: {}) -> None:
    gameItemID = cardGameInRoom(players, id, rooms, items, itemsDB)
    if not gameItemID:
        mud.sendMessage(id, '\nThere are no playing cards here.\n')
        return

    playerName = players[id]['name']
    if not items[gameItemID].get('gameState'):
        mud.sendMessage(id, '\nNo cards have been dealt.\n')
        return

    if not items[gameItemID]['gameState'].get('hands'):
        mud.sendMessage(id, '\nNo hands have been dealt.\n')
        return

    mud.sendMessage(id, '\nYou call.\n')
    items[gameItemID]['gameState']['called'] = 1
    for p in players:
        if players[p]['room'] != players[id]['room']:
            continue
        if p == id:
            continue
        if items[gameItemID]['gameState']['hands'].get(players[p]['name']):
            mud.sendMessage(p, '\n' + playerName + ' calls.\n')

    resultStr = ''
    for p in players:
        if players[p]['room'] != players[id]['room']:
            continue
        if items[gameItemID]['gameState']['hands'].get(players[p]['name']):
            handStr = \
                items[gameItemID]['gameState']['hands'][players[p]['name']]
            rankedStr = cardRank(handStr)
            if rankedStr:
                resultStr += '<f0><f32>' + players[p]['name'] + \
                    '<r> has ' + str(rankedStr[0]) + '.\n'
            else:
                resultStr += '<f0><f32>' + players[p]['name'] + \
                    '<r> has nothing.\n'

    if len(resultStr) == 0:
        mud.sendMessage(id, '\nNo hands have been dealt.\n')
        return

    for p in players:
        if players[p]['room'] != players[id]['room']:
            continue
        if items[gameItemID]['gameState']['hands'].get(players[p]['name']):
            mud.sendMessage(p, '\n' + resultStr)
