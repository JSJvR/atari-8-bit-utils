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
from .atascii import clear_dir
from .atascii import files_to_utf8

state_file = './state.json'

# Global variables
iterations = 0
current_config = None
default_cofig = {
        'delay': 5,
        'daemon': False,
        'iterations': 100
    }

exit_now = False
daemon_override = False

def get_default_config():
    global current_config
    print('\tNo config found in state.json. Using defaults')
    current_config = default_cofig
    print(textwrap.indent(json.dumps(current_config, indent=4), '\t'))

def load_state():
    f = open(state_file, mode='r')
    state = json.loads(f.read())
    f.close()
    return state

def apply_config():
    global current_config

    # Merge defaults with values loaded from file
    current_config = default_cofig | load_state()['config']
    print('\tUsing config:')
    print(textwrap.indent(json.dumps(current_config, indent=4), '\t  '))

def wait():
    delay = current_config['delay']
    print(f'\tSleeping for {delay} seconds')
    time.sleep(delay)


class Action(Enum):
    DEFAULT_CONFIG = 'config', lambda: get_default_config()
    APPLY_CONFIG = 'config', lambda: apply_config()
    EXTRACT_ATR = 'atr', lambda: extract_atr()
    DELETE_UTF8 = 'atascii', lambda: clear_dir('./utf8')
    WRITE_UTF8 = 'utf8', lambda: files_to_utf8('./atascii', './utf8')
    COMMIT = 'commit', lambda: commit()
    PUSH = 'commit' , lambda: subprocess.run('git push')
    WAIT = None, lambda: wait()
    EXIT = None, lambda: sys.exit("\tExiting sync process")
    ERROR = None, lambda: sys.exit("\tError encounted. Exiting sync process")
    
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

def extract_atr():
    clear_dir('./atascii')
    atr_file = get_current_state()['atr'][0]['name']
    subprocess.run(f'lsatr -X ./atascii ./atr/{atr_file}')

def commit():
    subprocess.run('git add ./utf8') 
    subprocess.run('git add ./atascii') 
    subprocess.run('git commit -F ./utf8/COMMIT.MSG')    

def save_state(state):
    f = open(state_file, mode='w')
    f.write(json.dumps(state, indent=4))
    f.close()

def decide_action(): 
    if exit_now:
        return Action.EXIT

    stored_state = load_state()
    current_state = get_current_state()

    if stored_state.get('config') is None:
        print('\tDefaulting config')
        return Action.DEFAULT_CONFIG

    if stored_state['config'] and (not current_config or current_config != stored_state['config']):
        return Action.APPLY_CONFIG

    if not (current_config['daemon'] or daemon_override) and iterations >= current_config['iterations']:
        return Action.EXIT

    if not current_state['atr']:
        return Action.ERROR
    
    if (not stored_state['atr']) or current_state['atr'][0] != stored_state['atr'][0]:
        return Action.EXTRACT_ATR
    
    if not current_state['atascii']:
        return Action.EXTRACT_ATR

    if (stored_state['atascii'] != current_state['atascii']):
        return Action.DELETE_UTF8
    
    if not current_state['utf8']:
        return Action.WRITE_UTF8

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
def recon_tick(once: bool):
    global iterations
    global exit_now
    action = decide_action()

    if once and action == Action.WAIT:
        exit_now = True
        return action

    total_iterations = '?'
    if current_config:
        if daemon_override or current_config['daemon']:
            total_iterations = '∞'
        elif current_config['iterations']:
            total_iterations = current_config['iterations']

    print(f'({iterations}/{total_iterations}) - Performing {action}... ')

    if not action.recon_action is None:
        action.recon_action()
    
    if not action.key is None:
        update_state(action.key)

    print("...Done\n")

    iterations += 1
    return action

def recon_loop(once: bool):
    global exit_now
    while True:
        try:
            recon_tick(once)
        except KeyboardInterrupt:
            global iterations
            iterations += 1
            exit_now = True

def init(clobber = False):

    if clobber or not os.path.isfile(state_file):
        state = get_current_state()
        save_state(state)
    else:
        print(f'Skipping initialization. State file "{state_file}" already exists')        

def sync_main(once: bool = False, reset: bool = False, daemon: bool = False):
    global daemon_override
    daemon_override = daemon
    init(reset)
    recon_loop(once)

if __name__ == '__main__':
    sync_main()