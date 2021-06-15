__filename__ = "reaper.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"
__module_group__ = "Core"

#                   ...
#                 ;::::;
#               ;::::; :;
#             ;:::::'   :;
#            ;:::::;     ;.
#           ,:::::'       ;           OOO\
#           ::::::;       ;          OOOOO\
#           ;:::::;       ;         OOOOOOOO
#          ,;::::::;     ;'         / OOOOOOO
#        ;:::::::::`. ,,,;.        /  / DOOOOOO
#      .';:::::::::::::::::;,     /  /     DOOOO
#     ,::::::;::::::;;;;::::;,   /  /        DOOO
#    ;`::::::`'::::::;;;::::: ,#/  /          DOOO
#    :`:::::::`;::::::;;::: ;::#  /            DOOO
#    ::`:::::::`;:::::::: ;::::# /              DOO
#    `:`:::::::`;:::::: ;::::::#/               DOO
#     :::`:::::::`;; ;:::::::::##                OO
#     ::::`:::::::`;::::::::;:::#                OO
#     `:::::`::::::::::::;'`:;::#                O
#      `:::::`::::::::;' /  / `:#
#       ::::::`:::::;'  /  /   `#

from functions import addToScheduler
from functions import deepcopy
from npcs import corpseExists
# from copy import deepcopy

import time


def removeCorpses(corpses: {}):
    # Iterate through corpses and remove ones older than their TTL
    corpsesCopy = deepcopy(corpses)
    for (c, pl) in corpsesCopy.items():
        if int(time.time()) >= corpsesCopy[c]['died'] + corpsesCopy[c]['TTL']:
            del corpses[c]


def runDeaths(mud, players: {}, npcs: {}, corpses, fights: {},
              eventSchedule, scriptedEventsDB):
    # Handle Player Deaths
    for (pid, pl) in list(players.items()):
        if players[pid]['authenticated']:
            if players[pid]['hp'] <= 0:
                corpseName = str(players[pid]['name'] + "'s corpse")
                if not corpseExists(corpses, players[pid]['room'], corpseName):
                    # Create player's corpse in the room
                    corpses[len(corpses)] = {
                        'room': players[pid]['room'],
                        'name': corpseName,
                        'inv': deepcopy(players[pid]['inv']),
                        'died': int(time.time()),
                        'TTL': players[pid]['corpseTTL'],
                        'owner': 1
                    }
                # Clear player's inventory, it stays on the corpse
                players[pid]['clo_lhand'] = 0
                players[pid]['clo_rhand'] = 0
                players[pid]['inv'] = []
                players[pid]['isInCombat'] = 0
                players[pid]['prone'] = 1
                players[pid]['shove'] = 0
                players[pid]['dodge'] = 0
                players[pid]['lastRoom'] = players[pid]['room']
                players[pid]['room'] = '$rid=1262$'
                fightsCopy = deepcopy(fights)
                for (fight, pl) in fightsCopy.items():
                    if ((fightsCopy[fight]['s1type'] == 'pc' and
                         fightsCopy[fight]['s1id'] == pid) or
                        (fightsCopy[fight]['s2type'] == 'pc' and
                         fightsCopy[fight]['s2id'] == pid)):
                        # clear the combat flag
                        if fightsCopy[fight]['s1type'] == 'pc':
                            fid = fightsCopy[fight]['s1id']
                            players[fid]['isInCombat'] = 0
                        elif fightsCopy[fight]['s1type'] == 'npc':
                            fid = fightsCopy[fight]['s1id']
                            npcs[fid]['isInCombat'] = 0
                        if fightsCopy[fight]['s2type'] == 'pc':
                            fid = fightsCopy[fight]['s2id']
                            players[fid]['isInCombat'] = 0
                        elif fightsCopy[fight]['s2type'] == 'npc':
                            fid = fightsCopy[fight]['s2id']
                            npcs[fid]['isInCombat'] = 0
                        players[pid]['isInCombat'] = 0
                        del fights[fight]
                for (pid2, pl) in list(players.items()):
                    if players[pid2]['authenticated'] is not None \
                       and players[pid2]['room'] == players[pid]['lastRoom'] \
                       and players[pid2]['name'] != players[pid]['name']:
                        mud.sendMessage(
                            pid2, '<u><f32>{}'.format(players[pid]['name']) +
                            '<r> <f124>has been killed.\n')
                        players[pid]['lastRoom'] = None
                        mud.sendMessage(
                            pid, '<b88><f158>Oh dear! You have died!\n')

                # Add Player Death event (ID:666) to eventSchedule
                addToScheduler(666, pid, eventSchedule, scriptedEventsDB)

                players[pid]['hp'] = 4
