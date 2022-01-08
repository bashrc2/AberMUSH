__filename__ = "scheduler.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Core"

from events import evaluate_event
from random import randint
# from copy import deepcopy
from functions import show_timing
from functions import deepcopy

import time


def run_messages(mud, channels, players):
    # go through channels messages queue and send messages to subscribed
    # players
    previous_timing = time.time()

    chans = deepcopy(channels)

    previous_timing = \
        show_timing(previous_timing, "copy channels")

    for plyr in players:
        if players[plyr]['channels'] is not None:
            for cha in players[plyr]['channels']:
                # print(c)
                for msg in chans:
                    if chans[msg]['channel'] == cha:
                        mud.send_message(
                            plyr, "[<f191>" + chans[msg]['channel'] +
                            "<r>] <f32>" + chans[msg]['sender'] +
                            "<r>: " + chans[msg]['message'] + "\n")
                        # del channels[m]
            previous_timing = \
                show_timing(previous_timing, "send message " +
                            str(len(players[plyr]['channels'])) + ' x ' +
                            str(len(chans)))


def run_environment(mud, players, env):
    # Iterate through ENV elements and see if it's time to send a message to
    # players in the same room as the ENV elements
    for eid, _ in list(env.items()):
        now = int(time.time())
        if now > \
           env[eid]['timeTalked'] + \
           env[eid]['talkDelay'] + \
           env[eid]['randomizer']:
            if len(env[eid]['vocabulary']) > 1:
                rnd = randint(0, len(env[eid]['vocabulary']) - 1)
                while rnd is env[eid]['lastSaid']:
                    rnd = randint(0, len(env[eid]['vocabulary']) - 1)
            else:
                rnd = 0

            for pid, _ in list(players.items()):
                if env[eid]['room'] == players[pid]['room']:
                    if len(env[eid]['vocabulary']) > 1:
                        msg = '<f68>[' + env[eid]['name'] + ']: <f69>' + \
                            env[eid]['vocabulary'][rnd] + "\n\n"
                        mud.send_message(pid, msg)
                        env[eid]['lastSaid'] = rnd
                        env[eid]['timeTalked'] = now
                    else:
                        msg = '<f68>[' + env[eid]['name'] + ']: <f69>' + \
                            env[eid]['vocabulary'][0] + "\n\n"
                        mud.send_message(pid, msg)
                        env[eid]['lastSaid'] = rnd
                        env[eid]['timeTalked'] = now
                        env[eid]['randomizer'] = \
                            randint(0, env[eid]['randomFactor'])


def run_schedule(mud, event_schedule, players: {}, npcs: {},
                 itemsInWorld: {}, env, npcs_db: {}, env_db: {}):
    # Evaluate the Event Schedule
    for event, _ in list(event_schedule.items()):
        if time.time() < event_schedule[event]['time']:
            continue
        # its time to run the event!
        if event_schedule[event]['type'] == "msg":
            mud.send_message(int(event_schedule[event]['target']),
                             str(event_schedule[event]['body']) + "\n")
        else:
            evaluate_event(
                event_schedule[event]['target'],
                event_schedule[event]['type'],
                event_schedule[event]['body'],
                players, npcs, itemsInWorld, env,
                npcs_db, env_db)
        del event_schedule[event]
