"""
This package contains some basic algorithms to solve the strategy searching problem.
"""


from .mcts import mcts, TreeNode
from .bs import beam_search


algo_set = {'mcts':    mcts,
            'bs':      beam_search}
