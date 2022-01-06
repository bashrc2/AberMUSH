__filename__ = "tests.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Unit Testing"


import os
import json
import configparser
from markets import money_purchase


def getFunctionCallArgs(name: str, lines: [], startLineCtr: int) -> []:
    """Returns the arguments of a function call given lines
    of source code and a starting line number
    """
    argsStr = lines[startLineCtr].split(name + '(')[1]
    if ')' in argsStr:
        argsStr = argsStr.split(')')[0].replace(' ', '').split(',')
        return argsStr
    for lineCtr in range(startLineCtr + 1, len(lines)):
        if ')' not in lines[lineCtr]:
            argsStr += lines[lineCtr]
            continue
        else:
            argsStr += lines[lineCtr].split(')')[0]
            break
    return argsStr.replace('\n', '').replace(' ', '').split(',')


def getFunctionCalls(name: str, lines: [], startLineCtr: int,
                     functionProperties: {}) -> []:
    """Returns the functions called by the given one,
    Starting with the given source code at the given line
    """
    callsFunctions = []
    functionContentStr = ''
    for lineCtr in range(startLineCtr + 1, len(lines)):
        lineStr = lines[lineCtr].strip()
        if lineStr.startswith('def '):
            break
        if lineStr.startswith('class '):
            break
        functionContentStr += lines[lineCtr]
    for funcName, properties in functionProperties.items():
        if funcName + '(' in functionContentStr:
            callsFunctions.append(funcName)
    return callsFunctions


def functionArgsMatch(callArgs: [], funcArgs: []):
    """Do the function artuments match the function call arguments
    """
    if len(callArgs) == len(funcArgs):
        return True

    # count non-optional arguments
    callArgsCtr = 0
    for a in callArgs:
        if a == 'self':
            continue
        if '=' not in a or a.startswith("'"):
            callArgsCtr += 1

    funcArgsCtr = 0
    for a in funcArgs:
        if a == 'self':
            continue
        if '=' not in a or a.startswith("'"):
            funcArgsCtr += 1

    return callArgsCtr >= funcArgsCtr


def _testFunctions():
    print('testFunctions')
    function = {}
    functionProperties = {}
    modules = {}
    modGroups = {}

    for subdir, dirs, files in os.walk('.'):
        for sourceFile in files:
            if not sourceFile.endswith('.py'):
                continue
            modName = sourceFile.replace('.py', '')
            modules[modName] = {
                'functions': []
            }
            sourceStr = ''
            with open(sourceFile, "r") as f:
                sourceStr = f.read()
                modules[modName]['source'] = sourceStr
            with open(sourceFile, "r") as f:
                lines = f.readlines()
                modules[modName]['lines'] = lines
                for line in lines:
                    if '__module_group__' in line:
                        if '=' in line:
                            groupName = line.split('=')[1].strip()
                            groupName = groupName.replace('"', '')
                            groupName = groupName.replace("'", '')
                            modules[modName]['group'] = groupName
                            if not modGroups.get(groupName):
                                modGroups[groupName] = [modName]
                            else:
                                if modName not in modGroups[groupName]:
                                    modGroups[groupName].append(modName)
                    if not line.strip().startswith('def '):
                        continue
                    methodName = line.split('def ', 1)[1].split('(')[0]
                    methodArgs = \
                        sourceStr.split('def ' + methodName + '(')[1]
                    methodArgs = methodArgs.split(')')[0]
                    methodArgs = methodArgs.replace(' ', '').split(',')
                    if function.get(modName):
                        function[modName].append(methodName)
                    else:
                        function[modName] = [methodName]
                    if methodName not in modules[modName]['functions']:
                        modules[modName]['functions'].append(methodName)
                    functionProperties[methodName] = {
                        "args": methodArgs,
                        "module": modName,
                        "calledInModule": []
                    }
        break

    excludeFuncArgs = [
        'pyjsonld'
    ]
    excludeFuncs = [
        'add_new_player',
        'link',
        'set',
        'get'
    ]
    # which modules is each function used within?
    for modName, modProperties in modules.items():
        print('Module: ' + modName + ' ✓')
        for name, properties in functionProperties.items():
            lineCtr = 0
            for line in modules[modName]['lines']:
                lineStr = line.strip()
                if lineStr.startswith('def '):
                    lineCtr += 1
                    continue
                if lineStr.startswith('class '):
                    lineCtr += 1
                    continue
                if name + '(' in line:
                    modList = \
                        functionProperties[name]['calledInModule']
                    if modName not in modList:
                        modList.append(modName)
                    if modName in excludeFuncArgs:
                        lineCtr += 1
                        continue
                    if name in excludeFuncs:
                        lineCtr += 1
                        continue
                    callArgs = \
                        getFunctionCallArgs(name,
                                            modules[modName]['lines'],
                                            lineCtr)
                    if not functionArgsMatch(callArgs,
                                             functionProperties[name]['args']):
                        print('Call to function ' + name +
                              ' does not match its arguments')
                        print('def args: ' +
                              str(len(functionProperties[name]['args'])) +
                              '\n' + str(functionProperties[name]['args']))
                        print('Call args: ' + str(len(callArgs)) + '\n' +
                              str(callArgs))
                        print('module ' + modName + ' line ' + str(lineCtr))
                        assert False
                lineCtr += 1

    # don't check these functions, because they are procedurally called
    exclusions = [
        'familiarIsHidden',
        '_nod',
        '_pose_prone',
        '_stand',
        '_shove',
        '_dodge',
        '_send_command_error',
        '_teleport',
        '_summon',
        '_mute',
        '_unmute',
        '_freeze',
        '_unfreeze',
        '_block',
        '_unblock',
        '_kick',
        '_shutdown',
        '_resetUniverse',
        '_quit',
        '_who',
        '_tell',
        '_whisper',
        '_help',
        '_cast_spell',
        '_affinity',
        '_clear_spells',
        '_spells_list',
        '_sit',
        '_prepare_spell',
        '_speak',
        '_laugh',
        '_thinking',
        '_grimace',
        '_applaud',
        '_wave',
        '_astonished',
        '_confused',
        '_bow',
        '_calm',
        '_cheer',
        '_curious',
        '_curtsey',
        '_frown',
        '_eyebrow',
        '_giggle',
        '_grin',
        '_yawn',
        '_smug',
        '_relieved',
        '_stick',
        '_escape_trap',
        '_begin_attack',
        '_describe',
        '_change_setting',
        '_write_on_item',
        '_check',
        '_wear',
        '_unwear',
        '_wield',
        '_stow',
        '_bio',
        '_eat',
        '_step_over',
        '_jump',
        '_deal',
        '_hand_of_cards',
        '_swap_a_card',
        '_shuffle',
        '_call_card_game',
        '_morris_game',
        '_chess',
        '_graphics',
        '_go_north',
        '_go_south',
        '_go_east',
        '_go_west',
        '_go_up',
        '_go_down',
        '_go_in',
        '_go_out',
        '_dismiss',
        '_conjure',
        '_destroy',
        '_give',
        '_drop',
        '_open_item',
        '_close_item',
        '_pull_lever',
        '_push_lever',
        '_wind_lever',
        '_unwind_lever',
        '_put_item',
        '_take',
        '_taunt',
        '_buy',
        '_sell',
        '_setPlayerCulture',
        '_setPlayerCanGo',
        '_setPlayerCanLook',
        '_setPlayerCanSay',
        '_setPlayerCanAttack',
        '_setPlayerCanDirectMessage',
        '_setPlayerName',
        '_setPlayerPrefix',
        '_setPlayerRoom',
        '_setPlayerLvl',
        '_modPlayerLvl',
        '_setPlayerExp',
        '_modPlayerExp',
        '_setPlayerStr',
        '_modPlayerStr',
        '_setPlayerSiz',
        '_modPlayerSiz',
        '_setPlayerWei',
        '_modPlayerWei',
        '_setPlayerPer',
        '_modPlayerPer',
        '_setPlayerCool',
        '_modPlayerCool',
        '_setPlayerEndu',
        '_modPlayerEndu',
        '_setPlayerCha',
        '_modPlayerCha',
        '_setPlayerInt',
        '_modPlayerInt',
        '_setPlayerAgi',
        '_modPlayerAgi',
        '_setPlayerLuc',
        '_modPlayerLuc',
        '_setPlayerCred',
        '_modPlayerCred',
        '_setPlayerGoldPieces',
        '_modPlayerGoldPieces',
        '_setPlayerSilverPieces',
        '_modPlayerSilverPieces',
        '_setPlayerCopperPieces',
        '_modPlayerCopperPieces',
        '_setPlayerElectrumPieces',
        '_modPlayerElectrumPieces',
        '_setPlayerPlatinumPieces',
        '_modPlayerPlatinumPieces',
        '_setPlayerInv',
        '_setAuthenticated',
        '_setPlayerClo_head',
        '_setPlayerClo_neck',
        '_setPlayerClo_larm',
        '_setPlayerClo_rarm',
        '_setPlayerClo_lhand',
        '_setPlayerClo_rhand',
        '_setPlayerClo_gloves',
        '_setPlayerClo_lfinger',
        '_setPlayerClo_rfinger',
        '_setPlayerClo_lwrist',
        '_setPlayerClo_rwrist',
        '_setPlayerClo_chest',
        '_setPlayerClo_lleg',
        '_setPlayerClo_rleg',
        '_setPlayerClo_feet',
        '_setPlayerImp_head',
        '_setPlayerImp_larm',
        '_setPlayerImp_rarm',
        '_setPlayerImp_lhand',
        '_setPlayerImp_rhand',
        '_setPlayerImp_chest',
        '_setPlayerImp_lleg',
        '_setPlayerImp_rleg',
        '_setPlayerImp_feet',
        '_setPlayerHp',
        '_modPlayerHp',
        '_setPlayerCharge',
        '_modPlayerCharge',
        '_setPlayerIsInCombat',
        '_setPlayerLastCombatAction',
        '_modPlayerLastCombatAction',
        '_setPlayerIsAttackable',
        '_setPlayerLastRoom',
        '_setPlayerCorpseTTL',
        '_modPlayerCorpseTTL',
        '_spawnItem',
        '_spawnNPC',
        '_spawnActor',
        '_health',
        '__run',
        'globaltrace',
        'localtrace',
        'kill',
        'clone',
        'removeDormantThreads',
        '_login_headers',
        '_set_headers_head',
        '_set_headers_etag',
        '_etag_exists',
        '_redirect_headers',
        '_fish',
        '_404',
        '_304',
        '_503',
        '_robotsTxt',
        '_clearLoginDetails',
        'runWebServer',
        'shuffle',
        'deal',
        'straightflush',
        'fourofakind',
        'fullhouse',
        'flush',
        'straight',
        'threeofakind',
        'twopair',
        'onepair',
        'highcard',
        '_profFightingStyleDamage',
        '_profSecondWind',
        '_profIndomitable',
        '_defenseProficiencyItem',
        'weaponProficiency',
        '_copy_list',
        '_copy_dict',
        'levelUp',
        'plotClouds',
        'handleMessage',
        'handleConnected',
        'handleClose',
        'get_next_id',
        'close_sig_handler',
        'run_websocket_server',
        'update',
        'get_new_players',
        'get_disconnected_players',
        'get_commands',
        'player_using_web_interface',
        'send_message_wrap',
        'send_message',
        'send_image',
        'send_game_board',
        'shutdown',
        'add_new_player',
        'receive_message',
        'handle_disconnect',
        'close',
        'sendFragmentStart',
        'sendFragment',
        'sendFragmentEnd',
        'serveonce',
        'serveforever',
        'do_GET',
        'do_POST',
        'do_HEAD'
    ]
    excludeImports = [
        'link',
        'start',
        'get_local_sunrise_time',
        'get_local_sunset_time'
    ]
    excludeLocal = [
        'pyjsonld',
        'daemon',
        'tests'
    ]
    excludeMods = [
        'pyjsonld'
    ]
    # check that functions are called somewhere
    for name, properties in functionProperties.items():
        if name.startswith('__'):
            if name.endswith('__'):
                continue
        if name in exclusions:
            continue
        if properties['module'] in excludeMods:
            continue
        isLocalFunction = False
        if not properties['calledInModule']:
            print('function ' + name +
                  ' in module ' + properties['module'] +
                  ' is not called anywhere')
        assert properties['calledInModule']

        if len(properties['calledInModule']) == 1:
            modName = properties['calledInModule'][0]
            if modName not in excludeLocal and \
               modName == properties['module']:
                isLocalFunction = True
                if not name.startswith('_'):
                    print('Local function ' + name +
                          ' in ' + modName + '.py does not begin with _')
                    assert False

        if name not in excludeImports:
            for modName in properties['calledInModule']:
                if modName == properties['module']:
                    continue
                importStr = 'from ' + properties['module'] + ' import ' + name
                if importStr not in modules[modName]['source']:
                    print(importStr + ' not found in ' + modName + '.py')
                    assert False

        if not isLocalFunction:
            if name.startswith('_'):
                excludePublic = [
                    'pyjsonld',
                    'daemon',
                    'tests'
                ]
                modName = properties['module']
                if modName not in excludePublic:
                    print('Public function ' + name + ' in ' +
                          modName + '.py begins with _')
                    assert False
        print('Function: ' + name + ' ✓')

    print('Constructing function call graph')
    moduleColors = ('red', 'green', 'yellow', 'orange', 'purple', 'cyan',
                    'darkgoldenrod3', 'darkolivegreen1', 'darkorange1',
                    'darkorchid1', 'darkseagreen', 'darkslategray4',
                    'deeppink1', 'deepskyblue1', 'dimgrey', 'gold1',
                    'goldenrod', 'burlywood2', 'bisque1', 'brown1',
                    'chartreuse2', 'cornsilk', 'darksalmon')
    maxModuleCalls = 1
    maxFunctionCalls = 1
    colorCtr = 0
    for modName, modProperties in modules.items():
        lineCtr = 0
        modules[modName]['color'] = moduleColors[colorCtr]
        colorCtr += 1
        if colorCtr >= len(moduleColors):
            colorCtr = 0
        for line in modules[modName]['lines']:
            if line.strip().startswith('def '):
                name = line.split('def ')[1].split('(')[0]
                callsList = \
                    getFunctionCalls(name, modules[modName]['lines'],
                                     lineCtr, functionProperties)
                functionProperties[name]['calls'] = callsList.copy()
                if len(callsList) > maxFunctionCalls:
                    maxFunctionCalls = len(callsList)
                # keep track of which module calls which other module
                for fn in callsList:
                    modCall = functionProperties[fn]['module']
                    if modCall != modName:
                        if modules[modName].get('calls'):
                            if modCall not in modules[modName]['calls']:
                                modules[modName]['calls'].append(modCall)
                                if len(modules[modName]['calls']) > \
                                   maxModuleCalls:
                                    maxModuleCalls = \
                                        len(modules[modName]['calls'])
                        else:
                            modules[modName]['calls'] = [modCall]
            lineCtr += 1
    callGraphStr = 'digraph AberMUSHModules {\n\n'
    callGraphStr += '  graph [fontsize=10 fontname="Verdana" compound=true];\n'
    callGraphStr += '  node [shape=record fontsize=10 fontname="Verdana"];\n\n'
    # colors of modules nodes
    for modName, modProperties in modules.items():
        if not modProperties.get('calls'):
            callGraphStr += '  "' + modName + \
                '" [fillcolor=yellow style=filled];\n'
            continue
        if len(modProperties['calls']) <= int(maxModuleCalls / 8):
            callGraphStr += '  "' + modName + \
                '" [fillcolor=green style=filled];\n'
        elif len(modProperties['calls']) < int(maxModuleCalls / 4):
            callGraphStr += '  "' + modName + \
                '" [fillcolor=orange style=filled];\n'
        else:
            callGraphStr += '  "' + modName + \
                '" [fillcolor=red style=filled];\n'
    callGraphStr += '\n'
    # connections between modules
    for modName, modProperties in modules.items():
        if not modProperties.get('calls'):
            continue
        for modCall in modProperties['calls']:
            callGraphStr += '  "' + modName + '" -> "' + modCall + '";\n'
    # module groups/clusters
    clusterCtr = 1
    for groupName, groupModules in modGroups.items():
        callGraphStr += '\n'
        callGraphStr += \
            '  subgraph cluster_' + str(clusterCtr) + ' {\n'
        callGraphStr += '    node [style=filled];\n'
        for modName in groupModules:
            callGraphStr += '    ' + modName + ';\n'
        callGraphStr += '    label = "' + groupName + '";\n'
        callGraphStr += '    color = blue;\n'
        callGraphStr += '  }\n'
        clusterCtr += 1
    callGraphStr += '\n}\n'
    with open('abermush_modules.dot', 'w+') as fp:
        fp.write(callGraphStr)
        print('Modules call graph saved to abermush_modules.dot')
        print('Plot using: ' +
              'sfdp -x -Goverlap=false -Goverlap_scaling=2 ' +
              '-Gsep=+100 -Tx11 abermush_modules.dot')

    callGraphStr = 'digraph AberMUSH {\n\n'
    callGraphStr += '  size="8,6"; ratio=fill;\n'
    callGraphStr += '  graph [fontsize=10 fontname="Verdana" compound=true];\n'
    callGraphStr += '  node [shape=record fontsize=10 fontname="Verdana"];\n\n'

    for modName, modProperties in modules.items():
        callGraphStr += '  subgraph cluster_' + modName + ' {\n'
        callGraphStr += '    label = "' + modName + '";\n'
        callGraphStr += '    node [style=filled];\n'
        moduleFunctionsStr = ''
        for name in modProperties['functions']:
            if name.startswith('test'):
                continue
            if name not in excludeFuncs:
                if not functionProperties[name]['calls']:
                    moduleFunctionsStr += \
                        '  "' + name + '" [fillcolor=yellow style=filled];\n'
                    continue
                noOfCalls = len(functionProperties[name]['calls'])
                if noOfCalls < int(maxFunctionCalls / 4):
                    moduleFunctionsStr += '  "' + name + \
                        '" [fillcolor=orange style=filled];\n'
                else:
                    moduleFunctionsStr += '  "' + name + \
                        '" [fillcolor=red style=filled];\n'

        if moduleFunctionsStr:
            callGraphStr += moduleFunctionsStr + '\n'
        callGraphStr += '    color=blue;\n'
        callGraphStr += '  }\n\n'

    for name, properties in functionProperties.items():
        if not properties['calls']:
            continue
        noOfCalls = len(properties['calls'])
        if noOfCalls <= int(maxFunctionCalls / 8):
            modColor = 'blue'
        elif noOfCalls < int(maxFunctionCalls / 4):
            modColor = 'green'
        else:
            modColor = 'red'
        for calledFunc in properties['calls']:
            if calledFunc.startswith('test'):
                continue
            if calledFunc not in excludeFuncs:
                callGraphStr += '  "' + name + '" -> "' + calledFunc + \
                    '" [color=' + modColor + '];\n'

    callGraphStr += '\n}\n'
    with open('abermush.dot', 'w+') as fp:
        fp.write(callGraphStr)
        print('Call graph saved to abermush.dot')
        print('Plot using: ' +
              'sfdp -x -Goverlap=prism -Goverlap_scaling=8 ' +
              '-Gsep=+120 -Tx11 abermush.dot')


def _testDuplicateExits():
    print('testDuplicateExits')

    Config = configparser.ConfigParser()
    Config.read('config.ini')
    rooms = {}
    with open(str(Config.get('Rooms', 'Definition')), "r") as read_file:
        rooms = json.loads(read_file.read())

    for roomId, item in rooms.items():
        if not item.get('exits'):
            continue
        ids = []
        for direction, exitRoomId in item['exits'].items():
            if exitRoomId in ids:
                print('Duplicate exit ' +
                      roomId + ' ' + item['name'] + ' ' + direction)
            else:
                ids.append(exitRoomId)


def _testMoneyPurchase() -> None:
    print("testMoneyPurchase")
    id = "me"
    players = {
        id: {
            "cp": 0,
            "sp": 0,
            "ep": 0,
            "gp": 0,
            "pp": 0
        }
    }
    assert money_purchase(id, players, "0gp")
    players[id]["gp"] = 100
    assert money_purchase(id, players, "0gp")
    assert not money_purchase(id, players, "101gp")
    assert money_purchase(id, players, "40gp")
    if players[id]["gp"] != 60:
        print('gp ' + str(players[id]["gp"]))
    assert players[id]["gp"] == 60
    players = {
        id: {
            "cp": 0,
            "sp": 30,
            "ep": 0,
            "gp": 0,
            "pp": 0
        }
    }
    assert money_purchase(id, players, "2gp")
    assert players[id]["sp"] == 10


def run_all_tests():
    print('Running tests...')
    _testFunctions()
    _testDuplicateExits()
    _testMoneyPurchase()
    print('Tests succeeded\n')
