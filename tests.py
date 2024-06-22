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
from functions import language_path


def get_func_call_args(name: str, lines: [], start_line_ctr: int) -> []:
    """Returns the arguments of a function call given lines
    of source code and a starting line number
    """
    args_str = lines[start_line_ctr].split(name + '(')[1]
    if ')' in args_str:
        args_str = args_str.split(')')[0].replace(' ', '').split(',')
        return args_str
    for line_ctr in range(start_line_ctr + 1, len(lines)):
        if ')' not in lines[line_ctr]:
            args_str += lines[line_ctr]
            continue
        args_str += lines[line_ctr].split(')')[0]
        break
    return args_str.replace('\n', '').replace(' ', '').split(',')


def get_func_calls(name: str, lines: [], start_line_ctr: int,
                   function_props: {}) -> []:
    """Returns the functions called by the given one,
    Starting with the given source code at the given line
    """
    calls_functions = []
    function_content_str = ''
    for line_ctr in range(start_line_ctr + 1, len(lines)):
        line_str = lines[line_ctr].strip()
        if line_str.startswith('def '):
            break
        if line_str.startswith('class '):
            break
        function_content_str += lines[line_ctr]
    for func_name, _ in function_props.items():
        if func_name + '(' in function_content_str:
            calls_functions.append(func_name)
    return calls_functions


def function_args_match(call_args: [], funcArgs: []) -> bool:
    """Do the function artuments match the function call arguments
    """
    if len(call_args) == len(funcArgs):
        return True

    # count non-optional arguments
    call_args_ctr = 0
    for aval in call_args:
        if aval == 'self':
            continue
        if '=' not in aval or aval.startswith("'"):
            call_args_ctr += 1

    func_args_ctr = 0
    for aval in funcArgs:
        if aval == 'self':
            continue
        if '=' not in aval or aval.startswith("'"):
            func_args_ctr += 1

    return call_args_ctr >= func_args_ctr


def _test_functions() -> None:
    print('testFunctions')
    function = {}
    function_props = {}
    modules = {}
    mod_groups = {}

    for _, _, files in os.walk('.'):
        for source_file in files:
            if not source_file.endswith('.py'):
                continue
            mod_name = source_file.replace('.py', '')
            modules[mod_name] = {
                'functions': []
            }
            source_str = ''
            with open(source_file, "r", encoding='utf-8') as fp_src:
                source_str = fp_src.read()
                modules[mod_name]['source'] = source_str
            with open(source_file, "r", encoding='utf-8') as fp_src:
                lines = fp_src.readlines()
                modules[mod_name]['lines'] = lines
                for line in lines:
                    if '__module_group__' in line:
                        if '=' in line:
                            group_name = line.split('=')[1].strip()
                            group_name = group_name.replace('"', '')
                            group_name = group_name.replace("'", '')
                            modules[mod_name]['group'] = group_name
                            if not mod_groups.get(group_name):
                                mod_groups[group_name] = [mod_name]
                            else:
                                if mod_name not in mod_groups[group_name]:
                                    mod_groups[group_name].append(mod_name)
                    if not line.strip().startswith('def '):
                        continue
                    method_name = line.split('def ', 1)[1].split('(')[0]
                    method_args = \
                        source_str.split('def ' + method_name + '(')[1]
                    method_args = method_args.split(')')[0]
                    method_args = method_args.replace(' ', '').split(',')
                    if function.get(mod_name):
                        function[mod_name].append(method_name)
                    else:
                        function[mod_name] = [method_name]
                    if method_name not in modules[mod_name]['functions']:
                        modules[mod_name]['functions'].append(method_name)
                    function_props[method_name] = {
                        "args": method_args,
                        "module": mod_name,
                        "calledInModule": []
                    }
        break

    exclude_func_args = [
        'pyjsonld'
    ]
    exclude_funcs = [
        'add_new_player',
        'link',
        'set',
        'get'
    ]
    # which modules is each function used within?
    for mod_name, mod_properties in modules.items():
        print('Module: ' + mod_name + ' ✓')
        for name, properties in function_props.items():
            line_ctr = 0
            for line in modules[mod_name]['lines']:
                line_str = line.strip()
                if line_str.startswith('def '):
                    line_ctr += 1
                    continue
                if line_str.startswith('class '):
                    line_ctr += 1
                    continue
                if name + '(' in line:
                    mod_list = \
                        function_props[name]['calledInModule']
                    if mod_name not in mod_list:
                        mod_list.append(mod_name)
                    if mod_name in exclude_func_args:
                        line_ctr += 1
                        continue
                    if name in exclude_funcs:
                        line_ctr += 1
                        continue
                    call_args = \
                        get_func_call_args(name,
                                           modules[mod_name]['lines'],
                                           line_ctr)
                    if not function_args_match(call_args,
                                               function_props[name]['args']):
                        print('Call to function ' + name +
                              ' does not match its arguments')
                        print('def args: ' +
                              str(len(function_props[name]['args'])) +
                              '\n' + str(function_props[name]['args']))
                        print('Call args: ' + str(len(call_args)) + '\n' +
                              str(call_args))
                        print('module ' + mod_name + ' line ' + str(line_ctr))
                        assert False
                line_ctr += 1

    # don't check these functions, because they are procedurally called
    exclusions = [
        'familiar_is_hidden',
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
        '_player_affinity',
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
        '_describe_thing',
        '_change_setting',
        '_write_on_item',
        '_check',
        '_wear',
        '_unwear',
        '_wield',
        '_stow',
        '_bio',
        '_eat',
        '_trip',
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
        '_item_give',
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
        '_item_sell',
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
        '_start_fishing',
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
        '_prof_fighting_style_damage',
        '_prof_second_wind',
        '_prof_indomitable',
        '_defense_proficiency_item',
        'weaponProficiency',
        '_copy_list',
        '_copy_dict',
        'levelUp',
        'plot_clouds',
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
        'do_HEAD',
        '_begin_throw_attack',
        '_punch'
    ]
    exclude_imports = [
        'link',
        'start',
        'get_local_sunrise_time',
        'get_local_sunset_time'
    ]
    exclude_local = [
        'pyjsonld',
        'daemon',
        'tests'
    ]
    exclude_mods = [
        'pyjsonld'
    ]
    # check that functions are called somewhere
    for name, properties in function_props.items():
        if name.startswith('__'):
            if name.endswith('__'):
                continue
        if name in exclusions:
            continue
        if properties['module'] in exclude_mods:
            continue
        is_local_function = False
        if not properties['calledInModule']:
            print('function ' + name +
                  ' in module ' + properties['module'] +
                  ' is not called anywhere')
        assert properties['calledInModule']

        if len(properties['calledInModule']) == 1:
            mod_name = properties['calledInModule'][0]
            if mod_name not in exclude_local and \
               mod_name == properties['module']:
                is_local_function = True
                if not name.startswith('_'):
                    print('Local function ' + name +
                          ' in ' + mod_name + '.py does not begin with _')
                    assert False

        if name not in exclude_imports:
            for mod_name in properties['calledInModule']:
                if mod_name == properties['module']:
                    continue
                import_str = 'from ' + properties['module'] + ' import ' + name
                if import_str not in modules[mod_name]['source']:
                    print(import_str + ' not found in ' + mod_name + '.py')
                    assert False

        if not is_local_function:
            if name.startswith('_'):
                exclude_public = [
                    'pyjsonld',
                    'daemon',
                    'tests'
                ]
                mod_name = properties['module']
                if mod_name not in exclude_public:
                    print('Public function ' + name + ' in ' +
                          mod_name + '.py begins with _')
                    assert False
        print('Function: ' + name + ' ✓')

    print('Constructing function call graph')
    module_colors = (
        'red', 'green', 'yellow', 'orange', 'purple', 'cyan',
        'darkgoldenrod3', 'darkolivegreen1', 'darkorange1',
        'darkorchid1', 'darkseagreen', 'darkslategray4',
        'deeppink1', 'deepskyblue1', 'dimgrey', 'gold1',
        'goldenrod', 'burlywood2', 'bisque1', 'brown1',
        'chartreuse2', 'cornsilk', 'darksalmon'
    )
    max_module_calls = 1
    max_function_calls = 1
    color_ctr = 0
    for mod_name, mod_properties in modules.items():
        line_ctr = 0
        modules[mod_name]['color'] = module_colors[color_ctr]
        color_ctr += 1
        if color_ctr >= len(module_colors):
            color_ctr = 0
        for line in modules[mod_name]['lines']:
            if line.strip().startswith('def '):
                name = line.split('def ')[1].split('(')[0]
                calls_list = \
                    get_func_calls(name, modules[mod_name]['lines'],
                                   line_ctr, function_props)
                function_props[name]['calls'] = calls_list.copy()
                if len(calls_list) > max_function_calls:
                    max_function_calls = len(calls_list)
                # keep track of which module calls which other module
                for func in calls_list:
                    mod_call = function_props[func]['module']
                    if mod_call != mod_name:
                        if modules[mod_name].get('calls'):
                            if mod_call not in modules[mod_name]['calls']:
                                modules[mod_name]['calls'].append(mod_call)
                                if len(modules[mod_name]['calls']) > \
                                   max_module_calls:
                                    max_module_calls = \
                                        len(modules[mod_name]['calls'])
                        else:
                            modules[mod_name]['calls'] = [mod_call]
            line_ctr += 1
    call_graph_str = 'digraph AberMUSHModules {\n\n'
    call_graph_str += \
        '  graph [fontsize=10 fontname="Verdana" compound=true];\n'
    call_graph_str += \
        '  node [shape=record fontsize=10 fontname="Verdana"];\n\n'
    # colors of modules nodes
    for mod_name, mod_properties in modules.items():
        if not mod_properties.get('calls'):
            call_graph_str += '  "' + mod_name + \
                '" [fillcolor=yellow style=filled];\n'
            continue
        if len(mod_properties['calls']) <= int(max_module_calls / 8):
            call_graph_str += '  "' + mod_name + \
                '" [fillcolor=green style=filled];\n'
        elif len(mod_properties['calls']) < int(max_module_calls / 4):
            call_graph_str += '  "' + mod_name + \
                '" [fillcolor=orange style=filled];\n'
        else:
            call_graph_str += '  "' + mod_name + \
                '" [fillcolor=red style=filled];\n'
    call_graph_str += '\n'
    # connections between modules
    for mod_name, mod_properties in modules.items():
        if not mod_properties.get('calls'):
            continue
        for mod_call in mod_properties['calls']:
            call_graph_str += '  "' + mod_name + '" -> "' + mod_call + '";\n'
    # module groups/clusters
    cluster_ctr = 1
    for group_name, group_modules in mod_groups.items():
        call_graph_str += '\n'
        call_graph_str += \
            '  subgraph cluster_' + str(cluster_ctr) + ' {\n'
        call_graph_str += '    node [style=filled];\n'
        for mod_name in group_modules:
            call_graph_str += '    ' + mod_name + ';\n'
        call_graph_str += '    label = "' + group_name + '";\n'
        call_graph_str += '    color = blue;\n'
        call_graph_str += '  }\n'
        cluster_ctr += 1
    call_graph_str += '\n}\n'
    with open('abermush_modules.dot', 'w+', encoding='utf-8') as fp_call:
        fp_call.write(call_graph_str)
        print('Modules call graph saved to abermush_modules.dot')
        print('Plot using: ' +
              'sfdp -x -Goverlap=false -Goverlap_scaling=2 ' +
              '-Gsep=+100 -Tx11 abermush_modules.dot')

    call_graph_str = 'digraph AberMUSH {\n\n'
    call_graph_str += '  size="8,6"; ratio=fill;\n'
    call_graph_str += \
        '  graph [fontsize=10 fontname="Verdana" compound=true];\n'
    call_graph_str += \
        '  node [shape=record fontsize=10 fontname="Verdana"];\n\n'

    for mod_name, mod_properties in modules.items():
        call_graph_str += '  subgraph cluster_' + mod_name + ' {\n'
        call_graph_str += '    label = "' + mod_name + '";\n'
        call_graph_str += '    node [style=filled];\n'
        module_functions_str = ''
        for name in mod_properties['functions']:
            if name.startswith('test'):
                continue
            if name not in exclude_funcs:
                if not function_props[name]['calls']:
                    module_functions_str += \
                        '  "' + name + '" [fillcolor=yellow style=filled];\n'
                    continue
                no_of_calls = len(function_props[name]['calls'])
                if no_of_calls < int(max_function_calls / 4):
                    module_functions_str += '  "' + name + \
                        '" [fillcolor=orange style=filled];\n'
                else:
                    module_functions_str += '  "' + name + \
                        '" [fillcolor=red style=filled];\n'

        if module_functions_str:
            call_graph_str += module_functions_str + '\n'
        call_graph_str += '    color=blue;\n'
        call_graph_str += '  }\n\n'

    for name, properties in function_props.items():
        if not properties['calls']:
            continue
        no_of_calls = len(properties['calls'])
        if no_of_calls <= int(max_function_calls / 8):
            mod_color = 'blue'
        elif no_of_calls < int(max_function_calls / 4):
            mod_color = 'green'
        else:
            mod_color = 'red'
        for called_func in properties['calls']:
            if called_func.startswith('test'):
                continue
            if called_func not in exclude_funcs:
                call_graph_str += '  "' + name + '" -> "' + called_func + \
                    '" [color=' + mod_color + '];\n'

    call_graph_str += '\n}\n'
    with open('abermush.dot', 'w+', encoding='utf-8') as fp_call:
        fp_call.write(call_graph_str)
        print('Call graph saved to abermush.dot')
        print('Plot using: ' +
              'sfdp -x -Goverlap=prism -Goverlap_scaling=8 ' +
              '-Gsep=+120 -Tx11 abermush.dot')


def _test_duplicate_exits():
    print('testDuplicateExits')

    Config = configparser.ConfigParser()
    Config.read('config.ini')
    rooms = {}
    with open(str(Config.get('Rooms', 'Definition')), "r",
              encoding='utf-8') as read_file:
        rooms = json.loads(read_file.read())

    for room_id, item in rooms.items():
        if not item.get('exits'):
            continue
        ids = []
        for direction, exit_room_id in item['exits'].items():
            if exit_room_id in ids:
                print('Duplicate exit ' +
                      room_id + ' ' + item['name'] + ' ' + direction)
            else:
                ids.append(exit_room_id)


def _test_purchase_with_money() -> None:
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


def _test_language_path2() -> None:
    print('language path')
    filename = '/some/filename.json'
    new_filename = language_path(filename, 'de', False)
    if new_filename != '/some/de/filename.json':
        print('filename: ' + new_filename)
    assert new_filename == '/some/de/filename.json'

    filename = 'filename.json'
    new_filename = language_path(filename, 'de', False)
    assert new_filename == '/de/filename.json'

    new_filename = language_path(filename, None, False)
    print('new_filename: ' + str(new_filename))
    assert new_filename == filename


def run_all_tests():
    print('Running tests...')
    _test_language_path2()
    _test_functions()
    _test_duplicate_exits()
    _test_purchase_with_money()
    print('Tests succeeded\n')
