import json
from enum import Enum
from collections.abc import Callable

class Result(Enum):
    SUCCESS = 1
    FAILURE = 2

type Predicate =  Callable[[], bool]
type Action = Callable[[], Result]

ALWAYS: Predicate = lambda: True
NEVER: Predicate = lambda: False

class Behavior:
    def should_run(self) -> bool:
        return self.predicate()
    
    def apply(self) -> Result:
        return Result.FAILURE
    
    def __init__(self, name: str, predicate: Predicate = NEVER) -> None:
        self.name: str = name
        self.predicate: Predicate = predicate
    
class Leaf(Behavior):
    def __init__(self, action: Action, **kwds) -> None:
        self.action: Action = action
        super().__init__(**kwds)    

    def apply(self) -> Result:
        return self.action()

class Sequence(Behavior):

    def __init__(self, behaviors: list[Behavior], **kwds) -> None:
        self.behaviors: list[Behavior] = behaviors
        super().__init__(**kwds)

    def apply(self) -> Result:
        todo = self.behaviors.copy()

        result = Result.SUCCESS
        while todo and result == Result.SUCCESS:
            action = todo.pop(0)
            result = action.apply() if action.should_run() else Result.FAILURE

        print(f'Sequence: {self.name} -> {result}')
        return result

class Selector(Behavior):

    def __init__(self, behaviors: list[Behavior], **kwds) -> None:
        self.behaviors: list[Behavior] = behaviors
        super().__init__(**kwds)

    def apply(self) -> Result:
        todo = self.behaviors.copy()

        result: Result = Result.FAILURE

        while todo and result == Result.FAILURE:
            action = todo.pop(0)
            if action.should_run():
                result = action.apply()

        print(f'Selector: {self.name} -> {result}')
        return result
    
class BehaviorTree:

    def __init__(self) -> None:
        self.behaviors: dict[str, Behavior] = {}
        self.root: Behavior = None
        pass

    def add_leaf(self, name: str, action: Action, predicate: Predicate = ALWAYS) -> Behavior:
        leaf = Leaf(name=name, action=action, predicate=predicate)
        self.behaviors[name] = leaf
        return leaf

    def add_sequence(self, name: str, children: list[str|Behavior], predicate: Predicate = lambda: True) -> Behavior:
        #seq = Sequence(name=name, behaviors=list(map(lambda b: b if b is Behavior else self.behaviors.get(b), children)), predicate=predicate)
        seq = Sequence(name=name, behaviors=children, predicate=predicate)
        self.behaviors[name] = seq
        return seq

    def add_selector(self, name: str, children: list[str], predicate: Predicate = lambda: True) -> Behavior:
        # sel = Selector(name=name, behaviors=list(map(lambda b: b if b is Behavior else self.behaviors.get(b), children)), predicate=predicate)
        sel = Selector(name=name, behaviors=children, predicate=predicate)
        self.behaviors[name] = sel
        return sel

    def set_root(self, root: str):
        self.root = root if root is Behavior else self.behaviors.get(root)

    def tick(self) -> Result:
        return self.root.apply() if self.root.should_run() else Result.FAILURE

i = 0
last = ''
names = []
tree = BehaviorTree()

def simpleAction(name: str) -> Result:
    global last
    global i
    last = name
    i += 1
    names.append(name)
    result = Result.SUCCESS if name in ['Wait', 'PreCommit', "Commit"] else Result.FAILURE

    print(f'Leaf: {name} --> {result}')
    return result

def leafAction(name: str) -> Action:
    return lambda: simpleAction(name)

def createBehavior(item) -> Behavior:
    if isinstance(item, str):
        return tree.add_leaf(item, leafAction(item))
    if isinstance(item, dict):
        if item.get('ref'):
            return tree.behaviors.get(item['ref'])
        children = list(map(lambda c: createBehavior(c), item['children']))
        if item['type'] == 'Sequence':
            return tree.add_sequence(item['name'], children)
        else:
            return tree.add_selector(item['name'], children)
    else:
        return f'Error: {type(item)} {item}'
    

def _test():
    f = open('src/atari_8_bit_utils/tree.json')
    treestr = json.loads(f.read())
        
    foo = createBehavior(treestr)   
    print(foo)

    tree.set_root('Root')     
    result = tree.tick()    
    print(result)

if __name__ == '__main__':
    _test()    