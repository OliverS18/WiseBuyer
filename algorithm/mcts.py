"""
This file implements the Monte Carlo Tree Search (MCTS) for optimal strategy search.

The MCTS algorithm here is referred to junxiaosong's implementation
(https://github.com/junxiaosong/AlphaZero_Gomoku/blob/master/mcts_pure.py)
Much thanks to the author.
"""


import math


class TreeNode:
    """
    A node in the MCTS tree. Each node keeps track of its own value Q and its visit-count score u.
    Throughout the class definition, `action` means the commodity to purchase.
    """

    def __init__(self, parent):
        self._parent = parent
        self._children = dict()                 # a map from action to TreeNode

        self._Q = 0
        self._u = 0

        self.n_visits = 0

    @property
    def uct(self):
        """
        Calculate and return the reward (UCT) for this node.
        It is a combination of leaf evaluations Q, and this node's prior adjusted for its visit count, u.
        """
        return self._Q + self._u

    def expand(self, actions):
        """
        Expand tree by creating new children.

        :param actions: a list of tuples of actions.
        """
        for action in actions:
            if action not in self._children:
                self._children[action] = TreeNode(self)

    def select(self):
        """
        Select action among children that gives maximum action value Q plus bonus u.

        :return: A tuple of (action, next_node)
        """
        return max(self._children.items(), key=lambda act_node: act_node[1].uct)

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

    def update_all(self, leaf_reward):
        """
        Like a call to update(), but applied recursively for all ancestors.
        """
        # If it is not root, this node's parent should be updated first.
        if self._parent:
            self._parent.update_all(leaf_reward)

        self.update(leaf_reward)

    def is_leaf(self):
        """
        Check if leaf node (i.e. no nodes below this have been expanded).
        """
        return self._children == {}

    def is_root(self):
        """
        Check if root node (i.e. no parents).
        """
        return self._parent is None

