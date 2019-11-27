"""
This file defines the visualization effect in the terminal.
"""


import prettytable as pt
import json
import os
from typing import *

from ..config import cfg


def visualize(max_length=60) -> NoReturn:
    proposals = json.load(open(os.path.join(cfg.io.temp_path, cfg.io.output_json)))

    table = pt.PrettyTable()
    table.field_names = ['\033[33;1mrank\033[0m',
                         '\033[32;1mcomposite score\033[0m',
                         '\033[32;1mtotal desiring\033[0m',
                         '\033[32;1moverall discount\033[0m',
                         '\033[32;1mtotal cost\033[0m',
                         '\033[32;1mstrategy detail\033[0m']
    table.hrules = pt.ALL

    for rank, proposal in enumerate(proposals):
        strategy, metrics = proposal

        for i in range(len(strategy)):
            if len(strategy[i]) > max_length:
                strategy[i] = strategy[i][:max_length] + '...'

        table.add_row(['\033[33;1m{}\033[0m'.format(rank + 1),
                       '\033[32m{:.2f}\033[0m'.format(metrics['score']),
                       '\033[32m{:^2d}\033[0m'.format(metrics['total want']),
                       '\033[32m{:.2f}%\033[0m'.format(100 * metrics['overall discount']),
                       '\033[32m¥ {:,.2f}\033[0m'.format(metrics['total cost']),
                       '\033[32m' + ',\033[0m\n\033[32m'.join(strategy) + '\033[0m'])

    table.align['strategy detail'] = 'l'

    print('\n')
    print(table)
