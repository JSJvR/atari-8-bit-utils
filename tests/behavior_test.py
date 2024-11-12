import unittest
import json
from atari_8_bit_utils.behavior import *



i = 0
last = ''
names = []
tree = BehaviorTree()

def simpleAction(name: str) -> Result:
    global last
    global i
    print(name)
    last = name
    i += 1
    names.append(name)
    return Result.FAILURE if name in ['Wait', 'WriteUTF8'] else Result.FAILURE

def leafAction(name: str) -> Action:
    return lambda: simpleAction(name)

def createBehavior(item) -> Behavior:
    if isinstance(item, str):
        return tree.add_leaf(item, leafAction(item))
    if isinstance(item, dict):
        children = list(map(lambda c: createBehavior(c), item['children']))
        if item['type'] == 'Sequence':
            return tree.add_sequence(item['name'], children)
        else:
            return tree.add_selector(item['name'], children)
    else:
        return f'Error: {type(item)} {item}'




class TestBehaviors(unittest.TestCase):

    def setUp(self) -> None:
        self.maxDiff = None
        return super().setUp()
    
    def test_simple(self):

        self.assertEqual(Result.SUCCESS, Result.SUCCESS)

    def test_parse_json(self):
        f = open('src/atari_8_bit_utils/tree.json')
        treestr = json.loads(f.read())
        
        foo = createBehavior(treestr)

        self.assertIsInstance(foo, Selector)
        self.assertEqual(foo.name, 'Root')
        tree.set_root('Root')

        self.assertEqual(tree.behaviors['ForceQuit'].name, 'ForceQuit')

        self.assertEqual(tree.root, foo)

        self.assertEqual(len(tree.behaviors), 18)
        result = tree.tick()
        self.assertEqual(last, 'Wait')
        self.assertEqual(i, 9)
        self.assertEqual(names, [])
        self.assertEqual(result, Result.SUCCESS)
        f.close()