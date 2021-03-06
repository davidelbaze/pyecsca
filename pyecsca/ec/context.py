from abc import abstractmethod, ABC
from collections import OrderedDict
from contextvars import ContextVar, Token
from copy import deepcopy
from typing import List, Optional, ContextManager, Any, Tuple

from public import public


@public
class Action(object):
    """An Action."""
    inside: bool

    def __init__(self):
        self.inside = False

    def __enter__(self):
        getcontext().enter_action(self)
        self.inside = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        getcontext().exit_action(self)
        self.inside = False


@public
class Tree(OrderedDict):

    def get_by_key(self, path: List) -> Any:
        """
        Get the value in the tree at a position given by the path.

        :param path: The path to get.
        :return: The value in the tree.
        """
        if len(path) == 0:
            return self
        value = self[path[0]]
        if len(path) == 1:
            return value
        elif isinstance(value, Tree):
            return value.get_by_key(path[1:])
        else:
            raise ValueError

    def get_by_index(self, path: List[int]) -> Tuple[Any, Any]:
        """
        Get the key and value in the tree at a position given by the path of indices
        (the nodes inside a level of a tree are ordered by insertion order).

        :param path: The path to get.
        :return: The key and value.
        """
        if len(path) == 0:
            raise ValueError
        key = list(self.keys())[path[0]]
        value = self[key]
        if len(path) == 1:
            return key, value
        elif isinstance(value, Tree):
            return value.get_by_index(path[1:])
        else:
            raise ValueError

    def repr(self, depth: int = 0) -> str:
        """
        Construct a textual representation of the tree. Useful for visualization and debugging.

        :param depth:
        :return: The resulting textual representation.
        """
        result = ""
        for key, value in self.items():
            if isinstance(value, Tree):
                result += "\t" * depth + str(key) + "\n"
                result += value.repr(depth + 1)
            else:
                result += "\t" * depth + str(key) + ":" + str(value) + "\n"
        return result

    def __repr__(self):
        return self.repr()


@public
class Context(ABC):
    """A context is an object that traces actions which happen. There is always one
    context active, see functions :py:func:`getcontext`, :py:func:`setcontext` and :py:func:`resetcontext`.
    """

    @abstractmethod
    def enter_action(self, action: Action) -> None:
        """
        Enter into an action (i.e. start executing it).

        :param action: The action.
        """
        ...

    @abstractmethod
    def exit_action(self, action: Action) -> None:
        """
        Exit from an action (i.e. stop executing it).

        :param action: The action.
        """
        ...

    def __str__(self):
        return self.__class__.__name__


@public
class NullContext(Context):
    """A context that does not trace any actions."""

    def enter_action(self, action: Action) -> None:
        pass

    def exit_action(self, action: Action) -> None:
        pass


@public
class DefaultContext(Context):
    """A context that traces executions of actions in a tree."""
    actions: Tree
    current: List[Action]

    def enter_action(self, action: Action) -> None:
        self.actions.get_by_key(self.current)[action] = Tree()
        self.current.append(action)

    def exit_action(self, action: Action) -> None:
        if len(self.current) < 1 or self.current[-1] != action:
            raise ValueError
        self.current.pop()

    def __init__(self):
        self.actions = Tree()
        self.current = []

    def __repr__(self):
        return f"{self.__class__.__name__}({self.actions!r}, current={self.current!r})"


_actual_context: ContextVar[Context] = ContextVar("operational_context", default=NullContext())


class _ContextManager(object):
    def __init__(self, new_context):
        self.new_context = deepcopy(new_context)

    def __enter__(self) -> Context:
        self.token = setcontext(self.new_context)
        return self.new_context

    def __exit__(self, t, v, tb):
        resetcontext(self.token)


@public
def getcontext() -> Context:
    """Get the current thread/task context."""
    return _actual_context.get()


@public
def setcontext(ctx: Context) -> Token:
    """
    Set the current thread/task context.

    :param ctx: A context to set.
    :return: A token to restore previous context.
    """
    return _actual_context.set(ctx)


@public
def resetcontext(token: Token):
    """
    Reset the context to a previous value.

    :param token: A token to restore.
    """
    _actual_context.reset(token)


@public
def local(ctx: Optional[Context] = None) -> ContextManager:
    """
    Use a local context.

    :param ctx: If none, current context is copied.
    :return: A context manager.
    """
    if ctx is None:
        ctx = getcontext()
    return _ContextManager(ctx)
