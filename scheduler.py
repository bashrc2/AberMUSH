__filename__ = "scheduler.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Core"

from events import evaluateEvent
from random import randint
# from copy import deepcopy
from functions import show_timing
from functions import deepcopy

import time


def run_messages(mud, channels, players):
    # go through channels messages queue and send messages to subscribed
    # players
    previousTiming = time.time()

    ch = deepcopy(channels)

    previousTiming = \
        show_timing(previousTiming, "copy channels")

    for p in players:
        if players[p]['channels'] is not None:
            for c in players[p]['channels']:
                # print(c)
                for m in ch:
                    if ch[m]['channel'] == c:
                        mud.send_message(
                            p, "[<f191>" + ch[m]['channel'] +
                            "<r>] <f32>" + ch[m]['sender'] +
                            "<r>: " + ch[m]['message'] + "\n")
                        # del channels[m]
            previousTiming = \
                show_timing(previousTiming, "send message " +
                            str(len(players[p]['channels'])) + ' x ' +
                            str(len(ch)))


def run_environment(mud, players, env):
    # Iterate through ENV elements and see if it's time to send a message to
    # players in the same room as the ENV elements
    for (eid, pl) in list(env.items()):
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

            for (pid, pl) in list(players.items()):
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
    for (event, pl) in list(event_schedule.items()):
        if time.time() < event_schedule[event]['time']:
            continue
        # its time to run the event!
        if event_schedule[event]['type'] == "msg":
            mud.send_message(int(event_schedule[event]['target']),
                             str(event_schedule[event]['body']) + "\n")
        else:
            evaluateEvent(
                event_schedule[event]['target'],
                event_schedule[event]['type'],
                event_schedule[event]['body'],
                players, npcs, itemsInWorld, env,
                npcs_db, env_db)
        del event_schedule[event]
