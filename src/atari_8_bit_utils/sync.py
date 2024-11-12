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
from .behavior import Predicate, Result

state_file = './state.json'

# Global variables
iterations = 0
current_config = None

# Config object holding any setting that were overridden for the current run
# These config values will be used in the program logic, but will not be persisted
# to state.json
override_config = {
    'exit_now': False
} 

stored_state: dict | None = None
current_state: dict | None = None

default_config = {
        'delay': 5,             # Time delay in seconds between executions of the recon loop

        # The next three config values are all related to how many times we should
        # run the recon loop before exiting. They are listed in order of precedence, i.e.
        # 'run_once' overrides the behavior of 'daemon' which override the behavior of
        # 'iterations'
        'run_once': False,      # If True, exit when we encounter Action.WAIT for the first time
        'daemon': False,        # In daemon mode we run forever
        'iterations': 100,      # The number of iterations of the recon loop to run before exiting
        
        'auto_commit': False    # Flag indicating whether we should commit every time a files changes
    }

predicates: dict[str, Predicate] = {
    "ForceQuit": lambda: get_config('exit_now'),
    "DefaultConfig": lambda: stored_state.get('config') is None,
    "ApplyConfig": lambda: stored_state['config'] and (not current_config or current_config != stored_state['config']),
    "ExtractATR": lambda: (not stored_state['atr']) or (current_state['atr'][0] != stored_state['atr'][0]) or not current_state['atascii'],
    "DeleteUTF8": lambda: (stored_state['atascii'] != current_state['atascii']),
    "AutoCommit": lambda: get_config('auto_commit'),
    "WriteUTF8": lambda: not current_state['utf8'],
    "ConditionalCommit": lambda: current_state.get('commit') and (not stored_state.get('commit') or stored_state['commit'] != current_state['commit'])
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
    """
    Get's the effective config value for the given key. This function
    should only be used in the main business logic and not in any code
    related to loading, saving or defaulting config values in
    in state.json
    """ 
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

actions: dict[str, Callable[[], Result]] = {
    'ForceQuit': lambda: sys.exit('\tExiting sync process'),
    'DefaultConfig': apply_default_config,
    'ApplyConfig': apply_config,
    'ExtractATR': extract_atr,
    'DeleteUTF8': delete_utf8,
    'WriteUTF8': write_utf8,
    'Commit': commit,
    'Wait': wait
}

class Action(Enum):
    DEFAULT_CONFIG = 'config', lambda: apply_default_config()
    APPLY_CONFIG = 'config', lambda: apply_config()
    EXTRACT_ATR = 'atr', lambda: extract_atr()
    DELETE_UTF8 = 'atascii', lambda: clear_dir('./utf8')
    WRITE_UTF8 = 'utf8', lambda: files_to_utf8('./atascii', './utf8')
    COMMIT = 'commit', lambda: commit()
    PUSH = 'commit' , lambda: subprocess.run('git push')
    WAIT = None, lambda: wait()
    EXIT = None, lambda: sys.exit("\tExiting sync process")
    ERROR = None, lambda: sys.exit("\tError encountered. Exiting sync process")
    
    def __new__(cls, *args, **kwds):
          value = len(cls.__members__) + 1
          obj = object.__new__(cls)
          obj._value_ = value
          return obj
    
    def __init__(self, key, recon_action):
          self.key = key
          self.recon_action = recon_action

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

def decide_action() -> Action | list[Action]: 
    if get_config('exit_now'):
        return Action.EXIT

    global stored_state
    global current_state
    stored_state = load_state()
    current_state = get_current_state()

    if stored_state.get('config') is None:
        print('\tDefaulting config')
        return Action.DEFAULT_CONFIG

    if stored_state['config'] and (not current_config or current_config != stored_state['config']):
        return Action.APPLY_CONFIG

    if not get_config('daemon') and iterations >= get_config('iterations'):
        return Action.EXIT

    if not current_state['atr']:
        return Action.ERROR
    
    if (not stored_state['atr']) or (current_state['atr'][0] != stored_state['atr'][0]) or not current_state['atascii']:
        return Action.EXTRACT_ATR

    if (stored_state['atascii'] != current_state['atascii']):
        return Action.DELETE_UTF8
    
    if not current_state['utf8']:
        return [Action.WRITE_UTF8, Action.COMMIT] if get_config('auto_commit') else Action.WRITE_UTF8

    if current_state.get('commit') and (not stored_state.get('commit') or stored_state['commit'] != current_state['commit']):
        # Magic commit message that makes us push instead of commit
        if current_state['commit']['msg'].strip(' \t\n\r') == 'PUSH':
            return Action.PUSH
        else:
            return Action.COMMIT

    return Action.WAIT

def update_state(key):
    stored_state = load_state()
    current_state = get_current_state()

    stored_state[key] = current_state[key]
    save_state(stored_state)

# Runs a single iteration of the reconciliation logic
def recon_tick():
    global iterations
    decision = decide_action()

    if get_config('run_once') and decision == Action.WAIT:
        print('Exiting immediately')
        override_config['exit_now'] = True
        return decision

    total_iterations = '?'
    if current_config:
        if get_config('daemon'):
            total_iterations = '∞'
        elif current_config['iterations']:
            total_iterations = current_config['iterations']

    sub_iteration = 0
    is_list = type(decision) is list
    print(f'IsList: {is_list}')
    if is_list:
        actions = decision
    else:
        actions = [decision]

    while actions:
        action = actions.pop(0)
        print(f'({iterations}.{sub_iteration}/{total_iterations}) - Performing {action}... ')
        if not action.recon_action is None:
            action.recon_action()
    
        if not action.key is None:
            update_state(decision.key)

        print("...Done\n")
        sub_iteration =+ 1

    iterations += 1
    
    return decision

def recon_loop():
    while True:
        try:
            recon_tick()
        except KeyboardInterrupt:
            global iterations
            iterations += 1
            override_config['exit_now'] = True

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

    recon_loop()

if __name__ == '__main__':
    sync_main()