__filename__ = "atcommands.py"
__author__ = "Bartek Radwanski"
__credits__ = ["Bartek Radwanski"]
__license__ = "MIT"
__version__ = "0.6.2"
__maintainer__ = "Bartek Radwanski"
__email__ = "bartek.radwanski@gmail.com"
__status__ = "Production"

from functions import addToScheduler
from functions import getFreeKey
from copy import deepcopy
import time
import configparser
from pathlib import Path
import os
from functions import sendToChannel

# example of config file usage
# print(str(Config.get('Database', 'Hostname')))
Config = configparser.ConfigParser()
Config.read('config.ini')

'''
Command function template:

def atcommandname(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket):
        print("I'm in!")
'''

def config(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket):
        configitem = params.split(" ")[0]
        parameter = " ".join(params.split(" ")[1:])
        #print(configitem)
        #print(parameter)
        if configitem.lower() == "defaultchannel":
                if parameter.lower() == "clear":
                        players[id]['defaultChannel'] = None
                        mud.send_message(id, "Default channel has been cleared.\n")
                elif parameter.lower() == "show":
                        if players[id]['defaultChannel'] != None:
                                mud.send_message(id, "Your default channel is currently set to [" + players[id]['defaultChannel'] + "]\n")
                        else:
                                mud.send_message(id, "You do not have a default channel set.\n")
                else:
                        mud.send_message(id, "Setting default channel to: " + parameter + "\n")
                        players[id]['defaultChannel'] = parameter
        else:
                mud.send_message(id, "Not sure what you would like to configure.\n")

def serverlog(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket):
        if players[id]['permissionLevel'] == 0:
                if params.lower() == 'show':
                        logLocation = str(Config.get('Logs', 'ServerLog'))
                        #print(logLocation)
                        logFile = Path(logLocation)
                        if logFile.is_file():
                                '''
                                with open(fname) as f:
                                content = f.readlines()
                                # you may also want to remove whitespace characters like `\n` at the end of each line
                                content = [x.strip() for x in content]
                                '''
                                with open(logLocation) as f:
                                        content = f.readlines()
                                f.close()
                                content = [x.strip() for x in content]

                                for l in content:
                                        mud.send_message(id, l.encode('utf-8').decode('latin-1'))

                                mud.send_message(id, "<f255>Total of " + str(len(content)) + " lines read from server log.\n")
                        else:
                                mud.send_message(id, "Nothing to show!\n")
                elif params.lower() == 'clear':
                        logLocation = str(Config.get('Logs', 'ServerLog'))
                        logFile = Path(logLocation)
                        if logFile.is_file():
                                os.remove(logLocation)
                                mud.send_message(id, "<f255>Server log has been cleared!\n")
                        else:
                                mud.send_message(id, "Nothing to clear!\n")
                else:
                        mud.send_message(id, "Invalid @serverlog parameter '" + params + "'\n")
        else:
                mud.send_message(id, "You do not have permission to do this.\n")

def sendAtCommandError(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket):
        mud.send_message(id, "Unknown @command " + str(params) + "!\n")

def quit(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket):
        mud._handle_disconnect(id)

def who(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket):
        counter = 1
        if players[id]['permissionLevel'] == 0:
                for p in players:
                        if players[p]['name'] == None:
                                name = "None"
                        else:
                                name = players[p]['name']

                        if players[p]['room'] == None:
                                room = "None"
                        else:
                                room = players[p]['room']

                        mud.send_message(id, str(counter) + ". Client ID: [" + str(p) + "] Player name: [" + name + "] Room: [" + room + "]\n")
                        counter += 1
        else:
                mud.send_message(id, "You do not have permission to do this.\n")

def subscribe(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket):
        # print("Subbing to a channel")
        invalidChannels = ["clear", "show"]
        params = params.replace(" ", "")
        if len(params) > 0:
                if str(params.lower()) in players[id]['channels']:
                        mud.send_message(id, "You are already subscribed to [<f191>" + params.lower() + "<r>]\n")
                else:
                        #if str(params.lower()) != 'clear':
                        if str(params.lower()) not in invalidChannels:
                                players[id]['channels'].append(str(params.lower()))
                                mud.send_message(id, "You have subscribed to [<f191>" + params + "<r>]\n")
                                if "@" in params:
                                        gsocket.msg_gen_message_channel_send(players[id]['name'], params.split("@")[0].lower(), players[id]['name'] + " has joined the channel!\n")
                                if params.lower() != "system":
                                        sendToChannel(players[id]['name'], params, players[id]['name'] + " has joined the channel.\n", chans)
                        else:
                                mud.send_message(id, "Invalid channel name [<f191>" + params + "<r>]\n")
        else:
                mud.send_message(id, "What channel would you like to subscribe to?\n")

def unsubscribe(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket):
        params = params.replace(" ", "")
        if len(params) > 0:
                try:
                        if "@" in params:
                                gsocket.msg_gen_message_channel_send(players[id]['name'], params.split("@")[0].lower(), players[id]['name'] + " has left the channel!")
                        if params.lower() != "system":
                                sendToChannel(players[id]['name'], params, players[id]['name'] + " has left the channel.\n", chans)
                        players[id]['channels'].remove(params.lower())
                        mud.send_message(id, "You have unsubscribed from [<f191>" + params.lower() + "<r>]\n")
                except Exception as e:
                        mud.send_message(id, "You are not currently subscribed to [<f191>" + params.lower() + "<r>]\n")
        else:
                mud.send_message(id, "What channel would you like to unsubscribe from?\n")

        if params.lower() == "system":
                mud.send_message(id, "<f230>You have un-subscribed from a [<f191>system<r>] channel. From now on, you will not receive any game-wide system messages (including server reboot notifications etc.). You can subscribe to SYSTEM at any time by typing '<f255>@subscribe system<r>'\n")

def channels(params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket):
        if len(players[id]['channels']):
                mud.send_message(id, "You are currently subscribed to the following channels:\n")
                # print(players[id]['channels'])
                for c in sorted(players[id]['channels']):
                        mud.send_message(id, " [<f191>" + c + "<r>]")
        else:
                mud.send_message(id, "You are not currently subscribed to any channels.\n")

def runAtCommand(command, params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket):
        switcher = {
                "sendAtCommandError": sendAtCommandError,
                "quit": quit,
                "subscribe": subscribe,
                "unsubscribe": unsubscribe,
                "channels": channels,
                "who": who,
                "serverlog": serverlog,
                "config": config,
        }

        try:
                switcher[command](params, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket)
        except Exception as e:
                switcher["sendAtCommandError"](e, mud, playersDB, players, rooms, npcsDB, npcs, itemsDB, items, envDB, env, eventDB, eventSchedule, id, fights, corpses, chans, gsocket)
