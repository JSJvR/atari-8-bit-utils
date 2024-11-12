import os
import hashlib
import os.path
import re
import json
import subprocess
import textwrap
from enum import Enum
import sys
import time
from collections.abc import Callable
from .atascii import clear_dir
from .atascii import files_to_utf8
from .behavior import ALWAYS, NEVER, Behavior, BehaviorTree, Predicate, Result

state_file = './state.json'

# Global variables
current_config = None
tree = BehaviorTree()

# Config object holding any setting that were overridden for the current run
# These config values will be used in the program logic, but will not be persisted
# to state.json
override_config = {
    'exit_now': False,
    'iterations': 0
} 

stored_state: dict | None = None
current_state: dict | None = None

default_config = {
        'delay': 5,             # Time delay in seconds between executions of the recon loop

        # The next three config values are all related to how many times we should
        # run the recon loop before exiting. They are listed in order of precedence, i.e.
        # 'run_once' overrides the behavior of 'daemon' which override the behavior of
        # 'max_iterations'
        'run_once': False,      # If True, exit when we encounter Action.WAIT for the first time
        'daemon': False,        # In daemon mode we run forever
        'max_iterations': 100,      # The number of iterations of the recon loop to run before exiting
        
        'auto_commit': False    # Flag indicating whether we should commit every time a files changes
    }

def apply_default_config():
    global current_config
    print('\tNo config found in state.json. Using defaults')
    current_config = default_config
    print(textwrap.indent(json.dumps(current_config, indent=4), '\t'))
    print('\tWith overrides:')
    print(textwrap.indent(json.dumps(override_config, indent=4), '\t  '))
    return Result.SUCCESS

def get_config(key: str):
    '''
    Get's the effective config value for the given key. This function
    should only be used in the main business logic and not in any code
    related to loading, saving or defaulting config values in
    in state.json
    ''' 
    config_val = None

    override = override_config.get(key)
    # print(f'\t\tOverride value: {override}')

    if not current_config:
        config_val = None
    elif not override_config.get(key) is None:
        config_val = override
    else:
        config_val = current_config.get(key)

    # print(f'\t\tget_config({key}) --> {config_val}')
    return config_val

def load_state():
    f = open(state_file, mode='r')
    state = json.loads(f.read())
    f.close()
    return state

def apply_config():
    global current_config

    # Merge defaults with values loaded from file
    current_config = default_config | load_state()['config']
    print('\tUsing config:')
    print(textwrap.indent(json.dumps(current_config, indent=4), '\t  '))
    print('\tWith overrides:')
    print(textwrap.indent(json.dumps(override_config, indent=4), '\t  '))
    return Result.SUCCESS

def wait():
    override_config['iterations'] += 1
    delay = get_config('delay')
    print(f'\tSleeping for {delay} seconds')
    time.sleep(delay)
    return Result.SUCCESS

def extract_atr():
    clear_dir('./atascii')
    atr_file = get_current_state()['atr'][0]['name']
    subprocess.run(f'lsatr -X ./atascii ./atr/{atr_file}')
    return Result.SUCCESS

def delete_utf8():
    clear_dir('./utf8')
    return Result.SUCCESS

def write_utf8():
    files_to_utf8('./atascii', './utf8')
    return Result.SUCCESS

def commit():
    subprocess.run('git add ./utf8') 
    subprocess.run('git add ./atascii') 
    subprocess.run('git commit -F ./utf8/COMMIT.MSG')  
    return Result.SUCCESS

def update_state(key, previous: Result = Result.SUCCESS) -> Result: 
    if previous != Result.SUCCESS:
        print(f'\nSkipping state up since step returned {previous}')
        return previous
    
    stored_state = load_state()
    current_state = get_current_state()

    print(f'\tUpdating state[{key}]')
    stored_state[key] = current_state[key]
    save_state(stored_state)
    return Result.SUCCESS

def update(key: str, action: Callable[[], Result]) -> Callable[[], Result]:
    return lambda: update_state(key, action())

def fail(msg: str) -> Result:
    print(msg)
    return Result.FAILURE

def success(msg: str) -> Result:
    print(msg)
    return Result.SUCCESS

predicates: dict[str, Predicate] = {
    'FatalError': lambda: get_config('error'),
    'ForceQuit': lambda: get_config('exit_now'),
    'DefaultConfig': lambda: stored_state.get('config') is None,
    'ApplyConfig': lambda: stored_state['config'] and (not current_config or current_config != stored_state['config']),
    'ExitOnIterations': lambda: not get_config('daemon') and get_config('iterations') >= get_config('max_iterations'),
    'ExtractATR': lambda: (not stored_state['atr']) or (current_state['atr'][0] != stored_state['atr'][0]) or not current_state['atascii'],
    'DeleteUTF8': lambda: (stored_state['atascii'] != current_state['atascii']),
    'AutoCommit': lambda: get_config('auto_commit'),
    'WriteUTF8': lambda: not current_state['utf8'],
    'RunOnceExit': lambda: get_config('run_once'),
    'ConditionalCommit': lambda: current_state.get('commit') and (not stored_state.get('commit') or stored_state['commit'] != current_state['commit'])
}

actions: dict[str, Callable[[], Result]] = {
    'FatalError': lambda: sys.exit('FATAL ERROR: ', get_config('error')),
    'ForceQuit': lambda: sys.exit('\tExiting sync process'),
    'DefaultConfig': update('config', apply_default_config),
    'ApplyConfig': update('config', apply_config),
    'ExitOnIterations': lambda: sys.exit('\tMax iterations reached. Exiting sync process'),
    'ExtractATR': update('atr', extract_atr),
    'DeleteUTF8': update('atascii', delete_utf8),
    'WriteUTF8': update('utf8', write_utf8),
    'PreCommit': lambda: success('PreCommit not yet implemented'),
    'Commit': update('commit', commit),
    'PostCommit': lambda: success('PostCommit not yet implemented'),
    'RunOnceExit': lambda: sys.exit('\tRunOnce complete. Exiting sync process'),
    'Wait': wait
}

def md5checksum(file):
    f = open(file,'rb')
    checksum = hashlib.md5(f.read()).hexdigest()
    f.close()
    return checksum

def scandir(path, output, pattern = '.*'):
    dir = os.scandir(path)
    with dir:
        for entry in dir:
            if not entry.name.startswith('.') and entry.is_file() and not re.search(pattern, entry.name) is None:
                checksum = md5checksum(entry.path)
                output.append({
                    'name': entry.name, 
                    'checksum': checksum
                })
    dir.close()
    output.sort(key=lambda x: x['name'])

def get_current_state():
    state = {
        'config': current_config,
        'atr': list(),
        'atascii': list(),
        'utf8': list()
    }
    
    # ATR
    scandir('./atr', state['atr'], '\\.atr$')
    
    # ATASCII
    scandir('./atascii', state['atascii'])
    
    # UTF-8
    scandir('./utf8', state['utf8'])

    # COMMIT MSG
    commit = './utf8/COMMIT.MSG'
    if os.path.isfile(commit):
        f = open(commit, encoding='utf-8')
        msg = f.read()
        f.close()
        state['commit'] = {
            'msg': msg
        }
    
    return state  

def save_state(state):
    f = open(state_file, mode='w')
    f.write(json.dumps(state, indent=4))
    f.close()

# Runs a single iteration of the reconciliation logic
def recon_tick():
    global stored_state
    global current_state

    stored_state = load_state()
    current_state = get_current_state()

    max_iterations = '?'

    if get_config('run_once'):
        max_iterations = ''
    if get_config('daemon'):
        max_iterations = '∞'
    else:
        max_iterations = get_config('max_iterations')

    print(f'({get_config('iterations')}/{max_iterations})... ', end='')
    tree.tick()

def recon_loop():
    while True:
        try:
            recon_tick()
        except KeyboardInterrupt:
            override_config['iterations'] += 1
            override_config['exit_now'] = True

def createBehavior(item: str | dict) -> Behavior:
    if isinstance(item, str):
        action = actions.get(item)
        if not action:
            print(f'No action found for behavior {item}. Short circuiting')
            predicate = NEVER
        else:
            predicate = predicates.get(item, ALWAYS)
        return tree.add_leaf(item, action, predicate)
    if isinstance(item, dict):
        if item.get('ref'):
            return tree.behaviors.get(item['ref'])
        children = list(map(lambda c: createBehavior(c), item['children']))
        name = item['name']
        predicate = predicates.get(name, ALWAYS)
        if item['type'] == 'Sequence':
            return tree.add_sequence(name, children, predicate)
        elif item['type'] == 'Selector':
            return tree.add_selector(name, children, predicate)
        else:
            return f'Error: {type(item)} {item}'
    else:
        return f'Error: {type(item)} {item}'

def build_tree():
    f = open('tree.json')
    treestr = json.loads(f.read())
        
    root = createBehavior(treestr)   

    tree.set_root(root)     

def init(clobber = False):

    if clobber or not os.path.isfile(state_file):
        state = get_current_state()
        save_state(state)
    else:
        print(f'Skipping initialization. State file "{state_file}" already exists')        

def sync_main(reset: bool = False, once: bool = None, daemon: bool = None):

    init(reset)

    # Apply overrides
    # In order to support overriding flag in both directions, we need to 
    # default to None and only apply the override if the flag is present
    if not once is None:
        override_config['run_once'] = once

    if not daemon is None:
        override_config['daemon'] = daemon
    build_tree()
    recon_loop()

if __name__ == '__main__':
    sync_main()