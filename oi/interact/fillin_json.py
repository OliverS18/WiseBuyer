"""
This scheme generates a json of default settings according to the parsed cart information and requires user to modify
it according to his/her willing.
"""


import json
import os
from typing import *
import time

from ..config import cfg


class UserOption:
    def __init__(self, arguments):
        self.preset = arguments

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

    def restore_prev(self) -> NoReturn:
        if os.path.isfile(os.path.join(cfg.io.temp_path, cfg.io.user_json)):
            self.options, self.want = json.load(open(os.path.join(cfg.io.temp_path, cfg.io.user_json)))
            print('\033[0;32mSuccefuly loaded previous options.\033[0m')
        else:
            print('\033[0;33mPrevious options not found.\033[0m')

    def reload_cart(self) -> NoReturn:
        if os.path.isfile(os.path.join(cfg.io.temp_path, cfg.io.cart_json)):
            self.commodities = json.load(open(os.path.join(cfg.io.temp_path, cfg.io.cart_json)))[0]
            self.want = {commodity: self.commodities[commodity][1] for commodity in self.commodities}
        else:
            print('\033[0;33mCart json not presented as expected.\033[0m')

        self.save_json()

        if not self.preset.use_default:
            print('\33[?25h', end='')
            _ = input('\n\033[0;34mNow please check \033[0;4m{}\033[0;34m to assign want scores for your desired '
                      'commodities. The scores is recommended in range 0 ~ 5 with \033[1;34mhigher\033[0;34m means '
                      '\033[1;34mmore desirable\033[0;34m.\nWhen finished or just intending to taking no account to '
                      'the subjective desiring score, press \033[36menter\033[34m to continue:\033[8m'
                      .format(os.path.join(cfg.io.temp_path, cfg.io.user_json)))

        print('\033[0m\33[?25l', end='')

        print('\n\033[0;32mOptions specified succesfully.\033[0m\n')

    def parse_options(self) -> NoReturn:
        if self.preset.budget is None:
            print('\33[?25h', end='')

            try:
                self.options['budget'] = float(input('\n\033[0;34mPlease specify your budget:\033[36;1m '))
                assert self.options['budget'] >= 0
            except (ValueError, AssertionError):
                while True:
                    try:
                        self.options['budget'] = float(
                            input('\033[0;33m\tInvalid input received. Sepecify again:\033[36;1m '))
                        assert self.options['budget'] >= 0
                        break
                    except (ValueError, AssertionError):
                        continue
        else:
            self.options['budget'] = self.preset.budget
            print('\nBudget set as \033[32;1m{}\033[0m.'.format(self.preset.budget))

        print('\33[?25l', end='')

        if self.preset.elaborate is None:
            if not self.preset.use_default:
                print('\33[?25h', end='')

                try:
                    turns = input('\n\033[0;34mPlease specify a number within 10 ~ 10000 representing how elaborate the '
                                  'program is expected to be.\n\033[0;34mLarger means expecting better solution, while '
                                  'costing more time. Default as \033[36m1000\033[34m:\033[36;1m ')
                    if turns:
                        self.options['turns'] = int(turns)
                        assert 10 <= self.options['turns'] <= 10000
                    else:
                        self.options['turns'] = 1000
                except (ValueError, AssertionError):
                    while True:
                        try:
                            turns = input('\033[0;33m\tInvalid input received. Please leave blank if intending to use '
                                          'default value \033[36m1000\033[33m, or sepecify again:\033[36;1m ')

                            if turns:
                                self.options['turns'] = int(turns)
                                assert 10 <= self.options['turns'] <= 10000
                            else:
                                self.options['turns'] = 1000

                            break
                        except (ValueError, AssertionError):
                            continue
            else:
                self.options['turns'] = 1000
        else:
            self.options['turns'] = self.preset.elaborate

        print('\33[?25l', end='')

        if self.preset.display_num is None:
            if not self.preset.use_default:
                print('\33[?25h', end='')

                try:
                    top_k = input('\n\033[0;34mPlease specify the number of strategies you would like to be shown. Default '
                                  'as \033[36m10\033[34m:\033[36;1m ')
                    if top_k:
                        self.options['top_k'] = int(top_k)
                        assert self.options['top_k'] > 0
                    else:
                        self.options['top_k'] = 10
                except (ValueError, AssertionError):
                    while True:
                        try:
                            top_k = input('\033[0;33m\tInvalid input received. Please leave blank if intending to use '
                                          'default value \033[36m10\033[33m, or sepecify again:\033[36;1m ')

                            if top_k:
                                self.options['top_k'] = int(top_k)
                                assert self.options['top_k'] > 0
                            else:
                                self.options['top_k'] = 10

                            break
                        except (ValueError, AssertionError):
                            continue
            else:
                self.options['top_k'] = 10
                print('\nTop \033[32;1m10\033[0m solutions will be predicted.')
        else:
            self.options['top_k'] = self.preset.display_num
            print('\nTop \033[32;1m{}\033[0m solutions will be predicted.'.format(self.preset.display_num))

        date = None
        if self.preset.date is None:
            if not self.preset.use_default:
                print('\33[?25h', end='')

                try:
                    date = str(input('\n\033[0;34mPlease specify the date to buy the items.\n'
                                     'Please follow the format of `yyyy.mm.dd`, default as \033[36mtoday\033[34m: '
                                     '\033[36;1m'))
                    if date:
                        date = time.strptime(date, '%Y.%m.%d')
                    else:
                        date = time.localtime()
                except ValueError:
                    while True:
                        try:
                            date = str(input('\033[0;33m\tInvalid input received. Sepecify again:\n'
                                             '\tPlease leave blank if intending to use default value \033[36mtoday'
                                             '\033[33m, or follow the format of `yyyy.mm.dd`, e.g. 2019.11.29:\033[36;1m '))
                            if date:
                                date = time.strptime(date, '%Y.%m.%d')
                            else:
                                date = time.localtime()

                            break
                        except ValueError:
                            continue
            else:
                date = time.localtime()
                print('\nThe program will consider discount on \033[32;1m{}\033[0m.'
                      .format(time.strftime('%b %d (%A), %Y')))
        else:
            date = self.preset.date
            print('\nThe program will consider discount on \033[32;1m{}\033[0m.'.format(time.strftime('%b %d (%A), %Y',
                                                                                                       date)))

        self.options['frugality'] = self.preset.frugality if self.preset.frugality is not None else 0

        print('\33[?25l')

        return date

    def save_json(self) -> NoReturn:
        json.dump((self.options, self.want),
                  open(os.path.join(cfg.io.temp_path, cfg.io.user_json), 'w'),
                  ensure_ascii=False,
                  indent=4)
