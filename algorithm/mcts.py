"""
This file implements the Monte Carlo Tree Search (MCTS) for optimal strategy search.

The MCTS algorithm here is based on junxiaosong's implementation
(https://github.com/junxiaosong/AlphaZero_Gomoku/blob/master/mcts_pure.py)
and tobegit3hub's implementation
(https://github.com/tobegit3hub/ml_implementation/blob/master/monte_carlo_tree_search/mcst_example.py)
Much thanks to the author.
"""


import math
import copy
import random
import tqdm
import inspect
from typing import *


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
        self._parent = parent
        self._children = dict()                 # a map from action to TreeNode

        # check validation
        if self.is_root():
            assert action is None

            for args in [available_actions, cost, limit]:
                assert args is not None
        else:
            assert prehistory is None

        # state information
        self._action = action

        self._Q = 0
        self._u = 0
        self.n_visits = 0

        # temps passed to properties
        self._prehistory = prehistory
        self._cost = cost
        self._limit = limit
        self._available_actions = available_actions

        # api for evaluation function
        self._eval = None

    @property
    def available_actions(self):
        """
        return a map from the currently available actions to their remaining counts.
        """

        if self._available_actions is not None:
            assert '*STOP*' in self._available_actions
            return self._available_actions
        else:
            return self._refresh_available()

    @property
    def terminate_limit(self):
        """
        return the terminate condition beyond which the simulation will terminated.
        """

        return self._limit if self._limit is not None else self._refresh_limit()

    @property
    def cost(self):
        """
        return the cost dictionary of each action.
        """

        return self._cost if self._cost is not None else self._refresh_cost()

    @property
    def history(self):
        """
        return the history of actions (states) along the searching path.
        """

        if self.is_root():
            return self._prehistory or list()
        else:
            return self._parent.history + [self._action]

    @property
    def v(self):
        """
        return the cumulative cost along the searching path.
        """

        return 0 if self.is_root() else self._refesh_v()

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
        return the reward acquired before current node.
        """

        assert inspect.isfunction(self._eval)
        return self._eval(self.history[:-1])

    def register_eval(self, func):
        """
        register a function as self's eval function.

        :param func: a handle of a func
        """

        assert inspect.isfunction(func)
        self._eval = func

    def expand(self):
        """
        Expand tree by creating new children.

        :return: next new node
        """

        if not self.is_terminated():
            space = self.available_actions.keys() - self._children.keys()
            action = random.choice(list(space))

            self._children[action] = self.__class__(self, action)
            return self._children[action]

    def select(self):
        """
        Select action among children that gives maximum action value Q plus bonus u.

        :return: next best node according to uct
        """

        return max(self._children.values(), key=lambda act_node: act_node.uct)

    def update(self, leaf_reward, c_puct=math.sqrt(0.5)):
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
        self._u = c_puct * math.sqrt(math.log(self._parent.n_visits + 1) / self.n_visits)

    def update_all(self, leaf_reward=None):
        """
        Like a call to update(), but applied recursively for all ancestors.

        :param leaf_reward: the reward of subtree evaluation.
        """

        # calculate the leaf_reward
        leaf_reward = leaf_reward or self.score

        # If it is not root, this node's parent should be updated first.
        if self._parent:
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

        return len(self._children) == len(self.available_actions)

    def is_terminated(self):
        """
        Check if the simulation has finished (i.e. total cost sum has exceeded the limit or all actions adopted).
        """

        return self.available_actions == {} or self.v > self.terminate_limit or self._action == '*STOP*'

    # overwritable methods
    def _refresh_cost(self):
        """
        This function should define the rule to update the cost of each commodity. By default there is no specific rule.

        :return: updated cost of each commodity
        """

        return self._parent.cost

    def _refresh_limit(self):
        """
        This function should define the rule to update the termination condition. By default there is no specific rule.

        :return: updated termination condition
        """

        return self._parent.terminate_limit

    def _refesh_v(self):
        """
        This function should define the rule to update the cumulative cost value. By default there is no specific rule.

        :return: updated cumulative cost value
        """

        return self._parent.v + self.cost[self._action]

    def _refresh_available(self):
        """
        This function should define the rule to update the actions available. By default there is no specific rule.

        :return: current actions available and their remaining counts
        """

        available_actions = copy.copy(self._parent.available_actions)
        available_actions[self._action] -= 1

        if not available_actions[self._action]:
            _ = available_actions.pop(self._action)

        return available_actions


def mcts(root: TreeNode, options: Dict) -> List:
    """
    This function defines the Monte Carlo Tree search process.
    Different from the traditional MCTS implementation, we update the reward along the entire path to the leaf node in
    stead of the expanded node, since there is no interactive gaming scene in such background and thus the state of the
    decadents can be recorded to save computation.

    For the traditional MCTS edition with beam search algorithm, see bs.py

    :param root: the given root node
    :param options: a dict containing the MCTS process settings

    :return: a list of tuples containing schemes and their scores respectively
    """

    # restore some settings
    turns = options.get('turns', 100000)
    top_k = options.get('top_k', 10)

    # set up containers and also value monitor for result
    current_min = -math.inf
    result = set()

    # launch the trailing process
    for _ in tqdm.trange(turns, dynamic_ncols=True, desc='Trails'):
        current = root
        while not current.is_terminated():
            if current.is_fully_expanded():
                current = current.select()
            else:
                current = current.expand()

        current.update_all()

        if current.score <= current_min:
            continue
        else:
            if len(result) < top_k:
                current_min = math.inf if current_min == -math.inf else current_min

                result.add((current.history[:-1], current.score))
                current_min = min(current_min, current.score)
            else:
                for solution in result:
                    if solution[1] == current_min:
                        result.remove(solution)
                        break

                result.add((current.history[:-1], current.score))

                current_min = math.inf
                for solution in result:
                    current_min = min(current_min, solution[1])

    return sorted(list(result), key=lambda item: item[1], reverse=True)
