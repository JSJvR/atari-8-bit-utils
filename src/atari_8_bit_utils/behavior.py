from __future__ import annotations
from enum import Enum
from collections.abc import Callable
# from typing import TypeAlias


class Result(Enum):
    SUCCESS = 1
    FAILURE = 2


ALWAYS: Callable[[], bool] = lambda: True
NEVER: Callable[[], bool] = lambda: False


class Behavior:
    def should_run(self) -> bool:
        return self.predicate()

    def apply(self) -> Result:
        return Result.FAILURE

    def __init__(self, name: str, predicate: Callable[[], bool] = NEVER) -> None:
        self.name: str = name
        self.predicate: Callable[[], bool] = predicate


class Leaf(Behavior):
    def __init__(self, action: Callable[[], Result], **kwds) -> None:
        self.action: Callable[[], Result] = action
        super().__init__(**kwds)

    def apply(self) -> Result:
        result = self.action()
        # print(f'Callable[[], Result] {self.name} done with result {result}')
        return result


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

        # print(f'Sequence: {self.name} -> {result}')
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
            # print(f'Selector {self.name}: {action.name} -> {action.should_run()}')
            if action.should_run():
                result = action.apply()

        # print(f'Selector: {self.name} -> {result}')
        return result


class BehaviorTree:

    def __init__(self) -> None:
        self.behaviors: dict[str, Behavior] = {}
        self.root: Behavior = None
        pass

    def add_leaf(self, name: str, action: Callable[[], Result], predicate: Callable[[], bool] = ALWAYS) -> Behavior:
        leaf = Leaf(name=name, action=action, predicate=predicate)
        self.behaviors[name] = leaf
        return leaf

    def add_sequence(self, name: str, children: list[str | Behavior], predicate: Callable[[], bool] = lambda: True) -> Behavior:
        seq = Sequence(name=name, behaviors=children, predicate=predicate)
        self.behaviors[name] = seq
        return seq

    def add_selector(self, name: str, children: list[str], predicate: Callable[[], bool] = lambda: True) -> Behavior:
        sel = Selector(name=name, behaviors=children, predicate=predicate)
        self.behaviors[name] = sel
        return sel

    def set_root(self, root: str):
        self.root = root if isinstance(
            root, Behavior) else self.behaviors.get(root)

    def tick(self) -> Result:
        return self.root.apply() if self.root.should_run() else Result.FAILURE
