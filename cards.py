__filename__ = "cards.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Some functions based on:
# https://rosettacode.org/wiki/Poker_hand_analyser#Python

import re, sys
from collections import namedtuple
from itertools import product
from random import randrange

suit = '♥ ♦ ♣ ♠'.split()
# ordered strings of faces
faces   = '2 3 4 5 6 7 8 9 10 j q k a'
lowaces = 'a 2 3 4 5 6 7 8 9 10 j q k'
# faces as lists
face   = faces.split()
lowace = lowaces.split()

class Card(namedtuple('Card', 'face, suit')):
    def __repr__(self):
        return ''.join(self)
 
class Deck():
    def __init__(self):
        self.__deck = [Card(f, s) for f,s in product(face, suit)]
 
    def __repr__(self):
        return ' '.join(repr(card) for card in self.__deck)
 
    def shuffle(self):
        pass
 
    def deal(self):
        return self.__deck.pop(randrange(len(self.__deck)))
 
  
def straightflush(hand: str) -> bool:
    f,fs = ( (lowace, lowaces) if any(card.face == '2' for card in hand)
             else (face, faces) )
    ordered = sorted(hand, key=lambda card: (f.index(card.face), card.suit))
    first, rest = ordered[0], ordered[1:]
    if ( all(card.suit == first.suit for card in rest) and
         ' '.join(card.face for card in ordered) in fs ):
        return 'straight-flush', ordered[-1].face
    return False
 
def fourofakind(hand: str) -> bool:
    allfaces = [f for f,s in hand]
    allftypes = set(allfaces)
    if len(allftypes) != 2:
        return False
    for f in allftypes:
        if allfaces.count(f) == 4:
            allftypes.remove(f)
            return 'four-of-a-kind', [f, allftypes.pop()]
    else:
        return False
 
def fullhouse(hand: str) -> bool:
    allfaces = [f for f,s in hand]
    allftypes = set(allfaces)
    if len(allftypes) != 2:
        return False
    for f in allftypes:
        if allfaces.count(f) == 3:
            allftypes.remove(f)
            return 'full-house', [f, allftypes.pop()]
    else:
        return False
 
def flush(hand: str) -> bool:
    allstypes = {s for f, s in hand}
    if len(allstypes) == 1:
        allfaces = [f for f,s in hand]
        return 'flush', sorted(allfaces,
                               key=lambda f: face.index(f),
                               reverse=True)
    return False
 
def straight(hand: str) -> bool:
    f,fs = ( (lowace, lowaces) if any(card.face == '2' for card in hand)
             else (face, faces) )
    ordered = sorted(hand, key=lambda card: (f.index(card.face), card.suit))
    first, rest = ordered[0], ordered[1:]
    if ' '.join(card.face for card in ordered) in fs:
        return 'straight', ordered[-1].face
    return False
 
def threeofakind(hand: str) -> bool:
    allfaces = [f for f,s in hand]
    allftypes = set(allfaces)
    if len(allftypes) <= 2:
        return False
    for f in allftypes:
        if allfaces.count(f) == 3:
            allftypes.remove(f)
            return ('three-of-a-kind', [f] +
                     sorted(allftypes,
                            key=lambda f: face.index(f),
                            reverse=True))
    else:
        return False
 
def twopair(hand: str) -> bool:
    allfaces = [f for f,s in hand]
    allftypes = set(allfaces)
    pairs = [f for f in allftypes if allfaces.count(f) == 2]
    if len(pairs) != 2:
        return False
    p0, p1 = pairs
    other = [(allftypes - set(pairs)).pop()]
    return 'two-pair', pairs + other if face.index(p0) > face.index(p1) else pairs[::-1] + other
 
def onepair(hand: str) -> bool:
    allfaces = [f for f,s in hand]
    allftypes = set(allfaces)
    pairs = [f for f in allftypes if allfaces.count(f) == 2]
    if len(pairs) != 1:
        return False
    allftypes.remove(pairs[0])
    return 'one-pair', pairs + sorted(allftypes,
                                      key=lambda f: face.index(f),
                                      reverse=True)
 
def highcard(hand: str):
    allfaces = [f for f,s in hand]
    return 'high-card', sorted(allfaces,
                               key=lambda f: face.index(f),
                               reverse=True)

handrankorder =  (
    straightflush, fourofakind, fullhouse,
    flush, straight, threeofakind,
    twopair, onepair, highcard
)
 
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

def rank(cards: str) -> []:
    hand = handy(cards)
    if not hand:
        return None
    rank=None
    for ranker in handrankorder:
        rank = ranker(hand)
        if rank:
            break
    return rank

def parseCard(cardDescription: str) -> str:
    """Takes a card description, such as "the ace of spades"
    and turns it into "a♠"
    """
    suitName={
        "heart": "♥",
        "diamond": "♦",
        "club": "♣",
        "spade": "♠"
    }
    detectedSuit=''
    detectedFace=''
    cardDescription=cardDescription.lower().replace('the ','').replace(' of ',' ').replace('.','').replace(',','')
    for name,symbol in suitName.items():
        if name+'s' in cardDescription:
            detectedSuit=symbol
        elif name in cardDescription:
            detectedSuit=symbol
    if not detectedSuit:
        return None
    faceNames = {
        "two":"2",
        "three":"3",
        "four":"4",
        "five":"5",
        "six":"6",
        "seven":"7",
        "eight":"8",
        "nine":"9",
        "ten":"10",
        "jack":"j",
        "queen":"q",
        "king":"k",
        "ace":"a"
    }
    for name,symbol in faceNames.items():
        if name in cardDescription:
            detectedFace=symbol
    if not detectedFace:
        for i in range(10,2,-1):
            if str(i) in cardDescription:
                detectedFace=str(i)
        return None
    return detectedFace+detectedSuit

def dealCardsToPlayer(players: {},dealerId,name: str,noOfCards: int,deck,mud,hands) -> None:
    """Deals a number of cards to a player
    """
    cardPlayerId=None
    name=name.lower()
    for p in players:
        if players[p]['room'] == players[dealerId]['room']:
            if players[p]['name'].lower()==name:
                cardPlayerId=p
                break
    if cardPlayerId==None:
        if 'myself' in name or ' me' in name:
            cardPlayerId=dealerId
        else:
            mud.send_message(dealerId, "\nThey're not in the room.\n")
            return
    cardPlayerName=players[cardPlayerId]['name']
    hands[cardPlayerName]=''
    ctr=0
    for i in range(noOfCards):
        topCard=deck.deal()
        if topCard:
            if ctr==0:
                hands[cardPlayerName]+=str(topCard)
            else:
                hands[cardPlayerName]+=' '+str(topCard)
            ctr+=1
    if ctr>0:
        hands[cardPlayerName]=hands[cardPlayerName]
        if dealerId==cardPlayerId:
            mud.send_message(dealerId, '\nYou deal '+str(ctr)+' cards to yourself.\n')
        else:
            mud.send_message(dealerId, '\nYou deal '+str(ctr)+' cards to '+cardPlayerName+'.\n')
            mud.send_message(cardPlayerId, '\n'+players[dealerId]['name']+' deals '+str(ctr)+' cards to you.\n')

def cardGameInRoom(players: {},id,rooms: {},items: {},itemsDB: {}):
    """Returns the item ID if there is a card game in the room
    """
    rid=players[id]['room']
    for i in items:
        if items[i]['room'] != rid:
            continue
        if itemsDB[items[i]['id']]['game'].lower() == 'cards':
            return i
    return None

def getNumberFromText(text: str) -> int:
    """If there is a number in the given text then return it
    """
    for i in range(10,2,-1):
        if str(i) in text:
            return i
    numStr={
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
    for name,num in numStr.items():
        if name in text:
            return num
    return None
    

def dealToPlayers(players: {},dealerId,description: str, \
                  mud,rooms: {},items: {},itemsDB: {}) -> None:
    """Deal cards to players
    """
    gameItemID=cardGameInRoom(players,dealerId,rooms,items,itemsDB)
    if not gameItemID:
        mud.send_message(dealerId, '\nThere are no playing cards here.\n')

    noOfCards=getNumberFromText(description)
    if noOfCards==None:
        noOfCards=5

    description=description.lower().replace('.',' ').replace(',',' ')+' '
    description=description.replace('myself',players[dealerId]['name'])
    description=description.replace(' me ',' '+players[dealerId]['name']+' ')

    playerCount=0
    for p in players:
        if players[p]['room'] != players[dealerId]['room']:
            continue
        if players[p]['name'].lower() not in description:
            continue
        playerCount+=1

    if playerCount==0:
        mud.send_message(dealerId, '\nName some players to deal to.\n')

    # initialise the deck
    deck=Deck()

    hands={}
    for p in players:
        if players[p]['room'] != players[dealerId]['room']:
            continue
        if players[p]['name'].lower() not in description:
            continue
        dealCardsToPlayer(players,dealerId,players[p]['name'], \
                          noOfCards,deck,mud,hands)

    # no cards played
    items[gameItemID]['gameState']={
        'hands': hands,
        'table': {},
        'deck': str(deck)
    }
