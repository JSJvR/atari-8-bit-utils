from collections.abc import Callable
import unittest

from atari_8_bit_utils.behavior import Behavior, BehaviorTree, Result, Selector
from atari_8_bit_utils.tree import atr_tree

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
    return Result.SUCCESS if name in ['Wait', 'WriteUTF8'] else Result.FAILURE


def leafAction(name: str) -> Callable[[], Result]:
    return lambda: simpleAction(name)


def createBehavior(item) -> Behavior:
    if isinstance(item, str):
        return tree.add_leaf(item, leafAction(item))
    if isinstance(item, dict):
        if item.get('ref'):
            return tree.behaviors.get(item['ref'])
        children = list(map(lambda c: createBehavior(c), item['children']))
        name = item['name']
        if item['type'] == 'Sequence':
            return tree.add_sequence(name, children)
        elif item['type'] == 'Selector':
            return tree.add_selector(name, children)
        else:
            return f'Error: {type(item)} {item}'


class TestBehaviors(unittest.TestCase):

    def setUp(self) -> None:
        self.maxDiff = None
        return super().setUp()

    def test_simple(self):

        self.assertEqual(Result.SUCCESS, Result.SUCCESS)

    def test_parse_json(self):

        root = createBehavior(atr_tree)

        self.assertIsInstance(root, Selector)
        self.assertEqual(root.name, 'Root')
        tree.set_root('Root')

        self.assertEqual(tree.behaviors['ForceQuit'].name, 'ForceQuit')

        self.assertEqual(tree.root, root)

        self.assertEqual(len(tree.behaviors), 19)

        result = tree.tick()
        self.assertEqual(last, 'WriteUTF8')
        self.assertEqual(i, 8)
        # self.assertEqual(names, [])
        self.assertEqual(result, Result.SUCCESS)
