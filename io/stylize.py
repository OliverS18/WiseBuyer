"""
This file takes the json-ed string and stylized them into dicts which can be processed by the rest part of the project.
"""


import os
import json
from typing import *
from easydict import EasyDict

from rules.crit import Reward
from rules.discount import Discount
from .config import cfg


def input_json(cart_json: str, user_json: str) -> Tuple[Dict, Dict, Dict, Dict, EasyDict]:
    """
    This function takes in all the information represented as json serialized strings, and then distribute them into
    multiple dicts used in different scenario.

    :param cart_json: path to a json serialized string parsed from web representing information of commodities.
        a typical item of the dict carried by the json string would be like:
        {commodity_name: [original_price, discounted_price, preferred_amount]}.
    :param user_json: path to a json serialized string parsed from the user interface representing user-defined arguments.
        there would be two part forming the list carried by the json string:
        [{algorithm_options_name: corresponding_value}, {commodity_name: want_score}]

    :return: a list of dict containing price, desired amount, commodity-wise discount in currency (rather than
        percentage), want score as well as the options for algorithms (as easydict).
    """

    cart_dict = json.load(open(cart_json))
    want, option = json.load(open(user_json))

    price = dict()
    amount = dict()
    discount = dict()

    for commodity, data in cart_dict.items():
        price[commodity] = data[1]
        amount[commodity] = data[2]
        discount[commodity] = data[0] - data[1]

    return price, amount, discount, want, EasyDict(option)


def output_json(strategies: List[Tuple], cache_path: str, commentator: Reward, calculator: Discount):
    """
    This function saves the proposed strategy into a json file.

    :param strategies: a list of strategies. each item within the list should follow the format as:
            ([commodity_name], strategy_score)
    :param commentator: a reward object used to be called to acquire enriched description about the given strategies
    :param calculator: a discount calculator object used to be called by commentator
    :param cache_path: the temp path to place the output json file
    """

    enriched = commentator.summarize(strategies, calculator)
    json.dump(enriched, open(os.path.join(cfg.io.temp_path, cache_path, 'w')))
