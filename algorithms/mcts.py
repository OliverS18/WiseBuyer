"""
This file implements the Monte Carlo Tree Search (MCTS) for optimal strategy search.

The MCTS algorithms here is implemented based on junxiaosong's script
(https://github.com/junxiaosong/AlphaZero_Gomoku/blob/master/mcts_pure.py)
and tobegit3hub's implementation
(https://github.com/tobegit3hub/ml_implementation/blob/master/monte_carlo_tree_search/mcst_example.py)
Much thanks to the authors.
"""


import math
import copy
import random
import tqdm
from typing import *

from oi.config import cfg


random.seed(20191129)


class TreeNode:
    """
    A node in the MCTS tree. Each node keeps track of its own value Q, its visit-count score u, its available searching
    space and cost w.r.t them, its cumulative value v and the terminate condition.

    Throughout the class definition, `action` means the commodity to purchase.
    """

    def __init__(self, parent=None, action=None, available_actions=None, cost=None, limit=None, prehistory=None):
        """
        Instantiate an object.

        :param parent: parent node
        :param action: Optional, set to simplify initialization arguments. Specify the action which let the parent node
            transit to current node
        :param available_actions: a map from actions to counts remaining. Note that it should contain a `*STOP*` term
        :param cost: a map from actions to their cost respectively
        :param limit: a termination condition where the MCST reaches its leaf node when the cumulative cost in the path
            exceeds such limit
        :param prehistory: a list containing the history before the root node. used in beam search version
        """

        # structure information
        self._action = action

        self._parent = parent
        self._children = dict()                 # a map from action to TreeNode

        # check validation
        if self.is_root():
            assert action is None
        else:
            assert prehistory is None

        # state information
        self._Q = 0
        self._u = 0
        self.n_visits = 0

        # temps passed to properties
        self._prehistory = prehistory
        self._cost = cost
        self._limit = limit or math.inf
        self._available_actions = available_actions
        self._num_actions = None

        # api for functions
        self.eval = None if self.is_root() else self._parent.eval
        self.refresh_cost = None if self.is_root() else self._parent.refresh_cost
        self.refresh_limit = None if self.is_root() else self._parent.refresh_limit
        self.refresh_v = None if self.is_root() else self._parent.refresh_v
        self.refresh_available = None if self.is_root() else self._parent.refresh_available

        self.arg_count = {'eval':               1,
                          'refresh_cost':       2,
                          'refresh_limit':      2,
                          'refresh_v':          2,
                          'refresh_available':  2}

    @property
    def children(self):
        """
        Return a list of children nodes.
        """

        return self._children.values()

    @property
    def available_actions(self):
        """
        Return a map from the currently available actions to their remaining counts.
        """

        if self._action == '*STOP*':
            return {}

        if self._available_actions is not None:
            assert '*STOP*' in self._available_actions
            return self._available_actions
        else:
            return self._refresh_available()

    @property
    def terminate_limit(self):
        """
        Return the terminate condition beyond which the simulation will terminated.
        """

        return min(self._limit, self._refresh_limit()) if not self.is_root() else self._limit

    @property
    def cost(self):
        """
        Return the cost dictionary of each action.
        """

        return self._cost if self._cost is not None else self._refresh_cost()

    @property
    def history(self):
        """
        Return the history of actions (states) along the searching path.
        """

        if self.is_root():
            return self._prehistory or list()
        else:
            return self._parent.history + [self._action]

    @property
    def v(self):
        """
        Return the cumulative cost along the searching path.
        """

        return 0 if self.is_root() else self._refresh_v()

    @property
    def uct(self):
        """
        Calculate and return the reward (UCT) for this node.
        It is a combination of leaf evaluations Q, and this node's prior adjusted for its visit count, u.
        """

        return self._Q + self._u

    @property
    def score(self):
        """
        Return the reward acquired before current node.
        """

        assert hasattr(self.eval, '__call__') and self.eval.__call__.__code__.co_argcount == 2
        return self.eval(self._parent)

    def register(self, func_name, func):
        """
        Register a function as self's method.

        :param func_name: name of the method to be overwrite
        :param func: a handle of a func
        """

        assert func_name in self.arg_count
        assert hasattr(func, '__call__') and func.__call__.__code__.co_argcount == self.arg_count[func_name] + 1

        setattr(self, func_name, func)

    def reset(self):
        """
        Reset the status as a newly expanded node.
        """

        self._children = dict()
        self._Q = 0
        self._u = 0
        self.n_visits = 0

    def as_root(self):
        """
        Reset the parents node as None so the current node will be treated as a root node in beam search steps.
        """

        self._available_actions = self.available_actions
        self._prehistory = self.history
        self._cost = self.cost
        self._limit = self.terminate_limit

        self._parent = None

    def expand(self):
        """
        Expand tree by creating new children.

        :return: next new node
        """

        if not self.is_terminated():
            space = self.available_actions.keys() - self._children.keys()

            if cfg.algorithm.stable == 'True':
                action = random.choice(sorted(space))
            else:
                assert cfg.algorithm.stable == 'False', \
                    '\033[31mUnrecognized configuration \033[31;1m{}\033[0;31m for algorithm.stable.\033[0m'\
                    .format(cfg.algorithm.stable)
                action = random.choice(list(space))

            self._children[action] = self.__class__(self, action)
            return self._children[action]

    def select(self):
        """
        Select action among children that gives maximum action value Q plus bonus u.

        :return: next best node according to uct
        """

        if cfg.algorithm.stable == 'True':
            candidates = [self._children[_action] for _action in sorted(self._children)]
        else:
            assert cfg.algorithm.stable == 'False', \
                '\033[31mUnrecognized configuration \033[31;1m{}\033[0;31m for algorithm.stable.\033[0m' \
                .format(cfg.algorithm.stable)
            candidates = list(self._children.values())

        random.shuffle(candidates)

        return max(candidates, key=lambda act_node: act_node.uct)

    def update(self, leaf_reward, c_puct=math.sqrt(2.4)):
        """
        Update node values from leaf evaluation.

        :param leaf_reward: the reward of subtree evaluation.
        :param c_puct: a number in (0, inf) controlling the relative impact of value Q on this node's score.
        """

        # Update Q
        self._Q = (self._Q * self.n_visits + leaf_reward) / (self.n_visits + 1)

        # Count visit.
        self.n_visits += 1

        # Update u
        self._u = 0 if self.is_root() else c_puct * math.sqrt(2 * math.log(self._parent.n_visits + 1) / self.n_visits)

    def update_all(self, leaf_reward=None):
        """
        Like a call to update(), but applied recursively for all ancestors.

        :param leaf_reward: the reward of subtree evaluation.
        """

        # calculate the leaf_reward
        leaf_reward = leaf_reward or self.score

        # If it is not root, this node's parent should be updated first.
        if self._parent is not None:
            self._parent.update_all(leaf_reward)

        self.update(leaf_reward)

    def is_root(self):
        """
        Check if root node (i.e. no parents).
        """

        return self._parent is None

    def is_leaf(self):
        """
        Check if leaf node (i.e. no children).
        """

        return len(self._children) == 0

    def is_fully_expanded(self):
        """
        Check if fully expanded (i.e. number of children equals to number of actions available).
        """

        if self._num_actions is None:
            self._num_actions = len(self.available_actions)

        return len(self._children) == self._num_actions

    def is_terminated(self):
        """
        Check if the simulation has finished (i.e. total cost sum has exceeded the limit or all actions adopted).
        """

        return self.available_actions == {} or self.v > self.terminate_limit or self._action == '*STOP*'

    def _refresh_cost(self):
        """
        This function should define the rule to update the cost of each commodity. By default there is no specific rule.

        :return: updated cost of each commodity
        """

        if self.refresh_cost is None:
            return self._parent.cost
        else:
            assert hasattr(self.refresh_cost, '__call__') and self.refresh_cost.__call__.__code__.co_argcount == 3
            return self.refresh_cost(self._parent, self._action)

    def _refresh_limit(self):
        """
        This function should define the rule to update the termination condition. By default there is no specific rule.

        :return: updated termination condition
        """

        if self.refresh_limit is None:
            return self._parent.terminate_limit
        else:
            assert hasattr(self.refresh_cost, '__call__') and self.refresh_cost.__call__.__code__.co_argcount == 3
            return self.refresh_limit(self._parent, self._action)

    def _refresh_v(self):
        """
        This function should define the rule to update the cumulative cost value. By default there is no specific rule.

        :return: updated cumulative cost value
        """

        if self.refresh_v is None:
            return self._parent.v + self.cost[self._action]
        else:
            assert hasattr(self.refresh_v, '__call__') and self.refresh_v.__call__.__code__.co_argcount == 3
            return self.refresh_v(self._parent, self._action)

    def _refresh_available(self):
        """
        This function should define the rule to update the actions available. By default there is no specific rule.

        :return: current actions available and their remaining counts
        """

        if self.refresh_available is None:
            available_actions = copy.copy(self._parent.available_actions)
            available_actions[self._action] -= 1

            if not available_actions[self._action]:
                _ = available_actions.pop(self._action)

            return available_actions
        else:
            assert hasattr(self.refresh_available, '__call__') \
                   and self.refresh_available.__call__.__code__.co_argcount == 3
            return self.refresh_available(self._parent, self._action)


def mcts(root: TreeNode, options: Dict) -> List:
    """
    This function defines the Monte Carlo Tree search process.
    Different from the traditional MCTS implementation, we update the reward along the entire path to the leaf node in
    stead of the expanded node, since there is no interactive gaming scene in such background and thus the state of the
    decadents can be recorded to save computation.

    For the traditional MCTS edition with beam search algorithms, see bs.py

    :param root: the given root node
    :param options: a dict containing the MCTS process settings

    :return: a list of tuples containing schemes and their scores respectively
    """

    # restore some settings
    turns = options.get('turns', 100000)
    top_k = options.get('top_k', 10)

    # set up containers and also value monitor for result
    current_min = -math.inf
    result = dict()                      # a map from (list of choices,) to score

    # launch the trailing process
    for _ in tqdm.trange(turns, dynamic_ncols=True, desc='Trails',
                         bar_format='\033[1;7;32m{desc} \033[0;7;32m{n_fmt}\033[1;7;32m/\033[0;7;32m{total_fmt}\033[0m '
                                    '|{bar}| '
                                    '\033[1;32m{percentage:3.0f}\033[0;32m%\033[0m '
                                    '\033[1m[\033[32m{elapsed}\033[0m elapsed, '
                                    '\033[1;32m{remaining}\033[0m remain\033[1m]\033[0m'):
        current = root

        while not current.is_terminated():
            if current.is_fully_expanded():
                current = current.select()
            else:
                current = current.expand()

        current.update_all()

        if current.score <= current_min or tuple(sorted(current.history[:-1])) in result:
            continue
        else:
            if len(result) < top_k:
                current_min = math.inf if current_min == -math.inf else current_min

                result[tuple(sorted(current.history[:-1]))] = current.score
                current_min = min(current_min, current.score)
            else:
                for solution in result:
                    if result[solution] == current_min:
                        _ = result.pop(solution)
                        break

                result[tuple(sorted(current.history[:-1]))] = current.score

                current_min = math.inf
                for solution in result:
                    current_min = min(current_min, result[solution])

    return sorted(list(result.items()), key=lambda item: item[1], reverse=True)
