__filename__ = "scheduler.py"
__author__ = "Bob Mottram"
__credits__ = ["Bob Mottram"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Core"

import time
from random import randint
from events import evaluate_event
# from copy import deepcopy
from functions import show_timing
from functions import deepcopy


def run_messages(mud, channels: {}, players: {}):
    """go through channels messages queue and send messages to subscribed
    players
    """
    previous_timing = time.time()

    chans = deepcopy(channels)

    previous_timing = \
        show_timing(previous_timing, "copy channels")

    for plyr_id, plyr in players.items():
        if plyr['channels'] is None:
            continue
        for cha in plyr['channels']:
            # print(c)
            for msg in chans:
                msgchan = chans[msg]
                if msgchan['channel'] != cha:
                    continue
                mud.send_message(
                    plyr_id, "[<f191>" + msgchan['channel'] +
                    "<r>] <f32>" + msgchan['sender'] +
                    "<r>: " + msgchan['message'] + "\n")
                # del channels[m]
        previous_timing = \
            show_timing(previous_timing, "send message " +
                        str(len(plyr['channels'])) + ' x ' +
                        str(len(chans)))


def run_environment(mud, players: {}, env: {}):
    """Iterate through ENV elements and see if it's time to send a message to
    players in the same room as the ENV elements
    """
    for _, envr in env.items():
        now = int(time.time())
        expire_time = \
            envr['timeTalked'] + envr['talkDelay'] + envr['randomizer']
        if now <= expire_time:
            continue

        if len(envr['vocabulary']) > 1:
            rnd = randint(0, len(envr['vocabulary']) - 1)
            while rnd is envr['lastSaid']:
                rnd = randint(0, len(envr['vocabulary']) - 1)
        else:
            rnd = 0

        for pid, plyr in players.items():
            if envr['room'] != plyr['room']:
                continue
            if len(envr['vocabulary']) > 1:
                msg = '<f68>[' + envr['name'] + ']: <f69>' + \
                    envr['vocabulary'][rnd] + "\n\n"
                mud.send_message(pid, msg)
                envr['lastSaid'] = rnd
                envr['timeTalked'] = now
            else:
                msg = '<f68>[' + envr['name'] + ']: <f69>' + \
                    envr['vocabulary'][0] + "\n\n"
                mud.send_message(pid, msg)
                envr['lastSaid'] = rnd
                envr['timeTalked'] = now
                envr['randomizer'] = \
                    randint(0, envr['randomFactor'])


def run_schedule(mud, event_schedule: {}, players: {}, npcs: {},
                 items_in_world: {}, env: {}, npcs_db: {}, env_db: {}):
    """Evaluate the Event Schedule
    """
    deleted_events = []
    for event, evnt in event_schedule.items():
        if time.time() < evnt['time']:
            continue
        # its time to run the event!
        if evnt['type'] == "msg":
            mud.send_message(int(evnt['target']),
                             str(evnt['body']) + "\n")
        else:
            evaluate_event(
                evnt['target'],
                evnt['type'],
                evnt['body'],
                players, npcs, items_in_world, env,
                npcs_db, env_db)
        deleted_events.append(event)

    for event in deleted_events:
        del event_schedule[event]
