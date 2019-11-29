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
                         '\033[33;1mcomposite score\033[0m',
                         '\033[33;1mtotal desiring\033[0m',
                         '\033[33;1moverall discount\033[0m',
                         '\033[33;1mtotal cost\033[0m',
                         '\033[33;1mstrategy detail\033[0m']
    table.hrules = pt.ALL

    color = '\033[33m'

    for rank, proposal in enumerate(proposals):
        strategy, metrics = proposal

        for i in range(len(strategy)):
            if len(strategy[i]) > max_length:
                strategy[i] = strategy[i][:max_length] + '...'

        color = '\033[32m' if color == '\033[33m' else '\033[33m'

        table.add_row([color + '\033[1m{}\033[0m'.format(rank + 1),
                       color + '{:.2f}\033[0m'.format(metrics['score']),
                       color + '{:^2d}\033[0m'.format(metrics['total want']),
                       color + '{:.2f}%\033[0m'.format(100 * metrics['overall discount']),
                       color + '¥ {:,.2f}\033[0m'.format(metrics['total cost']),
                       color + (',\033[0m\n' + color).join(strategy) + '\033[0m'])

    table.align['strategy detail'] = 'l'

    print('')
    print(table)
