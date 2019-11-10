"""
This file is the main entrance API of the service.
"""


import os

import oi
from oi import cfg
import algorithms as algos
import rules


def service():
    """
    This function reads configuration from cfg and do calculation according to the config file and cached json file to
    propose a set of sensible strategies. The result will be cached also into a json file according to the config file.
    """

    # parse information from cache
    price, count, discount, want, scheme, option = oi.input_json(cart_json=os.path.join(cfg.io.temp_path,
                                                                                        cfg.io.cart_json),
                                                                 user_json=os.path.join(cfg.io.temp_path,
                                                                                        cfg.io.user_json))

    # set up workers
    discounter = rules.coupon[option.coupon_scheme](scheme_of_commodities=scheme, price=price)
    scorer = rules.score[option.get('eval_metric', 'maoh')](lambd=option.get('frugality', 0.1),
                                                           count=count,
                                                           original_discount=discount,
                                                           want_score=want,
                                                           price=dict(map(lambda item: (item[0],
                                                                                        item[1] + discount[item[0]]),
                                                                          price.items())),
                                                           budget=option.budget)

    root_node = algos.TreeNode(available_actions=count, cost=price, limit=option.budget)
    root_node.register('eval', scorer)
    root_node.register('refresh_v', discounter)

    # launch scheme proposal searching
    result = algos.algo_set[option.get('algorithm', 'mcts')](root_node, option)

    # write the result into temp file
    oi.output_json(result, os.path.join(cfg.io.temp_path, cfg.io.output_json), scorer, discounter)
