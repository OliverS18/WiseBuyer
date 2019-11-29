#! /usr/bin/env python

"""
This file is the main entrance API of the service.
"""


import os
import json

import oi
from oi import cfg
from oi.interact import arguments as args
import algorithms as algos
import rules


def service():
    """
    This function reads configuration from cfg and do calculation according to the config file and cached json file to
    propose a set of sensible strategies. The result will be cached also into a json file according to the config file.
    """

    print('\n\033[35;1m' + oi.logo + '\033[0m')

    print('\n\n\033[35;1;7mProposal generation launched.\033[0m\n')
    if not os.path.isdir(cfg.io.temp_path):
        os.mkdir(cfg.io.temp_path)

    if not args.use_local:
        # crawl cart information
        print('\n\033[35;1mSimulated web browser environment launched.\033[0m')
        with oi.TaobaoBrowser() as crawler:
            json.dump(crawler.crawl(),
                      open(os.path.join(cfg.io.temp_path, cfg.io.cart_json), 'w'),
                      ensure_ascii=False,
                      indent=4)
    else:
        assert os.path.isfile(os.path.join(cfg.io.temp_path, cfg.io.cart_json)), \
            '\033[31;7;1mLocal cart json file is specified in usage but not found in path' \
            '\033[0;31;4m {}. \033[31;7;1Process terminated.\033[0m'\
            .format(os.path.join(cfg.io.temp_path, cfg.io.cart_json))
        print('\n\033[32;1mCart information acquired from local file \033[0;4m{}\033[0;1;32m.\033[0m'
              .format(os.path.join(cfg.io.temp_path, cfg.io.cart_json)))

    # use newly-defined options
    print('\n\033[35;1mReceiving options from User...\033[0m')
    oi.interact.UserOption(args).parse_options()

    # parse information from cache
    print('\n\033[35;1mPreparing component...\033[0m')
    price, count, discount, want, scheme, shop, coupon, option = oi.input_json(cart_json=os.path.join(cfg.io.temp_path,
                                                                                                      cfg.io.cart_json),
                                                                               user_json=os.path.join(cfg.io.temp_path,
                                                                                                      cfg.io.user_json))

    # set up workers
    discounter = rules.coupon[option.coupon_scheme](scheme_of_commodities=scheme,
                                                    price=price,
                                                    shop_of_commodities=shop,
                                                    shopwise_coupon=coupon)
    print('\n\033[0mDiscount calculator component established.\033[0m')

    scorer = rules.score[option.get('eval_metric', 'amoha')](lambd=option.get('frugality', 0.1),
                                                             count=count,
                                                             original_discount=discount,
                                                             want_score=want,
                                                             price=dict(map(lambda item: (item[0],
                                                                                          item[1] + discount[item[0]]),
                                                                            price.items())),
                                                             budget=option.budget,
                                                             discounter=discounter)
    print('\n\033[0mEvaluation metric component established.\033[0m')

    root_node = algos.TreeNode(available_actions=count, cost=price, limit=option.budget)
    print('\n\033[0mSearching structure component established.\033[0m')

    root_node.register('eval', scorer)
    root_node.register('refresh_v', discounter)
    print('\n\033[32mComponents organized successfully.\033[0m\n')

    # launch scheme proposal searching
    print('\n\033[35;1mSearching process launched.\033[0m\n')
    result = algos.algo_set[option.get('algorithm', 'mcts')](root_node, option)
    print('\n')

    # write the result into temp file
    oi.output_json(result, os.path.join(cfg.io.temp_path, cfg.io.output_json), scorer)

    # and visualize it through the terminal
    print('\n\033[35;1mSearching process finished. Results are displayed as follows:\033[0m')
    oi.interact.visualize()
    print('\n\033[32mSearching result can also be found at \033[0;4m{}\033[0m.\n'
          .format(os.path.join(cfg.io.temp_path, cfg.io.output_json)))
    print('\n\033[35;1;7mProgram finished.\033[0m\n')


if __name__ == '__main__':
    service()
