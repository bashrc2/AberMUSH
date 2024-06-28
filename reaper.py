__filename__ = "reaper.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
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

from functions import add_to_scheduler
from functions import deepcopy
from npcs import corpse_exists
# from copy import deepcopy

import time


def remove_corpses(corpses: {}):
    # Iterate through corpses and remove ones older than their TTL
    corpses_copy = deepcopy(corpses)
    curr_time = int(time.time())
    for cor, _ in corpses_copy.items():
        if curr_time >= corpses_copy[cor]['died'] + corpses_copy[cor]['TTL']:
            del corpses[cor]


def run_deaths(mud, players: {}, npcs: {}, corpses, fights: {},
               event_schedule, scripted_events_db):
    # Handle Player Deaths
    for pid, plyr in players.items():
        if plyr['authenticated']:
            if plyr['hp'] <= 0:
                corpse_name = str(plyr['name'] + "'s corpse")
                if not corpse_exists(corpses, plyr['room'],
                                     corpse_name):
                    # Create player's corpse in the room
                    corpses[len(corpses)] = {
                        'room': plyr['room'],
                        'name': corpse_name,
                        'inv': deepcopy(plyr['inv']),
                        'died': int(time.time()),
                        'TTL': plyr['corpseTTL'],
                        'owner': 1
                    }
                # Clear player's inventory, it stays on the corpse
                plyr['clo_lhand'] = 0
                plyr['clo_rhand'] = 0
                plyr['inv'] = []
                plyr['isInCombat'] = 0
                plyr['prone'] = 1
                plyr['shove'] = 0
                plyr['dodge'] = 0
                plyr['lastRoom'] = plyr['room']
                plyr['room'] = '$rid=1262$'
                fights_copy = deepcopy(fights)
                for fight, _ in fights_copy.items():
                    if ((fights_copy[fight]['s1type'] == 'pc' and
                         fights_copy[fight]['s1id'] == pid) or
                        (fights_copy[fight]['s2type'] == 'pc' and
                         fights_copy[fight]['s2id'] == pid)):
                        # clear the combat flag
                        if fights_copy[fight]['s1type'] == 'pc':
                            fid = fights_copy[fight]['s1id']
                            players[fid]['isInCombat'] = 0
                        elif fights_copy[fight]['s1type'] == 'npc':
                            fid = fights_copy[fight]['s1id']
                            npcs[fid]['isInCombat'] = 0
                        if fights_copy[fight]['s2type'] == 'pc':
                            fid = fights_copy[fight]['s2id']
                            players[fid]['isInCombat'] = 0
                        elif fights_copy[fight]['s2type'] == 'npc':
                            fid = fights_copy[fight]['s2id']
                            npcs[fid]['isInCombat'] = 0
                        plyr['isInCombat'] = 0
                        del fights[fight]
                for pid2, plyr2 in players.items():
                    if plyr2['authenticated'] is not None \
                       and plyr2['room'] == plyr['lastRoom'] \
                       and plyr2['name'] != plyr['name']:
                        mud.send_message(
                            pid2, '<u><f32>{}'.format(plyr['name']) +
                            '<r> <f124>has been killed.\n')
                        plyr['lastRoom'] = None
                        mud.send_message(
                            pid, '<b88><f158>Oh dear! You have died!\n')

                # Add Player Death event (ID:666) to event_schedule
                add_to_scheduler(666, pid, event_schedule, scripted_events_db)

                plyr['hp'] = 4
