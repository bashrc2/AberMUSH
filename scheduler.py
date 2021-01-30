__filename__ = "scheduler.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

from events import evaluateEvent
from random import randint
# from copy import deepcopy
from functions import showTiming
from functions import deepcopy

import time


def runMessages(mud, channels, players):
    # go through channels messages queue and send messages to subscribed
    # players
    previousTiming = time.time()

    ch = deepcopy(channels)

    previousTiming = \
        showTiming(previousTiming, "copy channels")

    for p in players:
        if players[p]['channels'] is not None:
            for c in players[p]['channels']:
                # print(c)
                for m in ch:
                    if ch[m]['channel'] == c:
                        mud.sendMessage(
                            p, "[<f191>" + ch[m]['channel'] +
                            "<r>] <f32>" + ch[m]['sender'] +
                            "<r>: " + ch[m]['message'] + "\n")
                        # del channels[m]
            previousTiming = \
                showTiming(previousTiming, "send message " +
                           str(len(players[p]['channels'])) + ' x ' +
                           str(len(ch)))


def runEnvironment(mud, players, env):
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
                        mud.sendMessage(pid, msg)
                        env[eid]['lastSaid'] = rnd
                        env[eid]['timeTalked'] = now
                    else:
                        msg = '<f68>[' + env[eid]['name'] + ']: <f69>' + \
                            env[eid]['vocabulary'][0] + "\n\n"
                        mud.sendMessage(pid, msg)
                        env[eid]['lastSaid'] = rnd
                        env[eid]['timeTalked'] = now
                        env[eid]['randomizer'] = \
                            randint(0, env[eid]['randomFactor'])


def runSchedule(mud, eventSchedule, players: {}, npcs: {},
                itemsInWorld: {}, env, npcsDB: {}, envDB: {}):
    # Evaluate the Event Schedule
    for (event, pl) in list(eventSchedule.items()):
        if time.time() < eventSchedule[event]['time']:
            continue
        # its time to run the event!
        if eventSchedule[event]['type'] == "msg":
            mud.sendMessage(int(eventSchedule[event]['target']),
                            str(eventSchedule[event]['body']) + "\n")
        else:
            evaluateEvent(
                eventSchedule[event]['target'],
                eventSchedule[event]['type'],
                eventSchedule[event]['body'],
                players, npcs, itemsInWorld, env,
                npcsDB, envDB)
        del eventSchedule[event]
