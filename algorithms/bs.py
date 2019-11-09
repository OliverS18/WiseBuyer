"""
This file implemented the original Monte Carlo Tree Search where the update does not take effect after the random search
launched. To acquire a set of relatively good strategies instead of a best one, Beam Search is also adopted.
"""


import tqdm
import copy

from .mcts import TreeNode
from typing import *


def _mcts_step(root: TreeNode, turns: int, bar_options: Dict) -> bool:
    if root.is_terminated():
        return True

    root.as_root()

    for _ in tqdm.trange(turns,
                         dynamic_ncols=True, desc=bar_options['title'], position=bar_options['offset'], leave=False):
        current = root
        while not current.is_leaf():
            current = current.select()

        update_root = current
        while not current.is_fully_expanded():
            current.expand()
        else:
            search_root = current.select()

        current = search_root
        while not current.is_terminated():
            current = current.expand()

        update_root.update_all(current.score)
        search_root.reset()

    return False


def beam_search(root: TreeNode, options: Dict) -> List:
    """
    This function defines the Monte Carlo Tree search process following the traditional update strategy with beam
    search included.

    :param root: the given root node
    :param options: a dict containing the MCTS process settings

    :return: a list of tuples containing schemes and their scores respectively
    """

    # restore some settings
    turns_per_step = options.get('turns', 100)
    max_n_actions = options.get('max_n_actions', 'inf')

    beam_size = options.get('beam_size', 10)
    top_k = options.get('top_k', 10)

    assert beam_size >= top_k

    # set up flags indicating the searching status
    step = 0

    # launch the searching process
    with tqdm.tqdm(total=max_n_actions if max_n_actions != 'inf' else None, dynamic_ncols=True, desc='Step') as bar:
        # launch the first step
        all_finished = _mcts_step(root, turns_per_step, {'offset': 2, 'title': 'First step'})

        beams = sorted(root.children, key=lambda node: node.score, reverse=True)    # beams is a list of latest nodes.
        if len(beams) > beam_size:
            beams = beams[:beam_size]

        step += 1
        bar.update()

        # launch the remaining steps
        while not all_finished and step < max_n_actions:
            # record status
            prev_beams = copy.copy(beams)
            all_finished = True

            # do for each candidate in beam
            for i, current in tqdm.tqdm(enumerate(prev_beams),
                                        dynamic_ncols=True, desc='Step {}'.format(step), position=2, leave=False):
                # MCTS
                all_finished = all_finished \
                           and _mcts_step(current, turns_per_step, {'offset': 4, 'title': 'Candidate {}'.format(i)})

                # enrich candidates
                beams += current.children

            # update beams
            beams = sorted(beams, key=lambda node: node.score, reverse=True)
            if len(beams) > beam_size:
                beams = beams[:beam_size]

            # update status
            step += 1
            bar.update()

        if step < max_n_actions:
            bar.update(max_n_actions - step)
            print('Searching process terminated in advance at step {}'.format(step))

    return sorted([(node.history[:-1], node.score) for node in beams[:top_k]], key=lambda item: item[1], reverse=True)
