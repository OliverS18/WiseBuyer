"""
This scheme generates a json of default settings according to the parsed cart information and requires user to modify
it according to his/her willing.
"""


import json
import os
from typing import *

from ..config import cfg


class UserOption:
    def __init__(self):
        self.width = os.get_terminal_size()[0]

        self.options = {
            "coupon_scheme": "tmall",
            "eval_metric": "amoha",
            "frugality": 0,
            "budget": 1600.0,
            "algorithm": "mcts",
            "turns": 3000,
            "top_k": 10,
            # "beam_size":        30,
            # "max_n_actions":    120
        }
        self.commodities = list()
        self.want = dict()

        self.reload_cart()

    def restore_prev(self) -> NoReturn:
        if os.path.isfile(os.path.join(cfg.io.temp_path, cfg.io.user_json)):
            self.options, self.want = json.load(open(os.path.join(cfg.io.temp_path, cfg.io.user_json)))
            print('\033[0;32mSuccefuly loaded previous options.\033[0m')
        else:
            print('\033[0;33mPrevious options not found.\033[0m')

    def reload_cart(self) -> NoReturn:
        if os.path.isfile(os.path.join(cfg.io.temp_path, cfg.io.cart_json)):
            self.commodities = json.load(open(os.path.join(cfg.io.temp_path, cfg.io.cart_json)))[0].keys()
            self.want = {commodity: 5 for commodity in self.commodities}
        else:
            print('\033[0;33mCart json not presented as expected.\033[0m')

    def parse_options(self) -> NoReturn:
        self.options['budget'] = float(input('\n\033[0;34mPlease specify your budget:\033[36;1m '))
        while self.options['budget'] < 0:
            self.options['budget'] = float(input('\033[0;33m\tInvalid input received. Sepecify again:\033[36;1m '))

        self.options['turns'] = int(input('\n\033[0;34mPlease specify a number within 0 ~ 10000 representing how '
                                          'elaborate the program is expected to be.\n\033[0;34mLarger means expecting '
                                          'better solution, while costing more time:\033[36;1m '))
        while self.options['turns'] < 0 or self.options['turns'] > 10000:
            self.options['turns'] = float(input('\033[0;33m\tInvalid input received. Sepecify again:\033[36;1m '))

        self.options['top_k'] = int(input('\n\033[0;34mPlease specify the number of strategies you would like to be '
                                          'shown:\033[36;1m '))
        while self.options['top_k'] <= 0:
            self.options['top_k'] = float(input('\033[0;33m\tInvalid input received. Sepecify again:\033[36;1m '))

        self.save_json()
        _ = input('\n\033[0;34mNow please check \033[0;4m{}\033[0;34m to assign want scores for your desired '
                  'commodities. The scores is recommended in range 0 ~ 5 with \033[1;34mhigher\033[0;34m means '
                  '\033[1;34mmore desirable\033[0;34m.\nWhen finished or just intending to taking no account to the '
                  'subjective desiring score, please type anything here to continue:\033[36;1m '
                  .format(os.path.join(cfg.io.temp_path, cfg.io.user_json)))

        print('\n\033[1;32mOptions specified succesfully. If you want to modify more configurations, please check '
              '\033[0;4m{}\033[0;1;32m and edit as you want.\033[0m'.format(os.path.join(cfg.io.temp_path,
                                                                                         cfg.io.user_json)))

    def save_json(self) -> NoReturn:
        json.dump((self.options, self.want),
                  open(os.path.join(cfg.io.temp_path, cfg.io.user_json), 'w'),
                  ensure_ascii=False,
                  indent=4)
